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
    dcc.Store(id='first-run', data=True),  # Track if this is the first simulation run
    dcc.Store(id='animation-start-time', data=None),  # Track animation start timestamp
    dcc.Store(id='animation-duration-ms', data=3000),  # Total animation duration in ms
    dcc.Store(id='base-duration-ms', data=3000),  # Base duration before speed factor
    
    # Animation frames store
    dcc.Store(id='animation-frames'),
    dcc.Store(id='displacement-base-figure'),  # Base displacement plot (without markers)
    
    # Animation interval component - fixed 30ms (~33fps) tick rate
    dcc.Interval(
        id='animation-interval',
        interval=30,
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
                        max=3,
                        step=0.1,
                        value=1.5,
                        marks={0.5: '0.5', 1.5: '1.5', 3: '3'},
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
                        dcc.Graph(id='animation-graph', style={'height': 'calc(100% - 60px)'}, config={'displayModeBar': False}),
                        html.Div(id='loading-output', style={'display': 'none'}) # Dummy output to trigger loader
                    ],
                    custom_spinner=html.H2(["Computing Simulation...", html.Br(), "Please Wait"], style={'marginTop': '100px', 'color': '#333'})
                ),
                # Player controls (hidden until animation completes)
                html.Div([
                    html.Div([
                    html.Button(
                        '▶',
                        id='play-pause-button',
                        style={'width': '40px', 'minWidth': '40px', 'height': '40px', 'fontSize': '18px', 'marginRight': '5px', 'cursor': 'pointer', 'borderRadius': '8px', 'border': '1px solid #ccc', 'background': 'white', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}
                    ),
                    # Video speed selector using RadioItems
                    dcc.RadioItems(
                        id='video-speed-dropdown',
                        options=[
                            {'label': '0.25x', 'value': 0.25},
                            {'label': '0.5x', 'value': 0.5},
                            {'label': '1x', 'value': 1},
                            {'label': '2x', 'value': 2}
                        ],
                        value=1,
                        inline=False,
                        style={'marginTop': '10px'},
                        labelStyle={'margin': '0 3px', 'fontSize': '13px', 'cursor': 'pointer'},
                        inputStyle={'marginRight': '3px'}
                    )]),
                    html.Div([
                        dcc.Slider(
                            id='time-slider',
                            min=0,
                            max=100,
                            step=1,
                            value=0,
                            marks=None,
                            tooltip={'placement': 'bottom', 'always_visible': False},
                            updatemode='drag'
                        )
                    ], style={'flex': '1', 'minWidth': '0', 'paddingTop': '10px'})
                ], id='player-controls', style={'display': 'none'})
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
    Output('displacement-base-figure', 'data'),
    Output('base-duration-ms', 'data'),
    Output('animation-duration-ms', 'data'),
    Output('animation-start-time', 'data', allow_duplicate=True),
    Output('frame-index', 'data', allow_duplicate=True),
    Output('is-running', 'data', allow_duplicate=True),
    Output('animation-interval', 'disabled', allow_duplicate=True),
    Output('status-display', 'children'),
    Output('loading-output', 'children'),
    Output('displacement-content', 'style'),
    Output('time-slider', 'max'),
    Output('time-slider', 'value', allow_duplicate=True),
    Output('player-controls', 'style'),
    Output('first-run', 'data'),
    Output('video-speed-dropdown', 'value'),
    Input('start-button', 'n_clicks'),
    State('slider-ks', 'value'),
    State('slider-cs', 'value'),
    State('slider-vel', 'value'),
    State('slider-kt', 'value'),
    State('first-run', 'data'),
    prevent_initial_call=True
)
def start_simulation(n_clicks, ks, cs, vel, kt, is_first_run):
    """Handle start button click - run simulation and pre-compute frames."""
    if n_clicks is None:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
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
    
    # Pre-compute base displacement figure (without markers)
    disp_fig = create_displacement_plot(result, current_time_idx=None)
    disp_fig_data = json.loads(disp_fig.to_json())
    
    # Calculate animation duration (always start at 1x speed)
    base_duration_ms = result.time[-1] * 1000  # Real-time duration
    animation_duration_ms = base_duration_ms  # Start at 1x speed
    
    status = f"Simulation: v={vel} m/s, duration={base_duration_ms/1000:.1f}s"
    
    # Always reset first-run to True for each new simulation
    # This ensures controls are hidden during the initial animation
    # Use -1 as start_time to signal clientside callback to initialize it
    return (data, frames, disp_fig_data, base_duration_ms, animation_duration_ms, -1,
            0, True, False, status, "loaded", 
            {'visibility': 'hidden', 'height': '100%'}, 
            num_frames - 1, 0,
            {'display': 'none'},
            True,  # Always reset first-run to True for new simulation
            1)  # Reset video speed to 1x


# Clientside callback for time-based frame advancement
app.clientside_callback(
    """
    function(n_intervals, start_time, duration_ms, sim_data, is_running) {
        // Return [frame_index, start_time, is_running, interval_disabled, slider_value]
        if (!is_running || !sim_data) {
            return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
        }
        
        var num_frames = sim_data.time.length;
        var now = Date.now();
        
        // Initialize start time if -1 (new animation)
        if (start_time === -1 || start_time === null) {
            start_time = now;
        }
        
        // Calculate elapsed time and corresponding frame
        var elapsed = now - start_time;
        var progress = Math.min(elapsed / duration_ms, 1.0);
        var frame = Math.floor(progress * (num_frames - 1));
        
        if (frame >= num_frames - 1) {
            // Animation complete - stop at last frame
            return [num_frames - 1, start_time, false, true, num_frames - 1];
        }
        
        return [frame, start_time, true, false, frame];
    }
    """,
    Output('frame-index', 'data'),
    Output('animation-start-time', 'data'),
    Output('is-running', 'data'),
    Output('animation-interval', 'disabled'),
    Output('time-slider', 'value'),
    Input('animation-interval', 'n_intervals'),
    State('animation-start-time', 'data'),
    State('animation-duration-ms', 'data'),
    State('simulation-data', 'data'),
    State('is-running', 'data')
)


# Clientside callback for smooth animation figure update
app.clientside_callback(
    """
    function(frame_idx, frames_data) {
        if (!frames_data || frame_idx === null || frame_idx >= frames_data.length) {
            return window.dash_clientside.no_update;
        }
        
        var frame = frames_data[frame_idx];
        
        return {
            'data': frame.data,
            'layout': {
                'title': frame.layout.title,
                'xaxis': frame.layout.xaxis,
                'yaxis': {'range': [-0.1, 1.5], 'title': 'z [m]'},
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


# Clientside callback for displacement plot marker update
app.clientside_callback(
    """
    function(frame_idx, base_fig_data, sim_data) {
        if (!base_fig_data || !sim_data || frame_idx === null) {
            return window.dash_clientside.no_update;
        }
        
        // Clone the base figure
        var fig = JSON.parse(JSON.stringify(base_fig_data));
        
        // Add marker traces if frame_idx is valid
        if (frame_idx >= 0 && frame_idx < sim_data.time.length) {
            var current_time = sim_data.time[frame_idx];
            var current_z_s = sim_data.z_s[frame_idx];
            var current_z_u = sim_data.z_u[frame_idx];
            
            // Add sprung mass marker
            fig.data.push({
                x: [current_time],
                y: [current_z_s],
                mode: 'markers',
                marker: {color: 'black', size: 12, symbol: 'circle'},
                showlegend: false,
                hoverinfo: 'skip'
            });
            
            // Add unsprung mass marker
            fig.data.push({
                x: [current_time],
                y: [current_z_u],
                mode: 'markers',
                marker: {color: 'black', size: 12, symbol: 'circle'},
                showlegend: false,
                hoverinfo: 'skip'
            });
        }
        
        return fig;
    }
    """,
    Output('displacement-graph', 'figure'),
    Input('frame-index', 'data'),
    State('displacement-base-figure', 'data'),
    State('simulation-data', 'data')
)


@callback(
    Output('displacement-content', 'style', allow_duplicate=True),
    Output('player-controls', 'style', allow_duplicate=True),
    Output('first-run', 'data', allow_duplicate=True),
    Input('is-running', 'data'),
    State('first-run', 'data'),
    prevent_initial_call=True
)
def update_controls_visibility(is_running, is_first_run):
    """Update visibility of controls based on animation state."""
    # During first run animation: hide controls
    if is_first_run and is_running:
        return {'visibility': 'hidden', 'height': '100%'}, {'display': 'none'}, no_update
    # First run just completed: show controls and set first-run to False
    elif is_first_run and not is_running:
        return {'visibility': 'visible', 'height': '100%'}, {'display': 'flex', 'alignItems': 'top', 'padding': '0px', 'marginTop': '0px'}, False
    # Subsequent runs: always show controls
    else:
        return {'visibility': 'visible', 'height': '100%'}, {'display': 'flex', 'alignItems': 'top', 'padding': '0px', 'marginTop': '0px'}, no_update


# Callback for slider scrubbing - only active when paused
@callback(
    Output('frame-index', 'data', allow_duplicate=True),
    Input('time-slider', 'value'),
    State('simulation-data', 'data'),
    State('is-running', 'data'),
    prevent_initial_call=True
)
def on_slider_change(slider_value, sim_data, is_running):
    """Handle slider scrubbing - only update frame when paused."""
    if sim_data is None or slider_value is None:
        return no_update
    
    # Only respond to slider when animation is paused
    # When running, ignore slider changes (they come from the interval sync)
    if is_running:
        return no_update
    
    # Animation is paused - user is scrubbing, update the frame
    return slider_value


# Callback for video speed slider change
@callback(
    Output('animation-duration-ms', 'data', allow_duplicate=True),
    Output('animation-start-time', 'data', allow_duplicate=True),
    Input('video-speed-dropdown', 'value'),
    State('base-duration-ms', 'data'),
    State('frame-index', 'data'),
    State('simulation-data', 'data'),
    State('is-running', 'data'),
    prevent_initial_call=True
)
def on_speed_change(speed_factor, base_duration_ms, frame_idx, sim_data, is_running):
    """Update animation duration when speed selector changes."""
    if base_duration_ms is None or speed_factor is None:
        return no_update, no_update
    
    # Calculate new duration based on speed factor
    new_duration_ms = base_duration_ms / speed_factor
    
    # If animation is running, adjust start_time to maintain current frame position
    if is_running and sim_data is not None:
        num_frames = len(sim_data['time'])
        if num_frames > 1:
            # Calculate current progress and set start_time accordingly
            progress = frame_idx / (num_frames - 1)
            elapsed = progress * new_duration_ms
            import time
            new_start_time = int(time.time() * 1000) - elapsed
            return new_duration_ms, new_start_time
    
    return new_duration_ms, no_update


# Callback for play/pause button
@callback(
    Output('is-running', 'data', allow_duplicate=True),
    Output('animation-interval', 'disabled', allow_duplicate=True),
    Output('play-pause-button', 'children'),
    Output('frame-index', 'data', allow_duplicate=True),
    Output('animation-start-time', 'data', allow_duplicate=True),
    Input('play-pause-button', 'n_clicks'),
    State('is-running', 'data'),
    State('simulation-data', 'data'),
    State('frame-index', 'data'),
    State('animation-duration-ms', 'data'),
    prevent_initial_call=True
)
def toggle_play_pause(n_clicks, is_running, sim_data, frame_idx, duration_ms):
    """Toggle play/pause state."""
    if n_clicks is None or sim_data is None:
        return no_update, no_update, no_update, no_update, no_update
    
    num_frames = len(sim_data['time'])
    
    # If currently not running
    if not is_running:
        # If at end, restart from beginning
        if frame_idx >= num_frames - 1:
            # Restart: reset frame to 0 and set start_time to -1 to initialize
            return True, False, '⏸', 0, -1
        else:
            # Resume from current position: calculate start_time to match current frame
            # We need to set start_time such that elapsed time corresponds to current frame
            progress = frame_idx / (num_frames - 1)
            elapsed = progress * duration_ms
            import time
            start_time = int(time.time() * 1000) - elapsed
            return True, False, '⏸', no_update, start_time
    else:
        # Pause
        return False, True, '▶', no_update, no_update


# Callback to update button when animation completes
@callback(
    Output('play-pause-button', 'children', allow_duplicate=True),
    Input('is-running', 'data'),
    prevent_initial_call=True
)
def update_button_on_animation_end(is_running):
    """Update button text when animation ends."""
    # When animation stops, show play button
    return '▶' if not is_running else '⏸'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(debug=True, host='127.0.0.1', port=port)
