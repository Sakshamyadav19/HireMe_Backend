"""Save and paginate match results from match_result_cache table."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.match_result_cache import MatchResultCache
from app.schemas.matching import MatchResult, MatchResultsCursorResponse


def clear_match_results_for_user(db: Session, user_id: str) -> None:
    """Delete the cached match result for this user (e.g. on logout)."""
    db.query(MatchResultCache).filter(MatchResultCache.user_id == user_id).delete()
    db.commit()


def save_match_results(
    db: Session,
    user_id: str,
    total_matches: int,
    matches: list[MatchResult],
) -> None:
    """Upsert latest match result for user. Replaces any existing row."""
    payload = [m.model_dump() for m in matches]
    row = db.query(MatchResultCache).filter(MatchResultCache.user_id == user_id).first()
    if row:
        row.total_matches = total_matches
        row.matches_json = payload
    else:
        row = MatchResultCache(
            user_id=user_id,
            total_matches=total_matches,
            matches_json=payload,
        )
        db.add(row)
    db.commit()


def get_match_results_page(
    db: Session,
    user_id: str,
    *,
    cursor: str | None = None,
    limit: int = 50,
    dir: str = "next",
) -> MatchResultsCursorResponse | None:
    """
    Return one page of matches for the user. Cursor is integer offset as string.
    dir=next: slice from cursor (default 0); dir=prev: cursor is current start, return previous page.
    Returns None if no cached result for user.
    """
    row = db.query(MatchResultCache).filter(MatchResultCache.user_id == user_id).first()
    if not row or not row.matches_json:
        return None
    total = row.total_matches
    matches_list = [MatchResult.model_validate(d) for d in row.matches_json]
    limit = max(1, min(limit, 100))

    if dir == "prev":
        if not cursor:
            return None
        try:
            start = int(cursor)
        except ValueError:
            return None
        # Previous page: [max(0, start - limit) : start]
        page_start = max(0, start - limit)
        page_end = start
        slice_matches = matches_list[page_start:page_end]
        next_cursor = str(start) if start < total else None
        prev_cursor = str(page_start) if page_start > 0 else None
    else:
        start = 0
        if cursor:
            try:
                start = int(cursor)
            except ValueError:
                start = 0
        page_end = min(start + limit, total)
        slice_matches = matches_list[start:page_end]
        next_cursor = str(start + limit) if start + limit < total else None
        prev_cursor = str(start) if start > 0 else None

    return MatchResultsCursorResponse(
        total_matches=total,
        matches=slice_matches,
        next_cursor=next_cursor,
        prev_cursor=prev_cursor,
    )
