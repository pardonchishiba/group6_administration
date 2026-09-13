"""
discover.py — Phase 1: HTML discovery of council PDF documents.

Crawls the Kabwe council website to find PDF links, supplements them with
a curated list of four verified documents, and saves the discovery result
to data/discovered/sources.json.

Usage:
    python scripts/IDP/discover.py

Output:
    data/discovered/sources.json
"""

import json
import warnings
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Local imports
from config import (
    BASE_URL, COUNCIL_FULL, DATA_DISCOVERED, DATA_RAW_IDP,
    CURATED_SOURCES, HEADERS,
)

warnings.filterwarnings("ignore", category=Warning)


def fetch_html(url: str, timeout: int = 30) -> str | None:
    """Fetch an HTML page and return its text. Returns None on error."""
    try:
        r = requests.get(
            url, headers=HEADERS, timeout=timeout,
            verify=False, allow_redirects=True,
        )
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  [error] {url} -> {type(e).__name__}: {e}")
        return None


def discover_pdf_links(html: str, base_url: str) -> list[str]:
    """Parse HTML for same-domain PDF URLs."""
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc
    found = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.lower().endswith(".pdf"):
            continue
        absolute = urljoin(base_url, href)
        if urlparse(absolute).netloc != base_domain:
            continue
        found.add(absolute)

    return sorted(found)


def run_discovery() -> None:
    """Main discovery routine."""
    print("=" * 72)
    print("PHASE 1 — DISCOVERY")
    print("=" * 72)
    print(f"Council  : {COUNCIL_FULL}")
    print(f"Base URL : {BASE_URL}")
    print(f"Run at   : {datetime.now().isoformat(timespec='seconds')}")
    print()

    # 1. Fetch the homepage
    print("Fetching homepage...")
    html = fetch_html(BASE_URL)

    # 2. Discover PDF links
    if html:
        pdfs = discover_pdf_links(html, BASE_URL)
        print(f"  -> {len(pdfs)} PDF links found on homepage")
    else:
        pdfs = []
        print("  -> Homepage fetch failed")

    # 3. Save discovery result
    DATA_DISCOVERED.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_at":          datetime.now().isoformat(timespec="seconds"),
        "base_url":        BASE_URL,
        "homepage_pdfs":   pdfs,
        "curated_sources": CURATED_SOURCES,
    }
    out_file = DATA_DISCOVERED / "sources.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print()
    print(f"Discovery saved to: {out_file}")
    print(f"  Homepage PDFs   : {len(pdfs)}")
    print(f"  Curated sources : {len(CURATED_SOURCES)}")

    # 4. Verify curated PDFs are on disk
    print()
    print("Verifying curated PDFs are present...")
    DATA_RAW_IDP.mkdir(parents=True, exist_ok=True)
    missing = []
    for s in CURATED_SOURCES:
        p = DATA_RAW_IDP / s["filename"]
        if p.exists():
            size_kb = p.stat().st_size / 1024
            print(f"  [ok]   {s['filename']:<55} ({size_kb:.1f} KB)")
        else:
            print(f"  [miss] {s['filename']}")
            missing.append(s["filename"])

    if missing:
        print()
        print("=" * 72)
        print(f"MANUAL DOWNLOAD REQUIRED ({len(missing)} missing)")
        print("=" * 72)
        for s in CURATED_SOURCES:
            if s["filename"] in missing:
                print(f"  {s['filename']}")
                print(f"  {s['url']}")
                print()
        print(f"Save to: {DATA_RAW_IDP.resolve()}")
    else:
        print()
        print("All curated PDFs verified. Ready for Phase 2.")


if __name__ == "__main__":
    run_discovery()
