# Kabwe Municipal Council CDF Dataset

## 1. Dataset Overview

This dataset contains curated data extracted from publicly available digital footprints of Kabwe Municipal Council, with a focus on Constituency Development Fund (CDF) activities.

The dataset was prepared for the CSC4792 Data Mining and Warehousing practical assignment at the University of Zambia.

The CDF datasets cover:

- CDF project records
- CDF budget allocations
- CDF funding and disbursements
- CDF financial receipts and payments
- CDF output indicators
- CDF project proposals for different years

The datasets are maintained as separate CSV files because each dataset represents a different level of detail.

## 2. Source

The primary source is the official Kabwe Municipal Council website:

https://www.kabwecouncil.gov.zm

The source documents include official council budget documents, financial statements and CDF project documents published by the council.

A complete list of sources is available in:

sources/source_inventory.csv

## 3. CDF Dataset Files

### 3.1 CDF Projects 2024

File: data/processed/db-unza26-csc4792-kabwe_cdf_projects_2024.csv

Contains CDF community project records from Bwacha and Kabwe Central constituencies.

Records: 79

The dataset includes project names, descriptions, wards, project sites, financial estimates, approved amounts, contract amounts and project status where these values were available in the source documents.

### 3.2 CDF Projects 2025

File: data/processed/db-unza26-csc4792-kabwe_cdf_projects_2025.csv

Contains proposed 2025 CDF projects for Kabwe Central Constituency.

Records: 33

The dataset includes project number, project description, ward, sector and comments from the source document.

### 3.3 CDF Budget 2024-2025

File: data/processed/db-unza26-csc4792-kabwe_cdf_budget_2024_2025.csv

Contains CDF budget allocations for 2024 and 2025.

Budget categories include Constituency Development, Community Projects, Women and Youth Empowerment, CDF Administration, and Secondary School and Skills Development Bursaries.

Records: 5

### 3.4 CDF Disbursements 2025

File: data/processed/db-unza26-csc4792-kabwe_cdf_disbursements_2025.csv

Contains constituency-level CDF funding recorded in the 2025 financial statement.

The records cover Kabwe Central and Bwacha constituencies.

Records: 2

### 3.5 CDF Financial Statement 2025

File: data/processed/db-unza26-csc4792-kabwe_cdf_financial_statement_2025.csv

Contains CDF receipts and payments extracted from the 2025 BI-Annual Financial Statements.

The dataset includes CDF funding, loan repayments, interest earned, infrastructure development, rehabilitation works, asset acquisition, social benefits, bursaries, administration costs, disaster contingency and other payments.

Records: 24

Total CDF receipts: K13,094,717

Total CDF payments: K34,462,069

These totals were checked against the reported CDF financial statement totals.

### 3.6 CDF Output Indicators 2025

File: data/processed/db-unza26-csc4792-kabwe_cdf_output_indicators_2025.csv

Contains CDF output indicators and reported targets and actual values for 2023-2025.

Examples include desks provided, maternity wings, ambulances, roads graded, youth groups, women groups, business entities receiving loans, CDFC meetings, project monitoring visits, projects branded, skills beneficiaries and secondary boarding beneficiaries.

Records: 12

## 4. Data Format

All curated datasets are stored as CSV files.

The pipe character (|) is used as the field delimiter as required by the assignment.

Example:

year|constituency|amount_kwacha
2025|Kabwe Central|6205128

When loading the files with pandas, use:

pd.read_csv("file.csv", sep="|")

## 5. Data Preparation

The data preparation process followed these stages:

1. Source identification
2. Document retrieval
3. Data extraction
4. Manual verification where required
5. Data cleaning
6. Standardisation of fields
7. Missing-value handling
8. Duplicate checking
9. Validation against source totals
10. Export to pipe-delimited CSV files

## 6. Missing Values

Missing values from the original source documents were not automatically replaced with zero.

A blank value can mean that the source document did not provide a value. Therefore, missing values are preserved where the source did not report a value.

Some 2024 project financial and status fields were blank in the original source document.

## 7. Financial Values

Financial amounts are represented in Zambian Kwacha (ZMW).

Numeric financial columns are stored as numeric values without currency symbols or thousands separators to make them suitable for data analysis.

For example, 6205128 represents K6,205,128.

## 8. Data Quality Checks

The curated datasets were checked for:

- Correct CSV structure
- Pipe delimiter usage
- Duplicate records
- Missing values
- Numeric financial fields
- Expected record counts
- Financial statement totals
- Consistency with source documents

## 9. Dataset Grain

The CDF datasets should not be blindly merged into one table because they represent different types of records.

Project datasets have one record per project.

Budget data has one record per budget category.

Disbursement data has one record per constituency funding record.

Financial statement data has one record per financial transaction category and constituency.

Output indicator data has one record per output indicator.

Keeping these datasets separate reduces duplication and preserves the meaning of each record.

## 10. Data Dictionary

A detailed description of every column is available in:

docs/cdf_data_dictionary.csv

## 11. Reproducibility

The project contains scripts and a Jupyter Notebook used during the extraction, cleaning and validation process.

Project structure:

CSC4792-Kabwe-Dataset/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
│   └── kabwe_council_dataset.ipynb
├── scripts/
│   ├── scrape.py
│   ├── extract.py
│   └── clean.py
├── sources/
│   └── source_inventory.csv
├── docs/
│   ├── cdf_data_dictionary.csv
│   └── CDF_README.md
├── requirements.txt
└── README.md

## 12. Intended Use

The curated CDF datasets can be used for exploratory data analysis, budget analysis, project distribution analysis, sector analysis, constituency comparisons, financial expenditure analysis, project status analysis, data visualisation, classification, clustering and data warehouse modelling.

The datasets should be interpreted together with their original source documents.

## 13. Source Attribution

Data was extracted from publicly available Kabwe Municipal Council documents.

The original source URLs and document names are retained in the dataset metadata columns and in the source inventory.