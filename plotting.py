"""
Plotting Module for Quarter Car Simulation

Converts MATLAB plotSpring.m and plotDamper.m to Python/Plotly.
Creates animation frames and displacement plots.
"""

import numpy as np
import plotly.graph_objects as go
from typing import List, Tuple
from simulation import SimulationResult


def get_spring_color(Kt: float) -> str:
    """
    Get spring color based on tire stiffness.
    Soft (low Kt) = red, Stiff (high Kt) = blue.
    
    Args:
        Kt: Tire stiffness in N/m.
        
    Returns:
        RGB color string.
    """
    kt_norm = min(max((Kt - 5e4) / (5e5 - 5e4), 0), 1)
    r = int((1 - kt_norm) * 255)
    b = int(kt_norm * 255)
    return f'rgb({r}, 0, {b})'


def create_spring_trace(
    x_center: float,
    z_bottom: float,
    z_top: float,
    L0: float,
    color: str = 'black',
    width: float = 0.1
) -> Tuple[List[float], List[float]]:
    """
    Create spring (zigzag) coordinates.
    
    Args:
        x_center: X position of spring center.
        z_bottom: Bottom z coordinate.
        z_top: Top z coordinate.
        L0: Natural length of spring.
        color: Spring color.
        width: Spring width.
        
    Returns:
        Tuple of (x_coords, z_coords) for the spring.
    """
    rod_pct = 0.15
    spring_pct = 0.5
    
    L = (z_top - z_bottom) - 2 * rod_pct * L0
    
    x_coords = [
        x_center, x_center,
        x_center + width, x_center - width,
        x_center + width, x_center - width,
        x_center, x_center
    ]
    
    z_coords = [
        z_bottom,
        z_bottom + rod_pct * L0,
        z_bottom + rod_pct * L0,
        z_bottom + rod_pct * L0 + spring_pct * L,
        z_bottom + rod_pct * L0 + spring_pct * L,
        z_bottom + rod_pct * L0 + 2 * spring_pct * L,
        z_bottom + rod_pct * L0 + 2 * spring_pct * L,
        z_bottom + 2 * rod_pct * L0 + 2 * spring_pct * L
    ]
    
    return x_coords, z_coords


def create_damper_traces(
    x_center: float,
    z_bottom: float,
    z_top: float,
    L0: float
) -> List[Tuple[List[float], List[float]]]:
    """
    Create damper component coordinates.
    
    Args:
        x_center: X position of damper center.
        z_bottom: Bottom z coordinate (unsprung mass top).
        z_top: Top z coordinate (sprung mass bottom).
        L0: Natural length.
        
    Returns:
        List of (x_coords, z_coords) tuples for each damper component.
    """
    rod_lower_pct = 0.1
    rod_upper_pct = 0.4
    cyl_pct = 0.4
    w = 0.05
    
    traces = []
    
    # Lower rod
    rod1_x = [x_center, x_center]
    rod1_z = [z_bottom, z_bottom + rod_lower_pct * L0]
    traces.append((rod1_x, rod1_z))
    
    # Cylinder
    cyl_x = [x_center - w, x_center - w, x_center + w, x_center + w]
    cyl_z = [
        z_bottom + rod_lower_pct * L0 + cyl_pct * L0,
        z_bottom + rod_lower_pct * L0,
        z_bottom + rod_lower_pct * L0,
        z_bottom + rod_lower_pct * L0 + cyl_pct * L0
    ]
    traces.append((cyl_x, cyl_z))
    
    # Upper rod
    rod2_x = [x_center, x_center]
    rod2_z = [z_top, z_top - rod_upper_pct * L0]
    traces.append((rod2_x, rod2_z))
    
    # Piston
    piston_x = [x_center - 0.8 * w, x_center + 0.8 * w]
    piston_z = [z_top - rod_upper_pct * L0, z_top - rod_upper_pct * L0]
    traces.append((piston_x, piston_z))
    
    return traces


def create_animation_frame(result: SimulationResult, frame_idx: int) -> go.Figure:
    """
    Create a Plotly figure for a single animation frame.
    
    Args:
        result: Simulation result data.
        frame_idx: Index of the current frame.
        
    Returns:
        Plotly Figure object.
    """
    i = frame_idx
    x_inst = result.lon[i]
    l_win = 2  # Window length
    
    fig = go.Figure()
    
    # Road profile - OPTIMIZATION: Only render visible section
    # Window is x_inst +/- l_win/2. Add buffer.
    x_min, x_max = x_inst - l_win, x_inst + l_win
    
    # Filter points within window
    road_x_extended = np.concatenate([[-10], result.road_x, [100]]) # Add bounds
    road_z_extended = np.concatenate([[0], result.road_z, [0]])
    
    mask = (road_x_extended >= x_min) & (road_x_extended <= x_max)
    
    # Add one point on each side to ensure continuity
    if np.any(mask):
        idx_first = np.argmax(mask)
        idx_last = len(mask) - 1 - np.argmax(mask[::-1])
        idx_start = max(0, idx_first - 1)
        idx_end = min(len(road_x_extended), idx_last + 2)
        
        road_x_view = road_x_extended[idx_start:idx_end]
        road_z_view = road_z_extended[idx_start:idx_end]
    else:
        # Fallback if out of bounds (shouldn't happen with padding)
        road_x_view = [x_min, x_max]
        road_z_view = [0, 0]

    fig.add_trace(go.Scatter(
        x=road_x_view,
        y=road_z_view,
        mode='lines',
        line=dict(color='black', width=3),
        name='Road',
        showlegend=False
    ))
    
    # Sprung mass (purple box)
    sprung_x = [
        x_inst - result.a/2, x_inst + result.a/2,
        x_inst + result.a/2, x_inst - result.a/2,
        x_inst - result.a/2
    ]
    sprung_z = [
        result.z_s[i], result.z_s[i],
        result.z_s[i] + result.h_s, result.z_s[i] + result.h_s,
        result.z_s[i]
    ]
    fig.add_trace(go.Scatter(
        x=sprung_x,
        y=sprung_z,
        mode='lines',
        fill='toself',
        fillcolor='rgb(148, 103, 189)',
        line=dict(color='black', width=2),
        name='Sprung mass',
        showlegend=False
    ))
    
    # Unsprung mass (cyan box)
    unsprung_x = [
        x_inst - result.a/2, x_inst + result.a/2,
        x_inst + result.a/2, x_inst - result.a/2,
        x_inst - result.a/2
    ]
    unsprung_z = [
        result.z_u[i], result.z_u[i],
        result.z_u[i] + result.h_u, result.z_u[i] + result.h_u,
        result.z_u[i]
    ]
    fig.add_trace(go.Scatter(
        x=unsprung_x,
        y=unsprung_z,
        mode='lines',
        fill='toself',
        fillcolor='rgb(44, 160, 196)',
        line=dict(color='black', width=2),
        name='Unsprung mass',
        showlegend=False
    ))
    
    # Tire spring (between road and unsprung mass)
    tire_spring_color = get_spring_color(result.Kt)
    tire_spring_x, tire_spring_z = create_spring_trace(
        x_center=x_inst,
        z_bottom=result.u[i],
        z_top=result.z_u[i],
        L0=result.L0_u,
        color=tire_spring_color
    )
    fig.add_trace(go.Scatter(
        x=tire_spring_x,
        y=tire_spring_z,
        mode='lines',
        line=dict(color=tire_spring_color, width=3),
        name='Tire spring',
        showlegend=False
    ))
    
    # Suspension spring (between unsprung and sprung mass)
    susp_spring_x, susp_spring_z = create_spring_trace(
        x_center=x_inst - 0.2,
        z_bottom=result.z_u[i] + result.h_u,
        z_top=result.z_s[i],
        L0=result.L0_s
    )
    fig.add_trace(go.Scatter(
        x=susp_spring_x,
        y=susp_spring_z,
        mode='lines',
        line=dict(color='black', width=3),
        name='Suspension spring',
        showlegend=False
    ))
    
    # Damper
    damper_traces = create_damper_traces(
        x_center=x_inst + 0.2,
        z_bottom=result.z_u[i] + result.h_u,
        z_top=result.z_s[i],
        L0=result.L0_s
    )
    for dx, dz in damper_traces:
        fig.add_trace(go.Scatter(
            x=dx,
            y=dz,
            mode='lines',
            line=dict(color='black', width=3),
            showlegend=False
        ))
    
    # Contact point
    fig.add_trace(go.Scatter(
        x=[x_inst],
        y=[result.u[i]],
        mode='markers',
        marker=dict(color='black', size=10),
        name='Contact point',
        showlegend=False
    ))
    
    # Layout - use uirevision to prevent full redraws
    fig.update_layout(
        title=f't = {result.time[i]:.2f} s',
        xaxis=dict(
            range=[x_inst - l_win/2, x_inst + l_win/2],
            title='x [m]',
            scaleanchor='y',
            scaleratio=1
        ),
        yaxis=dict(
            range=[-0.1, -0.1 + l_win],
            title='z [m]'
        ),
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='white',
        height=500,
        uirevision='constant'  # Preserves UI state between updates
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig


def create_displacement_plot(result: SimulationResult, current_time_idx: int | None = None) -> go.Figure:
    """
    Create the displacement vs time plot.
    
    Args:
        result: Simulation result data.
        current_time_idx: Index of current time to show marker (optional).
        
    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=result.time,
        y=result.z_s,
        mode='lines',
        name='Sprung mass',
        line=dict(width=2, color='rgb(148, 103, 189)')
    ))
    
    fig.add_trace(go.Scatter(
        x=result.time,
        y=result.z_u,
        mode='lines',
        name='Unsprung mass',
        line=dict(width=2, color='rgb(44, 160, 196)')
    ))
    
    # Add current time marker if index provided
    if current_time_idx is not None and 0 <= current_time_idx < len(result.time):
        current_time = result.time[current_time_idx]
        current_z_s = result.z_s[current_time_idx]
        current_z_u = result.z_u[current_time_idx]
        
        # Marker for sprung mass
        fig.add_trace(go.Scatter(
            x=[current_time],
            y=[current_z_s],
            mode='markers',
            marker=dict(color='black', size=12, symbol='circle'),
            name='Current (sprung)',
            showlegend=False
        ))
        
        # Marker for unsprung mass
        fig.add_trace(go.Scatter(
            x=[current_time],
            y=[current_z_u],
            mode='markers',
            marker=dict(color='black', size=12, symbol='circle'),
            name='Current (unsprung)',
            showlegend=False
        ))
    
    fig.update_layout(
        title='Vertical Displacement',
        xaxis_title='Time [s]',
        yaxis_title='z [m]',
        legend=dict(x=0.7, y=0.5),
        margin=dict(l=50, r=50, t=50, b=50),
        plot_bgcolor='white',
        height=500,
        uirevision='displacement'  # Preserve zoom/pan state
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig
