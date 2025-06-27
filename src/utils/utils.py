import pandas as pd
import logging
import re
import nltk
from nltk.tokenize import word_tokenize
import difflib
from src.config.translations import CODE_DICTIONARY
from src.config.constants import (
    FUZZY_SEARCH_SIMILARITY_THRESHOLD, TEXT_PREVIEW_LENGTH, TEXT_ENCODINGS, TEXTS_DIR
)

# Configure logging
logger = logging.getLogger(__name__)

def get_lang(lang_code):
    """Helper to get language dictionary"""
    from src.config.translations import TRANSLATIONS
    return TRANSLATIONS.get(lang_code, TRANSLATIONS['EN'])

def expand_code(code, lang_code='UA'):
    """
    Expand a code to its full description based on the language.
    Returns the code with description in parentheses if found, otherwise just the code.
    """
    if not code or pd.isna(code):
        return code
    
    code_str = str(code).strip()
    if code_str in CODE_DICTIONARY:
        description = CODE_DICTIONARY[code_str].get(lang_code, CODE_DICTIONARY[code_str].get('EN', ''))
        if description:
            return f"{code_str} ({description})"
    
    return code_str

def count_tokens(text):
    """
    Professional tokenization function that counts words and punctuation as tokens.
    Uses NLTK's word_tokenize which properly handles both words and punctuation.
    Handles None/NaN values gracefully.
    """
    if pd.isna(text) or text is None or text == '':
        return 0
    
    text = str(text)
    
    try:
        tokens = word_tokenize(text)
        
        tokens = [token for token in tokens if token.strip()]
        
        return len(tokens)
    except Exception as e:
        logger.warning(f"NLTK tokenization failed for text, falling back to simple tokenization: {e}")
        cleaned_text = re.sub(r'[^\w\s]', ' ', text)
        tokens = cleaned_text.split()
        tokens = [token for token in tokens if token.strip()]
        return len(tokens)

def get_effective_author(row):
    """
    Determine the effective author using this logic:
    1. Check if Translator 1 exists and is not empty, if yes use it as author
    2. If no, fallback to Author 1 Name
    
    Returns the effective author name and related info as a tuple:
    (name, sex, location_country, location_macroregion)
    """
    translator_name = row.get('Translator 1 Name', '')
    if pd.notna(translator_name) and translator_name != '':
        return (
            translator_name,
            row.get('Translator 1 Sex', ''),
            row.get('Translator 1 Location Country', ''),
            row.get('Translator 1 Location Macroregion', '')
        )
    else:
        return (
            row.get('Author 1 Name', ''),
            row.get('Author 1 Sex', ''),
            row.get('Author 1 Location Country', ''),
            row.get('Author 1 Location Macroregion', '')
        )

def add_effective_author_columns(df):
    """
    Add effective author columns to the dataframe based on translator-first logic
    """
    df = df.copy()
    
    effective_author_data = df.apply(get_effective_author, axis=1)
    
    df['Effective Author Name'] = [x[0] for x in effective_author_data]
    df['Effective Author Sex'] = [x[1] for x in effective_author_data]
    df['Effective Author Location Country'] = [x[2] for x in effective_author_data]
    df['Effective Author Location Macroregion'] = [x[3] for x in effective_author_data]
    
    return df

def fuzzy_search_match(text, query, similarity_threshold=FUZZY_SEARCH_SIMILARITY_THRESHOLD):
    """
    Perform fuzzy search matching for text fields.
    Returns True if the query matches the text with fuzzy logic.
    """
    if pd.isna(text) or pd.isna(query) or not text or not query:
        return False
    
    text = str(text).lower().strip()
    query = str(query).lower().strip()
    
    if query in text:
        return True
    
    query_words = query.split()
    text_words = text.split()
    
    for query_word in query_words:
        found = False
        for text_word in text_words:
            if query_word in text_word or text_word in query_word:
                found = True
                break
        if not found:
            best_ratio = 0
            for text_word in text_words:
                ratio = difflib.SequenceMatcher(None, query_word, text_word).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
            if best_ratio < similarity_threshold:
                return False
    
    return True

def read_text_content(file_path, lang_code='EN'):
    """Read the actual text content from a file"""
    lang = get_lang(lang_code)
    if pd.isna(file_path) or not file_path:
        return lang["file_not_found"]
    
    try:
        clean_path = file_path.replace("PluG2/", "") if file_path.startswith("PluG2/") else file_path
        full_path = f"{TEXTS_DIR}/{clean_path}"
        
        encodings = TEXT_ENCODINGS
        
        for encoding in encodings:
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    if content.strip():
                        return content[:TEXT_PREVIEW_LENGTH]
            except (UnicodeDecodeError, UnicodeError):
                continue
            except FileNotFoundError:
                break
        
        return lang["could_not_read_file"]
        
    except Exception as e:
        return lang["error_reading_file"].format(error=str(e)) 
