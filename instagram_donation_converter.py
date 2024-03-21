# Import necessary libraries
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, dash_table, callback, State
import dash_bootstrap_components as dbc
import pandas as pd
import json
import base64
import os  # Ensure os is imported for Heroku deployment
from dash.exceptions import PreventUpdate
import flask

# Initialize the Dash app (using Bootstrap for styling)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=True
    ),
    html.Div([
        dcc.Input(
            id='input-file-name',
            type='text',
            placeholder='Enter file name',
            style={'marginRight': '10px'}  # Add some spacing between the input and the button
        ),
        html.Button('Download CSV', id='btn-csv', n_clicks=0),
    ], style={'marginTop': '20px'}),  # Add some spacing above this Div
    dcc.Download(id='download-csv'),
    html.Div(id='output-data-upload'),
])

def parse_json(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    data = json.loads(decoded.decode('utf-8'))
    
    flat_data = []

    # Process 'saved_saved_media' structure
    if 'saved_saved_media' in data:
        for item in data['saved_saved_media']:
            title = item.get('title', 'No Title')
            saved_on_data = item['string_map_data'].get('Saved on', {})
            flat_data.append({
                'title': title,
                'href': saved_on_data.get('href', ''),
                'timestamp': pd.to_datetime(saved_on_data.get('timestamp', 0), unit='s'),
                'category': 'saved_saved_media',
                'file_name': 'saved_posts'
            })

    # Process 'likes_media_likes' structure
    if 'likes_media_likes' in data:
        for item in data['likes_media_likes']:
            title = item.get('title', 'No Title')
            for like_data in item.get('string_list_data', []):
                flat_data.append({
                    'title': title,
                    'href': like_data.get('href', ''),
                    'timestamp': pd.to_datetime(like_data.get('timestamp', 0), unit='s'),
                    'category': 'likes_media_likes',
                    'file_name': 'liked_posts'
                })

    # Process 'impressions_history_posts_seen' structure
    if 'impressions_history_posts_seen' in data:
        for item in data['impressions_history_posts_seen']:
            author_data = item['string_map_data'].get('Author', {}).get('value', 'Unknown')
            time_data = item['string_map_data'].get('Time', {})
            flat_data.append({
                'title': author_data,  # Using 'Author' as 'title' here
                'href': 'N/A',  # No 'href' in this structure
                'timestamp': pd.to_datetime(time_data.get('timestamp', 0), unit='s'),
                'category': 'impressions_history_posts_seen',
                'file_name': 'posts_viewed'
            })

    # Process 'impressions_history_chaining_seen' structure
    if 'impressions_history_chaining_seen' in data:
        for item in data['impressions_history_chaining_seen']:
            username_value = item['string_map_data'].get('Username', {}).get('value', 'Unknown')
            time_data = item['string_map_data'].get('Time', {})
            flat_data.append({
                'title': username_value,
                'href': 'N/A',
                'timestamp': pd.to_datetime(time_data.get('timestamp', 0), unit='s'),
                'category': 'impressions_history_chaining_seen',
                'file_name': 'suggested_accounts_viewed'
            })

    # Process 'impressions_history_videos_watched' structure
    if 'impressions_history_videos_watched' in data:
        for item in data['impressions_history_videos_watched']:
            author_value = item['string_map_data'].get('Author', {}).get('value', 'Unknown')
            time_data = item['string_map_data'].get('Time', {})
            flat_data.append({
                'title': author_value,
                'href': 'N/A',
                'timestamp': pd.to_datetime(time_data.get('timestamp', 0), unit='s'),
                'category': 'impressions_history_videos_watched',
                'file_name': 'videos_watched'
            })


    return pd.DataFrame(flat_data)

@app.callback(
    Output('output-data-upload', 'children'),
    Output('download-csv', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('input-file-name', 'value'),
    Input('btn-csv', 'n_clicks'),
    prevent_initial_call=True
)
def update_output(list_of_contents, list_of_names, file_name, n_clicks):
    if not list_of_contents:
        return html.Div('No files uploaded.'), None
    
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'btn-csv' and n_clicks > 0:
        frames = [parse_json(c, n) for c, n in zip(list_of_contents, list_of_names)]
        combined_df = pd.concat(frames, ignore_index=True)
        csv_string = combined_df.to_csv(index=False, encoding='utf-8')
        return None, dict(content=csv_string, filename=f"{file_name or 'downloaded_data'}.csv")
    
    # Display uploaded file names as feedback
    if trigger_id == 'upload-data':
        return html.Ul(children=[html.Li(f"File: {name}") for name in list_of_names]), None

    raise PreventUpdate
                                        
# Entry point for running the app on Heroku
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=int(os.environ.get('PORT', 8051)))
