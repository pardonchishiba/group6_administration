"""
extract.py — Phase 2: PDF extraction into raw CSVs.

Reads the four IDP source PDFs and extracts:
  - strategic areas
  - sector goals
  - baseline statistics
  - CDF project registry
  - Newsletter completed projects
  - Newsletter narrative sentences
  - sub-programmes
  - M&E framework
  - cost estimates
  - ward profiles
  - citizen IDP points

Outputs raw CSVs to data/extracted/IDP/.

Usage:
    python scripts/IDP/extract.py
"""

import json
import re
import warnings
from pathlib import Path

import pandas as pd
import pdfplumber

from config import (
    DATA_RAW_IDP, DATA_DISCOVERED, DATA_EXTRACTED_IDP,
    STRATEGIC_AREAS, SECTOR_KEYWORDS,
)

warnings.filterwarnings("ignore", category=Warning)


# ============================================================
# UTILITIES
# ============================================================

def load_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Return [(page_number, page_text), ...] for a PDF."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            pages.append((pno, page.extract_text() or ""))
    return pages


def make_unique_columns(cols) -> list[str]:
    """Return unique, non-empty column labels."""
    seen, out = {}, []
    for i, c in enumerate(cols):
        name = str(c).strip() if c is not None else ""
        if not name or name.lower() in ("nan", "none"):
            name = f"col_{i}"
        if name in seen:
            seen[name] += 1
            name = f"{name}__{seen[name]}"
        else:
            seen[name] = 0
        out.append(name)
    return out


def extract_all_tables(pdf_path: Path) -> list[pd.DataFrame]:
    """Extract every table using the 'lines' strategy."""
    LINE_SETTINGS = {
        "vertical_strategy":   "lines",
        "horizontal_strategy": "lines",
    }
    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            for tbl in page.extract_tables(LINE_SETTINGS):
                if tbl and len(tbl) > 1:
                    cols = make_unique_columns(tbl[0])
                    df = pd.DataFrame(tbl[1:], columns=cols)
                    df["_page"] = pno
                    tables.append(df)
    return tables


def guess_sector(text: str) -> str:
    """Best-effort sector classification."""
    if not isinstance(text, str):
        return "Unknown"
    s = text.lower()
    scores = {sec: sum(1 for kw in kws if kw in s)
              for sec, kws in SECTOR_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Unknown"


# ============================================================
# EXTRACTORS
# ============================================================

def extract_strategic_areas(idp_pages, out_dir: Path) -> None:
    """Extract the four 8NDP-aligned strategic areas."""
    rows = []
    for area in STRATEGIC_AREAS:
        pages_found = [p for p, t in idp_pages if area.lower() in t.lower()]
        rows.append({
            "strategic_area": area,
            "page_refs":      ",".join(map(str, pages_found)),
            "source_doc":     "IDP_MAIN",
        })
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "strategic_areas.csv", sep="|", index=False)
    print(f"  strategic_areas      : {len(df)} rows")


def extract_goals(idp_pages, out_dir: Path) -> None:
    """Extract development goal sentences from the IDP."""
    GOAL_PATTERNS = [
        r"\b(increase|reduce|expand|improve|achieve|ensure|promote|enhance|strengthen)\b.{10,300}",
        r"\bobjectives?\s+\d+(?:\.\d+)*[:\s].{10,300}",
        r"\b(target|goal|aim)s?\s*[:\-]\s*.{10,300}",
        r"\bby\s+20\d{2}\b.{0,200}",
        r"\bfrom\s+[\d.,%]+\s+to\s+[\d.,%]+\b.{0,200}",
    ]
    rows = []
    for pno, text in idp_pages:
        for s in re.split(r"(?<=[.!?])\s+", text):
            s_clean = re.sub(r"\s+", " ", s).strip()
            if not (40 <= len(s_clean) <= 500):
                continue
            if any(re.search(p, s_clean, re.IGNORECASE) for p in GOAL_PATTERNS):
                rows.append({
                    "page":       pno,
                    "sector":     guess_sector(s_clean),
                    "goal_text":  s_clean[:400],
                    "source_doc": "IDP_MAIN",
                })
    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["goal_text"])
            .reset_index(drop=True))
    df.to_csv(out_dir / "goals.csv", sep="|", index=False)
    print(f"  goals                : {len(df)} rows")


def extract_statistics(idp_pages, out_dir: Path) -> None:
    """Extract baseline statistics (number + unit)."""
    STAT_UNITS = [
        "school", "schools", "clinic", "clinics", "hospital", "hospitals",
        "health post", "health posts", "borehole", "boreholes",
        "market", "markets", "road", "roads", "km", "kilometre", "kilometres",
        "household", "households", "population", "people", "residents",
        "ward", "wards", "teacher", "teachers", "nurse", "nurses",
        "pupil", "pupils", "desk", "desks", "toilet", "toilets",
        "latrine", "latrines", "plot", "plots",
    ]
    unit_regex = "|".join(re.escape(u) for u in STAT_UNITS)
    stat_re = re.compile(rf"\b(\d[\d,]*)\s+({unit_regex})\b", re.IGNORECASE)

    rows = []
    for pno, text in idp_pages:
        for m in stat_re.finditer(text):
            ctx = text[max(0, m.start()-120):m.end()+120]
            rows.append({
                "page":       pno,
                "value":      int(m.group(1).replace(",", "")),
                "unit":       m.group(2).lower(),
                "context":    re.sub(r"\s+", " ", ctx).strip()[:300],
                "source_doc": "IDP_MAIN",
            })
    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["value", "unit", "context"])
            .reset_index(drop=True))
    df.to_csv(out_dir / "statistics.csv", sep="|", index=False)
    print(f"  statistics           : {len(df)} rows")


def extract_cdf_projects(cdf_path: Path, out_dir: Path) -> None:
    """Extract the CDF project registry."""
    def is_project_table(df):
        if df.shape[0] < 5 or df.shape[1] < 6:
            return False
        headers = " ".join(str(c).strip().upper() for c in df.columns)
        if "PROJECT NAME" not in headers:
            return False
        if "SUB TOTAL" in headers or "SUMMARY" in headers:
            return False
        if len(df) > 0:
            first = str(df.iloc[0, 0]).strip().upper()
            if first.startswith("SUB TOTAL") or first.startswith("SUMMARY"):
                return False
        return True

    tables = extract_all_tables(cdf_path)
    main = [t for t in tables if is_project_table(t)] or tables
    df = (pd.concat(main, ignore_index=True, sort=False)
            if main else pd.DataFrame())
    df["source_doc"] = "CDF_PROJECTS_2025"
    df.to_csv(out_dir / "cdf_projects_raw.csv", sep="|", index=False)
    print(f"  cdf_projects_raw     : {len(df)} rows")


def extract_newsletter_projects(news_pages, out_dir: Path) -> None:
    """Extract completed project lines from the Newsletter."""
    PROJECT_KEYWORDS = [
        "school", "classroom", "block", "toilet", "ablution", "clinic",
        "market", "borehole", "desk", "chair", "construction", "procurement",
        "rehabilitation", "installation", "supply", "road", "bridge",
        "hospital", "office", "staff house", "shelter", "wall fence",
        "water", "reticulated", "solar", "panel",
    ]
    NEWS_LINE = re.compile(
        r"(?P<name>(?:[A-Z][A-Za-z0-9'\-]+[\s,&]+){3,20}[A-Za-z0-9'\-]+)"
        r"[^\d]{0,80}(?:K|ZMW)?\s*"
        r"(?P<amount>\d{1,3}(?:,\d{3})+(?:\.\d{2})?)",
        re.MULTILINE,
    )
    YEAR_RE = re.compile(r"\b(20\d{2})\b")

    rows = []
    for pno, text in news_pages:
        if len(text) < 200:
            continue
        for m in NEWS_LINE.finditer(text):
            name = re.sub(r"\s+", " ", m.group("name")).strip()
            if not (20 <= len(name) <= 200):
                continue
            if not any(kw in name.lower() for kw in PROJECT_KEYWORDS):
                continue
            try:
                amount = float(m.group("amount").replace(",", ""))
            except ValueError:
                continue
            if not (5_000 <= amount <= 500_000_000):
                continue
            ctx = text[max(0, m.start()-250):m.end()+250]
            ym = YEAR_RE.search(ctx)
            rows.append({
                "project_name":        name[:200],
                "approved_amount_zmw": amount,
                "year_funded":         int(ym.group(1)) if ym else 2024,
                "sector":              guess_sector(name),
                "status":              "Completed",
                "source_doc":          "NEWSLETTER_2024",
                "page":                pno,
            })
    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["project_name", "approved_amount_zmw"])
            .reset_index(drop=True))
    df.to_csv(out_dir / "newsletter_raw.csv", sep="|", index=False)
    print(f"  newsletter_raw       : {len(df)} rows")


def extract_newsletter_narrative(news_pages, out_dir: Path) -> None:
    """Extract narrative sentences that mention a project keyword and a number."""
    NARRATIVE_KEYWORDS = [
        "school", "classroom", "clinic", "hospital", "market", "borehole",
        "desk", "water", "road", "bridge", "project", "handover",
        "commissioned", "completed", "constructed", "rehabilitated",
        "beneficiaries", "pupils", "patients", "residents",
    ]
    NUM_RE = re.compile(r"\d[\d,]*")

    rows = []
    for pno, text in news_pages:
        for s in re.split(r"(?<=[.!?])\s+", text):
            s_clean = re.sub(r"\s+", " ", s).strip()
            if not (50 <= len(s_clean) <= 500):
                continue
            lower = s_clean.lower()
            if not any(kw in lower for kw in NARRATIVE_KEYWORDS):
                continue
            if not NUM_RE.search(s_clean):
                continue
            numbers = [int(m.group().replace(",", ""))
                       for m in NUM_RE.finditer(s_clean)]
            rows.append({
                "page":          pno,
                "sector":        guess_sector(s_clean),
                "sentence":      s_clean[:400],
                "numbers_found": ",".join(map(str, numbers[:10])),
                "source_doc":    "NEWSLETTER_2024",
            })
    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["sentence"])
            .reset_index(drop=True))
    df.to_csv(out_dir / "newsletter_narrative.csv", sep="|", index=False)
    print(f"  newsletter_narrative : {len(df)} rows")


def extract_subprogrammes(idp_pages, out_dir: Path) -> None:
    """Extract real sub-programmes (strict filter)."""
    ACTION_VERBS = [
        "construction", "rehabilitation", "expansion", "improvement",
        "promotion", "provision", "development", "establishment",
        "strengthening", "enhancement", "maintenance", "installation",
        "supply", "upgrade", "extension", "creation",
    ]
    DOTTED_LEADER = re.compile(r"\.{3,}")
    ENDS_WITH_NUMBER = re.compile(r"\d\s*$")
    TRAILING_PREPS = re.compile(
        r"\b(?:for|of|in|to|with|and|by|at|on|the|a|an|from|as)\s*$",
        re.IGNORECASE,
    )
    BANNED = ["act no", "province", "district council", "citizens version"]
    PATTERN = re.compile(
        r"^\s*(?:\d+(?:\.\d+)*|[•\-*]|[a-z]\))\s*(.{15,180})$",
        re.MULTILINE,
    )
    PILLARS = ["economic transformation", "job creation",
               "human and social development", "environmental sustainability",
               "good governance"]

    def is_real(line):
        if not isinstance(line, str) or len(line) < 20:
            return False
        if len(line.split()) < 4:
            return False
        if DOTTED_LEADER.search(line) or ENDS_WITH_NUMBER.search(line):
            return False
        if TRAILING_PREPS.search(line):
            return False
        lower = line.lower()
        if not any(v in lower for v in ACTION_VERBS):
            return False
        if any(b in lower for b in BANNED):
            return False
        return True

    rows = []
    current = "Unknown"
    for pno, text in idp_pages:
        for kw in PILLARS:
            if kw in text.lower():
                current = kw.title()
                break
        for m in PATTERN.finditer(text):
            line = re.sub(r"\s+", " ", m.group(1)).strip()
            if not is_real(line):
                continue
            rows.append({
                "page":          pno,
                "pillar":        current,
                "sub_programme": line[:200],
                "source_doc":    "IDP_MAIN",
            })
    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["sub_programme"])
            .reset_index(drop=True))
    df.to_csv(out_dir / "subprogrammes.csv", sep="|", index=False)
    print(f"  subprogrammes        : {len(df)} rows")


def extract_cost_estimates(idp_path: Path, out_dir: Path) -> None:
    """Extract multi-year cost tables."""
    YEAR_TOKENS = [str(y) for y in range(2023, 2034)]
    rows = []
    with pdfplumber.open(idp_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            for tbl in page.extract_tables():
                if not tbl or len(tbl) < 3:
                    continue
                header = " ".join(str(c or "") for c in tbl[0])
                if sum(1 for y in YEAR_TOKENS if y in header) < 2:
                    continue
                for r in tbl[1:]:
                    if not r or len(r) < 3:
                        continue
                    label = str(r[0] or "").strip()
                    if len(label) < 4:
                        continue
                    for h, v in zip(tbl[0][1:], r[1:]):
                        year_str = str(h or "").strip()
                        if not year_str.isdigit():
                            continue
                        try:
                            cost = float(
                                str(v).replace(",", "")
                                      .replace("K", "")
                                      .replace("ZMW", "")
                                      .strip() or 0
                            )
                        except ValueError:
                            continue
                        if cost <= 0:
                            continue
                        rows.append({
                            "programme":  label[:120],
                            "year":       int(year_str),
                            "cost_zmw":   cost,
                            "page":       pno,
                            "source_doc": "IDP_MAIN",
                        })
    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["programme", "year", "cost_zmw"])
            .reset_index(drop=True))
    df.to_csv(out_dir / "cost_estimates.csv", sep="|", index=False)
    print(f"  cost_estimates       : {len(df)} rows")


def extract_me_framework(idp_path: Path, out_dir: Path) -> None:
    """Extract M&E framework table rows."""
    ME_KEYWORDS = (
        "indicator", "baseline", "target", "means of verification",
        "data source", "frequency", "responsible", "outcome",
        "strategies", "program", "activities", "location",
    )
    rows = []
    with pdfplumber.open(idp_path) as pdf:
        for pno, page in enumerate(pdf.pages, start=1):
            for tbl in page.extract_tables():
                if not tbl or len(tbl) < 2:
                    continue
                header = " ".join(str(c or "").lower() for c in tbl[0])
                if sum(1 for kw in ME_KEYWORDS if kw in header) < 2:
                    continue
                cols = [str(c or f"col_{i}").strip()[:60]
                        for i, c in enumerate(tbl[0])]
                for r in tbl[1:]:
                    if not r or not any(r):
                        continue
                    record = {"page": pno, "source_doc": "IDP_MAIN"}
                    for c, v in zip(cols, r):
                        record[c] = str(v or "").strip()[:300]
                    rows.append(record)
    df = pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)
    df.to_csv(out_dir / "me_framework.csv", sep="|", index=False)
    print(f"  me_framework         : {len(df)} rows")


def extract_wards(idp_pages, out_dir: Path) -> None:
    """Extract ward profile lines."""
    PATTERN = re.compile(
        r"ward\s+(\d+)\s*[:\-]?\s*([A-Za-z][A-Za-z\s\-']{2,60})",
        re.IGNORECASE,
    )
    rows = []
    for pno, text in idp_pages:
        for m in PATTERN.finditer(text):
            wno = m.group(1).strip()
            wname = re.sub(r"\s+", " ", m.group(2)).strip()
            if len(wname) < 3:
                continue
            if wname.lower() in ("development", "committee", "council",
                                 "the", "a", "an"):
                continue
            rows.append({
                "ward_number": wno,
                "ward_name":   wname[:80],
                "page":        pno,
                "source_doc":  "IDP_MAIN",
            })
    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["ward_number", "ward_name"])
            .reset_index(drop=True))
    df.to_csv(out_dir / "wards.csv", sep="|", index=False)
    print(f"  wards                : {len(df)} rows")


def extract_citizen_points(citizen_pages, out_dir: Path) -> None:
    """Extract citizen priority statements (bullet-split)."""
    PATTERN = re.compile(
        r"^\s*(?:\d+(?:\.\d+)*|[•\-*]|[a-z]\))\s*(.{15,180})$",
        re.MULTILINE,
    )
    ACTION_VERBS = [
        "construct", "rehabilitate", "establish", "install", "improve",
        "provide", "develop", "upgrade", "drill", "buy", "expand",
        "promote", "train", "conduct", "build",
    ]

    def split_on_bullet(text):
        if "•" in text:
            parts = [p.strip() for p in text.split("•") if p.strip()]
            return max(parts, key=len) if parts else text
        return text

    rows = []
    for pno, text in citizen_pages:
        for m in PATTERN.finditer(text):
            line = re.sub(r"\s+", " ", m.group(1)).strip()
            line = split_on_bullet(line)
            if len(line) < 20 or line[0].islower():
                continue
            if not any(v in line.lower() for v in ACTION_VERBS):
                continue
            rows.append({
                "page":       pno,
                "topic":      guess_sector(line),
                "point":      line[:300],
                "source_doc": "IDP_CITIZEN",
            })
    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["point"])
            .reset_index(drop=True))
    df.to_csv(out_dir / "citizen_points.csv", sep="|", index=False)
    print(f"  citizen_points       : {len(df)} rows")


# ============================================================
# MAIN
# ============================================================

def run_extraction() -> None:
    """Main extraction routine."""
    print("=" * 72)
    print("PHASE 2 — EXTRACTION")
    print("=" * 72)
    print(f"Input  : {DATA_RAW_IDP.resolve()}")
    print(f"Output : {DATA_EXTRACTED_IDP.resolve()}")
    print()

    DATA_EXTRACTED_IDP.mkdir(parents=True, exist_ok=True)

    # Load the four PDFs
    idp_main = DATA_RAW_IDP / "Kabwe-Approved-IDP_Final-Version-1.pdf"
    citizen  = DATA_RAW_IDP / "Kabwe-District-Citizen-IDP_Final-1.pdf"
    cdf_pdf  = DATA_RAW_IDP / "2025-Approved-Community-Projects_Kabwe-Central.pdf"
    news     = DATA_RAW_IDP / "Kabwe-Municipal-Council-Newsletter-2024-1.pdf"

    for p in [idp_main, citizen, cdf_pdf, news]:
        if not p.exists():
            raise FileNotFoundError(f"Missing PDF: {p}")

    print("Loading PDF text...")
    idp_pages     = load_pdf_pages(idp_main)
    citizen_pages = load_pdf_pages(citizen)
    news_pages    = load_pdf_pages(news)
    print(f"  IDP      : {sum(len(t) for _, t in idp_pages):>9,} chars, {len(idp_pages)} pages")
    print(f"  Citizen  : {sum(len(t) for _, t in citizen_pages):>9,} chars, {len(citizen_pages)} pages")
    print(f"  News     : {sum(len(t) for _, t in news_pages):>9,} chars, {len(news_pages)} pages")
    print()

    print("Extracting tables...")
    extract_strategic_areas(idp_pages, DATA_EXTRACTED_IDP)
    extract_goals(idp_pages, DATA_EXTRACTED_IDP)
    extract_statistics(idp_pages, DATA_EXTRACTED_IDP)
    extract_cdf_projects(cdf_pdf, DATA_EXTRACTED_IDP)
    extract_newsletter_projects(news_pages, DATA_EXTRACTED_IDP)
    extract_newsletter_narrative(news_pages, DATA_EXTRACTED_IDP)
    extract_subprogrammes(idp_pages, DATA_EXTRACTED_IDP)
    extract_cost_estimates(idp_main, DATA_EXTRACTED_IDP)
    extract_me_framework(idp_main, DATA_EXTRACTED_IDP)
    extract_wards(idp_pages, DATA_EXTRACTED_IDP)
    extract_citizen_points(citizen_pages, DATA_EXTRACTED_IDP)

    print()
    print("Extraction complete. Run clean.py for Phase 3.")


if __name__ == "__main__":
    run_extraction()
