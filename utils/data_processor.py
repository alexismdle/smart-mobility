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
        A tuple containing:
            - A pandas DataFrame (edges_df) with graph edge data.
            - A dictionary (node_info_map) mapping node IDs to their type and attributes.
        Returns (pd.DataFrame(), {}) if parsing fails, the file is None, or no data.
    """
    empty_df = pd.DataFrame(columns=["head", "head_type", "relation", "tail", "tail_type"])
    empty_node_map = {}

    if source_input is None:
        # TODO: Log that no input was provided
        print("Warning: No data source provided to load_json_data.")
        return empty_df, empty_node_map

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
                    return empty_df, empty_node_map
            else:
                 raw_content = raw_content_bytes.decode("utf-8")

        elif isinstance(source_input, (str, Path)):
            data_source_name = str(source_input)
            file_path = Path(source_input)
            if not file_path.exists():
                # TODO: Log file not found
                print(f"Error: File not found at path: {file_path}")
                return empty_df, empty_node_map
            if not file_path.is_file():
                 # TODO: Log path is not a file
                print(f"Error: Path is not a file: {file_path}")
                return empty_df, empty_node_map
            raw_content_bytes = file_path.read_bytes()
            raw_content = raw_content_bytes.decode("utf-8")
        else:
            # TODO: Log unsupported input type
            print(f"Error: Unsupported input type for load_json_data: {type(source_input)}")
            return empty_df, empty_node_map

        if not raw_content:
            # TODO: Log empty content
            print(f"Warning: Empty content from data source: {data_source_name}")
            return empty_df, empty_node_map
            
        data = json.loads(raw_content)

        # Corrected check: The root of the JSON should be a dictionary
        if not isinstance(data, dict):
            # TODO: Log that JSON data is not a dictionary (object)
            print(f"Warning: JSON data from {data_source_name} is not an object as expected.")
            return empty_df, empty_node_map

        # Check for 'nodes' and 'edges' keys, and ensure they are lists
        if not isinstance(data.get('nodes'), list) or not isinstance(data.get('edges'), list):
            print(f"Warning: JSON data from {data_source_name} does not contain 'nodes' and 'edges' as lists.")
            return empty_df, empty_node_map

        nodes_data = data['nodes']
        edges_data = data['edges']

        node_info_map = {}
        for node in nodes_data:
            node_id = node.get('id')
            if not node_id:
                # TODO: Log or print warning about skipping node due to missing id
                print(f"Warning: Skipping node due to missing 'id': {node}")
                continue

            source_file = node.get('source_file')
            node_attributes = node.get('attributes', []) # Default to empty list

            node_type = node_id # Fallback type
            if source_file and isinstance(source_file, str) and '.' in source_file:
                node_type = source_file.split('.')[0]
            elif source_file: # source_file exists but no dot, use it as is or a part of it
                node_type = source_file
            # else: node_type remains node_id as fallback

            node_info_map[node_id] = {'type': node_type, 'attributes': node_attributes}

        processed_edges = []
        for edge in edges_data:
            head_id = edge.get('from')
            tail_id = edge.get('to')
            relation = edge.get('label')

            if not all([head_id, tail_id, relation]):
                # TODO: Log or print warning about skipping malformed edge
                print(f"Warning: Skipping edge due to missing 'from', 'to', or 'label': {edge}")
                continue

            head_node_info = node_info_map.get(head_id)
            tail_node_info = node_info_map.get(tail_id)

            if not head_node_info:
                print(f"Warning: Skipping edge due to missing info for head_id '{head_id}': {edge}")
                continue
            if not tail_node_info:
                print(f"Warning: Skipping edge due to missing info for tail_id '{tail_id}': {edge}")
                continue

            head_type = head_node_info['type']
            tail_type = tail_node_info['type']

            processed_edges.append({
                "head": head_id,
                "head_type": head_type,
                "relation": relation,
                "tail": tail_id,
                "tail_type": tail_type
            })

        if not processed_edges and edges_data: # Only warn if there were edges to process
            print(f"Warning: No valid edges could be processed from {data_source_name}, though edges were present in the input.")
        elif not processed_edges and not edges_data:
            print(f"Info: No edges found in the input from {data_source_name}.")
            # If no edges, df will be empty. This is valid if input has no edges.
            return empty_df, node_info_map


        edges_df = pd.DataFrame(processed_edges)

        # Handle cases where processed_edges might be empty, leading to an empty DataFrame
        # Ensure DataFrame has the expected columns even if empty
        if edges_df.empty:
            # node_info_map might still contain data if there are nodes but no edges
            return empty_df, node_info_map

        # The following validation of column names is still relevant.
        # This was identified as an unreachable block and removed.
        # df = pd.DataFrame(processed_edges) # This line is redundant, using edges_df

        # The following validation of column names is still relevant.
        # However, the creation logic above ensures these columns exist if processed_edges is not empty.
        # This check is more of a safeguard if the logic were to change.
        expected_columns = ["head", "head_type", "relation", "tail", "tail_type"]
        if not all(col in edges_df.columns for col in expected_columns):
            # This case should ideally not be reached if processed_edges has data.
            print(f"Warning: DataFrame constructed from {data_source_name} is missing one or more expected columns: {expected_columns}.")
            # If this happens, it implies an issue with the edge processing logic.
            return empty_df, node_info_map # Return empty if structure is not as expected.

        return edges_df, node_info_map

    except json.JSONDecodeError as e:
        # TODO: Log JSON parsing error
        print(f"Error parsing JSON from {data_source_name}: {e}")
        return empty_df, empty_node_map
    except FileNotFoundError: # Should be caught by Path.exists() but as a safeguard
        print(f"Error: File not found (safeguard) for path: {data_source_name}")
        return empty_df, empty_node_map
    except Exception as e:
        # TODO: Log other potential errors
        print(f"An unexpected error occurred while loading/processing data from {data_source_name}: {e}")
        return empty_df, empty_node_map


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
    # Node identifiers in 'head' and 'tail' must retain their original casing.
    # Only normalize type-related columns.
    columns_to_normalize = ["head_type", "tail_type", "relation"] # Also normalize relation for consistency

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
