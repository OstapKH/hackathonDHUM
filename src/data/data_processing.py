import pandas as pd
import logging
from src.utils.utils import get_lang, add_effective_author_columns, fuzzy_search_match
from src.config.constants import METADATA_FILE, METADATA_SEPARATOR, METADATA_LOW_MEMORY

logger = logging.getLogger(__name__)

def load_metadata():
    """Load and preprocess the metadata file"""
    try:
        df = pd.read_csv(METADATA_FILE, sep=METADATA_SEPARATOR, low_memory=METADATA_LOW_MEMORY)
        lang = get_lang('EN')
        
        df['Date'] = pd.to_numeric(df['Date'], errors='coerce')
        
        text_columns = ['Name', 'Language Code', 'Style Code', 'Publication City', 
                       'Publisher', 'Author 1 Name', 'Author 1 Sex',
                       'Translator 1 Name', 'Translator 1 Sex']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
        
        df = add_effective_author_columns(df)
        
        return df
    except Exception as e:
        lang = get_lang('EN')
        logger.error(lang["error_loading_metadata"] + f": {e}")
        return pd.DataFrame()

def get_filtered_dataframe(filter_state, metadata_df):
    """Helper function to get filtered dataframe on demand"""
    if metadata_df.empty:
        return pd.DataFrame()
    
    filtered_df = metadata_df.copy()
    
    if filter_state['genre'] != 'all':
        filtered_df = filtered_df[filtered_df['Style Code'] == filter_state['genre']]
    
    if filter_state['year_range']:
        filtered_df = filtered_df[
            (filtered_df['Date'] >= filter_state['year_range'][0]) & 
            (filtered_df['Date'] <= filter_state['year_range'][1])
        ]
    
    if filter_state.get('fuzzy_search'):
        search_term = filter_state['fuzzy_search']
        lang = get_lang('EN')
        
        name_mask = filtered_df['Name'].apply(
            lambda x: fuzzy_search_match(x, search_term)
        )
        author_mask = filtered_df['Effective Author Name'].apply(
            lambda x: fuzzy_search_match(x, search_term)
        )
        
        combined_mask = name_mask | author_mask
        filtered_df = filtered_df[combined_mask]
        
    
    return filtered_df

def apply_table_filters(df, filter_query):
    """
    Apply custom fuzzy search filters to the dataframe based on filter_query.
    """
    if not filter_query:
        return df
    
    lang = get_lang('EN')
    
    filtered_df = df.copy()
    
    try:
        conditions = []
        
        if ' && ' in filter_query:
            conditions = filter_query.split(' && ')
        else:
            conditions = [filter_query]
        
        for condition in conditions:
            condition = condition.strip()
            
            column_name = None
            search_value = None
            
            operators = [' scontains ', ' icontains ', ' contains ']
            
            parsed = False
            for operator in operators:
                if operator in condition:
                    parts = condition.split(operator)
                    if len(parts) == 2:
                        column_part = parts[0].strip()
                        value_part = parts[1].strip()
                        
                        if column_part.startswith('{') and column_part.endswith('}'):
                            column_name = column_part[1:-1]
                        else:
                            column_name = column_part
                        
                        if value_part.startswith('"') and value_part.endswith('"'):
                            search_value = value_part[1:-1]
                        else:
                            search_value = value_part
                        
                        parsed = True
                        break
            
            if not parsed and ' = ' in condition:
                parts = condition.split(' = ')
                if len(parts) == 2:
                    column_part = parts[0].strip()
                    value_part = parts[1].strip()
                    
                    if column_part.startswith('{') and column_part.endswith('}'):
                        column_name = column_part[1:-1]
                    else:
                        column_name = column_part
                    
                    if value_part.startswith('"') and value_part.endswith('"'):
                        search_value = value_part[1:-1]
                    else:
                        search_value = value_part
            
            if column_name and search_value and column_name in filtered_df.columns:
                
                if column_name in ['Name', 'Effective Author Name']:
                    mask = filtered_df[column_name].apply(
                        lambda x: fuzzy_search_match(x, search_value)
                    )
                    filtered_df = filtered_df[mask]
                else:
                    mask = filtered_df[column_name].astype(str).str.lower().str.contains(
                        search_value.lower(), na=False, regex=False
                    )
                    filtered_df = filtered_df[mask]
            else:
                logger.warning(lang["could_not_apply_filter"].format(
                    column=column_name, value=search_value, 
                    exists=column_name in filtered_df.columns if column_name else 'N/A'))
    
    except Exception as e:
        logger.error(lang["error_parsing_filter_query"].format(query=filter_query, error=e))
        return df
    
    return filtered_df 
