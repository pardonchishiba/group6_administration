# CSC4792 Kabwe Municipal Council Dataset

## 1. Project Overview

This project contains a curated dataset extracted from publicly available
digital footprints of Kabwe Municipal Council, Zambia.

The project was prepared for the CSC4792 Data Mining and Warehousing
practical assignment at the University of Zambia.

The objective is to collect, extract, clean, standardise and document
information relating to the council's critical functions and financial
activities.

The current curated dataset includes a detailed Constituency Development Fund
(CDF) component, with additional council data to be incorporated as the
dataset development continues.

---

## 2. Council

**Kabwe Municipal Council**

Official website:

https://www.kabwecouncil.gov.zm

The data was obtained from publicly available council publications,
financial documents, budget documents, project records and other digital
footprints.

---

## 3. Dataset Design

The dataset follows a multi-source approach.

Different source documents are maintained as separate datasets where they
represent different levels of detail.

For example:

- A project dataset contains project-level records.
- A budget dataset contains budget-category records.
- A financial dataset contains financial transaction categories.
- An output indicator dataset contains indicator-level records.

The datasets are therefore not blindly merged into a single table.

This preserves the meaning and grain of each dataset and reduces unnecessary
duplication.

---

## 4. Current CDF Dataset

The CDF component currently contains the following curated datasets:

### CDF Projects 2024

`data/processed/db-unza26-csc4792-kabwe_cdf_projects_2024.csv`

Contains 79 CDF project records from Bwacha and Kabwe Central constituencies.

### CDF Projects 2025

`data/processed/db-unza26-csc4792-kabwe_cdf_projects_2025.csv`

Contains 33 proposed CDF project records for Kabwe Central Constituency.

### CDF Budget 2024-2025

`data/processed/db-unza26-csc4792-kabwe_cdf_budget_2024_2025.csv`

Contains CDF budget allocations for 2024 and 2025.

### CDF Disbursements 2025

`data/processed/db-unza26-csc4792-kabwe_cdf_disbursements_2025.csv`

Contains constituency-level CDF funding records for 2025.

### CDF Financial Statement 2025

`data/processed/db-unza26-csc4792-kabwe_cdf_financial_statement_2025.csv`

Contains CDF receipts and payments extracted from the 2025 BI-Annual
Financial Statements.

### CDF Output Indicators 2025

`data/processed/db-unza26-csc4792-kabwe_cdf_output_indicators_2025.csv`

Contains CDF output indicators and target/actual values reported by the
council.

Detailed documentation for these datasets is available in:

`docs/CDF_README.md`

The column definitions are available in:

`docs/cdf_data_dictionary.csv`

---

## 5. Data Format

All final curated datasets are stored in CSV format.

The pipe character (`|`) is used as the delimiter as required by the
assignment.

Example:

```text
year|constituency|amount_kwacha
2025|Kabwe Central|6205128
```
---
## 6. Notebook Organization

The project's notebooks are organized to mirror the four workstreams described in Section 2, plus a final consolidation step:

### Topic notebooks (`/notebooks`)
Each of the four workstreams has its own dedicated notebook, covering discovery, extraction, cleaning and export for that workstream's tables:

| Notebook | Workstream | Tables produced |
|---|---|---|
| `notebooks/cdf_*.ipynb` | CDF allocations, disbursements, projects and indicators | 6 |
| `notebooks/finance_*.ipynb` | Approved budgets, LGEF utilisation, local revenue | 3 |
| `notebooks/idp_*.ipynb` | IDPs and strategic community projects | 11 |
| `notebooks/administration_*.ipynb` | Council administration, services, WDCs, public reports | 5 |

Each topic notebook is self-contained: it reads its own raw source documents, applies workstream-specific cleaning rules, and writes its processed tables to `data/processed/`.

### Consolidated notebook (root folder)
`kabwe_council_consolidated.ipynb`, in the project root, pulls together the outputs of all four topic notebooks. It:

- loads the final tables selected by `scripts/Boas/prepare_submission.py`;
- re-runs the validation checks described in Section 3.4 (non-empty files, unique headers, consistent row widths, required filename prefix);
- confirms the package totals (25 tables, 854 records); and
- serves as the single notebook to run end-to-end if a user wants to reproduce the full submission package without opening each topic notebook individually.

This notebook is the one referenced as the **submission-quality-assurance notebook** in Section 5, and is the recommended entry point for anyone reviewing or reproducing the dataset.

