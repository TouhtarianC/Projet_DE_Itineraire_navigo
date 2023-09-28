import dash
from dash.dependencies import Input, Output
from dash import dcc, html, Dash
import plotly.express as px
import plotly.graph_objs as go

import flask
import pandas as pd
import os


def create_dash_app(geospatial_point_list) -> dash.Dash:
    token = "pk.eyJ1IjoiaGF6ZW1hbWFyYSIsImEiOiJjbGt2cmV6YXAwMGRlM3BwcGV0dHVjNW5kIn0.9ZSlxSY240CuAUQ1btlWuw"

    fig = go.Figure(go.Scattermapbox(
        name="Trip recommendation itinerary",
        mode="markers+text+lines",
        lon=[x.longitude for x in geospatial_point_list],
        lat=[x.latitude for x in geospatial_point_list],
        marker={'size': 10, 'symbol': ["bus" for _ in range(len(geospatial_point_list))]},
        text=[x.name for x in geospatial_point_list],
        textposition="bottom right"))

    fig.update_layout(
        mapbox={
            'accesstoken': token,
            'style': "outdoors",
            'zoom': 4.9,
            'center': {
                'lon': 2.209666999999996,
                'lat': 46.232192999999995,
            }
        },
        showlegend=False)

    fig.show()

    app = Dash()
    app.layout = html.Div([
        dcc.Graph(figure=fig)
    ])

    return app


# def create_dash_app(geospatial_point_list) -> dash.Dash:
#     """
#     Sample Dash application from Plotly: https://github.com/plotly/dash-hello-world/blob/master/app.py
#     """
#     server = flask.Flask(__name__)
#
#     df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/hello-world-stock.csv')
#
#     app = dash.Dash(__name__, server=server, requests_pathname_prefix="/dash/")
#
#     app.scripts.config.serve_locally = False
#     dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'
#
#     app.layout = html.Div([
#         html.H1('Stock Tickers'),
#         dcc.Dropdown(
#             id='my-dropdown',
#             options=[
#                 {'label': 'Tesla', 'value': 'TSLA'},
#                 {'label': 'Apple', 'value': 'AAPL'},
#                 {'label': 'Coke', 'value': 'COKE'}
#             ],
#             value='TSLA'
#         ),
#         dcc.Graph(id='my-graph')
#     ], className="container")
#
#     @app.callback(Output('my-graph', 'figure'),
#                   [Input('my-dropdown', 'value')])
#     def update_graph(selected_dropdown_value):
#         dff = df[df['Stock'] == selected_dropdown_value]
#         return {
#             'data': [{
#                 'x': dff.Date,
#                 'y': dff.Close,
#                 'line': {
#                     'width': 3,
#                     'shape': 'spline'
#                 }
#             }],
#             'layout': {
#                 'margin': {
#                     'l': 30,
#                     'r': 20,
#                     'b': 30,
#                     't': 20
#                 }
#             }
#         }
#
#     return app
