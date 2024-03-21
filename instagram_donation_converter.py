from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
import base64
import json
import io
from flask import send_file

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
        multiple=True
    ),
    html.Div([
        dcc.Input(id='input-file-name', type='text', placeholder='Enter file name',
                  style={'marginRight': '10px'}),
        html.Button('Download CSV', id='btn-csv', n_clicks=0),
    ], style={'marginTop': '20px'}),
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
    [Output('output-data-upload', 'children'),
     Output('download-csv', 'data')],
    [Input('upload-data', 'contents'),
     State('upload-data', 'filename'),
     State('input-file-name', 'value'),
     Input('btn-csv', 'n_clicks')],
    prevent_initial_call=True
)
def update_output(list_of_contents, list_of_names, file_name, n_clicks):
    if not list_of_contents:
        return html.Div('No files uploaded.'), None

    children = html.Ul([html.Li(name) for name in list_of_names])

    if n_clicks > 0:
        # Convert content into dataframe
        dfs = [pd.read_json(base64.b64decode(content.split(',')[1])) for content in list_of_contents]
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Convert DataFrame to CSV and encode
        return children, dcc.send_file(
            io.BytesIO(combined_df.to_csv(index=False, encoding='utf-8').encode('utf-8')),
            filename=f"{file_name or 'data'}.csv"
        )
    
    return children, None

if __name__ == '__main__':
    app.run_server(debug=True)
