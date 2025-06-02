import json
import pandas as pd

def load_json_data(uploaded_file):
    """
    Loads JSON data from a Streamlit UploadedFile object, parses it,
    and converts it into a pandas DataFrame.

    Args:
        uploaded_file: A Streamlit UploadedFile object.

    Returns:
        A pandas DataFrame containing the parsed JSON data, or an empty
        DataFrame if parsing fails or the file is None.
    """
    if uploaded_file is None:
        # TODO: Log that no file was uploaded
        return pd.DataFrame()

    try:
        file_content = uploaded_file.read().decode("utf-8")
        data = json.loads(file_content)

        # Assuming the JSON data is a list of records
        if not isinstance(data, list):
            # TODO: Log that the JSON data is not a list of records
            # Potentially raise a custom exception here
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Basic validation for expected columns
        expected_columns = ["head", "head_type", "relation", "tail", "tail_type"]
        if not all(col in df.columns for col in expected_columns):
            # TODO: Log that the DataFrame is missing expected columns
            # Potentially raise a custom exception here
            # Returning an empty DataFrame for now, or could return df and let caller handle
            return pd.DataFrame()

        return df
    except json.JSONDecodeError:
        # TODO: Log JSON parsing error
        # Consider raising a custom exception for better error handling upstream
        return pd.DataFrame()
    except Exception as e:
        # TODO: Log other potential errors during file processing
        # Consider raising a custom exception
        return pd.DataFrame()


def validate_data(df: pd.DataFrame) -> bool:
    """
    Validates a pandas DataFrame to ensure it contains the required columns
    and is not empty.

    Args:
        df: The pandas DataFrame to validate.

    Returns:
        True if the DataFrame is valid, False otherwise.
    """
    if df is None or df.empty:
        print("Warning: Input DataFrame is None or empty.")
        return False

    required_columns = ["head", "head_type", "relation", "tail", "tail_type"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        print(f"Warning: DataFrame is missing the following required columns: {', '.join(missing_columns)}")
        # TODO: Implement proper logging here
        return False

    return True


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans the input DataFrame by handling missing values, removing duplicates,
    and ensuring data type consistency for key columns.

    Args:
        df: The pandas DataFrame to clean.

    Returns:
        A new pandas DataFrame with cleaned data, or an empty DataFrame
        if the input is empty or None.
    """
    if df is None or df.empty:
        # TODO: Log or print a message about empty input DataFrame
        return pd.DataFrame()

    # Make a copy to avoid modifying the original DataFrame
    cleaned_df = df.copy()

    # Define columns for different handling of missing values
    essential_cols = ["head", "relation", "tail"]
    type_cols = ["head_type", "tail_type"]
    all_relevant_cols = essential_cols + type_cols

    # Drop rows where essential columns are missing
    cleaned_df.dropna(subset=essential_cols, inplace=True)

    # Fill missing values for type columns with "Unknown"
    for col in type_cols:
        if col in cleaned_df.columns:
            cleaned_df[col].fillna("Unknown", inplace=True)
        else:
            # If a type column itself is missing after validation (should not happen if validate_data is called first)
            # or if it was not in the original df, we might add it with "Unknown"
            # For now, this assumes validate_data has run and columns exist.
            pass


    # Ensure all relevant columns are treated as strings
    for col in all_relevant_cols:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].astype(str)

    # Remove duplicate rows
    cleaned_df.drop_duplicates(inplace=True)

    return cleaned_df


def normalize_entities(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes entity names and types in the DataFrame by converting them
    to lowercase and stripping leading/trailing whitespace.

    Args:
        df: The pandas DataFrame with entity data.

    Returns:
        A new pandas DataFrame with normalized entity strings, or an empty
        DataFrame if the input is empty or None.
    """
    if df is None or df.empty:
        # TODO: Log or print a message about empty input DataFrame
        return pd.DataFrame()

    normalized_df = df.copy()
    columns_to_normalize = ["head", "head_type", "tail", "tail_type"]

    for col in columns_to_normalize:
        if col in normalized_df.columns:
            # Ensure the column is of string type before applying string methods
            if pd.api.types.is_string_dtype(normalized_df[col]):
                normalized_df[col] = normalized_df[col].str.lower().str.strip()
            else:
                # This case should ideally be handled by clean_data ensuring string types.
                # If not, convert to string, then normalize.
                # This also handles non-string data that might have been missed or introduced.
                normalized_df[col] = normalized_df[col].astype(str).str.lower().str.strip()
                # TODO: Log a warning if a column had to be converted to string here,
                # as it might indicate an issue in preceding steps or unexpected data.
        else:
            # TODO: Log or print a warning if a column to normalize is missing.
            # This should ideally not happen if validate_data has been called.
            pass

    return normalized_df
