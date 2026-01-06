"""
Quarter Car Simulation Module

Converts the MATLAB runQuarterCarSim.m physics simulation to Python.
Uses scipy.signal for state-space modeling and linear simulation.
"""

import numpy as np
from scipy.signal import StateSpace, lsim
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SimulationParams:
    """Parameters for the quarter car simulation."""
    M: float = 1500.0    # Sprung mass (kg)
    m: float = 150.0     # Unsprung mass (kg)
    Ks: float = 48000.0  # Suspension stiffness (N/m)
    Cs: float = 1000.0   # Damping coefficient (Ns/m)
    Kt: float = 200000.0 # Tire stiffness (N/m)
    vel: float = 2.0     # Vehicle speed (m/s)


@dataclass
class SimulationResult:
    """Results from the quarter car simulation."""
    time: np.ndarray       # Time vector
    z_s: np.ndarray        # Sprung mass displacement
    z_u: np.ndarray        # Unsprung mass displacement
    u: np.ndarray          # Road input
    lon: np.ndarray        # Longitudinal position
    road_x: np.ndarray     # Road profile x coordinates
    road_z: np.ndarray     # Road profile z coordinates
    L0_s: float            # Suspension spring natural length
    L0_u: float            # Tire spring natural length
    h_s: float             # Sprung mass height
    h_u: float             # Unsprung mass height
    a: float               # Mass width
    Kt: float              # Tire stiffness (for spring color)


def generate_road_profile() -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate the road profile with a bump.
    
    Returns:
        Tuple of (x_coordinates, z_coordinates) for the road.
    """
    # Flat section before bump
    x1 = np.arange(0, 1.2, 0.1)
    z1 = np.zeros_like(x1)
    
    # Bump (semicircle)
    R = 0.10  # Bump radius
    th = np.linspace(0, np.pi, 50)
    x2 = -R * np.cos(th) + 1.1 + R
    z2 = R * np.sin(th)
    
    # Flat section after bump
    x3 = np.arange(1.1 + 2*R, 1.1 + 2*R + 5.1, 0.1)
    z3 = np.zeros_like(x3)
    
    # Concatenate all sections
    Xr = np.concatenate([x1, x2[1:], x3[1:]])
    Zr = np.concatenate([z1, z2[1:], z3[1:]])
    
    return Xr, Zr


def run_simulation(params: SimulationParams) -> SimulationResult:
    """
    Run the quarter car simulation.
    
    Args:
        params: Simulation parameters.
        
    Returns:
        SimulationResult containing all time series data.
    """
    # Extract parameters
    M = params.M
    m = params.m
    Ks = params.Ks
    Cs = params.Cs
    Kt = params.Kt
    vel = params.vel
    
    # Geometry constants
    L0_s = 0.4  # Suspension spring natural length
    L0_u = 0.3  # Tire spring natural length
    h_s = 0.2   # Sprung mass height
    h_u = 0.1   # Unsprung mass height
    a = 0.8     # Mass width
    
    # Simulation Extent
    xF = 6.0  # Fixed distance to cover in meters
    
    # Time parameters
    playback_speed = .5  # Playback speed multiplier (0.5 = 2x slow-mo)
    tF = xF / vel        # Time required to cover xF at given speed
    fR = 30 / playback_speed  # Target 30 fps for smooth animation
    num_frames = int(tF * fR)
    time = np.linspace(0, tF, num_frames)
    
    # Generate road profile
    road_x, road_z = generate_road_profile()
    
    # State-space model
    # State: [z_u, z_u_dot, z_s, z_s_dot]
    A = np.array([
        [0, 1, 0, 0],
        [-(Ks + Kt) / m, -Cs / m, Ks / m, Cs / m],
        [0, 0, 0, 1],
        [Ks / M, Cs / M, -Ks / M, -Cs / M]
    ])
    B = np.array([[0], [Kt / m], [0], [0]])
    C = np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0]
    ])
    D = np.array([[0], [0]])
    
    # Create state-space system
    sys = StateSpace(A, B, C, D)
    
    # Longitudinal position
    lon = vel * time
    
    # Road input (interpolate road profile at vehicle position)
    u = np.interp(lon, road_x, road_z)
    
    # Run simulation
    t_out, y_out, x_out = lsim(sys, u, time)
    
    # Extract outputs with offset for natural lengths
    z_u = y_out[:, 0] + L0_u
    z_s = y_out[:, 1] + L0_u + L0_s
    
    return SimulationResult(
        time=time,
        z_s=z_s,
        z_u=z_u,
        u=u,
        lon=lon,
        road_x=road_x,
        road_z=road_z,
        L0_s=L0_s,
        L0_u=L0_u,
        h_s=h_s,
        h_u=h_u,
        a=a,
        Kt=Kt
    )
