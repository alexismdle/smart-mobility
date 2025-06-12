import json
from pathlib import Path

import pandas as pd


def load_json_data(source_input):
    empty_df = pd.DataFrame(columns=["head", "head_type", "relation", "tail", "tail_type"])
    empty_node_map = {}

    if source_input is None:
        return empty_df, empty_node_map

    raw_content = None

    try:
        if hasattr(source_input, 'read'):
            if hasattr(source_input, 'getvalue'):
                raw_content_bytes = source_input.getvalue()
            else:
                raw_content_bytes = source_input.read()
            if not isinstance(raw_content_bytes, bytes):
                if isinstance(raw_content_bytes, str):
                    raw_content = raw_content_bytes
                else:
                    return empty_df, empty_node_map
            else:
                raw_content = raw_content_bytes.decode("utf-8")
        elif isinstance(source_input, (str, Path)):
            file_path = Path(source_input)
            if not file_path.exists() or not file_path.is_file():
                return empty_df, empty_node_map
            raw_content_bytes = file_path.read_bytes()
            raw_content = raw_content_bytes.decode("utf-8")
        else:
            return empty_df, empty_node_map

        if not raw_content:
            return empty_df, empty_node_map

        data = json.loads(raw_content)
        if not isinstance(data, dict):
            return empty_df, empty_node_map
        if not isinstance(data.get('nodes'), list) or not isinstance(data.get('edges'), list):
            return empty_df, empty_node_map

        nodes_data = data['nodes']
        edges_data = data['edges']

        node_info_map = {}
        for node in nodes_data:
            node_id = node.get('id')
            if not node_id:
                continue
            source_file = node.get('source_file')
            node_attributes = node.get('attributes', [])
            node_type = node_id
            if source_file and isinstance(source_file, str) and '.' in source_file:
                node_type = source_file.split('.')[0]
            elif source_file:
                node_type = source_file
            node_info_map[node_id] = {'type': node_type, 'attributes': node_attributes}

        processed_edges = []
        for edge in edges_data:
            head_id = edge.get('from')
            tail_id = edge.get('to')
            relation = edge.get('label')
            if not all([head_id, tail_id, relation]):
                continue
            head_node_info = node_info_map.get(head_id)
            tail_node_info = node_info_map.get(tail_id)
            if not head_node_info or not tail_node_info:
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

        if not processed_edges and not edges_data:
            return empty_df, node_info_map

        edges_df = pd.DataFrame(processed_edges)
        if edges_df.empty:
            return empty_df, node_info_map

        expected_columns = ["head", "head_type", "relation", "tail", "tail_type"]
        if not all(col in edges_df.columns for col in expected_columns):
            return empty_df, node_info_map

        return edges_df, node_info_map

    except Exception:
        return empty_df, empty_node_map

def validate_data(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False
    required_columns = ["head", "head_type", "relation", "tail", "tail_type"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False
    return True

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    cleaned_df = df.copy()
    essential_cols = ["head", "relation", "tail"]
    type_cols = ["head_type", "tail_type"]
    all_relevant_cols = essential_cols + type_cols
    cleaned_df.dropna(subset=essential_cols, inplace=True)
    for col in type_cols:
        if col in cleaned_df.columns:
            cleaned_df[col].fillna("Unknown", inplace=True)
    for col in all_relevant_cols:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].astype(str)
    cleaned_df.drop_duplicates(inplace=True)
    return cleaned_df

def normalize_entities(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    normalized_df = df.copy()
    columns_to_normalize = ["head_type", "tail_type", "relation"]
    for col in columns_to_normalize:
        if col in normalized_df.columns:
            normalized_df[col] = normalized_df[col].astype(str).str.lower().str.strip()
    return normalized_df