import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import numpy as np
from collections import Counter
import logging
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "PluG2 Linguistic Corpus Explorer"

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
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("PluG2 Linguistic Corpus Explorer", 
                   className="text-center mb-4 text-primary"),
            html.P("Explore the rich metadata of the PluG2 Ukrainian linguistic corpus",
                  className="text-center text-muted mb-4")
        ])
    ]),
    
    # Statistics cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Records", className="card-title"),
                    html.H2(f"{len(metadata_df):,}", className="text-primary")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Unique Authors", className="card-title"),
                    html.H2(f"{metadata_df['Author 1 Name'].nunique():,}", className="text-success")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Publication Years", className="card-title"),
                    html.H2(f"{metadata_df['Publication Year'].nunique():,}", className="text-info")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Genres", className="card-title"),
                    html.H2(f"{metadata_df['Genre Code'].nunique():,}", className="text-warning")
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Controls row
    dbc.Row([
        dbc.Col([
            html.Label("Select Visualization Type:"),
            dcc.Dropdown(
                id='chart-type-dropdown',
                options=[
                    {'label': 'Публікації за роками', 'value': 'year'},
                    {'label': 'Authors by Gender', 'value': 'gender'},
                    {'label': 'Genre Distribution', 'value': 'genre'},
                    {'label': 'Geographic Distribution', 'value': 'geography'},
                    {'label': 'Publication Cities', 'value': 'cities'}
                ],
                value='year',
                className="mb-3"
            )
        ], width=4),
        dbc.Col([
            html.Label("Filter by Genre:"),
            dcc.Dropdown(
                id='genre-filter',
                options=[{'label': 'All Genres', 'value': 'all'}] + 
                        [{'label': genre, 'value': genre} 
                         for genre in sorted(metadata_df['Genre Code'].dropna().unique()) if genre],
                value='all',
                className="mb-3"
            )
        ], width=4, id="genre-filter-col"),
        dbc.Col([
            html.Label("Year Range:"),
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
            html.Label("Trend Line Smoothing (Years):"),
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
            html.Label("Show Trend Line:"),
            dbc.Switch(
                id="trend-toggle",
                label="Enable trend line",
                value=True,
                className="mb-3"
            )
        ], width=6)
    ], id="trend-controls-row", style={"display": "block"}),
    
    # Additional controls row for genre chart (conditionally visible)
    dbc.Row([
        dbc.Col([
            html.Label("Number of Top Genres to Show:"),
            dcc.Slider(
                id='top-genres-count',
                min=5,
                max=30,
                step=1,
                value=15,
                marks={i: str(i) for i in range(5, 31, 5)},
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-3"
            )
        ], width=6),
        dbc.Col([
            html.Label("Sort Order:"),
            dcc.RadioItems(
                id="genre-sort-order",
                options=[
                    {"label": "Highest to Lowest", "value": "desc"},
                    {"label": "Lowest to Highest", "value": "asc"}
                ],
                value="desc",
                className="mb-3"
            )
        ], width=6)
    ], id="genre-controls-row", style={"display": "none"}),
    
    # Additional controls row for geography chart (conditionally visible)
    dbc.Row([
        dbc.Col([
            html.Label("Geographic Data Type:"),
            dcc.RadioItems(
                id="geo-data-type",
                options=[
                    {"label": "Publications per Country", "value": "publications"},
                    {"label": "Unique Authors per Country", "value": "authors"}
                ],
                value="publications",
                className="mb-3"
            )
        ], width=6),
    ], id="geography-controls-row", style={"display": "none"}),
    
    # Main visualization
    dbc.Row([
        dbc.Col([
            dcc.Graph(
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
        ], width=12)
    ], className="mb-4"),
    
    # Data table
    dbc.Row([
        dbc.Col([
            html.H3("Sample Data", className="mb-3"),
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

# Callbacks
@app.callback(
    Output('main-chart', 'figure'),
    [Input('chart-type-dropdown', 'value'),
     Input('genre-filter', 'value'),
     Input('year-range', 'value'),
     Input('trend-window', 'value'),
     Input('trend-toggle', 'value'),
     Input('top-genres-count', 'value'),
     Input('genre-sort-order', 'value'),
     Input('geo-data-type', 'value')]
)
def update_chart(chart_type, genre_filter, year_range, trend_window, show_trend, top_genres_count, genre_sort_order, geo_data_type):
    """Update the main chart based on user selections"""
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
                name='Publications'
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
                    name=f'Trend Line ({trend_window}-year avg)',
                    hovertemplate=f'Year: %{{x}}<br>Trend ({trend_window}yr): %{{y:.1f}}<extra></extra>'
                ))
            elif show_trend and len(year_counts) >= 3:
                # Fallback for insufficient data - show simplified trend
                fig.add_trace(go.Scatter(
                    x=year_counts['Publication Year'],
                    y=year_counts['count'],
                    mode='lines',
                    line=dict(color='red', width=2, dash='dash'),
                    name='Data Line (insufficient data for trend)',
                    hovertemplate='Year: %{x}<br>Publications: %{y}<extra></extra>'
                ))
            
            # Update layout
            fig.update_layout(
                title='Publications by Year (Histogram)',
                xaxis_title="Publication Year",
                yaxis_title="Number of Publications",
                bargap=0,  # No margins between bars
                showlegend=False
            )
        else:
            # Fallback if no valid years
            fig = px.histogram(
                x=[],
                title='Publications by Year: No valid publication years found'
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
            title='Authors by Gender',
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
            sort_label = "Lowest to Highest"
        else:  # 'desc'
            # Show top genres arranged from highest to lowest count  
            display_genres = top_genres.sort_values(ascending=False)
            sort_label = "Highest to Lowest"
        
        fig = px.bar(
            x=display_genres.values, 
            y=display_genres.index,
            orientation='h', 
            title=f'Top {top_genres_count} Genres ({sort_label})',
            labels={'x': 'Number of Works', 'y': 'Genre'}
        )
        
        # Customize bar appearance
        fig.update_traces(
            marker_color='#17a2b8',  # Bootstrap info color
            marker_line_color='rgba(0,0,0,0.2)',
            marker_line_width=1
        )
        
    elif chart_type == 'geography':
        # Geographic distribution - OpenStreetMap with country data
        if geo_data_type == 'authors':
            # Count unique authors per country
            geo_counts = filtered_df.groupby('Author 1 Location Country')['Author 1 Name'].nunique()
            data_label = "Unique Authors"
        else:
            # Count publications per country
            geo_counts = filtered_df['Author 1 Location Country'].value_counts()
            data_label = "Publications"
        
        # Country coordinates mapping using country codes
        country_coords = {
            'UA': [49.0, 32.0],  # Ukraine
            'RU': [55.7558, 37.6176],  # Russia
            'PL': [52.2297, 21.0122],  # Poland
            'DE': [51.1657, 10.4515],  # Germany
            'AT': [47.5162, 14.5501],  # Austria
            'US': [39.8283, -98.5795],  # USA
            'CA': [56.1304, -106.3468],  # Canada
            'FR': [46.2276, 2.2137],  # France
            'GB': [55.3781, -3.4360],  # United Kingdom
            'IT': [41.8719, 12.5674],  # Italy
            'CZ': [49.8175, 15.4730],  # Czech Republic
            'SK': [48.6690, 19.6990],  # Slovakia
            'HU': [47.1625, 19.5033],  # Hungary
            'RO': [45.9432, 24.9668],  # Romania
            'BG': [42.7339, 25.4858],  # Bulgaria
            'RS': [44.0165, 21.0059],  # Serbia
            'HR': [45.1000, 15.2000],  # Croatia
            'SI': [46.1512, 14.9955],  # Slovenia
            'BY': [53.7098, 27.9534],  # Belarus
            'LT': [55.1694, 23.8813],  # Lithuania
            'LV': [56.8796, 24.6032],  # Latvia
            'EE': [58.5953, 25.0136],  # Estonia
            'FI': [61.9241, 25.7482],  # Finland
            'SE': [60.1282, 18.6435],  # Sweden
            'NO': [60.4720, 8.4689],  # Norway
            'DK': [56.2639, 9.5018],  # Denmark
            'NL': [52.1326, 5.2913],  # Netherlands
            'BE': [50.5039, 4.4699],  # Belgium
            'CH': [46.8182, 8.2275],  # Switzerland
            'ES': [40.4637, -3.7492],  # Spain
            'PT': [39.3999, -8.2245],  # Portugal
            'AU': [-25.2744, 133.7751],  # Australia
            'BR': [-14.2350, -51.9253],  # Brazil
            'AR': [-38.4161, -63.6167],  # Argentina
            'IL': [31.0461, 34.8516],  # Israel
            'TR': [38.9637, 35.2433],  # Turkey
            'GR': [39.0742, 21.8243],  # Greece
            'JP': [36.2048, 138.2529],  # Japan
            'CN': [35.8617, 104.1954],  # China
            'IN': [20.5937, 78.9629],  # India
            'MX': [23.6345, -102.5528]  # Mexico
        }
        
        # Country names for display
        country_names = {
            'UA': 'Ukraine',
            'RU': 'Russia',
            'PL': 'Poland',
            'DE': 'Germany',
            'AT': 'Austria',
            'US': 'USA',
            'CA': 'Canada',
            'FR': 'France',
            'GB': 'United Kingdom',
            'IT': 'Italy',
            'CZ': 'Czech Republic',
            'SK': 'Slovakia',
            'HU': 'Hungary',
            'RO': 'Romania',
            'BG': 'Bulgaria',
            'RS': 'Serbia',
            'HR': 'Croatia',
            'SI': 'Slovenia',
            'BY': 'Belarus',
            'LT': 'Lithuania',
            'LV': 'Latvia',
            'EE': 'Estonia',
            'FI': 'Finland',
            'SE': 'Sweden',
            'NO': 'Norway',
            'DK': 'Denmark',
            'NL': 'Netherlands',
            'BE': 'Belgium',
            'CH': 'Switzerland',
            'ES': 'Spain',
            'PT': 'Portugal',
            'AU': 'Australia',
            'BR': 'Brazil',
            'AR': 'Argentina',
            'IL': 'Israel',
            'TR': 'Turkey',
            'GR': 'Greece',
            'JP': 'Japan',
            'CN': 'China',
            'IN': 'India',
            'MX': 'Mexico'
        }
        
        # Prepare data for map
        countries = []
        lats = []
        lons = []
        counts = []
        hover_texts = []
        
        for country_code, count in geo_counts.items():
            if country_code and country_code in country_coords:
                country_name = country_names.get(country_code, country_code)
                countries.append(country_code)
                lats.append(country_coords[country_code][0])
                lons.append(country_coords[country_code][1])
                counts.append(count)
                hover_texts.append(f"{country_name}<br>{data_label}: {count}")
        
        if countries:
            # Create size array for markers (scale based on counts)
            max_count = max(counts) if counts else 1
            marker_sizes = [max(8, min(50, (count / max_count) * 40 + 10)) for count in counts]
            
            fig = go.Figure(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=marker_sizes,
                    color=counts,
                    colorscale='RdBu_r',  # Blue to Red colorscale
                    showscale=True,
                    colorbar=dict(title=data_label),
                    sizemode='diameter',
                    opacity=0.8
                ),
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>',
                name='Publications by Country'
            ))
        else:
            # Fallback if no country data
            fig = go.Figure(go.Scattermapbox(
                lat=[49.0],
                lon=[32.0],
                mode='markers',
                marker=go.scattermapbox.Marker(size=0),
            ))
        
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=49.0, lon=32.0),
                zoom=3
            ),
            title=f'Geographic Distribution - {data_label} by Country',
            showlegend=False,
            height=600,
            # Ensure map controls are visible and functional
            dragmode='pan',
            # Show modebar (toolbar) with zoom controls
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        # Configure additional map controls
        fig.update_layout(
            # Enable all standard modebar buttons including zoom
            modebar=dict(
                bgcolor='rgba(255,255,255,0.8)',
                color='black',
                activecolor='blue'
            )
        )
        
    elif chart_type == 'cities':
        # Publication cities
        city_counts = filtered_df['Publication City'].value_counts().head(15)
        fig = px.bar(x=city_counts.values, y=city_counts.index,
                    orientation='h', title='Top 15 Publication Cities',
                    labels={'x': 'Number of Publications', 'y': 'City'})
    

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



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050) 
