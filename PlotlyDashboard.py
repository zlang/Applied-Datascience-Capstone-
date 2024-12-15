import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import urllib.request
import ssl

# Define the URL and file name
url = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/spacex_launch_dash.csv"
file_name = "spacex_launch_dash.csv"

# Disable SSL certificate verification
ssl_context = ssl._create_unverified_context()

# Open the URL and write the file
with urllib.request.urlopen(url, context=ssl_context) as response:
    with open(file_name, 'wb') as file:
        file.write(response.read())

#print(f"File downloaded and saved as {file_name}")

# Read the CSV file into a pandas DataFrame
spacex_df = pd.read_csv(file_name)

# Check that the CSV contains the required columns
required_columns = ['Launch Site', 'class']
if not all(column in spacex_df.columns for column in required_columns):
    raise ValueError(f"The CSV file must contain the following columns: {required_columns}")

# Display columns of dataframe
print(spacex_df.columns)

# Create Dash app
app = dash.Dash(__name__)

# Prepare options for the dropdown
dropdown_options = [{'label': 'All Sites', 'value': 'ALL'}] + [
    {'label': site, 'value': site} for site in spacex_df['Launch Site'].unique()
]

# Calculate min and max payload from the dataset
min_payload = int(spacex_df['Payload Mass (kg)'].min())
max_payload = int(spacex_df['Payload Mass (kg)'].max())

# App Layout
app.layout = html.Div([
    dcc.Dropdown(
        id='site-dropdown',
        options=[
            {'label': 'All Sites', 'value': 'ALL'},
            {'label': 'CCAFS LC-40', 'value': 'CCAFS LC-40'},
            {'label': 'VAFB SLC-4E', 'value': 'VAFB SLC-4E'},
            {'label': 'KSC LC-39A', 'value': 'KSC LC-39A'},
            {'label': 'CCAFS SLC-40', 'value': 'CCAFS SLC-40'}
        ],
        value='ALL',
        placeholder="Select a Launch Site Here",
        searchable=True
    ),
    dcc.RangeSlider(
        id='payload-slider',
        min=min_payload,
        max=max_payload,
        step=1000,
        marks={i: str(i) for i in range(min_payload, max_payload + 1, 1000)},
        value=[min_payload, max_payload]
    ),
    dcc.Graph(id='success-pie-chart'),  # Add the Graph component here
    dcc.Graph(id='success-payload-scatter-chart')  # Scatter chart for payload and success
])

@app.callback(
    Output(component_id='success-pie-chart', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value')
)
def get_pie_chart(entered_site):
    if entered_site == 'ALL':
        # Group data by Launch Site and count successful launches
        site_success_count = spacex_df[spacex_df['class'] == 1].groupby('Launch Site').size().reset_index(name='Success Count')
        fig = px.pie(
            site_success_count,
            names='Launch Site',  # Separate sections for each site
            values='Success Count',  # Use success count for values
            title='Total Success Launches By Site',
            color_discrete_sequence=px.colors.qualitative.Set3  # Custom color scheme
        )
    else:
        # Filter data for the selected site
        site_data = spacex_df[spacex_df['Launch Site'] == entered_site]
        success_count = site_data['class'].value_counts().reset_index()
        success_count.columns = ['Outcome', 'Count']
        fig = px.pie(
            success_count,
            names='Outcome',  # Show success (1) and failure (0)
            values='Count',
            title=f'Total Success Launches for Site {entered_site}',
            color_discrete_sequence=px.colors.qualitative.Set3  # Custom color scheme
        )
    return fig

@app.callback(
    Output(component_id='success-payload-scatter-chart', component_property='figure'),
    [Input(component_id='site-dropdown', component_property='value'),
     Input(component_id='payload-slider', component_property='value')]
)
def update_scatter_chart(entered_site, payload_range):
    # Filter the data based on payload range
    low, high = payload_range
    filtered_df = spacex_df[(spacex_df['Payload Mass (kg)'] >= low) &
                            (spacex_df['Payload Mass (kg)'] <= high)]

    if entered_site == 'ALL':
        # For all sites, show scatter plot
        fig = px.scatter(
            filtered_df,
            x='Payload Mass (kg)',
            y='class',
            color='Booster Version Category',
            title='Correlation between Payload and Success for All Sites',
            labels={'class': 'Launch Outcome (0=Fail, 1=Success)'}
        )
    else:
        # Filter for the specific site
        filtered_df = filtered_df[filtered_df['Launch Site'] == entered_site]
        fig = px.scatter(
            filtered_df,
            x='Payload Mass (kg)',
            y='class',
            color='Booster Version Category',
            title=f'Correlation between Payload and Success for {entered_site}',
            labels={'class': 'Launch Outcome (0=Fail, 1=Success)'}
        )
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
