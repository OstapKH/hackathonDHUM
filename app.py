import dash
from dash import dcc, html, Input, Output, callback, dash_table, State, ALL
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
from collections import Counter
import logging
import math
import re
import nltk

from src.utils.utils import get_lang, expand_code, count_tokens, read_text_content
from src.data.data_processing import load_metadata, get_filtered_dataframe, apply_table_filters
from src.visualizations.charts import generate_hierarchy_chart, create_no_data_chart, create_geography_chart
from src.components.layout import create_app_layout
from src.config.translations import TRANSLATIONS, CODE_DICTIONARY
from src.utils.geocoding import get_city_coords

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .dash-table-container .dash-cell div[data-dash-column="details_button"] {
                cursor: pointer !important;
            }
            .dash-table-container .dash-cell[data-dash-column="details_button"]:hover {
                background-color: #f8f9fa !important;
            }
            .dash-table-container .column-header--select,
            .dash-table-container .cell--select {
                min-width: 50px !important;
                width: 50px !important;
                max-width: 50px !important;
            }
            .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table {
                table-layout: fixed !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    lang = get_lang('EN')
    nltk.download('punkt_tab', quiet=True)

app.title = get_lang('UA')["app_title"]

metadata_df = load_metadata()

app.layout = create_app_layout(metadata_df)
@app.callback(
    Output('language-store', 'data'),
    Input('language-dropdown', 'value')
)
def update_language_store(language):
    return language


@app.callback(
    [Output('header-title', 'children'),
     Output('header-subtitle', 'children'),
     Output('stat-total-records', 'children'),
     Output('stat-unique-authors', 'children'),
     Output('stat-publication-years', 'children'),
     Output('stat-genres', 'children'),
     Output('label-viz-type', 'children'),
     Output('chart-type-dropdown', 'options'),
     Output('label-genre-filter', 'children'),
     Output('genre-filter', 'options'),
     Output('label-year-range', 'children'),
     Output('label-year-aggregation-type', 'children'),
     Output('year-aggregation-type', 'options'),
     Output('label-trend-smoothing', 'children'),
     Output('label-show-trend-line', 'children'),
     Output('trend-toggle', 'label'),
     Output('label-year-color-by', 'children'),
     Output('year-color-by', 'options'),
     Output('label-top-genres-count', 'children'),
     Output('label-sort-order', 'children'),
     Output('genre-sort-order', 'options'),
     Output('header-sample-data', 'children'),
     Output('data-table', 'columns'),
     Output('label-hierarchy-start', 'children'),
     Output('hierarchy-start-dropdown', 'options'),
     Output('hierarchy-breadcrumb-label', 'children'),
     Output('hierarchy-reset-btn', 'children'),
     Output('table-page-size-label', 'children'),
     Output('fuzzy-search-label', 'children'),
     Output('modal-metadata-title', 'children'),
     Output('modal-content-title', 'children'),
     Output('modal-close-btn', 'children'),
     Output('modal-basic-info-header', 'children'),
     Output('modal-publication-info-header', 'children'),
     Output('modal-media-info-header', 'children'),
     Output('modal-classification-info-header', 'children'),
     Output('modal-author-info-header', 'children'),
     Output('modal-translator-info-header', 'children'),
     Output('explanation-main-title', 'children'),
     Output('explanation-card-body', 'children')],
    [Input('language-store', 'data')]
)
def update_texts(lang_code):
    lang = get_lang(lang_code)
    
    chart_type_options = [
        {'label': lang['viz_type_year'], 'value': 'year'},
        {'label': lang['viz_type_gender'], 'value': 'gender'},
        {'label': lang['viz_type_genre'], 'value': 'genre'},
        {'label': lang['viz_type_geography'], 'value': 'geography'},
        {'label': lang.get('viz_type_cities', 'Publication Cities'), 'value': 'cities'},
        {'label': lang.get('viz_type_hierarchy', 'Hierarchical Drilling'), 'value': 'hierarchy'}
    ]

    genre_filter_options = [{'label': lang['all_genres'], 'value': 'all'}] + \
                           [{'label': expand_code(genre, lang_code), 'value': genre} 
                            for genre in sorted(metadata_df['Style Code'].dropna().unique()) if genre]

    genre_sort_options = [
        {"label": lang['sort_desc'], "value": "desc"},
        {"label": lang['sort_asc'], "value": "asc"}
    ]

    year_aggregation_options = [
        {"label": lang['year_agg_publications'], "value": "publications"},
        {"label": lang['year_agg_tokens'], "value": "tokens"},
        {"label": lang['year_agg_authors'], "value": "authors"}
    ]

    year_color_by_options = [
        {"label": lang.get('color_by_none', 'None'), "value": "none"},
        {"label": lang.get('color_by_genre', 'By Genre'), "value": "genre"},
        {"label": lang.get('color_by_gender', 'By Gender'), "value": "gender"}
    ]

    datatable_columns = [
        {"name": lang["datatable_name"], "id": "Name", "editable": True},
        {"name": lang["datatable_pub_year"], "id": "Date", "type": "numeric", "editable": True},
        {"name": lang["datatable_genre"], "id": "Style Code", "editable": True},
        {"name": lang["datatable_author"], "id": "Effective Author Name", "editable": True},
        {"name": lang["datatable_gender"], "id": "Effective Author Sex", "editable": True, "presentation": "dropdown"},
        {"name": lang["datatable_pub_city"], "id": "Publication City", "editable": True},
        {"name": lang.get("datatable_details", "Деталі" if lang_code == 'UA' else "Details"), "id": "details_button", "editable": False, "presentation": "markdown"}
    ]

    return (
        lang['header_title'],
        lang['header_subtitle'],
        lang['total_records'],
        lang['unique_authors'],
        lang.get('dates_stat', lang['publication_years_stat']),
        lang['genres_stat'],
        lang['select_viz_type'],
        chart_type_options,
        lang['filter_by_genre'],
        genre_filter_options,
        lang['year_range'],
        lang['year_aggregation_type'],
        year_aggregation_options,
        lang['trend_smoothing'],
        lang['show_trend_line'],
        lang['enable_trend_line'],
        lang.get('year_color_by', 'Color By'),
        year_color_by_options,
        lang['top_genres_count'],
        lang['sort_order'],
        genre_sort_options,
        lang['sample_data_header'],
        datatable_columns,
        lang['hierarchy_start_point'],
        [
            {'label': lang['hierarchy_start_gender'], 'value': 'gender'},
            {'label': lang['hierarchy_start_year'], 'value': 'year'},
            {'label': lang['hierarchy_start_author'], 'value': 'author'},
            {'label': lang['hierarchy_start_genre'], 'value': 'genre'},
            {'label': lang['hierarchy_start_country'], 'value': 'country'}
        ],
        lang['hierarchy_breadcrumb'],
        lang['hierarchy_reset'],
        lang.get('table_page_size', lang['table_page_size']),
        lang.get('fuzzy_search', lang['fuzzy_search']),
        lang.get('modal_metadata_title', lang['modal_metadata_title']),
        lang.get('modal_content_title', lang['modal_content_title']),
        lang.get('modal_close', lang['modal_close']),
        lang.get('modal_basic_info', '📄 Basic Document Information'),
        lang.get('modal_publication_info', '📚 Publication Info'),
        lang.get('modal_media_info', '🎬 Media Info'),
        lang.get('modal_classification_info', '🏷️ Classification Codes'),
        lang.get('modal_author_info', '👥 Authors Information'),
        lang.get('modal_translator_info', '🌐 Translators Information'),
        lang.get('explanation_main_title', lang['explanation_main_title']),
        [
            html.H4(lang.get('explanation_basic_metadata_title', '📝 Основні метадані твору:'), className="text-info mb-3"),
            html.Ul([
                html.Li(lang.get('explanation_name', 'Name - повна назва твору або документа'), className="mb-2"),
                html.Li(lang.get('explanation_path', 'Path - шлях до файлу в корпусі'), className="mb-2"),
                html.Li(lang.get('explanation_date', 'Date - дата створення твору'), className="mb-2"),
                html.Li(lang.get('explanation_pub_year', 'Date - дата створення твору'), className="mb-2"),
                html.Li(lang.get('explanation_language_code', 'Language Code - ISO код мови твору'), className="mb-2"),
                html.Li(lang.get('explanation_genre_code', 'Style Code - код літературного або документального стилю'), className="mb-2"),
                html.Li(lang.get('explanation_pub_city', 'Publication City - місто, де було опубліковано твір'), className="mb-2"),
                html.Li(lang.get('explanation_publisher', 'Publisher - назва видавця або видавничої організації'), className="mb-2"),
                html.Li(lang.get('explanation_publication', 'Publication - назва видання або збірки'), className="mb-2")
            ], className="mb-4"),
            
            html.H4(lang.get('explanation_media_info_title', '📺 Інформація про медіа:'), className="text-info mb-3"),
            html.Ul([
                html.Li(lang.get('explanation_media_name', 'Media Name - назва медіа-джерела'), className="mb-2"),
                html.Li(lang.get('explanation_media_type', 'Media Type - тип медіа (книга, газета, журнал тощо)'), className="mb-2"),
                html.Li(lang.get('explanation_media_location_code', 'Media Location Code - код місця видання медіа'), className="mb-2"),
                html.Li(lang.get('explanation_media_location_country', 'Media Location Country - країна видання медіа'), className="mb-2"),
                html.Li(lang.get('explanation_media_location_macroregion', 'Media Location Macroregion - макрорегіон видання медіа'), className="mb-2"),
                html.Li(lang.get('explanation_media_location_region', 'Media Location Region - регіон видання медіа'), className="mb-2")
            ], className="mb-4"),
            
            html.H4(lang.get('explanation_classification_title', '🏷 Коди класифікації:'), className="text-info mb-3"),
            html.Ul([
                html.Li(lang.get('explanation_age_code', 'Age Code - код вікової категорії твору'), className="mb-2"),
                html.Li(lang.get('explanation_ortography_code', 'Ortography Code - код системи правопису'), className="mb-2"),
                html.Li(lang.get('explanation_source_code', 'Source Code - код джерела твору'), className="mb-2"),
                html.Li(lang.get('explanation_style_code', 'Style Code - код стилістичної категорії'), className="mb-2"),
                html.Li(lang.get('explanation_branch_aca_code', 'Branch ACA Code - код галузі за академічною класифікацією'), className="mb-2"),
                html.Li(lang.get('explanation_theme_aca_code', 'Theme ACA Code - код тематики за академічною класифікацією'), className="mb-2")
            ], className="mb-4"),
            
            html.H4(lang.get('explanation_author_info_title', '👥 Інформація про авторів:'), className="text-info mb-3"),
            html.Ul([
                html.Li(lang.get('explanation_author_1_name', 'Author 1 Name - ім\'я першого автора'), className="mb-2"),
                html.Li(lang.get('explanation_author_1_sex', 'Author 1 Sex - стать першого автора (Ч/Ж)'), className="mb-2"),
                html.Li(lang.get('explanation_author_1_birthday', 'Author 1 Birthday - дата народження першого автора'), className="mb-2"),
                html.Li(lang.get('explanation_author_1_location_code', 'Author 1 Location Code - код місця народження/проживання першого автора'), className="mb-2"),
                html.Li(lang.get('explanation_author_1_location_country', 'Author 1 Location Country - країна першого автора'), className="mb-2"),
                html.Li(lang.get('explanation_author_1_location_macroregion', 'Author 1 Location Macroregion - макрорегіон першого автора'), className="mb-2"),
                html.Li(lang.get('explanation_author_1_location_region', 'Author 1 Location Region - регіон першого автора'), className="mb-2"),
                html.Li(lang.get('explanation_authors_234', 'Author 2-4 Name/Sex/Birthday/Location - аналогічна інформація для співавторів (2-4)'), className="mb-2", style={'fontStyle': 'italic'})
            ], className="mb-4"),
            
            html.H4(lang.get('explanation_translator_info_title', '🌐 Інформація про перекладачів:'), className="text-info mb-3"),
            html.Ul([
                html.Li(lang.get('explanation_translator_123', 'Translator 1-3 Name/Sex/Birthday/Location - повна інформація про перекладачів (ім\'я, стать, дата народження, місце)'), className="mb-2", style={'fontStyle': 'italic'})
            ], className="mb-4"),
            
            html.H4(lang.get('explanation_viz_title', '📈 Типи візуалізації та їх призначення:'), className="text-info mb-3"),
            html.Ul([
                html.Li(lang.get('explanation_viz_year', 'За роками - показує розподіл публікацій у часі, дозволяє відстежувати історичні тенденції та пікові періоди літературної активності'), className="mb-2"),
                html.Li(lang.get('explanation_viz_gender', 'Стать автора - аналізує гендерний розподіл серед авторів корпусу, показує співвідношення чоловіків та жінок-авторів'), className="mb-2"),
                html.Li(lang.get('explanation_viz_genre', 'Розподіл за стилями - відображає найпопулярніші літературні стилі в корпусі, дозволяє оцінити стильове різноманіття'), className="mb-2"),
                html.Li(lang.get('explanation_viz_geography', 'Географічний розподіл - показує географічне походження публікацій, допомагає зрозуміти регіональні особливості літературного процесу'), className="mb-2"),
                html.Li(lang.get('explanation_viz_cities', 'Міста публікації - відображає найактивніші центри видавничої діяльності'), className="mb-2")
            ], className="mb-4"),
            
            html.H4(lang.get('explanation_controls_title', '⚙️ Елементи керування та фільтри:'), className="text-info mb-3"),
            html.Ul([
                html.Li(lang.get('explanation_genre_filter', 'Фільтр за стилем - дозволяє обмежити аналіз конкретним літературним стилем для більш детального вивчення'), className="mb-2"),
                html.Li(lang.get('explanation_year_range', 'Діапазон років - встановлює часові межі для аналізу, корисно для вивчення конкретних історичних періодів'), className="mb-2"),
                html.Li(lang.get('explanation_aggregation', 'Агрегація даних - визначає, що саме підраховувати: кількість публікацій, кількість токенів (слів) або кількість унікальних авторів'), className="mb-2"),
                html.Li(lang.get('explanation_trend_line', 'Лінія тренду - показує загальну тенденцію зміни показників у часі, згладжуючи короткотермінові коливання'), className="mb-2"),
                html.Li(lang.get('explanation_color_coding', 'Розподіл за додатковими параметрами - дозволяє візуально розділити дані за стилем або статтю автора для багатовимірного аналізу'), className="mb-2")
            ], className="mb-4"),
            
            html.H4(lang.get('explanation_search_title', '🔍 Функціонал пошуку в таблиці:'), className="text-info mb-3"),
            html.Ul([
                html.Li(lang.get('explanation_search_filter', 'Використовуйте вбудовані фільтри в стовпцях таблиці для швидкого пошуку конкретних творів, авторів або років'), className="mb-2"),
                html.Li(lang.get('explanation_search_sort', 'Клікайте на заголовки стовпців для сортування даних за відповідним полем'), className="mb-2"),
                html.Li(lang.get('explanation_search_pagination', 'Таблиця підтримує пагінацію - використовуйте навігацію для перегляду всіх записів'), className="mb-2")
            ], className="mb-4"),
            
            html.H4(lang.get('explanation_tokens_title', '🔤 Токенізація тексту:'), className="text-info mb-3"),
            html.P(lang.get('explanation_tokens_desc', 'Токени - це окремі слова та розділові знаки в тексті. Використовується професійний токенізатор NLTK punkt_tab для точного підрахунку лексичних одиниць.'), className="mb-4"),
            
            html.H4(lang.get('explanation_corpus_abbreviations_title', '📋 Основні скорочення корпусу:'), className="text-info mb-3"),
            html.P(lang.get('explanation_genres_subtitle', 'У корпусі розмічено деякі стилі (DOC.GENRE):'), className="mb-2", style={'fontWeight': 'bold'}),
            html.Div([
                html.P(lang.get('explanation_genre_line1', 'AUT — автобіографія | BLO — блог | CHI — дитячий | DIA — щоденник | DIC — словник | DIS — дисертація | DRA — драма | EDU — навчальний'), className="mb-2"),
                html.P(lang.get('explanation_genre_line2', 'HUM — гумор | INT — інтерв\'ю | CON — бесіда | MON — монолог | LET — лист | MEM — спогади | POP — популярний | REV — рецензія | FIC — художня література'), className="mb-2")
            ], className="mb-3"),
            
            html.P(lang.get('explanation_age_subtitle', 'Для дитячих творів є розмітка за віком (DOC.AGECODE):'), className="mb-2", style={'fontWeight': 'bold'}),
            html.P(lang.get('explanation_age_line', 'DOS — дошкільний вік — 4-6 років | MLS — молодший шкільний вік — 6/7-11 років | SRS — середній шкільний вік — 11-15 років | STS — старший вік — 15-17 років'), className="mb-3"),
            
            html.P(lang.get('explanation_scientific_subtitle', 'Для наукових текстів додано тематичну розмітку. На сторінці пошуку можна обрати такі атрибути:'), className="mb-2", style={'fontWeight': 'bold'}),
            
            html.P(lang.get('explanation_branch_subtitle', 'Галузь (DOC.BRANCH):'), className="mb-1", style={'fontWeight': 'bold'}),
            html.P(lang.get('explanation_branch_line', 'SOC — суспільні науки | TEC — техніка | NAT — природничі науки'), className="mb-3"),
            
            html.P(lang.get('explanation_thema_subtitle', 'Тематика (DOC.THEMA):'), className="mb-1", style={'fontWeight': 'bold'}),
            html.Div([
                html.P(lang.get('explanation_thema_line1', 'ART — мистецтво | BIO — біологія | CHE — хімія | ECN — економіка | ETH — етнографія | FMA — фізика, математика | GEL — геологія'), className="mb-1"),
                html.P(lang.get('explanation_thema_line2', 'GEO — географія | HIS — історія | IT — інформаційні технології | JUR — правознавство | MED — медицина | MIL — військова справа'), className="mb-1"),
                html.P(lang.get('explanation_thema_line3', 'PED — педагогіка | PHL — філологія | PHS — філософія | POL — політологія | PSY — психологія | REZ — релігієзнавство'), className="mb-1")
            ])
        ]
    )

def generate_hierarchy_chart(df, hierarchy_path, hierarchy_selections, hierarchy_start, current_page, items_per_page, lang):
    """Generate hierarchical drill-down chart based on current path and selections"""
    
    drill_paths = {
        'gender': ['gender', 'country', 'author', 'genre', 'texts'],
        'year': ['year', 'country', 'gender', 'author', 'genre', 'texts'],
        'author': ['author', 'country', 'gender', 'genre', 'texts'],
        'genre': ['genre', 'country', 'gender', 'author', 'texts'],
        'country': ['country', 'gender', 'author', 'genre', 'texts']
    }
    
    expected_path = drill_paths.get(hierarchy_start, drill_paths['gender'])
    
    current_level_index = len(hierarchy_path)
    if current_level_index >= len(expected_path):
        current_level_index = len(expected_path) - 1
    
    current_level = expected_path[current_level_index]
    
    filtered_df = df.copy()
    for i, level in enumerate(hierarchy_path):
        if level in hierarchy_selections:
            selection = hierarchy_selections[level]
            if level == 'gender':
                filtered_df = filtered_df[filtered_df['Effective Author Sex'] == selection]
            elif level == 'country':
                filtered_df = filtered_df[filtered_df['Effective Author Location Country'] == selection]
            elif level == 'author':
                filtered_df = filtered_df[filtered_df['Effective Author Name'] == selection]
            elif level == 'genre':
                filtered_df = filtered_df[filtered_df['Style Code'] == selection]
            elif level == 'year':
                try:
                    year = int(selection)
                    filtered_df = filtered_df[filtered_df['Date'] == year]
                except (ValueError, TypeError):
                    pass
    if current_level == 'gender':
        counts = filtered_df['Effective Author Sex'].value_counts().sort_values(ascending=False)
        if counts.empty:
            return create_no_data_chart(lang)
        
        max_value = int(counts.max())
        
        total_items = len(counts)
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_counts = counts.iloc[start_idx:end_idx]
        
        paginated_counts = paginated_counts.iloc[::-1]
        
        title_suffix = f"{lang['hierarchy_level_gender']} ({lang.get('page_indicator', 'Page')} {current_page}, {len(paginated_counts)} {lang.get('of_total', 'of')} {total_items})"
        
        fig = px.bar(
            x=paginated_counts.values,
            y=paginated_counts.index,
            orientation='h',
            title=title_suffix,
            labels={'x': lang['chart_yaxis_publications'], 'y': lang['hierarchy_level_gender']}
        )
        
        fig.update_layout(
            xaxis=dict(
                range=[0, max_value * 1.1],
                dtick=max(1, max_value // 10),
                tickformat='d'
            )
        )
        
    elif current_level == 'country':
        counts = filtered_df['Effective Author Location Country'].value_counts().sort_values(ascending=False)
        if counts.empty:
            return create_no_data_chart(lang)
        
        max_value = int(counts.max())
        
        total_items = len(counts)
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_counts = counts.iloc[start_idx:end_idx]
        
        paginated_counts = paginated_counts.iloc[::-1]
        
        title_suffix = f"{lang['hierarchy_level_country']} ({lang.get('page_indicator', 'Page')} {current_page}, {len(paginated_counts)} {lang.get('of_total', 'of')} {total_items})"
        
        fig = px.bar(
            x=paginated_counts.values,
            y=paginated_counts.index,
            orientation='h',
            title=title_suffix,
            labels={'x': lang['chart_yaxis_publications'], 'y': lang['hierarchy_level_country']}
        )
        
        fig.update_layout(
            xaxis=dict(
                range=[0, max_value * 1.1],
                dtick=max(1, max_value // 10),
                tickformat='d'
            )
        )
        
    elif current_level == 'author':
        counts = filtered_df['Effective Author Name'].value_counts().sort_values(ascending=False)
        if counts.empty:
            return create_no_data_chart(lang)
        
        max_value = int(counts.max())
        
        total_items = len(counts)
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_counts = counts.iloc[start_idx:end_idx]
        
        paginated_counts = paginated_counts.iloc[::-1]
        
        title_suffix = f"{lang['hierarchy_level_author']} ({lang.get('page_indicator', 'Page')} {current_page}, {len(paginated_counts)} {lang.get('of_total', 'of')} {total_items})"
        
        fig = px.bar(
            x=paginated_counts.values,
            y=paginated_counts.index,
            orientation='h',
            title=title_suffix,
            labels={'x': lang['chart_yaxis_publications'], 'y': lang['hierarchy_level_author']}
        )
        
        fig.update_layout(
            xaxis=dict(
                range=[0, max_value * 1.1],
                dtick=max(1, max_value // 10),
                tickformat='d'
            )
        )
        
    elif current_level == 'genre':
        counts = filtered_df['Style Code'].value_counts().sort_values(ascending=False)
        if counts.empty:
            return create_no_data_chart(lang)
        
        max_value = int(counts.max())
        
        total_items = len(counts)
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_counts = counts.iloc[start_idx:end_idx]
        
        paginated_counts = paginated_counts.iloc[::-1]
        
        title_suffix = f"{lang['hierarchy_level_genre']} ({lang.get('page_indicator', 'Page')} {current_page}, {len(paginated_counts)} {lang.get('of_total', 'of')} {total_items})"
        
        fig = px.bar(
            x=paginated_counts.values,
            y=paginated_counts.index,
            orientation='h',
            title=title_suffix,
            labels={'x': lang['chart_yaxis_publications'], 'y': lang['hierarchy_level_genre']}
        )
        
        fig.update_layout(
            xaxis=dict(
                range=[0, max_value * 1.1],
                dtick=max(1, max_value // 10),
                tickformat='d'
            )
        )
        
    elif current_level == 'year':
        year_counts = filtered_df['Date'].value_counts().sort_values(ascending=False)
        if year_counts.empty:
            return create_no_data_chart(lang)
        
        max_value = int(year_counts.max())
        
        items_per_page_years = items_per_page * 2
        total_items = len(year_counts)
        start_idx = (current_page - 1) * items_per_page_years
        end_idx = start_idx + items_per_page_years
        paginated_counts = year_counts.iloc[start_idx:end_idx]
        
        paginated_counts = paginated_counts.sort_index()
        
        title_suffix = f"{lang['hierarchy_level_year']} ({lang.get('page_indicator', 'Page')} {current_page}, {len(paginated_counts)} {lang.get('of_total', 'of')} {total_items})"
        
        fig = px.bar(
            x=paginated_counts.index,
            y=paginated_counts.values,
            title=title_suffix,
            labels={'x': lang['chart_xaxis_year'], 'y': lang['chart_yaxis_publications']}
        )
        
        fig.update_layout(
            yaxis=dict(
                range=[0, max_value * 1.1],
                dtick=max(1, max_value // 10),
                tickformat='d'
            )
        )
        
    elif current_level == 'texts':
        if len(filtered_df) == 0:
            return create_no_data_chart(lang)
        
        total_texts = len(filtered_df)
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        sample_texts = filtered_df.iloc[start_idx:end_idx]
        
        fig = go.Figure()
        
        title_text = f"{lang['hierarchy_level_texts']} ({lang.get('page_indicator', 'Page')} {current_page}, {len(sample_texts)} {lang.get('of_total', 'of')} {total_texts})"
        
        text_list = []
        for i, (_, row) in enumerate(sample_texts.iterrows()):
            name = row['Name']
            year = row.get('Date', 'N/A')
            author = row.get('Effective Author Name', 'N/A')
            
            display_name = name[:80] + '...' if len(str(name)) > 80 else str(name)
            text_list.append(f"{i+1}. {display_name}")
            if str(year) != 'N/A' and not pd.isna(year):
                text_list[-1] += f" ({int(year)})"
            if str(author) != 'N/A' and author:
                author_short = author[:30] + '...' if len(str(author)) > 30 else str(author)
                text_list[-1] += f" - {author_short}"
        
        y_positions = list(range(len(text_list), 0, -1))
        
        for i, (text, y_pos) in enumerate(zip(text_list, y_positions)):
            fig.add_annotation(
                x=0,
                y=y_pos,
                text=text,
                showarrow=False,
                xref="x", yref="y",
                xanchor='left', yanchor='middle',
                font=dict(size=11, color='#333'),
                bordercolor='#ddd',
                borderwidth=1,
                bgcolor='#f8f9fa' if i % 2 == 0 else 'white',
                borderpad=8
            )
        
        fig.update_layout(
            title=title_text,
            xaxis=dict(
                visible=False,
                range=[-0.1, 1]
            ),
            yaxis=dict(
                visible=False,
                range=[0, len(text_list) + 1]
            ),
            height=max(400, len(text_list) * 35 + 100),
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False
        )
        

    else:
        return create_no_data_chart(lang)
    
    if current_level != 'texts':
        fig.update_traces(
            marker_color='#17a2b8',
            marker_line_color='rgba(0,0,0,0.2)',
            marker_line_width=1,
            hovertemplate='<b>%{y}</b><br>' + lang['hierarchy_publications_count'].format(count='%{x}') + '<extra></extra>'
        )
        
        fig.update_layout(
            annotations=[
                dict(
                    text=lang['hierarchy_click_to_drill'],
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.1,
                    xanchor='center', yanchor='top',
                    font=dict(size=12, color='gray')
                )
            ]
        )
    
    return fig

def create_no_data_chart(lang):
    """Create a chart showing no data message"""
    fig = go.Figure()
    fig.add_annotation(
        text=lang['hierarchy_no_data'],
        xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        font=dict(size=16, color='gray'),
        showarrow=False
    )
    fig.update_layout(
        title=lang['no_data'],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig

@app.callback(
    Output('zoom-threshold-store', 'data'),
    [Input('main-chart', 'relayoutData')],
    [State('zoom-threshold-store', 'data'),
     State('chart-type-dropdown', 'value')]
)
def detect_zoom_threshold_crossing(relayout_data, zoom_store, chart_type):
    if chart_type != 'geography':
        raise PreventUpdate
    
    COUNTRY_THRESHOLD = 3
    MACROREGION_THRESHOLD = 6
    current_zoom = zoom_store.get('last_zoom', 3.0)
    
    if relayout_data and isinstance(relayout_data, dict) and 'mapbox.zoom' in relayout_data:
        try:
            new_zoom = float(relayout_data['mapbox.zoom'])
            current_level = 0 if current_zoom < COUNTRY_THRESHOLD else (1 if current_zoom < MACROREGION_THRESHOLD else 2)
            new_level = 0 if new_zoom < COUNTRY_THRESHOLD else (1 if new_zoom < MACROREGION_THRESHOLD else 2)
            
            if current_level != new_level:
                import time
                return {'last_zoom': new_zoom, 'crossed': True, 'timestamp': time.time()}
            else:
                if abs(new_zoom - current_zoom) > 0.1:
                    return {**zoom_store, 'last_zoom': new_zoom}
        except (TypeError, ValueError):
            pass
    
    raise PreventUpdate

@app.callback(
    Output('main-chart', 'figure'),
    [Input('chart-type-dropdown', 'value'),
     Input('genre-filter', 'value'),
     Input('year-range', 'value'),
     Input('year-aggregation-type', 'value'),
     Input('trend-window', 'value'),
     Input('trend-toggle', 'value'),
     Input('top-genres-count', 'value'),
     Input('genre-sort-order', 'value'),
     Input('geo-data-type', 'value'),
     Input('year-color-by', 'value'),
     Input('zoom-threshold-store', 'data'),
     Input('hierarchy-path-store', 'data'),
     Input('hierarchy-selections-store', 'data'),
     Input('hierarchy-start-store', 'data'),
     Input('hierarchy-current-page-store', 'data'),
     Input('hierarchy-items-per-page-store', 'data'),
     Input('language-store', 'data')],
    [State('main-chart', 'relayoutData')]
)
def update_chart(chart_type, genre_filter, year_range, year_agg_type, trend_window, show_trend, top_genres_count, genre_sort_order, geo_data_type, year_color_by, zoom_store, hierarchy_path, hierarchy_selections, hierarchy_start, current_page, items_per_page, lang_code, relayout_data):
    """Update the main chart based on user selections"""
    lang = get_lang(lang_code)

    if metadata_df.empty:
        return {}
    
    filtered_df = metadata_df.copy()
    
    if genre_filter != 'all':
        filtered_df = filtered_df[filtered_df['Style Code'] == genre_filter]
    
    if year_range:
        filtered_df = filtered_df[
            (filtered_df['Date'] >= year_range[0]) & 
            (filtered_df['Date'] <= year_range[1])
        ]
    
    if chart_type == 'year':
        valid_years_df = filtered_df.dropna(subset=['Date'])
        
        if len(valid_years_df) > 0:
            fig = go.Figure()
            
            style_colors = px.colors.qualitative.Set3 + px.colors.qualitative.Pastel1 + px.colors.qualitative.Set1
            gender_colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc', '#c2c2f0']
            
            if year_color_by != 'none':
                color_field = 'Style Code' if year_color_by == 'genre' else 'Effective Author Sex'
                colors = style_colors if year_color_by == 'genre' else gender_colors
                
                categories = valid_years_df[color_field].dropna().unique()
                color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(categories)}
                
                if year_agg_type == 'publications':
                    grouped = valid_years_df.groupby(['Date', color_field]).size().reset_index(name='count')
                    y_axis_title = lang['chart_yaxis_publications']
                    chart_title = f"{lang['chart_title_year']} - {lang.get('color_by_' + year_color_by, year_color_by.title())}"
                    
                elif year_agg_type == 'tokens':
                    lang = get_lang('EN')
                    valid_years_df = valid_years_df.copy()
                    valid_years_df['token_count'] = valid_years_df['Name'].apply(count_tokens)
                    grouped = valid_years_df.groupby(['Date', color_field])['token_count'].sum().reset_index(name='count')
                    y_axis_title = lang['chart_yaxis_tokens']
                    chart_title = f"{lang['chart_title_year']} - {lang['year_agg_tokens']} - {lang.get('color_by_' + year_color_by, year_color_by.title())}"
                    
                elif year_agg_type == 'authors':
                    grouped = valid_years_df.groupby(['Date', color_field])['Effective Author Name'].nunique().reset_index(name='count')
                    y_axis_title = lang['chart_yaxis_authors']
                    chart_title = f"{lang['chart_title_year']} - {lang['year_agg_authors']} - {lang.get('color_by_' + year_color_by, year_color_by.title())}"
                
                year_totals = grouped.groupby('Date')['count'].sum().to_dict()
                
                for category in categories:
                    category_data = grouped[grouped[color_field] == category]
                    if not category_data.empty:
                        category_data = category_data.copy()
                        category_data['percentage'] = category_data.apply(
                            lambda row: (row['count'] / year_totals[row['Date']]) * 100, axis=1
                        )
                        category_data['total'] = category_data['Date'].map(year_totals)
                        
                        if year_color_by == 'genre':
                            category_label = lang.get('datatable_genre', 'Genre')
                        else:
                            category_label = lang.get('datatable_gender', 'Gender')
                        
                        agg_type_labels = {
                            'publications': lang.get('chart_legend_publications', 'Publications'),
                            'tokens': lang.get('chart_yaxis_tokens', 'Tokens'), 
                            'authors': lang.get('chart_yaxis_authors', 'Authors')
                        }
                        agg_label = agg_type_labels.get(year_agg_type, year_agg_type)
                        
                        hover_template = (
                            f"<b>{lang.get('chart_xaxis_year', 'Year')}: %{{x}}</b><br>"
                            f"<b>{category_label}: {str(category)}</b><br>"
                            f"{lang.get('hover_count', 'Count')}: %{{y}} {y_axis_title.lower()}<br>"
                            f"{lang.get('hover_percentage', 'Percentage')}: %{{customdata[0]:.1f}}%<br>"
                            f"<b>{lang.get('hover_total', 'Total')}: %{{customdata[1]}}</b><br>"
                            f"<extra></extra>"
                        )
                        
                        fig.add_trace(go.Bar(
                            x=category_data['Date'],
                            y=category_data['count'],
                            name=str(category),
                            marker_color=color_map[category],
                            marker_line_width=0,
                            width=0.8,
                            customdata=list(zip(category_data['percentage'], category_data['total'])),
                            hovertemplate=hover_template
                        ))
                
                year_counts = grouped.groupby('Date')['count'].sum().reset_index()
                
                fig.update_layout(
                    barmode='stack',
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=0.98,
                        xanchor="right",
                        x=1
                    )
                )
                
            else:
                if year_agg_type == 'publications':
                    year_counts = valid_years_df.groupby('Date').size().reset_index(name='count')
                    y_axis_title = lang['chart_yaxis_publications']
                    chart_title = lang['chart_title_year']
                    legend_label = lang['chart_legend_publications']
                    
                    fig.add_trace(go.Histogram(
                        x=valid_years_df['Date'],
                        xbins=dict(size=1),
                        marker_color='#0dcaf0',
                        marker_line_width=0,
                        name=legend_label,
                        hovertemplate=f"<b>{lang.get('chart_xaxis_year', 'Year')}: %{{x}}</b><br>{lang.get('chart_legend_publications', 'Publications')}: %{{y}}<extra></extra>"
                    ))
                    
                elif year_agg_type == 'tokens':
                    lang = get_lang('EN')
                    
                    valid_years_df = valid_years_df.copy()
                    valid_years_df['token_count'] = valid_years_df['Name'].apply(count_tokens)
                    
                    year_counts = valid_years_df.groupby('Date')['token_count'].sum().reset_index(name='count')
                    y_axis_title = lang['chart_yaxis_tokens']
                    chart_title = f"{lang['chart_title_year']} - {lang['year_agg_tokens']}"
                    legend_label = lang['year_agg_tokens']
                    
                    fig.add_trace(go.Bar(
                        x=year_counts['Date'],
                        y=year_counts['count'],
                        marker_color='#28a745',
                        marker_line_width=0,
                        name=legend_label,
                        width=0.8,
                        hovertemplate=f"<b>{lang.get('chart_xaxis_year', 'Year')}: %{{x}}</b><br>{lang.get('chart_yaxis_tokens', 'Tokens')}: %{{y:,}}<extra></extra>"
                    ))
                    
                elif year_agg_type == 'authors':
                    year_counts = valid_years_df.groupby('Date')['Effective Author Name'].nunique().reset_index(name='count')
                    y_axis_title = lang['chart_yaxis_authors']
                    chart_title = f"{lang['chart_title_year']} - {lang['year_agg_authors']}"
                    legend_label = lang['year_agg_authors']
                    
                    fig.add_trace(go.Bar(
                        x=year_counts['Date'],
                        y=year_counts['count'],
                        marker_color='#fd7e14',
                        marker_line_width=0,
                        name=legend_label,
                        width=0.8,
                        hovertemplate=f"<b>{lang.get('chart_xaxis_year', 'Year')}: %{{x}}</b><br>{lang.get('chart_yaxis_authors', 'Authors')}: %{{y}}<extra></extra>"
                    ))
                
                fig.update_layout(
                    showlegend=False
                )
            
            year_counts = year_counts.sort_values('Date')
            
            if show_trend and year_color_by == 'none' and len(year_counts) >= trend_window:
                min_periods = max(2, trend_window // 2)
                year_counts['trend'] = year_counts['count'].rolling(
                    window=trend_window, 
                    center=True, 
                    min_periods=min_periods
                ).mean()
                
                trend_data = year_counts.dropna(subset=['trend'])
                
                fig.add_trace(go.Scatter(
                    x=trend_data['Date'],
                    y=trend_data['trend'],
                    mode='lines',
                    line=dict(color='#009ab8', width=3, dash='solid'),
                    name=lang['chart_trend_line_label'].format(trend_window=trend_window),
                    hovertemplate=lang['chart_trend_hover'].format(trend_window=trend_window)
                ))
            elif show_trend and year_color_by == 'none' and len(year_counts) >= 3:
                fig.add_trace(go.Scatter(
                    x=year_counts['Date'],
                    y=year_counts['count'],
                    mode='lines',
                    line=dict(color='red', width=2, dash='dash'),
                    name=lang['chart_insufficient_data'],
                    hovertemplate=lang['chart_insufficient_data_hover']
                ))
            
            fig.update_layout(
                title=chart_title,
                xaxis_title=lang['chart_xaxis_year'],
                yaxis_title=y_axis_title,
                bargap=0.3,
                bargroupgap=0.1
            )
        else:
            fig = px.histogram(
                x=[],
                title=lang['chart_no_year_data']
            )
        
    elif chart_type == 'gender':
        gender_counts = filtered_df['Effective Author Sex'].value_counts()
        
        gender_colors = ["gold", "mediumturquoise", "darkorange", "lightgreen", "lightcoral", "lightskyblue"]
        gender_patterns = [".", "x", "+", "-", "/", "\\"]
        
        while len(gender_colors) < len(gender_counts):
            gender_colors.extend(["gold", "mediumturquoise", "darkorange", "lightgreen", "lightcoral", "lightskyblue"])
            gender_patterns.extend([".", "x", "+", "-", "/", "\\"])
        
        colors = gender_colors[:len(gender_counts)]
        patterns = gender_patterns[:len(gender_counts)]
        
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=gender_counts.index,
                    values=gender_counts.values,
                    textfont_size=16,
                    marker=dict(
                        colors=colors, 
                        pattern=dict(shape=patterns)
                    )
                )
            ]
        )
        
        fig.update_layout(
            title=lang['chart_title_gender'],
            font=dict(size=14)
        )
        
    elif chart_type == 'genre':
        style_counts = filtered_df['Style Code'].value_counts()
        
        top_styles = style_counts.head(top_genres_count)
        
        if genre_sort_order == 'asc':
            display_styles = top_styles.sort_values(ascending=True)
            sort_label = lang['sort_asc']
        else:
            display_styles = top_styles.sort_values(ascending=False)
            sort_label = lang['sort_desc']
        
        fig = px.bar(
            x=display_styles.values, 
            y=display_styles.index,
            orientation='h', 
            title=lang['chart_title_genre'].format(top_genres_count=top_genres_count, sort_label=sort_label),
            labels={'x': lang['chart_xaxis_works'], 'y': lang['chart_yaxis_genre']}
        )
        
        fig.update_traces(
            marker_color='#17a2b8',
            marker_line_color='rgba(0,0,0,0.2)',
            marker_line_width=1
        )
        
    elif chart_type == 'geography':
        
        zoom = 3.0
        center = {'lat': 49.0, 'lon': 32.0}
        if relayout_data:
            if 'mapbox.zoom' in relayout_data:
                zoom = float(relayout_data['mapbox.zoom'])
            if 'mapbox.center' in relayout_data:
                center = relayout_data['mapbox.center']

        COUNTRY_THRESHOLD = 3
        MACROREGION_THRESHOLD = 6

        lats, lons, counts, hover_texts = [], [], [], []
        marker_sizes = []
        colorscale = 'viridis'

        if zoom >= MACROREGION_THRESHOLD:
            if geo_data_type == 'authors':
                counts_by_loc = filtered_df.groupby('Publication City')['Effective Author Name'].nunique()
                data_label = lang['geo_authors_city']
                chart_title = lang['chart_title_geo_city'].format(data_label=data_label)
            elif geo_data_type == 'tokens':
                lang = get_lang('EN')
                filtered_df_copy = filtered_df.copy()
                filtered_df_copy['token_count'] = filtered_df_copy['Name'].apply(count_tokens)
                counts_by_loc = filtered_df_copy.groupby('Publication City')['token_count'].sum()
                data_label = lang.get('geo_tokens_city', 'Tokens by City')
                chart_title = lang['chart_title_geo_city'].format(data_label=data_label)
            else:
                counts_by_loc = filtered_df['Publication City'].value_counts()
                data_label = lang['geo_publications_city']
                chart_title = lang['chart_title_geo_city'].format(data_label=data_label)

            counts_by_loc = counts_by_loc[counts_by_loc.index != '']
            
            for city_name, count in counts_by_loc.items():
                coords = get_city_coords(city_name)
                if coords:
                    lats.append(coords[0])
                    lons.append(coords[1])
                    counts.append(count)
                    if geo_data_type == 'tokens':
                        hover_texts.append(f"{city_name}<br>{data_label}: {count:,}")
                    else:
                        hover_texts.append(f"{city_name}<br>{data_label}: {count}")

            if lats:
                marker_sizes = [max(5, min(40, math.log(c+1) * 5)) for c in counts]
                colorscale = 'YlOrRd'
        elif zoom >= COUNTRY_THRESHOLD:
            if geo_data_type == 'authors':
                counts_by_loc = filtered_df.groupby('Effective Author Location Macroregion')['Effective Author Name'].nunique()
                data_label = lang.get('geo_authors_macroregion', 'Authors by Macroregion')
                chart_title = lang['chart_title_geo_macroregion'].format(data_label=data_label)
            else:
                counts_by_loc = filtered_df['Effective Author Location Macroregion'].value_counts()
                data_label = lang.get('geo_publications_macroregion', 'Publications by Macroregion')
                chart_title = lang['chart_title_geo_macroregion'].format(data_label=data_label)

            counts_by_loc = counts_by_loc[counts_by_loc.index != '']
            
            macroregion_coords = {
                'W': [49.2, 24.8],
                'KYV': [50.4, 30.5],
                'E': [49.0, 37.8],
                'C': [49.0, 32.0],
                'S': [46.5, 31.0],
                'N': [51.5, 32.5]
            }
            
            macroregion_names = {
                'W': 'Захід (West)',
                'KYV': 'Київ (Kyiv)', 
                'E': 'Схід (East)',
                'C': 'Центр (Center)',
                'S': 'Південь (South)',
                'N': 'Північ (North)'
            }
            
            for macroregion_code, count in counts_by_loc.items():
                if macroregion_code and macroregion_code in macroregion_coords:
                    macroregion_name = macroregion_names.get(macroregion_code, macroregion_code)
                    lats.append(macroregion_coords[macroregion_code][0])
                    lons.append(macroregion_coords[macroregion_code][1])
                    counts.append(count)
                    hover_texts.append(f"{macroregion_name}<br>{data_label}: {count}")
            
            if lats:
                max_count = max(counts) if counts else 1
                marker_sizes = [max(10, min(50, (count / max_count) * 45 + 15)) for count in counts]
                colorscale = 'Plasma'
        else:
            if geo_data_type == 'authors':
                counts_by_loc = filtered_df.groupby('Effective Author Location Country')['Effective Author Name'].nunique()
                data_label = lang['chart_data_label_authors']
            else:
                counts_by_loc = filtered_df['Effective Author Location Country'].value_counts()
                data_label = lang['chart_data_label_publications']
            
            chart_title = lang['chart_title_geo'].format(data_label=data_label)

            country_coords = { 'UA': [49.0, 32.0], 'RU': [55.7558, 37.6176], 'PL': [52.2297, 21.0122], 'DE': [51.1657, 10.4515], 'AT': [47.5162, 14.5501], 'US': [39.8283, -98.5795], 'CA': [56.1304, -106.3468], 'FR': [46.2276, 2.2137], 'GB': [55.3781, -3.4360], 'IT': [41.8719, 12.5674], 'CZ': [49.8175, 15.4730], 'SK': [48.6690, 19.6990], 'HU': [47.1625, 19.5033], 'RO': [45.9432, 24.9668], 'BG': [42.7339, 25.4858], 'RS': [44.0165, 21.0059], 'HR': [45.1000, 15.2000], 'SI': [46.1512, 14.9955], 'BY': [53.7098, 27.9534], 'LT': [55.1694, 23.8813], 'LV': [56.8796, 24.6032], 'EE': [58.5953, 25.0136], 'FI': [61.9241, 25.7482], 'SE': [60.1282, 18.6435], 'NO': [60.4720, 8.4689], 'DK': [56.2639, 9.5018], 'NL': [52.1326, 5.2913], 'BE': [50.5039, 4.4699], 'CH': [46.8182, 8.2275], 'ES': [40.4637, -3.7492], 'PT': [39.3999, -8.2245], 'AU': [-25.2744, 133.7751], 'BR': [-14.2350, -51.9253], 'AR': [-38.4161, -63.6167], 'IL': [31.0461, 34.8516], 'TR': [38.9637, 35.2433], 'GR': [39.0742, 21.8243], 'JP': [36.2048, 138.2529], 'CN': [35.8617, 104.1954], 'IN': [20.5937, 78.9629], 'MX': [23.6345, -102.5528] }
            country_names = { 'UA': 'Ukraine', 'RU': 'Russia', 'PL': 'Poland', 'DE': 'Germany', 'AT': 'Austria', 'US': 'USA', 'CA': 'Canada', 'FR': 'France', 'GB': 'United Kingdom', 'IT': 'Italy', 'CZ': 'Czech Republic', 'SK': 'Slovakia', 'HU': 'Hungary', 'RO': 'Romania', 'BG': 'Bulgaria', 'RS': 'Serbia', 'HR': 'Croatia', 'SI': 'Slovenia', 'BY': 'Belarus', 'LT': 'Lithuania', 'LV': 'Latvia', 'EE': 'Estonia', 'FI': 'Finland', 'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark', 'NL': 'Netherlands', 'BE': 'Belgium', 'CH': 'Switzerland', 'ES': 'Spain', 'PT': 'Portugal', 'AU': 'Australia', 'BR': 'Brazil', 'AR': 'Argentina', 'IL': 'Israel', 'TR': 'Turkey', 'GR': 'Greece', 'JP': 'Japan', 'CN': 'China', 'IN': 'India', 'MX': 'Mexico' }

            for country_code, count in counts_by_loc.items():
                if country_code and country_code in country_coords:
                    country_name = country_names.get(country_code, country_code)
                    lats.append(country_coords[country_code][0])
                    lons.append(country_coords[country_code][1])
                    counts.append(count)
                    hover_texts.append(f"{country_name}<br>{data_label}: {count}")
            
            if lats:
                max_count = max(counts) if counts else 1
                marker_sizes = [max(8, min(50, (count / max_count) * 40 + 10)) for count in counts]
                colorscale = 'RdBu_r'

        if lats:
            text_labels = []
            if marker_sizes:
                max_size = max(marker_sizes)
                threshold_size = max_size * 0.6
                for i, size in enumerate(marker_sizes):
                    if size >= threshold_size:
                        text_labels.append(str(counts[i]))
                    else:
                        text_labels.append('')
            
            fig = go.Figure(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='markers+text',
                marker=go.scattermapbox.Marker(
                    size=marker_sizes,
                    color='#1f77b4',
                    sizemode='diameter',
                    opacity=0.8
                ),
                text=text_labels,
                textfont=dict(
                    size=10,
                    color='white',
                    family='Arial Black'
                ),
                textposition='middle center',
                hovertext=hover_texts,
                hovertemplate='%{hovertext}<extra></extra>',
                name=data_label
            ))
            

            
        else:
            fig = go.Figure(go.Scattermapbox(lat=[], lon=[]))
        
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=center,
                zoom=zoom
            ),
            title=chart_title,
            showlegend=False,
            height=600,
            margin=dict(l=0, r=0, t=40, b=0)
        )

    elif chart_type == 'cities':
        city_counts = filtered_df['Publication City'].value_counts().head(15)
        fig = px.bar(x=city_counts.values, y=city_counts.index,
                    orientation='h', title=lang['chart_title_cities'],
                    labels={'x': lang['chart_yaxis_publications'], 'y': lang['chart_yaxis_city']})
    
    elif chart_type == 'hierarchy':
        fig = generate_hierarchy_chart(
            filtered_df, hierarchy_path, hierarchy_selections, hierarchy_start, current_page, items_per_page, lang
        )

    else:
        fig = {}
    
    if fig:
        fig.update_layout(
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
    
    return fig

@app.callback(
    [Output('hierarchy-path-store', 'data'),
     Output('hierarchy-selections-store', 'data')],
    [Input('main-chart', 'clickData'),
     Input('hierarchy-reset-btn', 'n_clicks'),
     Input('hierarchy-start-dropdown', 'value')],
    [State('chart-type-dropdown', 'value'),
     State('hierarchy-path-store', 'data'),
     State('hierarchy-selections-store', 'data'),
     State('hierarchy-start-store', 'data')]
)
def handle_hierarchy_navigation(click_data, reset_clicks, start_point, chart_type, current_path, current_selections, current_start):
    """Handle clicks on hierarchy chart and navigation"""
    from dash import callback_context
    
    if chart_type != 'hierarchy':
        raise PreventUpdate
    
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'hierarchy-reset-btn':
        return [], {}
    
    elif trigger_id == 'hierarchy-start-dropdown':
        return [], {}
    
    elif trigger_id == 'main-chart' and click_data:
        try:
            drill_paths = {
                'gender': ['gender', 'country', 'author', 'genre', 'texts'],
                'year': ['year', 'country', 'gender', 'author', 'genre', 'texts'],
                'author': ['author', 'country', 'gender', 'genre', 'texts'],
                'genre': ['genre', 'country', 'gender', 'author', 'texts'],
                'country': ['country', 'gender', 'author', 'genre', 'texts']
            }
            
            expected_path = drill_paths.get(start_point, drill_paths['gender'])
            current_level_index = len(current_path)
            
            if current_level_index < len(expected_path) - 1:
                current_level = expected_path[current_level_index]
                
                if current_level == 'year':
                    clicked_item = click_data['points'][0]['x']
                else:
                    clicked_item = click_data['points'][0]['y']
                
                new_path = current_path + [current_level]
                new_selections = current_selections.copy()
                new_selections[current_level] = clicked_item
                
                return new_path, new_selections
        except (KeyError, IndexError, TypeError):
            pass
    
    raise PreventUpdate

@app.callback(
    Output('hierarchy-start-store', 'data'),
    [Input('hierarchy-start-dropdown', 'value')]
)
def update_hierarchy_start(start_point):
    """Update the hierarchy start point"""
    return start_point

@app.callback(
    Output('hierarchy-current-page-store', 'data'),
    [Input('hierarchy-first-btn', 'n_clicks'),
     Input('hierarchy-prev-btn', 'n_clicks'),
     Input('hierarchy-next-btn', 'n_clicks'),
     Input('hierarchy-last-btn', 'n_clicks'),
     Input('hierarchy-path-store', 'data'),
     Input('hierarchy-start-dropdown', 'value')],
    [State('hierarchy-current-page-store', 'data'),
     State('hierarchy-total-pages-store', 'data')]
)
def handle_pagination_navigation(first_clicks, prev_clicks, next_clicks, last_clicks, hierarchy_path, start_dropdown, current_page, total_pages):
    """Handle pagination navigation"""
    from dash import callback_context
    
    ctx = callback_context
    if not ctx.triggered:
        return current_page
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id in ['hierarchy-path-store', 'hierarchy-start-dropdown']:
        return 1
    
    if trigger_id == 'hierarchy-first-btn' and first_clicks:
        return 1
    elif trigger_id == 'hierarchy-prev-btn' and prev_clicks and current_page > 1:
        return current_page - 1
    elif trigger_id == 'hierarchy-next-btn' and next_clicks and current_page < total_pages:
        return current_page + 1
    elif trigger_id == 'hierarchy-last-btn' and last_clicks:
        return total_pages
    
    return current_page

@app.callback(
    Output('hierarchy-current-page-store', 'data', allow_duplicate=True),
    [Input('hierarchy-page-input', 'value')],
    [State('hierarchy-current-page-store', 'data'),
     State('hierarchy-total-pages-store', 'data')],
    prevent_initial_call=True
)
def handle_page_input(page_input, current_page, total_pages):
    """Handle direct page input"""
    if page_input is not None:
        try:
            new_page = int(page_input)
            if 1 <= new_page <= total_pages:
                return new_page
        except (ValueError, TypeError):
            pass
    return current_page

@app.callback(
    Output('hierarchy-total-pages-store', 'data'),
    [Input('hierarchy-path-store', 'data'),
     Input('hierarchy-selections-store', 'data'),
     Input('hierarchy-start-store', 'data'),
     Input('hierarchy-items-per-page-store', 'data'),
     Input('genre-filter', 'value'),
     Input('year-range', 'value'),
     Input('chart-type-dropdown', 'value')]
)
def calculate_total_pages(hierarchy_path, hierarchy_selections, hierarchy_start, items_per_page, genre_filter, year_range, chart_type):
    """Calculate total pages for pagination"""
    if chart_type != 'hierarchy':
        return 1
    
    filtered_df = metadata_df.copy()
    
    if genre_filter != 'all':
        filtered_df = filtered_df[filtered_df['Style Code'] == genre_filter]
    
    if year_range:
        filtered_df = filtered_df[
            (filtered_df['Date'] >= year_range[0]) & 
            (filtered_df['Date'] <= year_range[1])
        ]
    
    for i, level in enumerate(hierarchy_path):
        if level in hierarchy_selections:
            selection = hierarchy_selections[level]
            if level == 'gender':
                filtered_df = filtered_df[filtered_df['Effective Author Sex'] == selection]
            elif level == 'country':
                filtered_df = filtered_df[filtered_df['Effective Author Location Country'] == selection]
            elif level == 'author':
                filtered_df = filtered_df[filtered_df['Effective Author Name'] == selection]
            elif level == 'genre':
                filtered_df = filtered_df[filtered_df['Style Code'] == selection]
            elif level == 'year':
                try:
                    year = int(selection)
                    filtered_df = filtered_df[filtered_df['Date'] == year]
                except (ValueError, TypeError):
                    pass
    
    drill_paths = {
        'gender': ['gender', 'country', 'author', 'genre', 'texts'],
        'year': ['year', 'country', 'gender', 'author', 'genre', 'texts'],
        'author': ['author', 'country', 'gender', 'genre', 'texts'],
        'genre': ['genre', 'country', 'gender', 'author', 'texts'],
        'country': ['country', 'gender', 'author', 'genre', 'texts']
    }
    
    expected_path = drill_paths.get(hierarchy_start, drill_paths['gender'])
    current_level_index = len(hierarchy_path)
    if current_level_index >= len(expected_path):
        current_level_index = len(expected_path) - 1
    
    current_level = expected_path[current_level_index]
    
    if current_level == 'gender':
        total_items = len(filtered_df['Effective Author Sex'].value_counts())
    elif current_level == 'country':
        total_items = len(filtered_df['Effective Author Location Country'].value_counts())
    elif current_level == 'author':
        total_items = len(filtered_df['Effective Author Name'].value_counts())
    elif current_level == 'genre':
        total_items = len(filtered_df['Style Code'].value_counts())
    elif current_level == 'year':
        total_items = len(filtered_df['Date'].value_counts())
        items_per_page = items_per_page * 2
    elif current_level == 'texts':
        total_items = len(filtered_df)
    else:
        total_items = 0
    
    if total_items == 0:
        return 1
    
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    return total_pages

@app.callback(
    [Output('hierarchy-page-input', 'max'),
     Output('hierarchy-page-total', 'children'),
     Output('hierarchy-first-btn', 'disabled'),
     Output('hierarchy-prev-btn', 'disabled'),
     Output('hierarchy-next-btn', 'disabled'),
     Output('hierarchy-last-btn', 'disabled')],
    [Input('hierarchy-current-page-store', 'data'),
     Input('hierarchy-total-pages-store', 'data'),
     Input('chart-type-dropdown', 'value')]
)
def update_pagination_info(current_page, total_pages, chart_type):
    """Update pagination info and button states"""
    
    if chart_type != 'hierarchy':
        return 1, f"/ 1", True, True, True, True
    
    first_disabled = current_page <= 1
    prev_disabled = current_page <= 1
    next_disabled = current_page >= total_pages
    last_disabled = current_page >= total_pages
    
    page_total_text = f"/ {total_pages}"
    
    return total_pages, page_total_text, first_disabled, prev_disabled, next_disabled, last_disabled

@app.callback(
    Output('hierarchy-page-input', 'value'),
    [Input('hierarchy-current-page-store', 'data')]
)
def update_page_input_value(current_page):
    """Update the page input field to reflect current page"""
    return current_page

@app.callback(
    Output('hierarchy-breadcrumb', 'children'),
    [Input('hierarchy-path-store', 'data'),
     Input('hierarchy-selections-store', 'data'),
     Input('hierarchy-start-store', 'data'),
     Input('language-store', 'data')]
)
def update_breadcrumb(hierarchy_path, hierarchy_selections, hierarchy_start, lang_code):
    """Update the breadcrumb navigation"""
    lang = get_lang(lang_code)
    
    if not hierarchy_path:
        return html.Span(lang.get('hierarchy_start_' + hierarchy_start, hierarchy_start), 
                        style={'color': 'gray', 'fontSize': '12px'})
    
    breadcrumb_items = []
    
    breadcrumb_items.append(
        html.Span(lang.get('hierarchy_start_' + hierarchy_start, hierarchy_start), 
                 style={'fontSize': '12px', 'marginRight': '5px'})
    )
    
    for i, level in enumerate(hierarchy_path):
        breadcrumb_items.append(
            html.Span(" → ", style={'margin': '0 3px', 'color': 'gray', 'fontSize': '12px'})
        )
        
        selection = hierarchy_selections.get(level, level)
        display_selection = selection[:20] + '...' if len(str(selection)) > 20 else str(selection)
        
        breadcrumb_items.append(
            dbc.Button(
                display_selection,
                id={'type': 'breadcrumb-btn', 'index': i},
                color='link',
                size='sm',
                style={'fontSize': '11px', 'padding': '2px 5px', 'textDecoration': 'underline'}
            )
        )
    
    return html.Div(breadcrumb_items, style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap'})

@app.callback(
    [Output('hierarchy-path-store', 'data', allow_duplicate=True),
     Output('hierarchy-selections-store', 'data', allow_duplicate=True)],
         [Input({'type': 'breadcrumb-btn', 'index': ALL}, 'n_clicks')],
    [State('hierarchy-path-store', 'data'),
     State('hierarchy-selections-store', 'data')],
    prevent_initial_call=True
)
def handle_breadcrumb_click(breadcrumb_clicks, current_path, current_selections):
    """Handle clicks on breadcrumb items to go back in hierarchy"""
    from dash import callback_context
    
    ctx = callback_context
    if not ctx.triggered or not any(breadcrumb_clicks):
        raise PreventUpdate
    
    clicked_index = None
    for i, clicks in enumerate(breadcrumb_clicks):
        if clicks:
            clicked_index = i
            break
    
    if clicked_index is not None:
        new_path = current_path[:clicked_index + 1]
        new_selections = {k: v for k, v in current_selections.items() if k in new_path}
        return new_path, new_selections
    
    raise PreventUpdate

@app.callback(
    Output('table-filter-state-store', 'data'),
    [Input('genre-filter', 'value'),
     Input('year-range', 'value'),
     Input('fuzzy-search-input', 'value')]
)
def update_filter_state(genre_filter, year_range, fuzzy_search):
    """Update filter state without storing large data"""
    return {
        'genre': genre_filter or 'all',
        'year_range': year_range or [1800, 2025],
        'fuzzy_search': fuzzy_search or ''
    }

def get_filtered_dataframe(filter_state):
    """Helper function to get filtered dataframe on demand"""
    if metadata_df.empty:
        return pd.DataFrame()
    
    filtered_df = metadata_df.copy()
    
    if filter_state['genre'] != 'all':
        filtered_df = filtered_df[filtered_df['Genre Code'] == filter_state['genre']]
    
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

def fuzzy_search_match(text, query, similarity_threshold=0.6):
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

@app.callback(
    Output('table-info', 'children', allow_duplicate=True),
    [Input('data-table', 'filter_query')],
    prevent_initial_call=True
)
def debug_filter_query(filter_query):
    """Debug callback to see what filter query is being generated"""
    lang = get_lang('EN')
    if filter_query:
        return lang["filter_active"].format(query=filter_query)
    else:
        return lang["no_filter_active"]

def read_text_content(file_path, lang_code='EN'):
    """Read the actual text content from a file"""
    lang = get_lang(lang_code)
    if pd.isna(file_path) or not file_path:
        return lang["file_not_found"]
    
    try:
        clean_path = file_path.replace("PluG2/", "") if file_path.startswith("PluG2/") else file_path
        full_path = f"data/PluG2_texts/{clean_path}"
        
        encodings = ['utf-8', 'cp1251', 'latin-1', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    if content.strip():
                        return content[:10000]
            except (UnicodeDecodeError, UnicodeError):
                continue
            except FileNotFoundError:
                break
        
        return lang["could_not_read_file"]
        
    except Exception as e:
        return lang["error_reading_file"].format(error=str(e))

@app.callback(
    [Output('data-table', 'data'),
     Output('data-table', 'tooltip_data'),
     Output('data-table', 'page_count'),
     Output('table-info', 'children')],
    [Input('table-filter-state-store', 'data'),
     Input('data-table', 'page_current'),
     Input('table-page-size', 'value'),
     Input('data-table', 'sort_by'),
     Input('data-table', 'filter_query'),
     Input('table-edited-data-store', 'data'),
     Input('language-store', 'data')]
)
def update_table_display(filter_state, page_current, page_size, sort_by, filter_query, edited_data, lang_code):
    """Update the table display with pagination, sorting, fuzzy search, and edited data"""
    lang = get_lang(lang_code)
    
    df = get_filtered_dataframe(filter_state)
    
    if filter_query:
        lang_log = get_lang('EN')
        df = apply_table_filters(df, filter_query)
    
    if df.empty:
        return [], [], 0, lang.get('table_no_data', lang['table_no_data'])
    
    display_df = df[['Name', 'Date', 'Genre Code', 'Effective Author Name', 'Effective Author Sex', 'Publication City']].copy()
    
    display_df['_row_id'] = display_df.index
    
    if edited_data:
        for row_id, changes in edited_data.items():
            try:
                matching_rows = display_df[display_df['_row_id'] == int(row_id)]
                if not matching_rows.empty:
                    idx = matching_rows.index[0]
                    for column, value in changes.items():
                        if column in display_df.columns and column != '_row_id':
                            display_df.loc[idx, column] = value
            except (ValueError, KeyError, IndexError):
                continue
    
    if sort_by:
        sort_column = sort_by[0]['column_id']
        ascending = sort_by[0]['direction'] == 'asc'
        if sort_column in display_df.columns:
            display_df = display_df.sort_values(by=sort_column, ascending=ascending)
    
    total_rows = len(display_df)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)
    start_idx = page_current * page_size
    end_idx = start_idx + page_size
    
    display_columns = ['Name', 'Date', 'Genre Code', 'Effective Author Name', 'Effective Author Sex', 'Publication City']
    page_df = display_df.iloc[start_idx:end_idx]
    page_data = page_df[display_columns].to_dict('records')
    
    for i, record in enumerate(page_data):
        record['_row_id'] = page_df.iloc[i]['_row_id']
        record['details_button'] = f'📖 {lang.get("details_button", "Details")}'
    
    tooltip_data = [
        {
            column: {'value': str(row[column]), 'type': 'markdown'}
            for column in ['Name', 'Effective Author Name', 'Genre Code', 'Publication City']
            if column in row and pd.notna(row[column])
        } for row in page_data
    ]
    
    start_num = start_idx + 1 if page_data else 0
    end_num = min(end_idx, total_rows)
    info_text = lang.get('table_info_format', lang['table_info_format']).format(
        start=start_num, end=end_num, total=total_rows)
    
    return page_data, tooltip_data, total_pages, info_text

@app.callback(
    Output('data-table', 'style_data_conditional'),
    [Input('table-edited-data-store', 'data'),
     Input('data-table', 'data')]
)
def update_cell_styling(edited_data, current_data):
    """Update cell styling to highlight edited cells"""
    base_styles = [
        {
            'if': {'state': 'selected'},
            'backgroundColor': 'rgba(13, 110, 253, 0.1)',
            'border': '1px solid #0d6efd'
        },
        {
            'if': {'state': 'active'},
            'backgroundColor': 'rgba(13, 110, 253, 0.1)',
            'border': '1px solid #0d6efd'
        },
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': '#f8f9fa'
        },
        {
            'if': {'row_index': 'even'},
            'backgroundColor': 'white'
        }
    ]
    
    if not edited_data or not current_data:
        return base_styles
    
    for i, row in enumerate(current_data):
        if '_row_id' in row:
            row_id = str(row['_row_id'])
            if row_id in edited_data:
                for column in edited_data[row_id]:
                    if not column.endswith('_original'):
                        base_styles.append({
                            'if': {
                                'row_index': i,
                                'column_id': column
                            },
                            'backgroundColor': '#fff3cd',
                            'border': '2px solid #ffc107',
                            'fontWeight': 'bold'
                        })
    
    return base_styles

@app.callback(
    Output('table-edited-data-store', 'data'),
    [Input('data-table', 'data_timestamp')],
    [State('data-table', 'data'),
     State('data-table', 'data_previous'),
     State('table-edited-data-store', 'data')]
)
def track_edits(timestamp, current_data, previous_data, edited_data):
    """Track edits made to the table using unique row IDs"""
    if timestamp is None or not current_data or not previous_data:
        return edited_data or {}
    
    if len(current_data) != len(previous_data):
        return edited_data or {}
    
    new_edited_data = edited_data.copy() if edited_data else {}
    
    for current_row, previous_row in zip(current_data, previous_data):
        if '_row_id' not in current_row or '_row_id' not in previous_row:
            continue
            
        row_id = str(current_row['_row_id'])
        
        for column in current_row.keys():
            if column == '_row_id':
                continue
                
            if current_row[column] != previous_row[column]:
                if row_id not in new_edited_data:
                    new_edited_data[row_id] = {}
                new_edited_data[row_id][column] = current_row[column]
                
                if f'{column}_original' not in new_edited_data[row_id]:
                    new_edited_data[row_id][f'{column}_original'] = previous_row[column]
    
    return new_edited_data





@app.callback(
    [Output('selected-row-store', 'data'),
     Output('text-details-modal', 'is_open')],
    [Input('data-table', 'active_cell')],
    [State('data-table', 'data'),
     State('text-details-modal', 'is_open'),
     State('table-filter-state-store', 'data')]
)
def handle_cell_click(active_cell, table_data, modal_open, filter_state):
    if not active_cell or not table_data:
        return dash.no_update, modal_open
    
    if active_cell['column_id'] == 'details_button':
        row_index = active_cell['row']
        if 0 <= row_index < len(table_data):
            row_id = table_data[row_index]['_row_id']
            
            if row_id in metadata_df.index:
                row_data = metadata_df.loc[row_id].to_dict()
                return row_data, True
    
    return dash.no_update, modal_open

@app.callback(
    Output('text-details-modal', 'is_open', allow_duplicate=True),
    [Input('modal-close-btn', 'n_clicks')],
    [State('text-details-modal', 'is_open')],
    prevent_initial_call=True
)
def close_modal(n_clicks, is_open):
    if n_clicks:
        return False
    return is_open

@app.callback(
    [Output('modal-title', 'children'),
     Output('modal-basic-info', 'children'),
     Output('modal-publication-info', 'children'),
     Output('modal-media-info', 'children'),
     Output('modal-classification-info', 'children'),
     Output('modal-author-info', 'children'),
     Output('modal-translator-info', 'children'),
     Output('modal-text-content', 'children')],
    [Input('selected-row-store', 'data')],
    [State('language-store', 'data')]
)
def update_modal_content(row_data, language_data):
    if not row_data:
        return "", "", "", "", "", "", "", ""
    
    lang_code = language_data if isinstance(language_data, str) else language_data.get('language', 'EN')
    lang = get_lang(lang_code)
    
    title = row_data.get('Name', 'Unknown Text')
    
    def add_field(container, field_key, field_name, format_func=None, expand_codes=False):
        if field_name in row_data and row_data[field_name] and not pd.isna(row_data[field_name]):
            label = lang.get(field_key, field_key)
            value = row_data[field_name]
            if format_func:
                value = format_func(value)
            elif expand_codes:
                value = expand_code(value, lang_code)
            container.append(html.P([html.Strong(f"{label}: "), str(value)]))
    
    basic_info = []
    add_field(basic_info, "field_name", "Name")
    add_field(basic_info, "field_path", "Path") 
    add_field(basic_info, "field_date", "Date")
    add_field(basic_info, "field_publication_year", "Publication Year", lambda x: int(x) if not pd.isna(x) else "")
    add_field(basic_info, "field_language_code", "Language Code", expand_codes=True)
    add_field(basic_info, "field_genre_code", "Genre Code", expand_codes=True)
    
    pub_info = []
    add_field(pub_info, "field_publication_city", "Publication City")
    add_field(pub_info, "field_publisher", "Publisher")
    add_field(pub_info, "field_publication", "Publication")
    
    media_info = []
    add_field(media_info, "field_media_name", "Media Name")
    add_field(media_info, "field_media_type", "Media Type")
    add_field(media_info, "field_media_location_code", "Media Location Code")
    add_field(media_info, "field_media_location_country", "Media Location Country")
    add_field(media_info, "field_media_location_macroregion", "Media Location Macroregion")
    add_field(media_info, "field_media_location_region", "Media Location Region")
    
    class_info = []
    add_field(class_info, "field_age_code", "Age Code", expand_codes=True)
    add_field(class_info, "field_ortography_code", "Ortography Code", expand_codes=True)
    add_field(class_info, "field_source_code", "Source Code", expand_codes=True)
    add_field(class_info, "field_style_code", "Style Code", expand_codes=True)
    add_field(class_info, "field_branch_aca_code", "Branch ACA Code", expand_codes=True)
    add_field(class_info, "field_theme_aca_code", "Theme ACA Code", expand_codes=True)
    
    author_info = []
    for i in range(1, 5):
        author_section = []
        add_field(author_section, "field_author_name", f"Author {i} Name")
        add_field(author_section, "field_author_sex", f"Author {i} Sex", expand_codes=True)
        add_field(author_section, "field_author_birthday", f"Author {i} Birthday")
        add_field(author_section, "field_author_location_code", f"Author {i} Location Code")
        add_field(author_section, "field_author_location_country", f"Author {i} Location Country")
        add_field(author_section, "field_author_location_macroregion", f"Author {i} Location Macroregion")
        add_field(author_section, "field_author_location_region", f"Author {i} Location Region")
        
        if author_section:
            if i > 1:
                author_info.append(html.Hr())
            author_info.append(html.H6(f"{lang.get('field_author_name', 'Author')} {i}:", className="text-secondary"))
            author_info.extend(author_section)
    
    translator_info = []
    for i in range(1, 4):
        translator_section = []
        add_field(translator_section, "field_translator_name", f"Translator {i} Name")
        add_field(translator_section, "field_translator_sex", f"Translator {i} Sex", expand_codes=True)
        add_field(translator_section, "field_translator_birthday", f"Translator {i} Birthday")
        add_field(translator_section, "field_translator_location_code", f"Translator {i} Location Code")
        add_field(translator_section, "field_translator_location_country", f"Translator {i} Location Country")
        add_field(translator_section, "field_translator_location_macroregion", f"Translator {i} Location Macroregion")
        add_field(translator_section, "field_translator_location_region", f"Translator {i} Location Region")
        
        if translator_section:
            if i > 1:
                translator_info.append(html.Hr())
            translator_info.append(html.H6(f"{lang.get('field_translator_name', 'Translator')} {i}:", className="text-secondary"))
            translator_info.extend(translator_section)
    
    file_path = row_data.get('Path', '')
    text_content = read_text_content(file_path, lang_code)
    
    return title, basic_info, pub_info, media_info, class_info, author_info, translator_info, text_content



@app.callback(
    [Output('year-aggregation-col', 'style'),
     Output('year-color-col', 'style'),
     Output('trend-smoothing-col', 'style'),
     Output('trend-toggle-col', 'style'),
     Output('top-genres-col', 'style'),
     Output('sort-order-col', 'style'),
     Output('geo-data-col', 'style'),
     Output('genre-filter-col', 'style'),
     Output('hierarchy-controls-row', 'style')],
    [Input('chart-type-dropdown', 'value'),
     Input('year-color-by', 'value')]
)
def toggle_controls(chart_type, year_color_by):
    """Show/hide controls based on selected chart type and options"""
    show_style = {"display": "block"}
    hide_style = {"display": "none"}
    
    year_agg_style = show_style if chart_type == 'year' else hide_style
    year_color_style = show_style if chart_type == 'year' else hide_style
    
    trend_smoothing_style = show_style if (chart_type == 'year' and year_color_by == 'none') else hide_style
    trend_toggle_style = show_style if (chart_type == 'year' and year_color_by == 'none') else hide_style
    
    top_genres_style = show_style if chart_type == 'genre' else hide_style
    sort_order_style = show_style if chart_type == 'genre' else hide_style
    
    geo_data_style = show_style if chart_type == 'geography' else hide_style
    
    genre_filter_style = hide_style if chart_type == 'genre' else show_style
    
    hierarchy_controls_style = show_style if chart_type == 'hierarchy' else hide_style
    
    return (year_agg_style, year_color_style, trend_smoothing_style, trend_toggle_style, 
            top_genres_style, sort_order_style, geo_data_style, genre_filter_style, hierarchy_controls_style)

@app.callback(
    [Output('geo-data-type', 'options'),
     Output('label-geo-data-type', 'children')],
    [Input('main-chart', 'relayoutData'),
     Input('language-store', 'data'),
     Input('chart-type-dropdown', 'value')]
)
def update_geo_controls(relayout_data, lang_code, chart_type):
    if chart_type != 'geography':
        raise PreventUpdate
    
    lang = get_lang(lang_code)
    zoom = 3.0
    
    try:
        if relayout_data and isinstance(relayout_data, dict) and 'mapbox.zoom' in relayout_data:
            zoom = float(relayout_data['mapbox.zoom'])
    except (TypeError, ValueError, KeyError):
        zoom = 3.0
    
    COUNTRY_THRESHOLD = 3
    MACROREGION_THRESHOLD = 6

    if zoom >= MACROREGION_THRESHOLD:
        label = lang.get('geo_data_type_city', 'Data Type (City)')
        options = [
            {"label": lang.get('geo_publications_city', 'Publications by City'), "value": "publications"},
            {"label": lang.get('geo_tokens_city', 'Tokens by City'), "value": "tokens"}
        ]
    elif zoom >= COUNTRY_THRESHOLD:
        label = lang.get('geo_data_type_macroregion', 'Data Type (Macroregion)')
        options = [
            {"label": lang.get('geo_publications_macroregion', 'Publications by Macroregion'), "value": "publications"}
        ]
    else:
        label = lang.get('geo_data_type', 'Data Type')
        options = [
            {"label": lang.get('geo_publications', 'Publications by Country'), "value": "publications"}
        ]
    return options, label

@app.callback(
    [Output('chart-legend', 'children'),
     Output('legend-row', 'style')],
    [Input('chart-type-dropdown', 'value'),
     Input('language-store', 'data')]
)
def update_chart_legend(chart_type, lang_code):
    lang = get_lang(lang_code)
    
    if chart_type == 'geography':
        legend_content = [
            html.Div([
                html.P([
                    lang.get('map_legend_explanation', 'Bubble size represents the number of publications or authors. Larger bubbles indicate higher counts.'),
                    html.Br(),
                    lang.get('map_zoom_levels', '📍 Zoom levels: Countries (zoom < 3) → Macroregions (3-6) → Cities (zoom > 6)')
                ], style={'marginBottom': '10px', 'fontWeight': 'bold'}),
                html.Div([
                    html.Div([
                        html.Div(style={
                            'width': '12px',
                            'height': '12px',
                            'backgroundColor': '#1f77b4',
                            'borderRadius': '50%',
                            'display': 'inline-block',
                            'marginRight': '8px',
                            'verticalAlign': 'middle'
                        }),
                        html.Span("0-3%", style={'fontSize': '12px', 'verticalAlign': 'middle'})
                    ], style={'display': 'inline-block', 'marginRight': '30px', 'verticalAlign': 'middle'}),
                    
                    html.Div([
                        html.Div(style={
                            'width': '18px',
                            'height': '18px',
                            'backgroundColor': '#1f77b4',
                            'borderRadius': '50%',
                            'display': 'inline-block',
                            'marginRight': '8px',
                            'verticalAlign': 'middle'
                        }),
                        html.Span("3-10%", style={'fontSize': '14px', 'verticalAlign': 'middle'})
                    ], style={'display': 'inline-block', 'marginRight': '30px', 'verticalAlign': 'middle'}),
                    
                    html.Div([
                        html.Div(style={
                            'width': '24px',
                            'height': '24px',
                            'backgroundColor': '#1f77b4',
                            'borderRadius': '50%',
                            'display': 'inline-block',
                            'marginRight': '8px',
                            'verticalAlign': 'middle'
                        }),
                        html.Span("10-100%", style={'fontSize': '16px', 'verticalAlign': 'middle', 'fontWeight': 'bold'})
                    ], style={'display': 'inline-block', 'verticalAlign': 'middle'})
                    
                ], style={'textAlign': 'center', 'alignItems': 'center'})
            ])
        ]
        return legend_content, {"display": "block"}
    else:
        return "", {"display": "none"}

@app.callback(
    Output("download-csv", "data"),
    [Input("export-csv-btn", "n_clicks")],
    [State('data-table', 'selected_rows'),
     State('data-table', 'data'),
     State('language-store', 'data')],
    prevent_initial_call=True
)
def export_csv(n_clicks, selected_rows, table_data, lang_code):
    """Export selected table rows to CSV"""
    if not n_clicks:
        raise PreventUpdate
    
    if not selected_rows or not table_data:
        raise PreventUpdate
    
    selected_data = [table_data[i] for i in selected_rows if i < len(table_data)]
    
    if not selected_data:
        raise PreventUpdate
    
    import pandas as pd
    export_columns = ['Name', 'Date', 'Genre Code', 'Effective Author Name', 'Effective Author Sex', 'Publication City']
    export_df = pd.DataFrame(selected_data)[export_columns]
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"plug2_selected_export_{timestamp}.csv"
    
    return dcc.send_data_frame(export_df.to_csv, filename, index=False)

@app.callback(
    [Output('export-csv-btn', 'disabled'),
     Output('export-csv-btn', 'children')],
    [Input('data-table', 'selected_rows'),
     Input('language-store', 'data')]
)
def update_export_button(selected_rows, lang_code):
    """Update export button state based on selected rows"""
    lang = get_lang(lang_code)
    if not selected_rows:
        disabled_text = f"📥 {lang['export_csv_disabled']}"
        return True, disabled_text
    else:
        count = len(selected_rows)
        enabled_text = f"📥 {lang['export_csv_enabled'].format(count=count)}"
        return False, enabled_text

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050) 
