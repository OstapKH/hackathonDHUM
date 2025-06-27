import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from src.utils.utils import get_lang
from src.config.constants import (
    DEFAULT_PAGE_SIZE, BUTTON_TYPE_DEFAULT, FUZZY_SEARCH_PLACEHOLDER_LANG,
    ZOOM_THRESHOLD_STORE_DATA
)

def create_app_layout(metadata_df):
    """Create the main application layout"""
    
    return dbc.Container([
        dcc.Store(id='language-store', storage_type='session', data='UA'),

        dcc.Store(id='hierarchy-path-store', storage_type='session', data=[]),
        dcc.Store(id='hierarchy-selections-store', storage_type='session', data={}),
        dcc.Store(id='hierarchy-start-store', storage_type='session', data='gender'),
        dcc.Store(id='hierarchy-current-page-store', storage_type='session', data=1),
        dcc.Store(id='hierarchy-items-per-page-store', storage_type='session', data=10),
        dcc.Store(id='hierarchy-total-pages-store', storage_type='session', data=1),

        dcc.Store(id='table-filter-state-store', storage_type='memory', data={'genre': 'all', 'year_range': [1800, 2025], 'search': ''}),
        dcc.Store(id='table-sort-store', storage_type='memory', data={'column': None, 'direction': 'asc'}),
        dcc.Store(id='table-edited-data-store', storage_type='memory', data={}),
        dcc.Store(id='selected-row-store', storage_type='memory', data={}),

        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                    id='language-dropdown',
                    options=[
                        {'label': 'Українська', 'value': 'UA'},
                        {'label': 'English', 'value': 'EN'}
                    ],
                    value='UA',
                    clearable=False,
                ),
                xs=12, sm=8, md=6, lg=4, className="ms-sm-auto"
            )
        ], className="mb-2", style={'paddingTop': '10px'}),
        
        dbc.Row([
            dbc.Col([
                html.H1(id='header-title', className="text-center text-primary"),
                html.P(id='header-subtitle', className="text-center text-muted")
            ], lg=True)
        ], className="mb-4"),
        
        _create_statistics_cards(metadata_df),
        
        _create_controls_row(metadata_df),
        
        _create_secondary_controls_row(),
        
        _create_hierarchy_controls_row(),
        
        _create_main_chart(),
        
        _create_chart_legend(),
        
        _create_data_table(metadata_df),
        
        _create_text_details_modal(),
        
        _create_explanation_section(),

        dcc.Store(id='zoom-threshold-store', data=ZOOM_THRESHOLD_STORE_DATA)
    ], fluid=True, style={'paddingLeft': '25px', 'paddingRight': '25px'})

def _create_statistics_cards(metadata_df):
    """Create statistics cards row"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='stat-total-records', className="card-title h5"),
                    html.H2(f"{len(metadata_df):,}", className="text-primary h3")
                ])
            ])
        ], lg=3, md=6, xs=12, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='stat-unique-authors', className="card-title h5"),
                    html.H2(f"{metadata_df['Effective Author Name'].nunique():,}", className="text-success h3")
                ])
            ])
        ], lg=3, md=6, xs=12, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='stat-publication-years', className="card-title h5"),
                    html.H2(f"{metadata_df['Date'].nunique():,}", className="text-info h3")
                ])
            ])
        ], lg=3, md=6, xs=12, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(id='stat-genres', className="card-title h5"),
                    html.H2(f"{metadata_df['Style Code'].nunique():,}", className="text-warning h3")
                ])
            ])
        ], lg=3, md=6, xs=12, className="mb-3")
    ], className="mb-4")

def _create_controls_row(metadata_df):
    """Create main controls row"""
    return dbc.Row([
        dbc.Col([
            html.Label(id='label-viz-type', style={'marginBottom': '2px'}),
            dcc.Dropdown(
                id='chart-type-dropdown',
                value='year',
                className="mb-2",
            )
        ], lg=2, md=6, xs=12),
        dbc.Col([
            html.Label(id='label-genre-filter', style={'marginBottom': '2px'}),
            dcc.Dropdown(
                id='genre-filter',
                value='all',
                className="mb-2",
            )
        ], lg=2, md=6, xs=12, id="genre-filter-col"),
        dbc.Col([
            html.Label(id='label-year-aggregation-type', style={'marginBottom': '2px'}),
            dcc.Dropdown(
                id='year-aggregation-type',
                value='publications',
                className="mb-2",
            )
        ], lg=2, md=6, xs=12, id="year-aggregation-col"),
        dbc.Col([
            html.Label(id='label-year-color-by', style={'marginBottom': '2px'}),
            dcc.Dropdown(
                id='year-color-by',
                value='none',
                className="mb-2",
            )
        ], lg=2, md=6, xs=12, id="year-color-col"),
        dbc.Col([
            html.Label(id='label-year-range', style={'marginBottom': '2px'}),
            dcc.RangeSlider(
                id='year-range',
                min=metadata_df['Date'].min() if not metadata_df['Date'].isna().all() else 1800,
                max=metadata_df['Date'].max() if not metadata_df['Date'].isna().all() else 2023,
                step=1,
                marks={year: str(year) for year in range(0, 2025, 50)},
                value=[1800, 2025],
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-4"
            )
        ], lg=4, md=12, xs=12)
    ], className="mb-3", align="start")

def _create_secondary_controls_row():
    """Create secondary controls row"""
    return dbc.Row([
        dbc.Col([
            html.Label(id='label-trend-smoothing', style={'marginBottom': '2px'}),
            dcc.Slider(
                id='trend-window',
                min=3,
                max=15,
                step=1,
                value=5,
                marks={i: str(i) for i in range(3, 16, 2)},
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-2"
            )
        ], lg=3, md=6, xs=12, id="trend-smoothing-col"),
        dbc.Col([
            html.Label(id='label-show-trend-line', style={'marginBottom': '2px'}),
            dbc.Switch(
                id="trend-toggle",
                value=True,
                className="mb-2",
            )
        ], lg=3, md=6, xs=12, id="trend-toggle-col"),
        dbc.Col([
            html.Label(id='label-top-genres-count', style={'marginBottom': '2px'}),
            dcc.Slider(
                id='top-genres-count',
                min=5,
                max=14,
                step=1,
                value=10,
                marks={i: str(i) for i in range(5, 31, 5)},
                tooltip={"placement": "bottom", "always_visible": True},
                className="mb-4"
            )
        ], lg=2, md=6, xs=12, id="top-genres-col"),
        dbc.Col([
            html.Label(id='label-sort-order', style={'marginBottom': '2px'}),
            dcc.RadioItems(
                id="genre-sort-order",
                value="desc",
                className="mb-2",
            )
        ], lg=2, md=6, xs=12, id="sort-order-col"),
        dbc.Col([
            html.Label(id='label-geo-data-type', style={'marginBottom': '2px'}),
            dcc.RadioItems(
                id="geo-data-type",
                value="publications",
                className="mb-2",
            )
        ], lg=2, md=6, xs=12, id="geo-data-col")
    ], className="mb-3", id="secondary-controls-row")

def _create_hierarchy_controls_row():
    """Create hierarchy controls row"""
    return dbc.Row([
        dbc.Col([
            html.Label(id='label-hierarchy-start', style={'fontSize': '12px', 'marginBottom': '2px'}),
            dcc.Dropdown(
                id='hierarchy-start-dropdown',
                value='gender',
                className="mb-2",
                style={'fontSize': '12px'}
            )
        ], width=3, id="hierarchy-start-col"),
        dbc.Col([
            html.Div([
                html.Span(id='hierarchy-breadcrumb-label', style={'fontSize': '12px', 'marginRight': '10px'}),
                html.Div(id='hierarchy-breadcrumb', style={'display': 'inline-block'})
            ], style={'marginTop': '20px'})
        ], width=6, id="hierarchy-breadcrumb-col"),
        dbc.Col([
            html.Div([
                dbc.Button(
                    id='hierarchy-reset-btn',
                    color='secondary',
                    size='sm',
                    style={'fontSize': '12px', 'marginRight': '10px'}
                ),
                dbc.ButtonGroup([
                    dbc.Button(
                        "⇤",
                        id='hierarchy-first-btn',
                        color='outline-secondary',
                        size='sm',
                        style={'fontSize': '12px', 'width': '35px'},
                        title='First page'
                    ),
                    dbc.Button(
                        "←",
                        id='hierarchy-prev-btn',
                        color='outline-primary',
                        size='sm',
                        style={'fontSize': '12px', 'width': '35px'},
                        title='Previous page'
                    ),
                    dbc.Input(
                        id='hierarchy-page-input',
                        type='number',
                        min=1,
                        value=1,
                        size='sm',
                        style={'fontSize': '11px', 'width': '50px', 'textAlign': 'center', 'height': '31px'}
                    ),
                    dbc.Button(
                        "→",
                        id='hierarchy-next-btn',
                        color='outline-primary',
                        size='sm',
                        style={'fontSize': '12px', 'width': '35px'},
                        title='Next page'
                    ),
                    dbc.Button(
                        "⇥",
                        id='hierarchy-last-btn',
                        color='outline-secondary',
                        size='sm',
                        style={'fontSize': '12px', 'width': '35px'},
                        title='Last page'
                    )
                ], size='sm'),
                html.Div(
                    id='hierarchy-page-total',
                    style={'fontSize': '11px', 'color': 'gray', 'marginLeft': '10px', 'marginTop': '5px'}
                )
            ], style={'marginTop': '18px'})
        ], width=3, id="hierarchy-reset-col")
    ], className="mb-3", id="hierarchy-controls-row")

def _create_main_chart():
    """Create main chart section"""
    return dbc.Row([
        dbc.Col([
            dcc.Loading(
                id="loading-main-chart",
                                        type=BUTTON_TYPE_DEFAULT,
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
    ], className="mb-2")

def _create_chart_legend():
    """Create chart legend section"""
    return dbc.Row([
        dbc.Col([
            html.Div(
                id='chart-legend',
                className="text-center text-muted",
                style={
                    'padding': '10px',
                    'backgroundColor': '#f8f9fa',
                    'border': '1px solid #dee2e6',
                    'borderRadius': '5px',
                    'fontSize': '14px'
                }
            )
        ], width=12)
    ], className="mb-4", id="legend-row")

def _create_data_table(metadata_df):
    """Create data table section"""
    return dbc.Row([
        dbc.Col([
            html.H3(
                id='header-sample-data', 
                className="mb-4 text-primary",
                style={
                    'fontSize': '24px',
                    'fontWeight': '600',
                    'color': '#000000',
                    'borderBottom': '2px solid #e9ecef',
                    'paddingBottom': '10px'
                }
            ),
            dash_table.DataTable(
                id='data-table',
                columns=[
                    {"name": "Name", "id": "Name", "editable": True},
                    {"name": "Date", "id": "Date", "type": "numeric", "editable": True},
                    {"name": "Style", "id": "Style Code", "editable": True},
                    {"name": "Author", "id": "Effective Author Name", "editable": True},
                    {"name": "Gender", "id": "Effective Author Sex", "editable": True, "presentation": "dropdown"},
                    {"name": "Publication City", "id": "Publication City", "editable": True},
                    {"name": "Details", "id": "details_button", "editable": False, "presentation": "markdown"}
                ],
                data=metadata_df.head(50).to_dict('records'),
                page_action='custom',
                page_current=0,
                page_size=DEFAULT_PAGE_SIZE,
                page_count=0,
                style_table={
                    'overflowX': 'auto',
                    'width': '100%',
                    'maxWidth': '100%',
                    'border': '1px solid #dee2e6',
                    'borderRadius': '8px',
                    'backgroundColor': 'white'
                },
                style_cell={
                    'textAlign': 'left', 
                    'padding': '12px 15px',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': 0,
                    'whiteSpace': 'nowrap',
                    'fontSize': '14px',
                    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    'border': '1px solid #f0f0f0'
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Name'},
                        'width': '28%',
                        'maxWidth': '280px'
                    },
                    {
                        'if': {'column_id': 'Date'},
                        'width': '10%',
                        'maxWidth': '100px'
                    },
                    {
                        'if': {'column_id': 'Style Code'},
                        'width': '12%',
                        'maxWidth': '120px'
                    },
                    {
                        'if': {'column_id': 'Effective Author Name'},
                        'width': '22%',
                        'maxWidth': '220px'
                    },
                    {
                        'if': {'column_id': 'Effective Author Sex'},
                        'width': '8%',
                        'maxWidth': '80px'
                    },
                    {
                        'if': {'column_id': 'Publication City'},
                        'width': '10%',
                        'maxWidth': '100px'
                    },
                    {
                        'if': {'column_id': 'details_button'},
                        'width': '15%',
                        'maxWidth': '150px',
                        'textAlign': 'center'
                    }
                ],
                style_header={
                    'backgroundColor': '#f8f9fa', 
                    'fontWeight': '600',
                    'fontSize': '14px',
                    'color': '#495057',
                    'textAlign': 'left',
                    'padding': '15px',
                    'border': '1px solid #dee2e6',
                    'borderBottom': '2px solid #dee2e6',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': 0,
                    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                },
                style_data={
                    'backgroundColor': 'white',
                    'overflow': 'hidden',
                    'textOverflow': 'ellipsis',
                    'maxWidth': 0,
                    'color': '#212529',
                    'borderBottom': '1px solid #f8f9fa'
                },
                style_filter={
                    'backgroundColor': '#f8f9fa',
                    'border': '1px solid #ced4da',
                    'borderRadius': '4px',
                    'padding': '6px 12px',
                    'fontSize': '13px',
                    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    'color': '#6c757d'
                },
                filter_action="custom",
                sort_action="custom",
                sort_mode="single",
                row_selectable="multi",
                selected_rows=[],
                dropdown={
                    'Effective Author Sex': {
                        'options': [
                            {'label': get_lang('EN')['male'], 'value': 'M'},
                            {'label': get_lang('EN')['female'], 'value': 'F'},
                            {'label': get_lang('EN')['unknown'], 'value': ''},
                            {'label': get_lang('EN')['other'], 'value': 'O'}
                        ]
                    }
                },
                tooltip_data=[
                    {
                        column: {'value': str(row[column]), 'type': 'markdown'}
                        for column in ['Name', 'Effective Author Name', 'Style Code', 'Publication City']
                        if column in row
                    } for row in metadata_df.head(50).to_dict('records')
                ],
                tooltip_duration=None
            ),
            
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Label(
                            id='table-page-size-label', 
                            style={
                                'fontSize': '13px', 
                                'marginBottom': '5px',
                                'fontWeight': '500',
                                'color': '#495057'
                            }
                        ),
                        dcc.Dropdown(
                            id='table-page-size',
                            options=[
                                {'label': '10', 'value': 10},
                                {'label': '25', 'value': 25},
                                {'label': '50', 'value': 50},
                                {'label': '100', 'value': 100}
                            ],
                            value=25,
                            clearable=False,
                            style={'fontSize': '13px'},
                            className="shadow-sm"
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label(
                            id='fuzzy-search-label', 
                            style={
                                'fontSize': '13px', 
                                'marginBottom': '5px',
                                'fontWeight': '500',
                                'color': '#495057'
                            }
                        ),
                        dbc.Input(
                            id='fuzzy-search-input',
                            type='text',
                            placeholder=get_lang('UA')['search_placeholder'],
                            size='sm',
                            style={
                                'fontSize': '13px',
                                'border': '1px solid #ced4da',
                                'borderRadius': '6px',
                                'padding': '8px 12px'
                            },
                            className="shadow-sm"
                        )
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.Span(
                                id='table-info', 
                                style={
                                    'fontSize': '12px', 
                                    'color': '#6c757d',
                                    'fontWeight': '500',
                                    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                                }
                            )
                        ], style={'marginTop': '25px', 'textAlign': 'right'})
                    ], width=6)
                ], className="mb-3")
            ], className="mt-3"),
            
            html.Div([
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            id="export-csv-btn",
                            color="success",
                            outline=True,
                            size="sm",
                            className="mt-2",
                            style={
                                'fontSize': '13px',
                                'fontWeight': '500',
                                'borderRadius': '6px'
                            }
                        ),
                        dcc.Download(id="download-csv")
                    ], width=12, style={'textAlign': 'right'})
                ])
            ], className="mt-2")
        ])
    ], className="mb-5", style={
        'backgroundColor': 'white',
        'borderRadius': '12px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
        'padding': '25px',
        'border': '1px solid #e9ecef'
    })

def _create_text_details_modal():
    """Create text details modal"""
    return dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle(id="modal-title")
        ]),
        dbc.ModalBody([
            html.Div([
                html.H5(id="modal-metadata-title", className="text-info mb-3"),
                
                dbc.Card([
                    dbc.CardHeader(html.H6(id="modal-basic-info-header", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="modal-basic-info")
                    ])
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6(id="modal-publication-info-header", className="mb-0")),
                            dbc.CardBody([
                                html.Div(id="modal-publication-info")
                            ])
                        ])
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H6(id="modal-media-info-header", className="mb-0")),
                            dbc.CardBody([
                                html.Div(id="modal-media-info")
                            ])
                        ])
                    ], width=6)
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader(html.H6(id="modal-classification-info-header", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="modal-classification-info")
                    ])
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader(html.H6(id="modal-author-info-header", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="modal-author-info")
                    ])
                ], className="mb-3"),
                
                dbc.Card([
                    dbc.CardHeader(html.H6(id="modal-translator-info-header", className="mb-0")),
                    dbc.CardBody([
                        html.Div(id="modal-translator-info")
                    ])
                ], className="mb-3"),
                
                html.H5(id="modal-content-title", className="text-info mb-3"),
                dbc.Card([
                    dbc.CardBody([
                        html.Div(id="modal-text-content", 
                                style={
                                    'maxHeight': '400px', 
                                    'overflowY': 'auto',
                                    'whiteSpace': 'pre-wrap',
                                    'fontFamily': 'monospace',
                                    'fontSize': '14px',
                                    'lineHeight': '1.4',
                                    'backgroundColor': '#f8f9fa',
                                    'padding': '15px',
                                    'borderRadius': '5px'
                                })
                    ])
                ], className="mt-3")
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button(
                id="modal-close-btn",
                className="ms-auto",
                color="secondary"
            )
        ])
    ], id="text-details-modal", size="xl", scrollable=True)

def _create_explanation_section():
    """Create explanation section"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H3(id="explanation-main-title", className="mb-0 text-primary"),
                ]),
                dbc.CardBody(id="explanation-card-body")
            ], className="shadow-sm")
        ])
    ]) 
