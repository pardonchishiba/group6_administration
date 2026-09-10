import requests
import pdfplumber
import pandas as pd
import urllib3


PDF_URL = (
    "https://www.kabwecouncil.gov.zm/"
    "wp-content/uploads/2024/11/"
    "2024-Bwacha-community-projects-Recieved.pdf"
)

OUTPUT_PATH = "../data/raw/2024_bwacha_cdf_projects.pdf"


# Disable the warning caused by verify=False
urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


def download_pdf(url, output_path):
    response = requests.get(
        url,
        timeout=60,
        verify=False
    )

    print("Status code:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("File size:", len(response.content), "bytes")
    print("First 20 bytes:", response.content[:20])

    response.raise_for_status()

    # Make sure the server actually returned a PDF
    content_type = response.headers.get("Content-Type", "")

    if (
        "application/pdf" not in content_type.lower()
        and not response.content.startswith(b"%PDF-")
    ):
        raise ValueError(
            "The URL did not return a PDF. "
            "The server returned HTML or another file type."
        )

    with open(output_path, "wb") as file:
        file.write(response.content)

    print(f"PDF downloaded successfully: {output_path}")


def extract_project_rows(pdf_path):
    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"Number of pages: {len(pdf.pages)}")

        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()

            print(
                f"Page {page_number}: "
                f"{len(tables)} table(s) found"
            )

            for table in tables:
                for row in table:
                    if row:
                        all_rows.append(row)

    project_rows = []

    for row in all_rows:
        if (
            row[0] is not None
            and str(row[0]).strip().isdigit()
        ):
            project_rows.append(row)

    return project_rows


def create_dataframe(project_rows):
    columns = [
        "project_number",
        "project_name",
        "project_description",
        "ward",
        "project_site",
        "application_amount",
        "engineers_estimate",
        "approved_amount",
        "contract_amount",
        "status"
    ]

    df = pd.DataFrame(
        project_rows,
        columns=columns
    )

    return df


if __name__ == "__main__":
    download_pdf(PDF_URL, OUTPUT_PATH)

    rows = extract_project_rows(OUTPUT_PATH)

    df = create_dataframe(rows)

    print("\nProjects extracted:", len(df))
    print("\nFirst five projects:")
    print(df.head())