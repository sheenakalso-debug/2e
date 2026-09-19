"""A deliberately simple flight-physics simulator.

This is not a CFD tool -- it's a toy glide-dynamics model that turns fold
parameters into plausible relative differences (bigger wings glide longer,
a sharp heavy dart goes fast but drops quickly, too much dihedral drags,
an untrimmed plane stalls or dives) so a genetic algorithm has a real
landscape to climb, in real time, without needing a wind tunnel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .genome import Genome

G = 9.81           # m/s^2
RHO = 1.225        # kg/m^3, sea-level air density
DT = 0.01          # s, integration step
MAX_TIME = 30.0    # s, safety cutoff
LAUNCH_HEIGHT_M = 1.5
LAUNCH_SPEED_MS = 7.0
LAUNCH_ANGLE_DEG = 15.0

BASE_MASS_KG = 0.0025          # bare folded sheet of paper
NOSE_WEIGHT_MASS_KG = 0.004    # extra tape/folds at full nose_weight=1.0
LAYER_MASS_KG = 0.0006         # per extra nose fold layer

CL_MAX = 1.2                   # crude stall limit


@dataclass
class FlightResult:
    distance_m: float
    time_aloft_s: float
    top_speed_ms: float
    trajectory: list[tuple[float, float]]  # (x, y) samples for plotting


def _aero_coeffs(genome: Genome) -> tuple[float, float, float, float]:
    """Return (S, aspect_ratio, CL_alpha_per_rad, CD0)."""
    span = genome.wingspan_m
    chord = genome.wing_chord_m
    S = max(span * chord, 1e-4)
    aspect_ratio = (span * span) / S

    cl_alpha = 2 * math.pi * aspect_ratio / (aspect_ratio + 2)

    blunt_drag = (genome.nose_angle_deg / 60.0) * 0.04
    layer_drag = genome.fold_layers * 0.002
    dihedral_drag = (genome.dihedral_deg / 30.0) * 0.01
    cd0 = 0.02 + blunt_drag + layer_drag + dihedral_drag

    return S, aspect_ratio, cl_alpha, cd0


def _mass_kg(genome: Genome) -> float:
    return (
        BASE_MASS_KG
        + genome.nose_weight * NOSE_WEIGHT_MASS_KG
        + genome.fold_layers * LAYER_MASS_KG
    )


def simulate_flight(genome: Genome) -> FlightResult:
    S, aspect_ratio, cl_alpha, cd0 = _aero_coeffs(genome)
    mass = _mass_kg(genome)
    oswald_e = 0.7

    # Nose-heavy planes pitch down, trimming out at a lower angle of attack.
    alpha_deg = genome.trim_deg - genome.nose_weight * 10.0
    alpha = math.radians(alpha_deg)

    cl0 = 0.05
    cl = cl0 + cl_alpha * alpha
    stall_excess = max(0.0, abs(cl) - CL_MAX)
    cl = max(-CL_MAX, min(CL_MAX, cl))
    cd_induced = (cl * cl) / (math.pi * oswald_e * max(aspect_ratio, 0.1))
    cd = cd0 + cd_induced + 0.3 * stall_excess

    theta0 = math.radians(LAUNCH_ANGLE_DEG)
    vx = LAUNCH_SPEED_MS * math.cos(theta0)
    vy = LAUNCH_SPEED_MS * math.sin(theta0)
    x, y = 0.0, LAUNCH_HEIGHT_M
    t = 0.0
    top_speed = LAUNCH_SPEED_MS
    trajectory: list[tuple[float, float]] = [(x, y)]

    prev_x, prev_y, prev_t = x, y, t

    while t < MAX_TIME and y > 0:
        v = math.hypot(vx, vy)
        if v < 1e-6:
            break
        lift = 0.5 * RHO * v * v * S * cl
        drag = 0.5 * RHO * v * v * S * cd

        ux, uy = vx / v, vy / v          # unit vector along velocity
        lx, ly = -uy, ux                 # perpendicular ("up" for forward flight)

        fx = -drag * ux + lift * lx
        fy = -drag * uy + lift * ly - mass * G

        ax, ay = fx / mass, fy / mass

        prev_x, prev_y, prev_t = x, y, t
        vx += ax * DT
        vy += ay * DT
        x += vx * DT
        y += vy * DT
        t += DT

        top_speed = max(top_speed, v)
        if len(trajectory) < 3000:
            trajectory.append((x, y))

    if y <= 0 and prev_y > 0:
        # Linear interpolation back to y == 0 for a cleaner landing point.
        frac = prev_y / (prev_y - y) if prev_y != y else 0.0
        x = prev_x + frac * (x - prev_x)
        t = prev_t + frac * (t - prev_t)

    return FlightResult(
        distance_m=max(0.0, x),
        time_aloft_s=max(0.0, t),
        top_speed_ms=top_speed,
        trajectory=trajectory,
    )
