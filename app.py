import dash
from dash import dcc, html, Input, Output, callback, dash_table, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
from collections import Counter
import logging
import math
from translations import TRANSLATIONS
from geocoding import get_city_coords

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Helper to get language
def get_lang(lang_code):
    return TRANSLATIONS.get(lang_code, TRANSLATIONS['EN'])

# Set the app title (will be updated by callback)
app.title = get_lang('UA')["app_title"]

# Data loading function
def load_metadata():
    """Load and preprocess the metadata file"""
    try:
        # Read the PSV file
        df = pd.read_csv('PluG2_metadata.psv', sep='|', low_memory=False)
        logger.info(f"Loaded {len(df)} records from metadata file")
        
        # Basic data cleaning
        # Convert Publication Year to numeric, handling errors
        df['Publication Year'] = pd.to_numeric(df['Publication Year'], errors='coerce')
        
        # Fill NaN values with empty strings for text columns
        text_columns = ['Name', 'Language Code', 'Genre Code', 'Publication City', 
                       'Publisher', 'Author 1 Name', 'Author 1 Sex']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('')
        
        return df
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
        return pd.DataFrame()

# Load data
metadata_df = load_metadata()

# App layout
app.layout = dbc.Container([
    # Store for language selection
    dcc.Store(id='language-store', storage_type='session', data='UA'),

    # Header
    dbc.Row([
        dbc.Col([
            html.H1(id='header-title', className="text-center mb-4 text-primary"),
            html.P(id='header-subtitle', className="text-center text-muted mb-4")
        ]),
        dbc.Col([
            dcc.Dropdown(
                id='language-dropdown',
                options=[
                    {'label': 'Українська', 'value': 'UA'},
                    {'label': 'English', 'value': 'EN'}
                ],
                value='UA',
                clearable=False,
                style={'width': '150px', 'float': 'right'}
            )
        ], width='auto')
    ]),
    
    # Statistics cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='stat-total-records', className="card-title"),
                    html.H2(f"{len(metadata_df):,}", className="text-primary")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='stat-unique-authors', className="card-title"),
                    html.H2(f"{metadata_df['Author 1 Name'].nunique():,}", className="text-success")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='stat-publication-years', className="card-title"),
                    html.H2(f"{metadata_df['Publication Year'].nunique():,}", className="text-info")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='stat-genres', className="card-title"),
                    html.H2(f"{metadata_df['Genre Code'].nunique():,}", className="text-warning")
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Controls row
    dbc.Row([
        dbc.Col([
            html.Label(id='label-viz-type'),
            dcc.Dropdown(
                id='chart-type-dropdown',
                value='year',
                className="mb-3"
            )
        ], width=4),
        dbc.Col([
            html.Label(id='label-genre-filter'),
            dcc.Dropdown(
                id='genre-filter',
                value='all',
                className="mb-3"
            )
        ], width=4, id="genre-filter-col"),
        dbc.Col([
            html.Label(id='label-year-range'),
            dcc.RangeSlider(
                id='year-range',
                min=metadata_df['Publication Year'].min() if not metadata_df['Publication Year'].isna().all() else 1800,
                max=metadata_df['Publication Year'].max() if not metadata_df['Publication Year'].isna().all() else 2023,
                step=1,
                marks={year: str(year) for year in range(0, 2025, 500)},
                value=[1800, 2025],
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3"
            )
        ], width=4)
    ]),
    
    # Additional controls row for trend line (conditionally visible)
    dbc.Row([
        dbc.Col([
            html.Label(id='label-trend-smoothing'),
            dcc.Slider(
                id='trend-window',
                min=3,
                max=15,
                step=1,
                value=5,
                marks={i: str(i) for i in range(3, 16, 2)},
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3"
            )
        ], width=6),
        dbc.Col([
            html.Label(id='label-show-trend-line'),
            dbc.Switch(
                id="trend-toggle",
                value=True,
                className="mb-3"
            )
        ], width=6)
    ], id="trend-controls-row", style={"display": "block"}),
    
    # Additional controls row for genre chart (conditionally visible)
    dbc.Row([
        dbc.Col([
            html.Label(id='label-top-genres-count'),
            dcc.Slider(
                id='top-genres-count',
                min=5,
                max=14,
                step=1,
                value=10,
                marks={i: str(i) for i in range(5, 31, 5)},
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3"
            )
        ], width=6),
        dbc.Col([
            html.Label(id='label-sort-order'),
            dcc.RadioItems(
                id="genre-sort-order",
                value="desc",
                className="mb-3"
            )
        ], width=6)
    ], id="genre-controls-row", style={"display": "none"}),
    
    # Additional controls row for geography chart (conditionally visible)
    dbc.Row([
        dbc.Col([
            html.Label(id='label-geo-data-type'),
            dcc.RadioItems(
                id="geo-data-type",
                value="publications",
                className="mb-3"
            )
        ], width=6),
    ], id="geography-controls-row", style={"display": "none"}),
    
    # Main visualization
    dbc.Row([
        dbc.Col([
            dcc.Loading(
                id="loading-main-chart",
                type="default",
                children=dcc.Graph(
                    id='main-chart',
                    config={
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToRemove': [],
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': 'plug2_chart',
                            'height': 500,
                            'width': 700,
                            'scale': 1
                        }
                    }
                )
            )
        ], width=12)
    ], className="mb-4"),
    
    # Data table
    dbc.Row([
        dbc.Col([
            html.H3(id='header-sample-data', className="mb-3"),
            dash_table.DataTable(
                id='data-table',
                columns=[
                    {"name": "Name", "id": "Name"},
                    {"name": "Publication Year", "id": "Publication Year"},
                    {"name": "Genre", "id": "Genre Code"},
                    {"name": "Author", "id": "Author 1 Name"},
                    {"name": "Gender", "id": "Author 1 Sex"},
                    {"name": "Publication City", "id": "Publication City"}
                ],
                data=metadata_df.head(100).to_dict('records'),
                page_size=10,
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                style_data={'backgroundColor': 'rgb(248, 249, 250)'},
                filter_action="native",
                sort_action="native"
            )
        ])
    ])
], fluid=True)

# Callback to store language choice
@app.callback(
    Output('language-store', 'data'),
    Input('language-dropdown', 'value')
)
def update_language_store(language):
    return language

# Callback to update all text elements based on language
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
     Output('label-trend-smoothing', 'children'),
     Output('label-show-trend-line', 'children'),
     Output('trend-toggle', 'label'),
     Output('label-top-genres-count', 'children'),
     Output('label-sort-order', 'children'),
     Output('genre-sort-order', 'options'),
     Output('header-sample-data', 'children'),
     Output('data-table', 'columns')],
    [Input('language-store', 'data')]
)
def update_texts(lang_code):
    lang = get_lang(lang_code)
    
    chart_type_options = [
        {'label': lang['viz_type_year'], 'value': 'year'},
        {'label': lang['viz_type_gender'], 'value': 'gender'},
        {'label': lang['viz_type_genre'], 'value': 'genre'},
        {'label': lang['viz_type_geography'], 'value': 'geography'},
        {'label': lang.get('viz_type_cities', 'Publication Cities'), 'value': 'cities'}
    ]

    genre_filter_options = [{'label': lang['all_genres'], 'value': 'all'}] + \
                           [{'label': genre, 'value': genre} 
                            for genre in sorted(metadata_df['Genre Code'].dropna().unique()) if genre]

    genre_sort_options = [
        {"label": lang['sort_desc'], "value": "desc"},
        {"label": lang['sort_asc'], "value": "asc"}
    ]

    datatable_columns = [
        {"name": lang["datatable_name"], "id": "Name"},
        {"name": lang["datatable_pub_year"], "id": "Publication Year"},
        {"name": lang["datatable_genre"], "id": "Genre Code"},
        {"name": lang["datatable_author"], "id": "Author 1 Name"},
        {"name": lang["datatable_gender"], "id": "Author 1 Sex"},
        {"name": lang["datatable_pub_city"], "id": "Publication City"}
    ]

    return (
        lang['header_title'],
        lang['header_subtitle'],
        lang['total_records'],
        lang['unique_authors'],
        lang['publication_years_stat'],
        lang['genres_stat'],
        lang['select_viz_type'],
        chart_type_options,
        lang['filter_by_genre'],
        genre_filter_options,
        lang['year_range'],
        lang['trend_smoothing'],
        lang['show_trend_line'],
        lang['enable_trend_line'],
        lang['top_genres_count'],
        lang['sort_order'],
        genre_sort_options,
        lang['sample_data_header'],
        datatable_columns
    )

# Main chart callback
@app.callback(
    Output('main-chart', 'figure'),
    [Input('chart-type-dropdown', 'value'),
     Input('genre-filter', 'value'),
     Input('year-range', 'value'),
     Input('trend-window', 'value'),
     Input('trend-toggle', 'value'),
     Input('top-genres-count', 'value'),
     Input('genre-sort-order', 'value'),
     Input('geo-data-type', 'value'),
     Input('main-chart', 'relayoutData')],
    [State('language-store', 'data')]
)
def update_chart(chart_type, genre_filter, year_range, trend_window, show_trend, top_genres_count, genre_sort_order, geo_data_type, relayout_data, lang_code):
    """Update the main chart based on user selections"""
    lang = get_lang(lang_code)

    if metadata_df.empty:
        return {}
    
    # Filter data
    filtered_df = metadata_df.copy()
    
    # Apply genre filter
    if genre_filter != 'all':
        filtered_df = filtered_df[filtered_df['Genre Code'] == genre_filter]
    
    # Apply year filter
    if year_range:
        filtered_df = filtered_df[
            (filtered_df['Publication Year'] >= year_range[0]) & 
            (filtered_df['Publication Year'] <= year_range[1])
        ]
    
    # Generate chart based on type
    if chart_type == 'year':
        # Publications by year - Histogram
        # Filter out NaN years for cleaner visualization
        valid_years = filtered_df['Publication Year'].dropna()
        
        if len(valid_years) > 0:
            # Calculate bin size based on data range
            year_range = valid_years.max() - valid_years.min()
            bin_size = max(1, year_range / 50)  # Adjust bin size for good granularity
            
            # Create histogram using graph_objects for better control
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=valid_years,
                xbins=dict(size=1),  # One year per bar
                marker_color='#0dcaf0',
                marker_line_width=0,
                name=lang['chart_legend_publications']
            ))
            
            # Calculate yearly publication counts
            year_counts = filtered_df.groupby('Publication Year').size().reset_index(name='count')
            year_counts = year_counts.sort_values('Publication Year')
            
            # Add trend line if enabled
            if show_trend and len(year_counts) >= trend_window:
                # Calculate dynamic rolling average for trend
                min_periods = max(2, trend_window // 2)  # Ensure reasonable minimum
                year_counts['trend'] = year_counts['count'].rolling(
                    window=trend_window, 
                    center=True, 
                    min_periods=min_periods
                ).mean()
                
                # Remove NaN values for clean trend line
                trend_data = year_counts.dropna(subset=['trend'])
                
                # Add smoothed trend line
                fig.add_trace(go.Scatter(
                    x=trend_data['Publication Year'],
                    y=trend_data['trend'],
                    mode='lines',
                    line=dict(color='#009ab8', width=3, dash='solid'),
                    name=lang['chart_trend_line_label'].format(trend_window=trend_window),
                    hovertemplate=lang['chart_trend_hover'].format(trend_window=trend_window)
                ))
            elif show_trend and len(year_counts) >= 3:
                # Fallback for insufficient data - show simplified trend
                fig.add_trace(go.Scatter(
                    x=year_counts['Publication Year'],
                    y=year_counts['count'],
                    mode='lines',
                    line=dict(color='red', width=2, dash='dash'),
                    name=lang['chart_insufficient_data'],
                    hovertemplate=lang['chart_insufficient_data_hover']
                ))
            
            # Update layout
            fig.update_layout(
                title=lang['chart_title_year'],
                xaxis_title=lang['chart_xaxis_year'],
                yaxis_title=lang['chart_yaxis_publications'],
                bargap=0,  # No margins between bars
                showlegend=False
            )
        else:
            # Fallback if no valid years
            fig = px.histogram(
                x=[],
                title=lang['chart_no_year_data']
            )
        
    elif chart_type == 'gender':
        # Authors by gender with custom colors and patterns
        gender_counts = filtered_df['Author 1 Sex'].value_counts()
        
        # Define colors and patterns for different genders
        gender_colors = ["gold", "mediumturquoise", "darkorange", "lightgreen", "lightcoral", "lightskyblue"]
        gender_patterns = [".", "x", "+", "-", "/", "\\"]
        
        # Extend colors and patterns if more genders than predefined
        while len(gender_colors) < len(gender_counts):
            gender_colors.extend(["gold", "mediumturquoise", "darkorange", "lightgreen", "lightcoral", "lightskyblue"])
            gender_patterns.extend([".", "x", "+", "-", "/", "\\"])
        
        # Truncate to match number of genders
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
        # Genre distribution with dynamic controls
        # Always get the TOP genres first (by count)
        genre_counts = filtered_df['Genre Code'].value_counts()
        
        # Get the top N genres (always the most frequent ones)
        top_genres = genre_counts.head(top_genres_count)
        
        # Apply display sorting based on user selection
        if genre_sort_order == 'asc':
            # Show top genres arranged from lowest to highest count
            display_genres = top_genres.sort_values(ascending=True)
            sort_label = lang['sort_asc']
        else:  # 'desc'
            # Show top genres arranged from highest to lowest count  
            display_genres = top_genres.sort_values(ascending=False)
            sort_label = lang['sort_desc']
        
        fig = px.bar(
            x=display_genres.values, 
            y=display_genres.index,
            orientation='h', 
            title=lang['chart_title_genre'].format(top_genres_count=top_genres_count, sort_label=sort_label),
            labels={'x': lang['chart_xaxis_works'], 'y': lang['chart_yaxis_genre']}
        )
        
        # Customize bar appearance
        fig.update_traces(
            marker_color='#17a2b8',  # Bootstrap info color
            marker_line_color='rgba(0,0,0,0.2)',
            marker_line_width=1
        )
        
    elif chart_type == 'geography':
        # --- Geography View (Countries and Cities) ---
        
        # Determine current view from map's relayoutData
        zoom = 3.0
        center = {'lat': 49.0, 'lon': 32.0}
        if relayout_data:
            if 'mapbox.zoom' in relayout_data:
                zoom = relayout_data['mapbox.zoom']
            if 'mapbox.center' in relayout_data:
                center = relayout_data['mapbox.center']

        ZOOM_THRESHOLD = 5

        lats, lons, counts, hover_texts = [], [], [], []
        marker_sizes = []
        colorscale = 'viridis'

        if zoom >= ZOOM_THRESHOLD:
            # --- City View ---
            if geo_data_type == 'authors':
                counts_by_loc = filtered_df.groupby('Publication City')['Author 1 Name'].nunique()
                data_label = lang['geo_authors_city']
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
                    hover_texts.append(f"{city_name}<br>{data_label}: {count}")

            if lats:
                marker_sizes = [max(5, min(40, math.log(c+1) * 5)) for c in counts]
                colorscale = 'YlOrRd'
        else:
            # --- Country View ---
            if geo_data_type == 'authors':
                counts_by_loc = filtered_df.groupby('Author 1 Location Country')['Author 1 Name'].nunique()
                data_label = lang['chart_data_label_authors']
            else:
                counts_by_loc = filtered_df['Author 1 Location Country'].value_counts()
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

        # Create the figure
        if lats:
            fig = go.Figure(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=marker_sizes,
                    color=counts,
                    colorscale=colorscale,
                    showscale=True,
                    colorbar=dict(title=data_label),
                    sizemode='diameter',
                    opacity=0.8
                ),
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>',
            ))
        else:
            fig = go.Figure(go.Scattermapbox(lat=[], lon=[]))
        
        # General map layout settings
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
        # Publication cities
        city_counts = filtered_df['Publication City'].value_counts().head(15)
        fig = px.bar(x=city_counts.values, y=city_counts.index,
                    orientation='h', title=lang['chart_title_cities'],
                    labels={'x': lang['chart_yaxis_publications'], 'y': lang['chart_yaxis_city']})
    

    else:
        fig = {}
    
    # Update layout
    if fig:
        fig.update_layout(
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
    
    return fig

@app.callback(
    Output('data-table', 'data'),
    [Input('genre-filter', 'value'),
     Input('year-range', 'value')]
)
def update_table(genre_filter, year_range):
    """Update the data table based on filters"""
    if metadata_df.empty:
        return []
    
    # Filter data
    filtered_df = metadata_df.copy()
    
    # Apply genre filter
    if genre_filter != 'all':
        filtered_df = filtered_df[filtered_df['Genre Code'] == genre_filter]
    
    # Apply year filter
    if year_range:
        filtered_df = filtered_df[
            (filtered_df['Publication Year'] >= year_range[0]) & 
            (filtered_df['Publication Year'] <= year_range[1])
        ]
    
    return filtered_df.head(100).to_dict('records')

@app.callback(
    [Output('trend-controls-row', 'style'),
     Output('genre-controls-row', 'style'),
     Output('geography-controls-row', 'style'),
     Output('genre-filter-col', 'style')],
    [Input('chart-type-dropdown', 'value')]
)
def toggle_controls(chart_type):
    """Show/hide controls based on selected chart type"""
    trend_style = {"display": "block"} if chart_type == 'year' else {"display": "none"}
    genre_controls_style = {"display": "block"} if chart_type == 'genre' else {"display": "none"}
    geography_controls_style = {"display": "block"} if chart_type == 'geography' else {"display": "none"}
    genre_filter_style = {"display": "none"} if chart_type == 'genre' else {"display": "block"}
    return trend_style, genre_controls_style, geography_controls_style, genre_filter_style

# Callback to update geo control labels based on zoom AND language
@app.callback(
    [Output('geo-data-type', 'options'),
     Output('label-geo-data-type', 'children')],
    [Input('main-chart', 'relayoutData'),
     Input('language-store', 'data')]
)
def update_geo_controls(relayout_data, lang_code):
    lang = get_lang(lang_code)
    zoom = 3.0
    if relayout_data and 'mapbox.zoom' in relayout_data:
        zoom = relayout_data['mapbox.zoom']
    
    ZOOM_THRESHOLD = 5

    if zoom >= ZOOM_THRESHOLD:
        # City view
        label = lang['geo_data_type_city']
        options = [
            {"label": lang['geo_publications_city'], "value": "publications"},
            {"label": lang['geo_authors_city'], "value": "authors"}
        ]
    else:
        # Country view
        label = lang['geo_data_type']
        options = [
            {"label": lang['geo_publications'], "value": "publications"},
            {"label": lang['geo_authors'], "value": "authors"}
        ]
    return options, label

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050) 
