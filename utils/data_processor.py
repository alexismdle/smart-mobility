import json
from pathlib import Path

import pandas as pd


def load_json_data(source_input):
    """
    Loads JSON data from various sources (Streamlit UploadedFile object, file path string,
    or Path object), parses it, and converts it into a pandas DataFrame.

    Args:
        source_input: A Streamlit UploadedFile object, a string representing a file path,
                      or a pathlib.Path object.

    Returns:
        A pandas DataFrame containing the parsed JSON data, or an empty
        DataFrame if parsing fails or the file is None.
    """
    if source_input is None:
        # TODO: Log that no input was provided
        print("Warning: No data source provided to load_json_data.")
        return pd.DataFrame()

    raw_content = None
    data_source_name = "Unknown" # For logging/error messages

    try:
        if hasattr(source_input, 'read'): # Duck typing for Streamlit UploadedFile or BytesIO
            if hasattr(source_input, 'name'):
                data_source_name = source_input.name
            else:
                data_source_name = "Uploaded Stream"
            
            # Streamlit's UploadedFile might return bytes from read() or getvalue()
            # Ensure we handle both potential interfaces if they differ across versions/usage
            if hasattr(source_input, 'getvalue'):
                raw_content_bytes = source_input.getvalue()
            else:
                raw_content_bytes = source_input.read()

            if not isinstance(raw_content_bytes, bytes):
                 # If it's already a string (e.g. from a mock object in tests)
                if isinstance(raw_content_bytes, str):
                    raw_content = raw_content_bytes
                else:
                    # TODO: Log this unexpected type
                    print(f"Warning: Unexpected content type from stream-like object: {type(raw_content_bytes)}")
                    return pd.DataFrame()
            else:
                 raw_content = raw_content_bytes.decode("utf-8")

        elif isinstance(source_input, (str, Path)):
            data_source_name = str(source_input)
            file_path = Path(source_input)
            if not file_path.exists():
                # TODO: Log file not found
                print(f"Error: File not found at path: {file_path}")
                return pd.DataFrame()
            if not file_path.is_file():
                 # TODO: Log path is not a file
                print(f"Error: Path is not a file: {file_path}")
                return pd.DataFrame()
            raw_content_bytes = file_path.read_bytes()
            raw_content = raw_content_bytes.decode("utf-8")
        else:
            # TODO: Log unsupported input type
            print(f"Error: Unsupported input type for load_json_data: {type(source_input)}")
            return pd.DataFrame()

        if not raw_content:
            # TODO: Log empty content
            print(f"Warning: Empty content from data source: {data_source_name}")
            return pd.DataFrame()
            
        data = json.loads(raw_content)

        if not isinstance(data, list):
            # TODO: Log that JSON data is not a list of records
            print(f"Warning: JSON data from {data_source_name} is not a list of records.")
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Column validation can remain, or be moved to a separate validation function if preferred
        expected_columns = ["head", "head_type", "relation", "tail", "tail_type"]
        if not all(col in df.columns for col in expected_columns):
            # TODO: Log missing columns
            print(f"Warning: DataFrame from {data_source_name} is missing one or more expected columns: {expected_columns}.")
            # Depending on strictness, might return df or empty df. For now, returning df.
            # Consider how critical these columns are for downstream processing.
            # If they are essential, returning pd.DataFrame() might be better.
            pass # Allow partial data for now, validate_data can catch this more formally

        return df

    except json.JSONDecodeError as e:
        # TODO: Log JSON parsing error
        print(f"Error parsing JSON from {data_source_name}: {e}")
        return pd.DataFrame()
    except FileNotFoundError: # Should be caught by Path.exists() but as a safeguard
        print(f"Error: File not found (safeguard) for path: {data_source_name}")
        return pd.DataFrame()
    except Exception as e:
        # TODO: Log other potential errors
        print(f"An unexpected error occurred while loading/processing data from {data_source_name}: {e}")
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
