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

    
def add_points_to_figure(fig, df, filter_name=None):
    logger.info(f'Adding {len(df)} points to map')
    
    
    for i, point in df.iterrows():
        logger.info(f"Point {i} : {point['name']}")
        if filter_name and point['name'] != filter_name:
            continue
                                
        symbol = point['symbol']
        poi_text = f"{symbol} {point['name']}"
        hover_text = f"{symbol}<br>{point['name']}<br>Note: {point['notation']}" # 
        # adapt size for toilets
        marker_size = 60 if filter_name == 'WC' else 15
        
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
        Output('include-toilets-div', 'style'),
        [Input('day-dropdown', 'value')]
    )
    def update_checkbox_visibility(selected_day):
        if selected_day == 'all':
            logger.info(f'All day map, no checkbox')
            
            return {'display': 'none'}
        else:
            logger.info(f'Selecting day {selected_day}, adding WC checkbox')
            return {'width': '48%', 'display': 'inline-block'}
    
    @app.callback(
        Output('map-fig', 'figure'),
        [Input('day-dropdown', 'value'),
         Input('include-toilets-checkbox', 'value')]
    )
    
    def update_map(selected_day, include_toilets=False):
        logger.info(f'Updating map')
        if selected_day == 'all':
            filtered_df = df.copy()
            include_toilets = False  # no toilets on map with all-days
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
            toilets_df  = get_toilets_data(selected_day)
            add_points_to_figure(new_fig, toilets_df, filter_name='WC')
        
            
        return new_fig
    
    logger.info('App successfully created')
    return app


def get_toilets_data(selected_day):
    reference_lon, reference_lat = -0.567765, 44.852951
    toilets_data = [
        {
            'longitude': reference_lon + 0.002,
            'latitude': reference_lat + 0.002,
            'type': 'POI',
            'name': 'WC',
            'colors': 'red',
            'notation': '5.0',
            'symbol': '🚽',
            'day': selected_day
        },
        {
            'longitude': reference_lon - 0.001,
            'latitude': reference_lat - 0.001,
            'type': 'POI',
            'name': 'WC',
            'colors': 'red',
            'notation': '5.0',
            'symbol': '🚽',
            'day': selected_day
        },
        {
            'longitude': reference_lon + 0.003,
            'latitude': reference_lat - 0.001,
            'type': 'POI',
            'name': 'WC',
            'colors': 'red',
            'notation': '5.0',
            'symbol': '🚽',
            'day': selected_day
        },
        {
            'longitude': reference_lon - 0.002,
            'latitude': reference_lat + 0.002,
            'type': 'POI',
            'name': 'WC',
            'colors': 'red',
            'notation': '5.0',
            'symbol': '🚽',
            'day': selected_day
        },
        {
            'longitude': reference_lon + 0.001,
            'latitude': reference_lat - 0.002,
            'type': 'POI',
            'name': 'WC',
            'colors': 'red',
            'notation': '5.0',
            'symbol': '🚽',
            'day': selected_day
        }
    ]
    toilets_df = pd.DataFrame(toilets_data)
    msg = f'Toilets df :\n {toilets_df}'
    logger.info(msg)
    
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


if __name__ == "__main__":
    from dataclasses import dataclass

    @dataclass
    class GeospatialPoint:
        longitude: float
        latitude: float

        city: str
        city_code: int

        type: str
        name: str = ""

        category: str = ""
        notation: float = 0
        score: float = 0.0

        uuid: str = ""
        cluster: int | None = None
        day: int | None = None
        rank: int | None = None

    @dataclass
    class POI(GeospatialPoint):
        type: str = "POI"

    @dataclass
    class Restaurant(GeospatialPoint):
        type: str = "Restaurant"

    @dataclass
    class Hosting(GeospatialPoint):
        type: str = "Hosting"

    @dataclass
    class Trail(GeospatialPoint):
        type: str = "Trail"

    @dataclass
    class WC(GeospatialPoint):
        type: str = "POI"
        name: str = "WC"

    list_points = [POI(longitude='-0.5766451', latitude='44.8375888', city='Bordeaux', city_code=33000, type='POI', name='Tour Pey-Berland', category='', notation=0, score=180, uuid='3ebfbd0f-3af2-46bf-ae99-30c0dd30ac1f', cluster=0, day=1, rank=1),
                   POI(longitude='-0.571477', latitude='44.8354741', city='Bordeaux', city_code=33000, type='POI', name='Grosse Cloche', category='', notation=0, score=70, uuid='fecd1c7a-6235-495d-952e-3b6b95bb5a8a', cluster=0, day=1, rank=2),
                   POI(longitude='-0.5834431', latitude='44.8360031', city='Bordeaux', city_code=33000, type='POI', name='Bibliothèque municipale', category='', notation=0, score=0, uuid='2e236e91-24d2-4f33-820f-f43bd45f767a', cluster=0, day=1, rank=4),
                   POI(longitude='-0.587269', latitude='44.8350088', city='Bordeaux', city_code=33000, type='POI', name='Ville de Bordeaux', category='', notation=0, score=0, uuid='183332b5-a11c-4f63-8b66-63a06f3b0fff', cluster=0, day=1, rank=5),
                   POI(longitude='-0.57598', latitude='44.84542', city='Bordeaux', city_code=33000, type='POI', name='Monument aux Girondins', category='', notation=0, score=140, uuid='4b1c1c4d-7f93-4bd4-b6f7-e35cdffa2f6a', cluster=5, day=2, rank=1),
                   POI(longitude='-0.575835', latitude='44.848596', city='Bordeaux', city_code=33000, type='POI', name='Jardin public', category='', notation=0, score=90, uuid='9a528304-aa19-497e-8697-5447aebbbedb', cluster=5, day=2, rank=2),
                   POI(longitude='-0.5691914', latitude='44.8419351', city='Bordeaux', city_code=33000, type='POI', name="Miroir d'eau", category='', notation=0, score=80, uuid='5fac44d2-951d-47f3-b46f-4ad6542ae80f', cluster=5, day=2, rank=4),
                   POI(longitude='-0.5696669', latitude='44.841551', city='Bordeaux', city_code=33000, type='POI', name='Place de la Bourse', category='', notation=0, score=110, uuid='d943859e-a57d-435b-b2b8-549e267828d7', cluster=5, day=2, rank=5),
                   POI(longitude='-0.567257', latitude='44.838489', city='Bordeaux', city_code=33000, type='POI', name='Maison écocitoyenne de Bordeaux', category='', notation=0, score=0, uuid='3304ade6-f20c-4a96-82fe-641dc0297f9b', cluster=1, day=3, rank=1),
                   POI(longitude='-0.5630737', latitude='44.8384504', city='Bordeaux', city_code=33000, type='POI', name='Pont de pierre', category='', notation=0, score=0, uuid='308318e7-83fe-4ba3-a626-ffb1f1566b1e', cluster=1, day=3, rank=2),
                   POI(longitude='-0.561741', latitude='44.849484', city='Bordeaux', city_code=33000, type='POI', name='Darwin / Caserne Niel', category='', notation=0, score=0, uuid='02182ce2-0b74-4eb0-8a06-62e2541f291e', cluster=1, day=3, rank=4),
                   POI(longitude='-0.5555191', latitude='44.8287161', city='Bordeaux', city_code=33800, type='POI', name='Gare Saint Jean', category='', notation=0, score=0, uuid='2353074d-d5e1-47aa-a5f5-e28253d4f210', cluster=1, day=3, rank=5),
                   POI(longitude='-0.5628944', latitude='44.8610315', city='Bordeaux', city_code=33300, type='POI', name='La Galerie Lumière', category='', notation=0, score=0, uuid='3b409ed1-9ca8-4a05-a88f-8ebd3254754f', cluster=4, day=4, rank=1),
                   POI(longitude='-0.5589808', latitude='44.8702832', city='Bordeaux', city_code=33000, type='POI', name='Base sous-marine', category='', notation=0, score=0, uuid='86e69d0c-c682-43c2-bec1-d2b17355ccfd', cluster=4, day=4, rank=2),
                   POI(longitude='-0.5495055', latitude='44.8640443', city='Bordeaux', city_code=33300, type='POI', name="Les Vivres de l'Art", category='', notation=0, score=0, uuid='35d91622-204f-4450-a1f6-cadf3cb7c06a', cluster=4, day=4, rank=4),
                   POI(longitude='-0.5359228', latitude='44.87952', city='Bordeaux', city_code=33000, type='POI', name="Pont d'Aquitaine", category='', notation=0, score=0, uuid='212220f4-78d8-4fc2-9f77-1eb7cdb4731c', cluster=4, day=4, rank=5),
                   POI(longitude='-0.573964', latitude='44.907501', city='Bordeaux', city_code=33300, type='POI', name='Réserve écologique des Barails', category='', notation=0, score=0, uuid='6b90d53a-ba18-411b-96d2-55e7bc899cfd', cluster=6, day=5, rank=1),
                   POI(longitude='-0.6017062', latitude='44.8794938', city='Bruges', city_code=33520, type='POI', name='Le parc Ausone', category='', notation=0, score=0, uuid='60004c32-d0e7-4088-806b-4e634f9a760e', cluster=3, day=5, rank=2),
                   POI(longitude='-0.6017074', latitude='44.8533258', city='Bordeaux', city_code=33000, type='POI', name='Parc Bordelais', category='', notation=0, score=30, uuid='03b5155e-9f91-408b-ba2c-f3578f52c5de', cluster=3, day=5, rank=4),
                   POI(longitude='-0.5891036', latitude='44.8539365', city='Bordeaux', city_code=33000, type='POI', name='Institut culturel Bernard Magrez', category='', notation=0, score=0, uuid='5278e56b-6502-48f1-b3c3-3f9c1108af7d', cluster=3, day=5, rank=5),
                   POI(longitude='-0.5889146', latitude='44.852782', city='Bordeaux', city_code=33000, type='POI', name='La Grande Maison de Bernard Magrez', category='', notation=0, score=0, uuid='12753d54-cdb4-4bc5-9550-97da4dbf043a', cluster=3, day=6, rank=1),
                   POI(longitude='-0.612311', latitude='44.864726', city='Le Bouscat', city_code=33110, type='POI', name="Parc de la Chêneraie et le Castel d'Andorte", category='', notation=0, score=0, uuid='aeefc24e-1d23-4d1a-a60c-4994ab1c80e2', cluster=2, day=6, rank=2),
                   POI(longitude='-0.6265706', latitude='44.8748152', city='Le Bouscat', city_code=33110, type='POI', name='Bois du Bouscat', category='', notation=0, score=0, uuid='c7752635-e5cc-42fb-8666-257b937864e9', cluster=2, day=6, rank=4),
                   Restaurant(longitude='-0.5808558', latitude='44.836883000483', city='Bordeaux', city_code=33063, type='Restaurant', name='Les taquineries de Marie', category='', notation=0, score=0, uuid='015db241-37e1-4fda-8c07-3e280f1b9c5b', cluster=None, day=1, rank=3),
                   Restaurant(longitude='-0.5821213', latitude='44.8405135004827', city='Bordeaux', city_code=33063, type='Restaurant', name='Woof', category='', notation=0, score=0, uuid='0192f339-6fdc-4fd2-b66b-5e5598de81e8', cluster=None, day=1, rank=6),
                   Restaurant(longitude='-0.5821213', latitude='44.8405135004827', city='Bordeaux', city_code=33063, type='Restaurant', name='Woof', category='', notation=0, score=0, uuid='0192f339-6fdc-4fd2-b66b-5e5598de81e8', cluster=None, day=2, rank=3),
                   Restaurant(longitude='-0.5808558', latitude='44.836883000483', city='Bordeaux', city_code=33063, type='Restaurant', name='Les taquineries de Marie', category='', notation=0, score=0, uuid='015db241-37e1-4fda-8c07-3e280f1b9c5b', cluster=None, day=2, rank=6),
                   Restaurant(longitude='-0.562081', latitude='44.8505459004818', city='Bordeaux', city_code=33063, type='Restaurant', name='Guinguette Alriq', category='', notation=0, score=0, uuid='01506767-f4a3-4414-b586-3266199fc259', cluster=None, day=3, rank=3),
                   Restaurant(longitude='-0.5821213', latitude='44.8405135004827', city='Bordeaux', city_code=33063, type='Restaurant', name='Woof', category='', notation=0, score=0, uuid='0192f339-6fdc-4fd2-b66b-5e5598de81e8', cluster=None, day=3, rank=6),
                   Restaurant(longitude='-0.5547727', latitude='44.8679696004803', city='Bordeaux', city_code=33063, type='Restaurant', name='Saudade', category='', notation=0, score=0, uuid='0083784d-d725-4edf-a0c5-779be3dc6dcb', cluster=None, day=4, rank=3),
                   Restaurant(longitude='-0.5679394', latitude='44.8789830004793', city='Bordeaux', city_code=33063, type='Restaurant', name='Nachos', category='', notation=0, score=0, uuid='00725a36-2c08-4ebe-ad0f-66b0bd8f6f2a', cluster=None, day=4, rank=6),
                   Restaurant(longitude='-0.569928', latitude='44.8794691004793', city='Bordeaux', city_code=33063, type='Restaurant', name='Lettuce Garden', category='', notation=0, score=0, uuid='0024d2f4-18e9-4f0d-8613-c7e4ed3895c6', cluster=None, day=5, rank=3),
                   Restaurant(longitude='-0.5821213', latitude='44.8405135004827', city='Bordeaux', city_code=33063, type='Restaurant', name='Woof', category='', notation=0, score=0, uuid='0192f339-6fdc-4fd2-b66b-5e5598de81e8', cluster=None, day=5, rank=6),
                   Restaurant(longitude='-0.5821213', latitude='44.8405135004827', city='Bordeaux', city_code=33063, type='Restaurant', name='Woof', category='', notation=0, score=0, uuid='0192f339-6fdc-4fd2-b66b-5e5598de81e8', cluster=None, day=6, rank=3),
                   Restaurant(longitude='-0.569928', latitude='44.8794691004793', city='Bordeaux', city_code=33063, type='Restaurant', name='Lettuce Garden', category='', notation=0, score=0, uuid='0024d2f4-18e9-4f0d-8613-c7e4ed3895c6', cluster=None, day=6, rank=6),
                   Hosting(longitude='-0.5786053', latitude='44.8423259004825', city='Bordeaux', city_code=33063, type='Hosting', name='Konti By Happyculture', category='', notation=0, score=0, uuid='146aa648-28c1-4bd6-8dd8-f1cf94a292f7', cluster=None, day=1, rank=7),
                   Hosting(longitude='-0.5786053', latitude='44.8423259004825', city='Bordeaux', city_code=33063, type='Hosting', name='Konti By Happyculture', category='', notation=0, score=0, uuid='146aa648-28c1-4bd6-8dd8-f1cf94a292f7', cluster=None, day=2, rank=7),
                   Hosting(longitude='-0.5786053', latitude='44.8423259004825', city='Bordeaux', city_code=33063, type='Hosting', name='Konti By Happyculture', category='', notation=0, score=0, uuid='146aa648-28c1-4bd6-8dd8-f1cf94a292f7', cluster=None, day=3, rank=7),
                   Hosting(longitude='-0.551434', latitude='44.8646983004806', city='Bordeaux', city_code=33063, type='Hosting', name='Mer & Golf', category='', notation=0, score=0, uuid='06c7fa7a-3e01-4afa-8203-c4d4d91d7b65', cluster=None, day=4, rank=7),
                   Hosting(longitude='-0.5786053', latitude='44.8423259004825', city='Bordeaux', city_code=33063, type='Hosting', name='Konti By Happyculture', category='', notation=0, score=0, uuid='146aa648-28c1-4bd6-8dd8-f1cf94a292f7', cluster=None, day=5, rank=7)]
    app = create_dash_app(list_points)
       