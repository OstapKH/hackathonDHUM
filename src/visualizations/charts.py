import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
from src.utils.utils import get_lang, count_tokens, expand_code
from src.utils.geocoding import get_city_coords

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
                # For year, we might want to use a range or specific year
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
                tickformat='d'  # Integer format, no decimals
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

def create_geography_chart(filtered_df, geo_data_type, relayout_data, lang_code):
    """Create geography chart with different zoom levels"""
    lang = get_lang(lang_code)
    
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
    
    return fig 
