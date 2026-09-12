from pathlib import Path
import re
import pandas as pd


PROCESSED_DIR = Path("../data/processed")


def clean_amount(value):
    """
    Convert financial values such as 'K6,205,128' or '6,205,128'
    into numeric values.
    """

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if value == "" or value.lower() in {
        "nan",
        "none",
        "n/a",
        "na",
        "-"
    }:
        return pd.NA

    value = re.sub(r"[^0-9.\-]", "", value)

    if value == "":
        return pd.NA

    return float(value)


def standardise_columns(df):
    """
    Standardise column names by removing spaces and using lowercase.
    """

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    return df


def remove_duplicate_rows(df):
    """
    Remove exact duplicate records.
    """

    before = len(df)

    df = df.drop_duplicates()

    after = len(df)

    print(f"Duplicates removed: {before - after}")

    return df


def clean_financial_statement(df):
    """
    Clean the CDF financial statement dataset.
    """

    df = standardise_columns(df)

    if "amount_kwacha" in df.columns:
        df["amount_kwacha"] = df["amount_kwacha"].apply(clean_amount)

    df = remove_duplicate_rows(df)

    return df


def clean_disbursements(df):
    """
    Clean the CDF disbursement dataset.
    """

    df = standardise_columns(df)

    if "amount_kwacha" in df.columns:
        df["amount_kwacha"] = df["amount_kwacha"].apply(clean_amount)

    df = remove_duplicate_rows(df)

    return df


def clean_budget(df):
    """
    Clean the CDF budget dataset.
    """

    df = standardise_columns(df)

    financial_columns = [
        "budget_2024",
        "budget_2025"
    ]

    for column in financial_columns:
        if column in df.columns:
            df[column] = df[column].apply(clean_amount)

    df = remove_duplicate_rows(df)

    return df


def clean_projects_2024(df):
    """
    Clean the 2024 CDF project dataset.
    """

    df = standardise_columns(df)

    financial_columns = [
        "application_amount",
        "engineers_estimate",
        "approved_amount",
        "contract_amount"
    ]

    for column in financial_columns:
        if column in df.columns:
            df[column] = df[column].apply(clean_amount)

    df = remove_duplicate_rows(df)

    return df


def clean_projects_2025(df):
    """
    Clean the 2025 CDF project dataset.
    """

    df = standardise_columns(df)

    df = remove_duplicate_rows(df)

    return df


def clean_output_indicators(df):
    """
    Clean the CDF output indicator dataset.
    """

    df = standardise_columns(df)

    numeric_columns = [
        "target_2023",
        "actual_2023",
        "target_2024",
        "actual_2024",
        "target_2025"
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    df = remove_duplicate_rows(df)

    return df


def save_cleaned_dataset(df, filename):
    """
    Save a cleaned dataframe as a pipe-delimited CSV.
    """

    output_path = PROCESSED_DIR / filename

    df.to_csv(
        output_path,
        sep="|",
        index=False
    )

    print(f"Saved: {output_path}")


def main():

    print("Kabwe Municipal Council CDF Data Cleaning")
    print("=" * 50)

    datasets = {
        "db-unza26-csc4792-kabwe_cdf_budget_2024_2025.csv":
            clean_budget,

        "db-unza26-csc4792-kabwe_cdf_disbursements_2025.csv":
            clean_disbursements,

        "db-unza26-csc4792-kabwe_cdf_financial_statement_2025.csv":
            clean_financial_statement,

        "db-unza26-csc4792-kabwe_cdf_output_indicators_2025.csv":
            clean_output_indicators,

        "db-unza26-csc4792-kabwe_cdf_projects_2024.csv":
            clean_projects_2024,

        "db-unza26-csc4792-kabwe_cdf_projects_2025.csv":
            clean_projects_2025,
    }

    for filename, cleaning_function in datasets.items():

        input_path = PROCESSED_DIR / filename

        if not input_path.exists():
            print(f"Skipping missing file: {filename}")
            continue

        print(f"\nProcessing: {filename}")

        df = pd.read_csv(
            input_path,
            sep="|"
        )

        original_rows = len(df)

        df = cleaning_function(df)

        print(f"Original rows: {original_rows}")
        print(f"Final rows: {len(df)}")

        save_cleaned_dataset(
            df,
            filename
        )

    print("\nCleaning process completed.")


if __name__ == "__main__":
    main()