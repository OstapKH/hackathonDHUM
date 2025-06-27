"""
Application Constants and Configuration Settings
===============================================

This file contains all constants and configuration settings for the Ukrainian Text Corpus Dashboard.
Centralizing these values makes the application easier to maintain and configure.
"""

import plotly.express as px

# =============================================================================
# FILE PATHS AND DATA CONFIGURATION
# =============================================================================

# Data file paths
DATA_DIR = "data"
METADATA_FILE = f"{DATA_DIR}/PluG2_metadata.psv"
TEXTS_DIR = f"{DATA_DIR}/PluG2_texts"
CITY_COORDINATES_FILE = f"{DATA_DIR}/city_coordinates.csv"

# Metadata file configuration
METADATA_SEPARATOR = "|"
METADATA_LOW_MEMORY = False

# Text file configuration
TEXT_PREVIEW_LENGTH = 10000
TEXT_ENCODINGS = ['utf-8', 'cp1251', 'latin-1', 'utf-16']

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

# Default application settings
DEFAULT_LANGUAGE = 'UA'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8050
DEBUG_MODE = True

# Application title
APP_TITLE_KEY = "app_title"

# =============================================================================
# UI AND LAYOUT CONSTANTS
# =============================================================================

# Table configuration
DEFAULT_PAGE_SIZE = 25
TABLE_PAGINATION = True
TABLE_FIXED_LAYOUT = True

# Search configuration
FUZZY_SEARCH_SIMILARITY_THRESHOLD = 0.6
FUZZY_SEARCH_PLACEHOLDER_LANG = 'UA'

# Form controls
BUTTON_TYPE_DEFAULT = "default"

# =============================================================================
# CHART AND VISUALIZATION SETTINGS
# =============================================================================

# Chart dimensions
CHART_HEIGHT = 500
CHART_MARGIN = dict(l=20, r=20, t=40, b=20)

# Chart backgrounds
CHART_PLOT_BGCOLOR = 'rgba(0,0,0,0)'
CHART_PAPER_BGCOLOR = 'rgba(0,0,0,0)'

# Geographic visualization settings
GEOGRAPHIC_DEFAULT_ZOOM = 3.0
GEOGRAPHIC_DEFAULT_CENTER = {'lat': 49.0, 'lon': 32.0}

# Zoom thresholds for different geographic levels
COUNTRY_ZOOM_THRESHOLD = 3
MACROREGION_ZOOM_THRESHOLD = 6

# Map configuration
MAP_STYLE = "open-street-map"
MAP_HEIGHT = 600
MAP_MARGIN = dict(l=0, r=0, t=40, b=0)

# Bubble size configuration
BUBBLE_SIZE_MIN = 5
BUBBLE_SIZE_MAX = 50
BUBBLE_TEXT_THRESHOLD = 0.6
BUBBLE_OPACITY = 0.8

# =============================================================================
# COLOR SCHEMES AND STYLING
# =============================================================================

# Chart color schemes
STYLE_COLORS = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel1 + px.colors.qualitative.Set1

# Gender colors for pie charts and stacked bars
GENDER_COLORS = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0']

# Gender colors for pie chart patterns
GENDER_PIE_COLORS = ["gold", "mediumturquoise", "darkorange", "lightgreen", "lightcoral", "lightskyblue"]
GENDER_PIE_PATTERNS = [".", "x", "+", "-", "/", "\\"]

# Single chart colors
CHART_COLOR_PRIMARY = '#0dcaf0'      # Blue for publications
CHART_COLOR_TOKENS = '#28a745'       # Green for tokens  
CHART_COLOR_AUTHORS = '#fd7e14'      # Orange for authors
CHART_COLOR_INFO = '#17a2b8'         # Bootstrap info color
CHART_COLOR_TREND = '#009ab8'        # Trend line color
CHART_COLOR_FALLBACK_TREND = 'red'   # Fallback trend color

# Geographic color scales
GEO_COLORSCALE_CITY = 'YlOrRd'
GEO_COLORSCALE_MACROREGION = 'Plasma'
GEO_COLORSCALE_COUNTRY = 'RdBu_r'
GEO_COLORSCALE_DEFAULT = 'viridis'

# Map marker colors
MAP_MARKER_COLOR = '#1f77b4'
MAP_TEXT_COLOR = 'white'

# =============================================================================
# HIERARCHY AND PAGINATION SETTINGS
# =============================================================================

# Hierarchy drill-down paths
HIERARCHY_DRILL_PATHS = {
    'gender': ['gender', 'country', 'author', 'genre', 'texts'],
    'year': ['year', 'country', 'gender', 'author', 'genre', 'texts'],
    'author': ['author', 'country', 'gender', 'genre', 'texts'],
    'genre': ['genre', 'country', 'gender', 'author', 'texts'],
    'country': ['country', 'gender', 'author', 'genre', 'texts']
}

# Pagination settings
HIERARCHY_ITEMS_PER_PAGE = 10
HIERARCHY_YEARS_MULTIPLIER = 2  # Show more years per page in year view
HIERARCHY_PAGE_INPUT_MIN = 1

# Chart styling for hierarchy
HIERARCHY_MARKER_COLOR = '#17a2b8'
HIERARCHY_MARKER_LINE_COLOR = 'rgba(0,0,0,0.2)'
HIERARCHY_MARKER_LINE_WIDTH = 1

# =============================================================================
# DATA FILTERING AND PROCESSING
# =============================================================================

# Year range settings
DEFAULT_YEAR_MIN = 1800
DEFAULT_YEAR_MAX = 2025

# Genre filtering
ALL_GENRES_VALUE = 'all'

# Trend line settings
TREND_LINE_WIDTH = 3
TREND_LINE_STYLE = 'solid'
TREND_FALLBACK_WIDTH = 2
TREND_FALLBACK_STYLE = 'dash'
TREND_MIN_PERIODS_RATIO = 0.5

# Bar chart settings
BAR_WIDTH = 0.8
BAR_GAP = 0.3
BAR_GROUP_GAP = 0.1

# =============================================================================
# TABLE STYLING AND INTERACTION
# =============================================================================

# Table cell styling colors
TABLE_SELECTED_BG = 'rgba(13, 110, 253, 0.1)'
TABLE_SELECTED_BORDER = '1px solid #0d6efd'
TABLE_ODD_ROW_BG = '#f8f9fa'
TABLE_EVEN_ROW_BG = 'white'
TABLE_EDITED_CELL_BG = '#fff3cd'
TABLE_EDITED_CELL_BORDER = '2px solid #ffc107'

# Table column sizing
TABLE_CHECKBOX_WIDTH = 50
TABLE_DETAILS_BUTTON_EMOJI = '📖'

# =============================================================================
# GEOGRAPHIC COORDINATES
# =============================================================================

# Country coordinates for mapping
COUNTRY_COORDINATES = {
    'UA': [49.0, 32.0], 'RU': [55.7558, 37.6176], 'PL': [52.2297, 21.0122], 
    'DE': [51.1657, 10.4515], 'AT': [47.5162, 14.5501], 'US': [39.8283, -98.5795], 
    'CA': [56.1304, -106.3468], 'FR': [46.2276, 2.2137], 'GB': [55.3781, -3.4360], 
    'IT': [41.8719, 12.5674], 'CZ': [49.8175, 15.4730], 'SK': [48.6690, 19.6990], 
    'HU': [47.1625, 19.5033], 'RO': [45.9432, 24.9668], 'BG': [42.7339, 25.4858], 
    'RS': [44.0165, 21.0059], 'HR': [45.1000, 15.2000], 'SI': [46.1512, 14.9955], 
    'BY': [53.7098, 27.9534], 'LT': [55.1694, 23.8813], 'LV': [56.8796, 24.6032], 
    'EE': [58.5953, 25.0136], 'FI': [61.9241, 25.7482], 'SE': [60.1282, 18.6435], 
    'NO': [60.4720, 8.4689], 'DK': [56.2639, 9.5018], 'NL': [52.1326, 5.2913], 
    'BE': [50.5039, 4.4699], 'CH': [46.8182, 8.2275], 'ES': [40.4637, -3.7492], 
    'PT': [39.3999, -8.2245], 'AU': [-25.2744, 133.7751], 'BR': [-14.2350, -51.9253], 
    'AR': [-38.4161, -63.6167], 'IL': [31.0461, 34.8516], 'TR': [38.9637, 35.2433], 
    'GR': [39.0742, 21.8243], 'JP': [36.2048, 138.2529], 'CN': [35.8617, 104.1954], 
    'IN': [20.5937, 78.9629], 'MX': [23.6345, -102.5528]
}

# Country names for display
COUNTRY_NAMES = {
    'UA': 'Ukraine', 'RU': 'Russia', 'PL': 'Poland', 'DE': 'Germany', 'AT': 'Austria', 
    'US': 'USA', 'CA': 'Canada', 'FR': 'France', 'GB': 'United Kingdom', 'IT': 'Italy', 
    'CZ': 'Czech Republic', 'SK': 'Slovakia', 'HU': 'Hungary', 'RO': 'Romania', 
    'BG': 'Bulgaria', 'RS': 'Serbia', 'HR': 'Croatia', 'SI': 'Slovenia', 'BY': 'Belarus', 
    'LT': 'Lithuania', 'LV': 'Latvia', 'EE': 'Estonia', 'FI': 'Finland', 'SE': 'Sweden', 
    'NO': 'Norway', 'DK': 'Denmark', 'NL': 'Netherlands', 'BE': 'Belgium', 'CH': 'Switzerland', 
    'ES': 'Spain', 'PT': 'Portugal', 'AU': 'Australia', 'BR': 'Brazil', 'AR': 'Argentina', 
    'IL': 'Israel', 'TR': 'Turkey', 'GR': 'Greece', 'JP': 'Japan', 'CN': 'China', 
    'IN': 'India', 'MX': 'Mexico'
}

# Ukrainian macroregion coordinates
MACROREGION_COORDINATES = {
    'W': [49.2, 24.8],          # Захід (West)
    'KYV': [50.4, 30.5],        # Київ (Kyiv)
    'E': [49.0, 37.8],          # Схід (East)
    'C': [49.0, 32.0],          # Центр (Center)
    'S': [46.5, 31.0],          # Південь (South)
    'N': [51.5, 32.5]           # Північ (North)
}

# Macroregion display names
MACROREGION_NAMES = {
    'W': 'Захід (West)',
    'KYV': 'Київ (Kyiv)', 
    'E': 'Схід (East)',
    'C': 'Центр (Center)',
    'S': 'Південь (South)',
    'N': 'Північ (North)'
}

# =============================================================================
# ZOOM THRESHOLD SETTINGS
# =============================================================================

# Store data for zoom threshold tracking
ZOOM_THRESHOLD_STORE_DATA = {'last_zoom': GEOGRAPHIC_DEFAULT_ZOOM, 'crossed': False}
ZOOM_THRESHOLD_UPDATE_TOLERANCE = 0.1

# =============================================================================
# UI STYLING CONSTANTS
# =============================================================================

# Font sizes and styling
FONT_SIZE_SMALL = '11px'
FONT_SIZE_DEFAULT = '12px'
FONT_SIZE_MEDIUM = '14px'
FONT_SIZE_LARGE = '16px'

# UI colors
UI_COLOR_GRAY = 'gray'
UI_COLOR_DARK_GRAY = '#333'
UI_COLOR_LIGHT_GRAY = '#ddd'
UI_COLOR_BACKGROUND_LIGHT = '#f8f9fa'
UI_COLOR_WHITE = 'white'
UI_COLOR_LINK = 'link'

# Breadcrumb styling
BREADCRUMB_ARROW = " → "
BREADCRUMB_MARGIN = '0 3px'
BREADCRUMB_PADDING = '2px 5px'

# Modal and text styling
MODAL_TEXT_FONT_FAMILY = 'Arial Black'
MODAL_ANNOTATION_BORDER_PADDING = 8

# =============================================================================
# EXPORT AND CSV SETTINGS
# =============================================================================

# CSV export configuration
CSV_EXPORT_COLUMNS = ['Name', 'Date', 'Genre Code', 'Effective Author Name', 'Effective Author Sex', 'Publication City']
CSV_FILENAME_PREFIX = "plug2_selected_export"
CSV_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# =============================================================================
# NLTK AND TEXT PROCESSING
# =============================================================================

# NLTK configuration
NLTK_PUNKT_RESOURCE = 'tokenizers/punkt_tab'
NLTK_PUNKT_PACKAGE = 'punkt_tab'

# =============================================================================
# LEGEND AND ANNOTATION SETTINGS
# =============================================================================

# Chart legend positioning
LEGEND_ORIENTATION = "h"
LEGEND_Y_ANCHOR = "bottom"
LEGEND_Y_POSITION = 0.98
LEGEND_X_ANCHOR = "right"
LEGEND_X_POSITION = 1

# Legend bubble sizes for geographic charts
LEGEND_BUBBLE_SMALL = 12
LEGEND_BUBBLE_MEDIUM = 18
LEGEND_BUBBLE_LARGE = 24

# Annotation positioning
ANNOTATION_XREF = "paper"
ANNOTATION_YREF = "paper"
ANNOTATION_CENTER_X = 0.5
ANNOTATION_CENTER_Y = 0.5
ANNOTATION_INSTRUCTION_Y = -0.1

# =============================================================================
# DEFAULT VALUES FOR DROPDOWNS AND INPUTS
# =============================================================================

# Default selections
DEFAULT_CHART_TYPE = 'year'
DEFAULT_GENRE_FILTER = 'all'
DEFAULT_YEAR_AGGREGATION = 'publications'
DEFAULT_TREND_WINDOW = 3
DEFAULT_TREND_ENABLED = False
DEFAULT_TOP_GENRES_COUNT = 10
DEFAULT_GENRE_SORT_ORDER = 'desc'
DEFAULT_GEO_DATA_TYPE = 'publications'
DEFAULT_YEAR_COLOR_BY = 'none'
DEFAULT_HIERARCHY_START = 'gender'
DEFAULT_HIERARCHY_ITEMS_PER_PAGE = 10

# =============================================================================
# VALIDATION AND LIMITS
# =============================================================================

# Maximum values for various inputs
MAX_TOP_GENRES = 50
MAX_TREND_WINDOW = 20
MIN_TREND_WINDOW = 2
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 5

# Text length limits
MAX_DISPLAY_NAME_LENGTH = 80
MAX_AUTHOR_NAME_LENGTH = 30
MAX_BREADCRUMB_LENGTH = 20

# Chart value limits
CHART_MAX_DTICK_RATIO = 10
CHART_RANGE_MULTIPLIER = 1.1 

# =============================================================================
# HELPER CONSTANTS
# =============================================================================

# Common CSS display values
CSS_DISPLAY_BLOCK = {"display": "block"}
CSS_DISPLAY_NONE = {"display": "none"}

# Common data aggregation types
AGGREGATION_TYPES = ['publications', 'tokens', 'authors']

# Chart types
CHART_TYPES = ['year', 'gender', 'genre', 'geography', 'cities', 'hierarchy']

# Geographic data types  
GEO_DATA_TYPES = ['publications', 'tokens', 'authors']

# Sort orders
SORT_ORDERS = ['asc', 'desc']

# Color grouping options
COLOR_BY_OPTIONS = ['none', 'genre', 'gender'] 
