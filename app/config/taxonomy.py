"""Domain enum for job and resume classification."""

from __future__ import annotations

from enum import Enum


class Domain(str, Enum):
    ENGINEERING = "Engineering"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    DESIGN = "Design"
    LEGAL = "Legal"
    SALES_MARKETING = "Sales & Marketing"
