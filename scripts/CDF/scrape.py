import requests
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


BASE_URL = "https://www.kabwecouncil.gov.zm"

RAW_DIR = Path("../data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


CDF_SOURCES = {
    "2024_bwacha_cdf_projects.pdf":
        "https://www.kabwecouncil.gov.zm/wp-content/uploads/2024/11/2024-Bwacha-community-projects-Recieved.pdf",

    "2024_kabwe_central_cdf_projects.pdf":
        "https://www.kabwecouncil.gov.zm/wp-content/uploads/2024/11/2024-Community-Projects-Kabwe-Central-received.pdf",

    "2025_proposed_kabwe_central_cdf_projects.pdf":
        "https://www.kabwecouncil.gov.zm/wp-content/uploads/2025/08/Proposed-2025-CDF-projects.pdf",

    "2025_kabwe_council_obb.pdf":
        "https://www.kabwecouncil.gov.zm/wp-content/uploads/2025/05/2025-KABWE-M-COUNCIL-OBB.pdf",

    "2025_bi_annual_financial_statement.pdf":
        "https://www.kabwecouncil.gov.zm/wp-content/uploads/2025/08/2025-BI-ANNUAL-FINANCIAL-STATEMENT-KABWE-M-COUNCIL-1-1.pdf",
}


def download_file(filename, url):
    output_path = RAW_DIR / filename

    print(f"Downloading: {filename}")

    response = requests.get(
        url,
        timeout=60,
        verify=False
    )

    response.raise_for_status()

    output_path.write_bytes(response.content)

    print(f"Saved to: {output_path}")
    print(f"Size: {len(response.content):,} bytes")
    print()


def main():
    print("Kabwe Municipal Council CDF Source Downloader")
    print("=" * 50)

    for filename, url in CDF_SOURCES.items():
        try:
            download_file(filename, url)
        except requests.RequestException as error:
            print(f"Failed to download {filename}")
            print(f"Error: {error}")
            print()

    print("Download process completed.")


if __name__ == "__main__":
    main()