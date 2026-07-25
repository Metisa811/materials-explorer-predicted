import pandas as pd
import json
import re
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import linregress
import dash
from dash import dcc, html, Input, Output, State, callback_context
import numpy as np
import os
import sys

# --- Helper Function for .exe file paths ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- 1. Data Loading and Processing ---
def load_data():
    try:
        ptable_path = resource_path("ptable2.csv")
        ptable_df = pd.read_csv(ptable_path)
        ptable_df.rename(columns={"symbol": "element"}, inplace=True)
        ptable_df['element'] = ptable_df['element'].str.strip()

        json_path = resource_path("vaspkit_output.json")
        with open(json_path, "r") as f:
            mech_data_nested = json.load(f)

        mechanical_properties_list = []
        for material, data in mech_data_nested.items():
            if not data:
                continue
                
            props = {"material": material}
            for root_key in ["Crystal_System", "Space_Group", "Independent_Elastic_Constants", "Is_DFT_Verified"]:
                if root_key in data:
                    props[root_key] = data[root_key]

            if "Elastic_Tensor_Voigt" in data:
                for k, v in data["Elastic_Tensor_Voigt"].items():
                    props[f"Elastic_{k}"] = v

            if "Anisotropic_Mechanical_Properties" in data:
                for key, stats in data["Anisotropic_Mechanical_Properties"].items():
                    clean_key = key.lstrip('|__').replace('__', '_')
                    if isinstance(stats, dict):
                        for stat in ["Min", "Max", "Anisotropy"]:
                            if stat in stats:
                                props[f"Aniso_{clean_key}_{stat}"] = stats[stat]

            if "Average_Mechanical_Properties" in data:
                for key, stats in data["Average_Mechanical_Properties"].items():
                    clean_key = key.lstrip('|__').replace('__', '_')
                    if isinstance(stats, dict):
                        for stat in ["Voigt", "Reuss", "Hill"]:
                            if stat in stats:
                                props[f"Avg_{clean_key}_{stat}"] = stats[stat]

            if "Additional_Properties" in data:
                for key, val in data["Additional_Properties"].items():
                    props[key] = val
            
            mechanical_properties_list.append(props)

        mech_df = pd.DataFrame(mechanical_properties_list)
        if mech_df.empty:
            return pd.DataFrame(), [], []

    except Exception as e:
        print(f"An error occurred during data loading: {e}")
        return pd.DataFrame(), [], []

    def extract_elements(formula):
        return re.findall(r'[A-Z][a-z]?', formula)

    feature_cols = [c for c in ptable_df.columns if c not in ['element']]
    materials_data = []

    for _, row in mech_df.iterrows():
        material = row['material']
        elements = extract_elements(material)
        sub_df = ptable_df[ptable_df['element'].isin(elements)]
        
        if len(sub_df) == 0 or len(sub_df) != len(elements):
            continue
            
        averaged = sub_df[feature_cols].mean(numeric_only=True)
        averaged['material'] = material
        materials_data.append(averaged)

    features_avg_df = pd.DataFrame(materials_data)
    if features_avg_df.empty:
        return pd.DataFrame(), [], []

    merged_df = pd.merge(features_avg_df, mech_df, on='material', how='inner')
    atomic_features = sorted([c for c in features_avg_df.columns if c not in ['material']])
    numeric_mech_cols = mech_df.select_dtypes(include=[np.number]).columns.tolist()
    excluded_y_cols = ['material', 'Independent_Elastic_Constants', 'Is_DFT_Verified']
    mechanical_properties = sorted([c for c in numeric_mech_cols if c not in excluded_y_cols])
    
    return merged_df, atomic_features, mechanical_properties

global_df, atomic_features, mechanical_properties = load_data()

# --- 2. Initialize Dash App ---
app = dash.Dash(__name__)
app.title = "Materials Property Explorer"

# Base style for the custom modal overlay
MODAL_STYLE = {
    'display': 'none',
    'position': 'fixed',
    'zIndex': 1000,
    'left': 0,
    'top': 0,
    'width': '100%',
    'height': '100%',
    'overflow': 'auto',
    'backgroundColor': 'rgba(0,0,0,0.5)',
    'fontFamily': 'Arial, sans-serif'
}

# --- 3. App Layout ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px', 'backgroundColor': '#f9f9f9', 'minHeight': '100vh'}, children=[
    
    html.H1("Interactive Materials Property Explorer", style={'textAlign': 'center', 'color': '#333'}),
    html.Hr(),

    html.Div([
        html.Div([
            html.Label("Select Atomic Feature (X-Axis):", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='x-axis-dropdown',
                options=[{'label': f, 'value': f} for f in atomic_features],
                value=atomic_features[0] if atomic_features else None,
                clearable=False
            )
        ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),

        html.Div([
            html.Label("Select Mechanical Property (Y-Axis):", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            dcc.Dropdown(
                id='y-axis-dropdown',
                options=[{'label': p, 'value': p} for p in mechanical_properties],
                value=mechanical_properties[0] if mechanical_properties else None,
                clearable=False
            )
        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'}),
    ], style={'marginBottom': '20px', 'padding': '20px', 'backgroundColor': 'white', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),

    dcc.Graph(id='scatter-plot', style={'height': '600px'}),

    # Custom HTML Modal
    html.Div(id='material-modal', style=MODAL_STYLE, children=[
        html.Div(style={
            'backgroundColor': 'white',
            'margin': '10% auto',
            'padding': '20px',
            'border': '1px solid #888',
            'width': '60%',
            'borderRadius': '8px',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'
        }, children=[
            html.Div([
                html.H2("Material Details", style={'color': '#333', 'margin': '0', 'display': 'inline-block'}),
                html.Button("×", id='modal-close-button', n_clicks=0, style={
                    'float': 'right', 'fontSize': '28px', 'fontWeight': 'bold', 
                    'background': 'none', 'border': 'none', 'cursor': 'pointer', 'color': '#888'
                }),
            ], style={'borderBottom': '1px solid #eee', 'paddingBottom': '10px', 'marginBottom': '20px'}),
            
            html.Div(id='modal-content', style={'maxHeight': '60vh', 'overflowY': 'auto'})
        ])
    ])
])

# --- 4. Callbacks ---

@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('x-axis-dropdown', 'value'),
     Input('y-axis-dropdown', 'value')]
)
def update_graph(x_axis_name, y_axis_name):
    if not x_axis_name or not y_axis_name or global_df.empty:
        return go.Figure()

    plot_df = global_df[['material', x_axis_name, y_axis_name]].copy()
    plot_df[x_axis_name] = pd.to_numeric(plot_df[x_axis_name], errors='coerce')
    plot_df[y_axis_name] = pd.to_numeric(plot_df[y_axis_name], errors='coerce')
    plot_df = plot_df.dropna(subset=[x_axis_name, y_axis_name])

    if plot_df.empty:
        return go.Figure().update_layout(title_text=f"No valid data for {x_axis_name} vs {y_axis_name}")

    fig = px.scatter(
        plot_df, x=x_axis_name, y=y_axis_name, hover_data=['material'], custom_data=['material']
    )

    try:
        x = plot_df[x_axis_name]
        y = plot_df[y_axis_name]
        if x.nunique() > 1:
            slope, intercept, r, p, stderr = linregress(x, y)
            line_x = np.array([x.min(), x.max()])
            line_y = slope * line_x + intercept
            
            fig.add_trace(go.Scatter(
                x=line_x, y=line_y, mode='lines',
                line=dict(color='red', dash='dash'),
                name=f'Regression (R² = {r**2:.3f})'
            ))
    except Exception as e:
        print(f"Could not compute regression: {e}")

    fig.update_layout(
        title=f'{y_axis_name} vs. {x_axis_name}',
        xaxis_title=x_axis_name,
        yaxis_title=y_axis_name,
        hovermode="closest",
        plot_bgcolor='white',
        paper_bgcolor='#f9f9f9',
        font_color='#333',
        transition_duration=500
    )
    
    fig.update_xaxes(gridcolor='#eee', zerolinecolor='#ddd')
    fig.update_yaxes(gridcolor='#eee', zerolinecolor='#ddd')

    return fig


@app.callback(
    [Output('material-modal', 'style'),
     Output('modal-content', 'children')],
    [Input('scatter-plot', 'clickData'),
     Input('modal-close-button', 'n_clicks')],
    [State('material-modal', 'style')]
)
def toggle_material_modal(clickData, n_clicks_close, current_style):
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'No-trigger'

    # Create a fresh copy of the style to modify
    style_dict = dict(current_style) if current_style else dict(MODAL_STYLE)

    # Close button was clicked
    if trigger_id == 'modal-close-button':
        style_dict['display'] = 'none'
        return style_dict, dash.no_update

    # A point on the graph was clicked
    if trigger_id == 'scatter-plot' and clickData:
        material_name = clickData['points'][0]['customdata'][0]
        material_data = global_df[global_df['material'] == material_name].iloc[0]
        
        content = []
        content.append(html.H3(material_name, style={'color': '#007bff', 'borderBottom': '2px solid #007bff', 'paddingBottom': '5px'}))
        
        table_header = [html.Thead(html.Tr([html.Th("Property", style={'textAlign': 'left', 'padding': '8px'}), html.Th("Value", style={'textAlign': 'left', 'padding': '8px'})]))]
        table_body = []
        
        for key, value in material_data.items():
            if key == 'material' or pd.isna(value):
                continue
            if isinstance(value, (int, float, np.number)):
                value = round(value, 4)
            table_body.append(html.Tr([
                html.Td(key, style={'fontWeight': 'bold', 'padding': '8px', 'borderBottom': '1px solid #eee'}), 
                html.Td(str(value), style={'padding': '8px', 'borderBottom': '1px solid #eee'})
            ]))

        table = html.Table(table_header + [html.Tbody(table_body)], style={
            'width': '100%', 'borderCollapse': 'collapse', 'marginTop': '15px'
        })
        content.append(table)
        
        style_dict['display'] = 'block' # Show modal
        return style_dict, content

    return style_dict, dash.no_update

if __name__ == '__main__':
    # Streamlit Cloud needs port 8501, usually local needs 8050
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)
