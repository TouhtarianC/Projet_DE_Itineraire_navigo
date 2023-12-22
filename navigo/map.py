import dash
from dash import dcc, html, Dash
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import logging

from navigo.settings import DASH_TOKEN

logger = logging.getLogger(__name__)


def center_coordinates(df):
    '''
    Function that calculates the center coordinates based on latitude and longitude.

    Parameters:
        df (pd.DataFrame): The DataFrame containing location data.

    Returns:
        Tuple: A tuple containing the mean latitude and mean longitude.
    '''
    logger.info('Centering map with coorinates in df')
    latitudes = df['latitude'].astype(float)
    longitudes = df['longitude'].astype(float)
    center_lat = latitudes.mean()
    center_lon = longitudes.mean()
    logger.info(f'Centered latitude : {center_lat}')
    logger.info(f'Centered longitude : {center_lon}')
    return center_lat, center_lon


def calculate_zoom(df):
    '''
    Function that calculates the zoom level based on latitude and longitude ranges.

    Parameters:
        df (pd.DataFrame): The DataFrame containing location data.
        
    Returns:
        float: The calculated zoom level.
    '''
    logger.info('Calculating appropriate zoom')
    
    lat_range = df['latitude'].max() - df['latitude'].min()
    lon_range = df['longitude'].max() - df['longitude'].min()

    zoom_lat = 12 - lat_range * 2
    zoom_lon = 12 - lon_range * 2
    logger.info(f'Zoom Value for latitude : {zoom_lat}')
    logger.info(f'Zoom Value for latitude : {zoom_lon}')
    return min(zoom_lat, zoom_lon)


def get_symbol(point_type, is_first_point, is_last_point):
    # logger.info('Adding appropriate symbol to data')
    if is_first_point:
        return '🚀' 
    elif is_last_point:
        return  '🏁'
    elif point_type == 'POI':
        return ' 🏛️'
    elif point_type == 'Restaurant':
        return '🍽️'
    elif point_type == 'Hosting':
        return "🛏️"  
    else:
        return "default" 
    logger.info('Symbols correctly added')

    
def add_points_to_figure(fig, df, filter_type=None):
    logger.info(f'Adding {len(df)} points to map')
    
    for i, point in df.iterrows():
        #symbol = 'toilet' if filter_type == 'WC' else point['symbol']
        symbol = point['symbol']
        poi_text = f"{symbol} {point['name']}"
        hover_text = f"{symbol}<br>{point['name']}" if filter_type == 'WC' else f"{symbol}<br>{point['name']}<br>Note: {point['notation']}"
        marker_size = 30 if filter_type == 'WC' else 15
        
        fig.add_trace(go.Scattermapbox(
            mode="markers+text",
            lon=[point["longitude"]],
            lat=[point["latitude"]],
            marker={'size': marker_size, 
                    'symbol': symbol,
                    'color': point['colors'], 
                    'opacity': 0.7},
            text=poi_text,
            name=point["name"],
            hoverinfo="text",
            textposition="bottom left",
            hovertext=hover_text,
            textfont=dict(color=point['colors'])
        ))
    #logger.info('Points correctly added')


def add_lines_between_days(fig, df, selected_day=None):
    # logger.info('Adding lines to map')
    df = df.sort_values(by=['day', 'rank']).reset_index(drop=True)
    #logger.info(f'Day points: \n{day_points}')
    
    if selected_day:
        day_df = df[df['day'] == selected_day]
    else:
        day_df = df
    
    for i in range(len(df) - 1):
        current_point = df.iloc[i]
        next_point = df.iloc[i + 1]
        
        # filter by day
        if selected_day is not None and current_point['day'] != selected_day:
            continue
        
        # adapt color and text for lines between 2 days
        if current_point['day'] == next_point['day']:
            line_color = current_point['colors']
            line_text = f"Day : {current_point['day']}<br>From {current_point['name']} to {next_point['name']}"
        else:
            line_color = next_point['colors']
            line_text = f"Day : {next_point['day']}<br>From {current_point['name']} to {next_point['name']}"
        
         # add specific point in middle of the line to print text   
        mid_lon = (current_point['longitude'] + next_point['longitude']) / 2
        mid_lat = (current_point['latitude'] + next_point['latitude']) / 2
        fig.add_trace(go.Scattermapbox(
            mode='text',
            lon=[mid_lon],
            lat=[mid_lat],
            text=line_text,
            hoverinfo='text',
            showlegend=False
        ))
        # logger.info('Middle line point added')
                           
        # trace lines                        
        fig.add_trace(go.Scattermapbox(
            mode='lines',
            lon=[current_point['longitude'], next_point['longitude']],
            lat=[current_point['latitude'], next_point['latitude']],
            line=dict(color=line_color, width=2),
            text=[],
            hoverinfo='none',
            showlegend=False            
        ))
        # logger.info(f"Line {current_point['name']} successfully updated")
              

def create_figure(df):
    '''
    Function that creates a Plotly figure for visualizing trip data on a map.
    For each day of the trip, put points on the map, then trace the lines.

    Parameters:
        df (pd.DataFrame): The DataFrame containing trip data.

    Returns:
        go.Figure: The Plotly figure for the trip visualization.
    '''
    logger.info('Creating figure')
    df = df.sort_values(by=['day', 'rank']).reset_index(drop=True)
    fig = go.Figure()
    
    # adding oblects to map
    add_lines_between_days(fig, df)
    add_points_to_figure(fig, df)
    
    center_lat, center_lon = center_coordinates(df)
    zoom = calculate_zoom(df)
    
    fig.update_layout(
        mapbox={
            'accesstoken': DASH_TOKEN,
            'style': "outdoors",
            'zoom': zoom,
            'center': {'lon': center_lon, 'lat': center_lat},
        },
        showlegend=False
    )

    logger.info('Figure successfuly created')
    return fig


def create_dash_app(geospatial_point_list: list, selected_toilets: list = []) -> dash.Dash:
    '''
    Creates a Dash web application layout.

    Parameters:
        df (pd.DataFrame): The DataFrame containing trip data.
        fig (go.Figure): The Plotly figure for trip visualization.
        token (str): The Mapbox access token.

    Returns:
        dash.Dash: The Dash web application.
    '''
    logger.info('Creating App')
    df = preprocess_geospatial_data(geospatial_point_list)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None,'display.width', 1000):
        msg = f'Data for the Trip :\n {df}'
        logger.info(msg)

    df_toilets = get_toilets_data(selected_toilets)
    logger.info(f'Toilets data\n{df_toilets}')
    
    fig = create_figure(df)
    
    app = Dash(__name__, requests_pathname_prefix='/dash/')
    app.layout = html.Div([
        dcc.Dropdown(
            id='day-dropdown',
            options=[{'label': 'All Days', 'value': 'all'}] + [
                {'label': f'Day {day}', 'value': day} for day in df['day'].unique()
            ],
            value='all',
            multi=False,
            style={'width': '50%', 'display': 'inline-block'}
        ),
        html.Div([
            dcc.Checklist(
                id='include-toilets-checkbox',
                options=[{'label': 'With Toilets', 'value': 'include-toilets'}],
                value=False, # checklist not visible
            ),
        ], id='include-toilets-div', style={'width': '48%', 'display': 'inline-block'}),
        dcc.Graph(figure=fig, style={'height': '100vh'}, id='map-fig')
    ])
    
    @app.callback(
        Output('map-fig', 'figure'),
        [Input('day-dropdown', 'value'),
        Input('include-toilets-checkbox', 'value')]
    )
    
    def update_map(selected_day, include_toilets=False):
        logger.info(f'Updating map')
        if selected_day == 'all':
            filtered_df = df.copy()
        else:
            filtered_df = df[df['day'] == int(selected_day)].reset_index(drop=True)
            if selected_day != '1':
                logger.info(f'Adding last day point do df')
                previous_day_last_point = df[(df['day'] == selected_day - 1) & (df['rank'] == df[df['day'] == selected_day - 1]['rank'].max())]
                
            if not previous_day_last_point.empty:
                filtered_df = pd.concat([filtered_df, previous_day_last_point], ignore_index=True)
                day_color = filtered_df['colors'].iloc[0] # added line in loc|-1]
                filtered_df.loc[filtered_df.index[-1], 'colors'] = day_color
                filtered_df
                logger.info(f'Updating color for last day to {day_color}')
                
        logger.info(f"Data :\n {filtered_df}")
                
        new_fig = create_figure(filtered_df)
        
        if include_toilets:
            add_points_to_figure(new_fig, df_toilets, filter_type='WC')
        
            
        return new_fig
    
    logger.info('App successfully created')
    return app


def get_toilets_data(selected_toilets):
    wc_dict = {
        'longitude': [wc.longitude for wc in selected_toilets],
        'latitude': [wc.latitude for wc in selected_toilets],
        'city': [wc.city for wc in selected_toilets],
        'city_code': [wc.city_code for wc in selected_toilets],
        'type': ['WC' for wc in selected_toilets],
        'name': [wc.name for wc in selected_toilets],
        'colors': ['red' for wc in selected_toilets],
        'day': [wc.day for wc in selected_toilets],
        'symbol': ['toilet' for wc in selected_toilets]
    }

    toilets_df = pd.DataFrame(wc_dict)
    
    return toilets_df


def preprocess_geospatial_data(geospatial_point_list):
    logger.info('Preprocessing data')
    df = pd.DataFrame(geospatial_point_list)\
        .sort_values(by=['day', 'rank'])\
        .drop_duplicates(subset=["day", "rank"])\
        .drop(['uuid', 'cluster'], axis=1)\
        .reset_index(drop=True)

    colors = ['blue', 'green', 'purple', 'orange', 'cyan', 'magenta',
              'yellow', 'lime', 'pink', 'teal', 'indigo', 'brown', 'olive',
              'gray', 'violet', 'azure', 'lavender', 'plum', 'gold', 'maroon']
   
    df['latitude'] = df['latitude'].astype(float)
    df['longitude'] = df['longitude'].astype(float)
    df['colors'] = df['day'].map(lambda x: colors[x - 1])
    df['symbol'] = df.apply(lambda row: get_symbol(row['type'], row.name == df.index[-1], row.name == 0), axis=1)
    df['normalized_score'] = ((df['score'] / df['score'].max())*5).round(2)
    df['step'] = df['day'].astype(str) + '.' + df['rank'].astype(str)
    
    logger.info('Preprocessing done')
    return df

