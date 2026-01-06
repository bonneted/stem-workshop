"""
Quarter Car Simulation Web Application

A Dash-based web app that simulates a quarter car suspension model.
Converted from MATLAB GUI (quarterCarUI.m).
"""

import os
from dash import Dash, html, dcc, callback, Input, Output, State, no_update
import plotly.graph_objects as go
import json

from simulation import SimulationParams, run_simulation, SimulationResult
from plotting import create_animation_frame, create_displacement_plot


# Initialize the Dash app
app = Dash(__name__)
app.title = "Quarter Car Model"

# Expose the Flask server for gunicorn
server = app.server

# Animation interval in milliseconds (33ms ≈ 30fps)
ANIMATION_INTERVAL_MS = 33

# Custom CSS styles
styles = {
    'container': {
        'display': 'flex',
        'flexDirection': 'row',
        'height': '100vh',
        'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        'backgroundColor': '#f5f5f5'
    },
    'control_panel': {
        'width': '320px',
        'padding': '20px',
        'backgroundColor': '#ffffff',
        'borderRight': '1px solid #e0e0e0',
        'overflowY': 'auto'
    },
    'plot_container': {
        'flex': '1',
        'display': 'flex',
        'flexDirection': 'row',
        'padding': '10px'
    },
    'plot_panel': {
        'flex': '1',
        'padding': '10px'
    },
    'title': {
        'fontSize': '24px',
        'fontWeight': 'bold',
        'marginBottom': '20px',
        'color': '#333'
    },
    'slider_container': {
        'marginBottom': '25px'
    },
    'slider_label': {
        'fontSize': '14px',
        'fontWeight': '500',
        'color': '#555',
        'marginBottom': '10px'
    },
    'button': {
        'width': '100%',
        'padding': '15px',
        'fontSize': '16px',
        'fontWeight': 'bold',
        'backgroundColor': '#4CAF50',
        'color': 'white',
        'border': 'none',
        'borderRadius': '8px',
        'cursor': 'pointer',
        'marginTop': '20px'
    },
    'status': {
        'marginTop': '15px',
        'padding': '10px',
        'backgroundColor': '#e8f5e9',
        'borderRadius': '4px',
        'fontSize': '14px',
        'color': '#2e7d32'
    }
}

# App layout
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([
    # Hidden stores for simulation data
    dcc.Store(id='simulation-data'),
    dcc.Store(id='frame-index', data=0),
    dcc.Store(id='is-running', data=False),
    
    # Animation frames store
    dcc.Store(id='animation-frames'),
    
    # Animation interval component
    dcc.Interval(
        id='animation-interval',
        interval=60, # 60ms = ~16fps, safer for mobile
        n_intervals=0,
        disabled=True
    ),
    
    # Main container
    html.Div([
        # Control panel
        html.Div([
            html.H1('Quarter Car Model', className='app-title'),
            
            # Sliders grid (responsive 2-column on tablet)
            html.Div([
                # Suspension stiffness slider
                html.Div([
                    html.Label('Suspension Stiffness Ks [N/m]', className='slider-label'),
                    dcc.Slider(
                        id='slider-ks',
                        min=10000,
                        max=100000,
                        step=1000,
                        value=48000,
                        marks={10000: '10k', 50000: '50k', 100000: '100k'},
                        tooltip={'placement': 'bottom', 'always_visible': True}
                    )
                ], className='slider-container'),
                
                # Damping slider
                html.Div([
                    html.Label('Damping Cs [Ns/m]', className='slider-label'),
                    dcc.Slider(
                        id='slider-cs',
                        min=100,
                        max=5000,
                        step=100,
                        value=1000,
                        marks={100: '100', 2500: '2500', 5000: '5000'},
                        tooltip={'placement': 'bottom', 'always_visible': True}
                    )
                ], className='slider-container'),
                
                # Vehicle speed slider
                html.Div([
                    html.Label('Vehicle Speed [m/s]', className='slider-label'),
                    dcc.Slider(
                        id='slider-vel',
                        min=0.5,
                        max=5,
                        step=0.1,
                        value=2,
                        marks={0.5: '0.5', 2.5: '2.5', 5: '5'},
                        tooltip={'placement': 'bottom', 'always_visible': True}
                    )
                ], className='slider-container'),
                
                # Tire stiffness slider
                html.Div([
                    html.Label('Tire Stiffness Kt [N/m]', className='slider-label'),
                    dcc.Slider(
                        id='slider-kt',
                        min=50000,
                        max=500000,
                        step=10000,
                        value=200000,
                        marks={50000: '50k', 250000: '250k', 500000: '500k'},
                        tooltip={'placement': 'bottom', 'always_visible': True}
                    )
                ], className='slider-container'),
            ], className='sliders-grid'),
            
            # Start button
            html.Button(
                '▶ Start Simulation',
                id='start-button',
                className='start-button'
            ),
            
            # Status display
            html.Div(id='status-display', className='status-display', children='Ready to simulate')
            
        ], className='control-panel'),
        
        # Plot container
        html.Div([
            # Animation plot
            html.Div([
                dcc.Loading(
                    id="loading-animation",
                    type="default",
                    children=[
                        dcc.Graph(id='animation-graph', style={'height': '100%'}, config={'displayModeBar': False}),
                        html.Div(id='loading-output', style={'display': 'none'}) # Dummy output to trigger loader
                    ],
                    overlay_style={"visibility":"visible", "opacity": .5, "backgroundColor": "white"},
                    custom_spinner=html.H2(["Computing Simulation...", html.Br(), "Please Wait"], style={'marginTop': '100px'})
                )
            ], className='plot-panel'),
            
            # Displacement plot
            html.Div([
                html.Div([
                    dcc.Graph(id='displacement-graph', style={'height': '100%'}, config={'displayModeBar': False})
                ], id='displacement-content', style={'height': '100%'})
            ], id='displacement-container', className='plot-panel')
        ], className='plot-container')
        
    ], className='app-container')
])


def serialize_result(result: SimulationResult) -> dict:
    """Convert SimulationResult to JSON-serializable dict."""
    return {
        'time': result.time.tolist(),
        'z_s': result.z_s.tolist(),
        'z_u': result.z_u.tolist(),
        'u': result.u.tolist(),
        'lon': result.lon.tolist(),
        'road_x': result.road_x.tolist(),
        'road_z': result.road_z.tolist(),
        'L0_s': result.L0_s,
        'L0_u': result.L0_u,
        'h_s': result.h_s,
        'h_u': result.h_u,
        'a': result.a,
        'Kt': result.Kt
    }


def deserialize_result(data: dict) -> SimulationResult:
    """Convert dict back to SimulationResult."""
    import numpy as np
    return SimulationResult(
        time=np.array(data['time']),
        z_s=np.array(data['z_s']),
        z_u=np.array(data['z_u']),
        u=np.array(data['u']),
        lon=np.array(data['lon']),
        road_x=np.array(data['road_x']),
        road_z=np.array(data['road_z']),
        L0_s=data['L0_s'],
        L0_u=data['L0_u'],
        h_s=data['h_s'],
        h_u=data['h_u'],
        a=data['a'],
        Kt=data['Kt']
    )


@callback(
    Output('simulation-data', 'data'),
    Output('animation-frames', 'data'),
    Output('frame-index', 'data', allow_duplicate=True),
    Output('is-running', 'data', allow_duplicate=True),
    Output('animation-interval', 'disabled', allow_duplicate=True),
    Output('status-display', 'children'),
    Output('loading-output', 'children'),
    Output('displacement-content', 'style', allow_duplicate=True),
    Input('start-button', 'n_clicks'),
    State('slider-ks', 'value'),
    State('slider-cs', 'value'),
    State('slider-vel', 'value'),
    State('slider-kt', 'value'),
    prevent_initial_call=True
)
def start_simulation(n_clicks, ks, cs, vel, kt):
    """Handle start button click - run simulation and pre-compute frames."""
    if n_clicks is None:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    # Create simulation parameters
    params = SimulationParams(
        Ks=ks,
        Cs=cs,
        Kt=kt,
        vel=vel
    )
    
    # Run simulation
    result = run_simulation(params)
    
    # Serialize result for storage
    data = serialize_result(result)
    
    # Pre-compute all animation frames
    # We extract the updating parts of the figure for each frame
    frames = []
    num_frames = len(result.time)
    
    for i in range(num_frames):
        fig = create_animation_frame(result, i)
        frame_data = json.loads(fig.to_json())['data']
        layout_update = {
            'title': fig.layout.title.text,
            'xaxis': {'range': fig.layout.xaxis.range}
        }
        frames.append({'data': frame_data, 'layout': layout_update})
    
    status = f"Running simulation... Ks={ks}, Cs={cs}, Kt={kt}, v={vel}"
    
    # Start: Hide displacement content using visibility: hidden (keeps layout space)
    return data, frames, 0, True, False, status, "loaded", {'visibility': 'hidden', 'height': '100%'}


@callback(
    Output('frame-index', 'data'),
    Output('is-running', 'data'),
    Output('animation-interval', 'disabled'),
    Input('animation-interval', 'n_intervals'),
    State('frame-index', 'data'),
    State('simulation-data', 'data'),
    State('is-running', 'data'),
    prevent_initial_call=True
)
def update_frame_index(n_intervals, current_frame, sim_data, is_running):
    """Advance frame index during animation."""
    if not is_running or sim_data is None:
        return no_update, no_update, no_update
    
    num_frames = len(sim_data['time'])
    next_frame = current_frame + 1
    
    if next_frame >= num_frames:
        # Animation complete
        return num_frames - 1, False, True
    
    return next_frame, True, False


# Clientside callback for smooth animation
app.clientside_callback(
    """
    function(frame_idx, frames_data) {
        if (!frames_data || frame_idx >= frames_data.length) {
            return window.dash_clientside.no_update;
        }
        
        var frame = frames_data[frame_idx];
        
        return {
            'data': frame.data,
            'layout': {
                'title': frame.layout.title,
                'xaxis': frame.layout.xaxis,
                'yaxis': {'range': [-0.1, 2.1], 'title': 'z [m]'},
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50},
                'height': 500,
                'uirevision': 'constant'
            }
        };
    }
    """,
    Output('animation-graph', 'figure'),
    Input('frame-index', 'data'),
    State('animation-frames', 'data')
)


@callback(
    Output('displacement-graph', 'figure'),
    Output('displacement-content', 'style'),
    Input('is-running', 'data'),
    State('simulation-data', 'data'),
    prevent_initial_call=True
)
def update_displacement_plot(is_running, sim_data):
    """Update displacement plot ONLY when animation completes."""
    if is_running or sim_data is None:
        return no_update, no_update
    
    # Show displacement plot once animation is done
    result = deserialize_result(sim_data)
    fig = create_displacement_plot(result)
    
    return fig, {'visibility': 'visible', 'height': '100%'}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(debug=True, host='0.0.0.0', port=port)
