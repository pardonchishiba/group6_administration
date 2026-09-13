"""
clean.py — Phase 3: Cleaning, enrichment, and export.

Reads raw CSVs from data/extracted/IDP/, applies cleaning and
canonicalisation, merges the project tables, and writes final
pipe-delimited CSVs to data/processed/IDP/.

Usage:
    python scripts/IDP/clean.py
"""

import re
import warnings
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import (
    DATA_EXTRACTED_IDP, DATA_PROCESSED_IDP,
    PROJECT_CODE, COUNCIL_SLUG, COUNCIL_FULL, CONSTITUENCY,
)

warnings.filterwarnings("ignore", category=Warning)

RUN_STAMP = datetime.now().isoformat(timespec="seconds")


# ============================================================
# CLEANING UTILITIES
# ============================================================

NULL_STRINGS = {"none", "nan", "nat", "null", "n/a", "", "-", "unknown"}
VAGUE_WARDS  = {"various wards", "all wards", "unknown", "none", "", "entire district"}


def clean_text(value, max_len=None):
    if pd.isna(value):
        return None
    s = re.sub(r"[\r\n\t]+", " ", str(value))
    s = re.sub(r"\s+", " ", s).strip()
    if s.lower() in NULL_STRINGS:
        return None
    return s[:max_len] if max_len else s


def clean_amount(value):
    if pd.isna(value):
        return None
    s = str(value).upper()
    s = re.sub(r"(ZMW|K|MK|KWACHA)", "", s)
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s) if s else None
    except ValueError:
        return None


SECTOR_MAP = {
    "education": "Education", "school": "Education",
    "health": "Health", "clinic": "Health",
    "water and sanitation": "Water and Sanitation",
    "water & sanitation":   "Water and Sanitation",
    "water": "Water and Sanitation",
    "roads and drainages": "Roads and Drainages",
    "roads": "Roads and Drainages",
    "commerce": "Commerce", "market": "Commerce",
    "agriculture": "Agriculture", "farming": "Agriculture",
    "energy": "Energy", "electricity": "Energy",
    "governance": "Governance", "environment": "Environment",
}


def canonical_sector(value):
    if pd.isna(value):
        return "Unknown"
    return SECTOR_MAP.get(str(value).strip().lower(),
                          str(value).strip().title())


def canonical_ward(value):
    if pd.isna(value):
        return None
    s = re.sub(r"\s+", " ", str(value)).strip().strip(",.")
    return s.title() if s else None


def make_project_ids(n, prefix="KAB"):
    return [f"{prefix}-{i:04d}" for i in range(1, n + 1)]


# ============================================================
# CLEANING FUNCTIONS
# ============================================================

def load_extracted(name: str) -> pd.DataFrame:
    p = DATA_EXTRACTED_IDP / f"{name}.csv"
    return pd.read_csv(p, sep="|") if p.exists() else pd.DataFrame()


def clean_cdf_projects() -> pd.DataFrame:
    """Clean the raw CDF project registry."""
    cdf = load_extracted("cdf_projects_raw")
    if cdf.empty:
        return pd.DataFrame()

    cdf.columns = [str(c).strip().upper() for c in cdf.columns]

    RENAME = {
        "NO.": "project_no", "NO": "project_no", "#": "project_no",
        "S/N": "project_no", "SN": "project_no",
        "PROJECT NAME": "project_name", "PROJECT_NAME": "project_name",
        "PROJECT": "project_name", "NAME": "project_name",
        "PROJECT DESCRIPTION": "description", "DESCRIPTION": "description",
        "SECTOR": "sector", "CATEGORY": "sector",
        "WARD": "ward", "LOCATION": "ward", "AREA": "ward",
        "PROJECT SITE": "site", "SITE": "site",
        "COL_5": "site",
        "ENGINEERS ESTIMATE": "engineer_estimate_zmw",
        "ENGINEER'S ESTIMATE": "engineer_estimate_zmw",
        "ENGINEER ESTIMATE": "engineer_estimate_zmw",
        "ENGINEERS ESTIMAT": "engineer_estimate_zmw",
        "ESTIMATE": "engineer_estimate_zmw",
        "APPROVED AMOUNT": "approved_amount_zmw",
        "APPROVED AMOUNT (ZMW)": "approved_amount_zmw",
        "APPROVED AMOUN": "approved_amount_zmw",
        "APPROVED AMOU": "approved_amount_zmw",
        "AMOUNT": "approved_amount_zmw",
        "AMOUNT (ZMW)": "approved_amount_zmw",
        "COST": "approved_amount_zmw", "BUDGET": "approved_amount_zmw",
        "ESTIMATE__1": "approved_amount_zmw",
        "SOURCE_DOC": "source_doc",
    }
    cdf = cdf.rename(columns=RENAME)

    DROP = [c for c in cdf.columns
            if c.startswith("COL_") or c == "_PAGE"
            or c.startswith("ESTIMATE__") or c.startswith("AMOUNT__")]
    cdf = cdf.drop(columns=DROP, errors="ignore")

    def coalesce(df, col):
        positions = [i for i, c in enumerate(df.columns) if c == col]
        if len(positions) <= 1:
            return df
        combined = df.iloc[:, positions[0]]
        for pos in positions[1:]:
            combined = combined.where(combined.notna(), df.iloc[:, pos])
        df = df.drop(df.columns[positions], axis=1)
        df.insert(positions[0], col, combined)
        return df

    for c in ["project_name", "approved_amount_zmw",
              "engineer_estimate_zmw", "ward", "sector",
              "description", "site", "project_no", "source_doc"]:
        cdf = coalesce(cdf, c)

    for c in ["project_name", "description", "sector", "ward", "site"]:
        if c in cdf.columns:
            cdf[c] = cdf[c].apply(clean_text)
    for c in ["engineer_estimate_zmw", "approved_amount_zmw"]:
        if c in cdf.columns:
            cdf[c] = cdf[c].apply(clean_amount)

    if "project_no" in cdf.columns:
        cdf = cdf[~cdf["project_no"].astype(str).str.upper()
                      .str.contains("PROJECT|NAME|WARD|SECTOR", na=False, regex=True)]

    if "project_name" in cdf.columns:
        cdf = cdf[
            cdf["project_name"].notna()
            & (cdf["project_name"].astype(str).str.len() >= 5)
            & (~cdf["project_name"].str.lower()
                    .str.contains("sub total|total|summary", na=False))
        ]

    amt_cols = [c for c in ["engineer_estimate_zmw", "approved_amount_zmw"]
                if c in cdf.columns]
    if amt_cols:
        cdf = cdf[cdf[amt_cols].notna().any(axis=1)]

    if "sector" in cdf.columns:
        cdf["sector"] = cdf["sector"].apply(canonical_sector)
    if "ward" in cdf.columns:
        cdf["ward"] = cdf["ward"].apply(canonical_ward)

    for c in ["sector", "ward", "site", "description"]:
        if c in cdf.columns:
            cdf[c] = cdf[c].fillna("Unknown")

    if "SOURCE_DOC" in cdf.columns:
        cdf = cdf.drop(columns=["SOURCE_DOC"])

    cdf["council"]        = COUNCIL_FULL
    cdf["constituency"]   = CONSTITUENCY
    cdf["status"]         = "Approved"
    cdf["funding_source"] = "CDF"
    cdf["source_doc"]     = "CDF_PROJECTS_2025"
    cdf["scraped_at"]     = RUN_STAMP

    return cdf.reset_index(drop=True)


def clean_newsletter_projects() -> pd.DataFrame:
    """Clean the Newsletter projects."""
    news = load_extracted("newsletter_raw")
    if news.empty:
        return pd.DataFrame()
    for c in ["project_name", "sector", "status"]:
        if c in news.columns:
            news[c] = news[c].apply(clean_text)
    if "approved_amount_zmw" in news.columns:
        news["approved_amount_zmw"] = news["approved_amount_zmw"].apply(clean_amount)
    if "sector" in news.columns:
        news["sector"] = news["sector"].apply(canonical_sector)
    news["council"]        = COUNCIL_FULL
    news["constituency"]   = CONSTITUENCY
    news["funding_source"] = "CDF"
    news["scraped_at"]     = RUN_STAMP
    if "project_name" in news.columns:
        news = news[news["project_name"].notna()
                    & (news["project_name"].astype(str).str.len() >= 5)]
    return news.reset_index(drop=True)


def merge_projects(cdf_clean: pd.DataFrame,
                   news_clean: pd.DataFrame) -> pd.DataFrame:
    """Merge CDF and Newsletter into a master project table."""
    COLS = ["project_id", "council", "project_name", "sector", "constituency",
            "ward", "approved_amount_zmw", "status", "funding_source",
            "source_doc", "scraped_at"]
    frames = []
    if not cdf_clean.empty:
        frames.append(cdf_clean.reindex(columns=COLS))
    if not news_clean.empty:
        frames.append(news_clean.reindex(columns=COLS))
    master = (pd.concat(frames, ignore_index=True, sort=False)
                if frames else pd.DataFrame(columns=COLS))
    master["project_id"] = make_project_ids(len(master))
    master["approved_amount_zmw"] = pd.to_numeric(
        master["approved_amount_zmw"], errors="coerce"
    )
    return master.reset_index(drop=True)


def enrich_projects(projects: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns."""
    projects["has_amount_zmw"] = projects["approved_amount_zmw"].notna()
    projects["is_approved"] = (
        projects["status"].astype(str).str.lower() == "approved"
    )
    SECTOR_GROUP = {
        "Education": "Social", "Health": "Social",
        "Water and Sanitation": "Infrastructure",
        "Roads and Drainages": "Infrastructure",
        "Commerce": "Economic", "Agriculture": "Economic",
        "Energy": "Infrastructure",
        "Governance": "Governance", "Environment": "Environment",
    }
    projects["sector_category"] = (
        projects["sector"].map(SECTOR_GROUP).fillna("Other")
    )
    def band(a):
        if pd.isna(a): return "Unknown"
        if a < 100_000:      return "Small (<100K)"
        if a < 1_000_000:    return "Medium (100K-1M)"
        if a < 5_000_000:    return "Large (1M-5M)"
        return "Very Large (>=5M)"
    projects["amount_band"] = projects["approved_amount_zmw"].apply(band)
    projects["has_ward"] = (
        projects["ward"].notna()
        & (~projects["ward"].astype(str).str.lower().isin(VAGUE_WARDS))
    )
    return projects


def deduplicate(projects: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates on composite key."""
    key = (
        projects["project_name"].fillna("").str.lower().str.strip()
        + "|" + projects["ward"].fillna("").str.lower().str.strip()
        + "|" + projects["approved_amount_zmw"].fillna(-1).astype(str)
    )
    df = (projects.assign(_key=key)
            .drop_duplicates(subset=["_key"], keep="first")
            .drop(columns=["_key"])
            .reset_index(drop=True))
    df["project_id"] = make_project_ids(len(df))
    return df


def clean_narrative_tables() -> dict:
    """Clean the smaller narrative tables and return a dict of DataFrames."""
    TEXT_COL_FOR_JUNK = {
        "goals": "goal_text", "subprogrammes": "sub_programme",
        "me_framework": "Activities", "citizen_points": "point",
        "newsletter_narrative": "sentence",
        "strategic_areas": "strategic_area", "wards": "ward_name",
        "statistics": "context", "cost_estimates": "programme",
    }

    def is_real(line, min_words=3):
        if not isinstance(line, str): return False
        if re.search(r"\.{3,}", line): return False
        if re.search(r"\d\s*$", line): return False
        if len(line.split()) < min_words: return False
        if line.isupper() and len(line) > 60: return False
        return True

    result = {}
    for key in ["strategic_areas", "goals", "statistics", "subprogrammes",
                "me_framework", "cost_estimates", "newsletter_narrative",
                "citizen_points", "wards"]:
        df = load_extracted(key)
        if df.empty:
            result[key] = pd.DataFrame()
            continue
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].apply(clean_text)
        if key in TEXT_COL_FOR_JUNK:
            col = TEXT_COL_FOR_JUNK[key]
            if col in df.columns:
                df = df[df[col].apply(lambda s: is_real(s))].reset_index(drop=True)
        if key == "cost_estimates":
            if "year" in df.columns:
                df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
            if "cost_zmw" in df.columns:
                df["cost_zmw"] = pd.to_numeric(df["cost_zmw"], errors="coerce")
        if key == "statistics" and "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
        result[key] = df
    return result


def build_derived_tables(projects: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build sector-by-ward matrix and timeline."""
    sector_by_ward = (
        projects[projects["has_ward"] == True]
          .groupby(["ward", "sector"], dropna=False)
          .size()
          .unstack(fill_value=0)
          .reset_index()
    )
    sector_by_ward.columns.name = None
    sector_by_ward = sector_by_ward.rename(columns={"ward": "ward_name"})
    sector_cols = [c for c in sector_by_ward.columns if c != "ward_name"]
    sector_by_ward["total_projects"] = sector_by_ward[sector_cols].sum(axis=1)

    def infer_year(sd):
        if "NEWSLETTER" in str(sd): return 2024
        if "CDF_PROJECTS_2025" in str(sd): return 2025
        return None
    projects["inferred_year"] = projects["source_doc"].apply(infer_year)
    timeline = (
        projects.dropna(subset=["inferred_year"])
          .groupby("inferred_year", as_index=False)
          .agg(project_count=("project_id", "count"),
               total_amount_zmw=("approved_amount_zmw", "sum"))
          .rename(columns={"inferred_year": "year"})
    )
    return sector_by_ward, timeline


# ============================================================
# MAIN
# ============================================================

def run_cleaning() -> None:
    """Main cleaning routine."""
    print("=" * 72)
    print("PHASE 3 — CLEANING & PREPROCESSING")
    print("=" * 72)
    print(f"Input  : {DATA_EXTRACTED_IDP.resolve()}")
    print(f"Output : {DATA_PROCESSED_IDP.resolve()}")
    print()

    DATA_PROCESSED_IDP.mkdir(parents=True, exist_ok=True)

    print("Cleaning project tables...")
    cdf_clean  = clean_cdf_projects()
    news_clean = clean_newsletter_projects()
    print(f"  CDF projects       : {len(cdf_clean)} rows")
    print(f"  Newsletter projects: {len(news_clean)} rows")

    print("\nMerging into master table...")
    projects = merge_projects(cdf_clean, news_clean)
    projects = enrich_projects(projects)
    projects = deduplicate(projects)
    print(f"  Master projects    : {len(projects)} rows")

    print("\nCleaning narrative tables...")
    tables = clean_narrative_tables()
    for k, df in tables.items():
        print(f"  {k:<22}: {len(df)} rows")

    print("\nBuilding derived tables...")
    sector_by_ward, timeline = build_derived_tables(projects)
    print(f"  sector_by_ward     : {sector_by_ward.shape}")
    print(f"  timeline           : {timeline.shape}")

    # Write all files
    print("\nWriting outputs...")
    outputs = {
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_idp_projects.csv":           projects,
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_idp_strategic_areas.csv":    tables["strategic_areas"],
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_idp_goals.csv":              tables["goals"],
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_idp_statistics.csv":         tables["statistics"],
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_idp_subprogrammes.csv":      tables["subprogrammes"],
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_idp_me_framework.csv":       tables["me_framework"],
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_idp_cost_estimates.csv":     tables["cost_estimates"],
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_idp_citizen_points.csv":     tables["citizen_points"],
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_newsletter_narrative.csv":   tables["newsletter_narrative"],
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_sector_by_ward.csv":         sector_by_ward,
        f"{PROJECT_CODE}-{COUNCIL_SLUG}_timeline.csv":               timeline,
    }
    written = 0
    for fname, df in outputs.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.to_csv(DATA_PROCESSED_IDP / fname, sep="|", index=False, encoding="utf-8")
            print(f"  [written] {fname:<60} {len(df):>5} rows")
            written += 1
        else:
            print(f"  [skip]    {fname:<60} (empty)")

    print(f"\n✅ {written} files written to {DATA_PROCESSED_IDP}")


if __name__ == "__main__":
    run_cleaning()
