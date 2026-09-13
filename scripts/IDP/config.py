"""
config.py — Shared configuration for the IDP workstream.

Defines folder paths, source documents, and constants used by
discover.py, extract.py, and clean.py.
"""

from pathlib import Path

# ============================================================
# PROJECT METADATA
# ============================================================
PROJECT_CODE = "db-unza26-csc4792"
COUNCIL_SLUG = "kabwe"
COUNCIL_FULL = "Kabwe Municipal Council"
CONSTITUENCY = "Kabwe Central"
BASE_URL = "https://www.kabwecouncil.gov.zm"

# ============================================================
# FOLDER PATHS (resolved relative to repo root)
# ============================================================
def get_repo_root() -> Path:
    """Resolve repo root whether the script runs from root or elsewhere."""
    here = Path(__file__).resolve()
    # scripts/IDP/config.py → up 3 levels = repo root
    return here.parent.parent.parent


REPO_ROOT = get_repo_root()

DATA_RAW_IDP       = REPO_ROOT / "data" / "raw" / "IDP"
DATA_DISCOVERED    = REPO_ROOT / "data" / "discovered"
DATA_EXTRACTED_IDP = REPO_ROOT / "data" / "extracted" / "IDP"
DATA_PROCESSED_IDP = REPO_ROOT / "data" / "processed" / "IDP"

# ============================================================
# CURATED SOURCE LIST
# ============================================================
CURATED_SOURCES = [
    {
        "doc_id":   "IDP_MAIN",
        "title":    "Kabwe Approved IDP Final Version 1 (2023-2033)",
        "category": "Integrated Development Plan",
        "filename": "Kabwe-Approved-IDP_Final-Version-1.pdf",
        "url":      f"{BASE_URL}/wp-content/uploads/2024/09/"
                    f"Kabwe-Approved-IDP_Final-Version-1.pdf",
    },
    {
        "doc_id":   "IDP_CITIZEN",
        "title":    "Kabwe District Citizen IDP",
        "category": "Integrated Development Plan",
        "filename": "Kabwe-District-Citizen-IDP_Final-1.pdf",
        "url":      f"{BASE_URL}/wp-content/uploads/2024/09/"
                    f"Kabwe-District-Citizen-IDP_Final-1.pdf",
    },
    {
        "doc_id":   "CDF_PROJECTS_2025",
        "title":    "2025 Approved Community Projects — Kabwe Central",
        "category": "Strategic Community Projects",
        "filename": "2025-Approved-Community-Projects_Kabwe-Central.pdf",
        "url":      f"{BASE_URL}/wp-content/uploads/2025/06/"
                    f"2025-Approved-Community-Projects_Kabwe-Central.pdf",
    },
    {
        "doc_id":   "NEWSLETTER_2024",
        "title":    "Kabwe Municipal Council Newsletter 2024",
        "category": "Council Newsletter",
        "filename": "Kabwe-Municipal-Council-Newsletter-2024-1.pdf",
        "url":      f"{BASE_URL}/wp-content/uploads/2024/09/"
                    f"Kabwe-Municipal-Council-Newsletter-2024-1.pdf",
    },
]

# HTTP headers used for all requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

# Strategic areas from the 8NDP
STRATEGIC_AREAS = [
    "Economic Transformation and Job Creation",
    "Human and Social Development",
    "Environmental Sustainability",
    "Good Governance Environment",
]

# Sector keyword map
SECTOR_KEYWORDS = {
    "Education":            ["education", "school", "classroom", "teacher",
                             "pupil", "literacy", "desk"],
    "Health":               ["health", "clinic", "hospital", "nurse",
                             "doctor", "maternal", "malaria", "hiv"],
    "Water and Sanitation": ["water", "sanitation", "borehole", "toilet",
                             "latrine", "sewer", "sewage"],
    "Roads and Drainages":  ["road", "drain", "street", "bridge",
                             "culvert", "pavement", "tarmac"],
    "Commerce":             ["market", "trade", "commerce", "business",
                             "sme", "entrepreneur"],
    "Agriculture":          ["agriculture", "farm", "crop", "livestock",
                             "irrigation", "maize"],
    "Energy":               ["electricity", "power", "solar", "grid",
                             "energy", "zesco"],
    "Governance":           ["governance", "council", "ward", "community",
                             "participation", "committee"],
    "Environment":          ["environment", "climate", "forest", "tree",
                             "green", "pollution", "waste"],
}
