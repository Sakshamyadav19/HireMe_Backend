#!/usr/bin/env python3
"""Generate jobs.sample.json with 500 jobs: global mix of domains, locations, and roles."""

from __future__ import annotations

import json
import random
from pathlib import Path

DOMAINS = [
    ("Engineering", ["Backend", "Frontend", "ML/AI", "DevOps", "Data Engineering", "Security", "Mobile", ""]),
    ("Finance", ["Investment Banking", "FP&A", "Quant", "Risk", "Treasury", ""]),
    ("Healthcare", ["Research", "Nursing", "Clinical", "Pharma", "Health Tech", ""]),
    ("Design", ["Product Design", "UX Research", "Visual Design", "Design Systems", ""]),
    ("Legal", ["Corporate", "Litigation", "IP", "Compliance", ""]),
    ("Sales & Marketing", ["Enterprise Sales", "Content", "Growth", "Brand", "Demand Gen", ""]),
]

LOCATIONS = [
    ("San Francisco, CA", "USA"),
    ("New York, NY", "USA"),
    ("Seattle, WA", "USA"),
    ("Austin, TX", "USA"),
    ("Boston, MA", "USA"),
    ("Chicago, IL", "USA"),
    ("Los Angeles, CA", "USA"),
    ("Denver, CO", "USA"),
    ("Washington, DC", "USA"),
    ("Houston, TX", "USA"),
    ("Remote", "USA"),
    ("London, UK", "GBR"),
    ("Manchester, UK", "GBR"),
    ("Berlin, Germany", "DEU"),
    ("Munich, Germany", "DEU"),
    ("Bangalore, India", "IND"),
    ("Mumbai, India", "IND"),
    ("Hyderabad, India", "IND"),
    ("Toronto, Canada", "CAN"),
    ("Vancouver, Canada", "CAN"),
    ("Sydney, Australia", "AUS"),
    ("Melbourne, Australia", "AUS"),
    ("Singapore", "SGP"),
    ("Tokyo, Japan", "JPN"),
    ("Paris, France", "FRA"),
    ("Amsterdam, Netherlands", "NLD"),
    ("Dublin, Ireland", "IRL"),
    ("Dubai, UAE", "ARE"),
    ("Tel Aviv, Israel", "ISR"),
    ("Stockholm, Sweden", "SWE"),
    ("Zurich, Switzerland", "CHE"),
    ("Hong Kong", "HKG"),
    ("Remote", "GBR"),
    ("Remote", "IND"),
    ("Remote", "DEU"),
]

COMPANIES = [
    "TechCorp", "DesignLab", "AI Startup", "Capital Partners", "CreativeHQ", "CloudNine", "DataFlow Inc",
    "MedResearch", "ScaleSales", "ScaleUp", "Merchant Bank Co", "UserInsight", "SecureNet", "Barrister LLP",
    "BrandVoice", "AppWorks", "Growth Finance", "City General Hospital", "AcquireCo", "Nexus Labs", "Vertex Systems",
    "Apex Consulting", "Pinnacle Health", "Summit Capital", "Horizon Media", "Catalyst Tech", "Fusion Design",
    "Prime Analytics", "Core Solutions", "Elite Legal", "NextGen Pharma", "Bright Marketing", "Swift Engineering",
    "Global Finance Co", "Metro Hospital Group", "Digital First", "Innovate Labs", "Pacific Ventures", "Nordic Bank",
    "Asia Tech Hub", "Euro Design Studio", "London Markets", "Berlin Health", "Sydney Finance", "Toronto Digital",
    "Singapore Innovations", "Dubai Ventures", "Tel Aviv Tech", "Stockholm Labs", "Zurich Capital",
]

TITLE_TEMPLATES = {
    "Engineering": [
        "Senior Backend Engineer", "Frontend Developer", "ML Engineer", "DevOps Engineer", "Data Engineer",
        "Security Engineer", "Full Stack Engineer", "Mobile Developer (iOS)", "Mobile Developer (Android)",
        "Site Reliability Engineer", "Cloud Architect", "Software Engineer", "Staff Engineer", "Principal Engineer",
    ],
    "Finance": [
        "Financial Analyst", "Investment Banking Analyst", "FP&A Analyst", "Quant Analyst", "Risk Analyst",
        "Treasury Analyst", "Finance Manager", "VP Finance", "Controller",
    ],
    "Healthcare": [
        "Clinical Research Associate", "Registered Nurse (ICU)", "Medical Writer", "Healthcare Data Analyst",
        "Clinical Project Manager", "Regulatory Affairs Specialist", "Pharmacovigilance Associate",
    ],
    "Design": [
        "Product Designer", "UX Researcher", "Visual Designer", "Design Lead", "UX Designer", "Design Manager",
    ],
    "Legal": [
        "Corporate Counsel", "Litigation Associate", "IP Attorney", "Compliance Officer", "Legal Counsel",
    ],
    "Sales & Marketing": [
        "Enterprise Sales Representative", "Content Marketing Manager", "Growth Marketing Lead",
        "Brand Manager", "Demand Generation Manager", "Sales Development Representative", "Account Executive",
    ],
}

SKILLS_BY_DOMAIN = {
    "Engineering": [
        ["Python", "PostgreSQL", "AWS", "REST APIs", "Docker"],
        ["React", "TypeScript", "JavaScript", "HTML", "CSS"],
        ["Python", "PyTorch", "TensorFlow", "AWS", "Docker"],
        ["AWS", "Terraform", "Kubernetes", "Docker", "CI/CD"],
        ["Python", "SQL", "Apache Spark", "Snowflake", "dbt"],
        ["AWS", "Linux", "Python", "Security Auditing", "Networking"],
        ["React", "Python", "Node.js", "PostgreSQL", "AWS"],
        ["Swift", "iOS", "REST APIs", "Git"],
        ["Kotlin", "Android", "REST APIs", "Jetpack"],
    ],
    "Finance": [
        ["Financial Modeling", "Excel", "SQL", "Bloomberg Terminal"],
        ["Financial Modeling", "Excel", "VBA", "Valuation"],
        ["Financial Modeling", "Excel", "Budgeting", "Power BI"],
        ["Python", "Quantitative Modeling", "Statistics", "Risk"],
    ],
    "Healthcare": [
        ["Clinical Trials", "GCP", "Protocol Compliance", "Data Management"],
        ["Critical Care", "ACLS", "Patient Assessment", "Documentation"],
        ["Medical Writing", "Regulatory", "ICH Guidelines"],
    ],
    "Design": [
        ["Figma", "Prototyping", "User Research", "Design Systems"],
        ["User Research", "Usability Testing", "Survey Design", "Figma"],
    ],
    "Legal": [
        ["Contract Law", "Compliance", "Corporate Governance", "Negotiation"],
        ["Legal Research", "Writing", "Discovery", "Court Procedures"],
    ],
    "Sales & Marketing": [
        ["Enterprise Sales", "CRM", "Negotiation", "Pipeline Management"],
        ["Content Strategy", "SEO", "Google Analytics", "Copywriting"],
        ["Paid Acquisition", "Meta Ads", "Google Ads", "A/B Testing"],
    ],
}

REMOTE_OPTIONS = ["remote", "hybrid", "onsite"]
SALARY_BANDS = [
    (60_000, 95_000),
    (70_000, 110_000),
    (85_000, 130_000),
    (100_000, 150_000),
    (120_000, 180_000),
    (140_000, 200_000),
    (160_000, 240_000),
    (180_000, 280_000),
]


def pick(lst):
    return random.choice(lst)


def generate_job(index: int) -> dict:
    domain, subdomains = pick(DOMAINS)
    subdomain = pick(subdomains)
    titles = TITLE_TEMPLATES.get(domain, TITLE_TEMPLATES["Engineering"])
    title = pick(titles)
    company = pick(COMPANIES)
    location, country = pick(LOCATIONS)
    remote = pick(REMOTE_OPTIONS)
    band = pick(SALARY_BANDS)
    salary_min = random.randint(band[0], band[1] - 20000) if band[1] - band[0] > 20000 else band[0]
    salary_max = random.randint(salary_min + 15000, band[1] + 10000)
    yoe_min = random.choice([0, 1, 2, 3, 4, 5, 6, 7])
    yoe_max = min(99, yoe_min + random.randint(2, 5))
    skills_pool = SKILLS_BY_DOMAIN.get(domain, SKILLS_BY_DOMAIN["Engineering"])
    skills = pick(skills_pool).copy()
    if random.random() < 0.3 and len(skills) < 6:
        skills.append(pick(["Agile", "Jira", "Git", "SQL", "REST", "API Design"]))

    description = (
        f"We are looking for a {title} to join our team. "
        f"Strong experience in {', '.join(skills[:3])} required. "
        f"Location: {location}. {remote.capitalize()} work."
    )

    return {
        "title": title,
        "company_name": company,
        "description": description,
        "domain": domain,
        "subdomain": subdomain,
        "years_experience_min": yoe_min,
        "years_experience_max": yoe_max,
        "skills_required": skills,
        "location": location,
        "country": country,
        "remote": remote,
        "salary_min": salary_min,
        "salary_max": salary_max,
    }


def main():
    random.seed(42)
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "jobs.sample.json"
    jobs = [generate_job(i) for i in range(1000)]
    with open(out_path, "w") as f:
        json.dump(jobs, f, indent=0)
    print(f"Wrote {len(jobs)} jobs to {out_path}")


if __name__ == "__main__":
    main()
