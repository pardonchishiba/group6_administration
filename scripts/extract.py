from pathlib import Path
import fitz


RAW_DIR = Path("../data/raw")
EXTRACTED_DIR = Path("../data/extracted")

EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)


PDF_FILES = [
    "2024_bwacha_cdf_projects.pdf",
    "2024_kabwe_central_cdf_projects.pdf",
    "2025_proposed_kabwe_central_cdf_projects.pdf",
    "2025_kabwe_council_obb.pdf",
    "2025_bi_annual_financial_statement.pdf",
]


def extract_pdf_text(pdf_path):
    """
    Extract text from a PDF using PyMuPDF.
    """

    document = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(document, start=1):
        text = page.get_text("text")

        pages.append(
            f"\n--- PAGE {page_number} ---\n{text}"
        )

    document.close()

    return "\n".join(pages)


def extract_file(filename):
    """
    Extract text from one PDF and save it as a TXT file.
    """

    pdf_path = RAW_DIR / filename

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        return

    print(f"Extracting: {filename}")

    text = extract_pdf_text(pdf_path)

    output_filename = pdf_path.stem + ".txt"
    output_path = EXTRACTED_DIR / output_filename

    output_path.write_text(
        text,
        encoding="utf-8"
    )

    print(f"Saved: {output_path}")
    print(f"Characters extracted: {len(text):,}")
    print()


def main():
    print("Kabwe Municipal Council CDF PDF Extraction")
    print("=" * 50)

    for filename in PDF_FILES:
        extract_file(filename)

    print("Extraction process completed.")


if __name__ == "__main__":
    main()