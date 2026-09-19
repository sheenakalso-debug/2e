"""Genome representation for a paper airplane.

Each gene is a continuous (or small integer) parameter that a real paper
airplane fold actually controls. There's no "correct" paper airplane
encoded here -- the genome just exposes the handful of fold choices that
matter aerodynamically, and evolution is left to discover which
combinations work for whichever objectives are switched on.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, fields

# name -> (low, high). Order here defines crossover/mutation iteration order.
PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "wingspan_m": (0.08, 0.28),     # tip-to-tip wing span
    "wing_chord_m": (0.03, 0.12),   # wing depth (front to back)
    "nose_weight": (0.0, 1.0),      # fraction of extra tape/folds at the nose
    "dihedral_deg": (0.0, 30.0),    # wingtip fold-up angle (roll stability)
    "nose_angle_deg": (10.0, 60.0), # nose taper: low = sharp dart, high = blunt
    "trim_deg": (-5.0, 15.0),       # trailing-edge flap bend (sets cruise AoA)
    "fold_layers": (1.0, 6.0),      # how many times the nose is folded over
}


@dataclass
class Genome:
    wingspan_m: float
    wing_chord_m: float
    nose_weight: float
    dihedral_deg: float
    nose_angle_deg: float
    trim_deg: float
    fold_layers: float

    def clipped(self) -> "Genome":
        values = {}
        for f in fields(self):
            lo, hi = PARAM_BOUNDS[f.name]
            values[f.name] = min(hi, max(lo, getattr(self, f.name)))
        return Genome(**values)

    def copy(self) -> "Genome":
        return Genome(**{f.name: getattr(self, f.name) for f in fields(self)})


def random_genome(rng: random.Random) -> Genome:
    values = {name: rng.uniform(lo, hi) for name, (lo, hi) in PARAM_BOUNDS.items()}
    return Genome(**values)


def crossover(a: Genome, b: Genome, rng: random.Random) -> Genome:
    """Uniform crossover: each gene independently comes from a or b."""
    values = {}
    for name in PARAM_BOUNDS:
        values[name] = getattr(a, name) if rng.random() < 0.5 else getattr(b, name)
    return Genome(**values)


def mutate(genome: Genome, rng: random.Random, rate: float = 0.15) -> Genome:
    """Gaussian jitter on every gene, plus an occasional full re-roll of a
    single gene so the population doesn't converge too fast.
    """
    child = genome.copy()
    for name, (lo, hi) in PARAM_BOUNDS.items():
        span = hi - lo
        current = getattr(child, name)
        current += rng.gauss(0, rate * span)
        setattr(child, name, current)

    if rng.random() < 0.1:
        reroll = rng.choice(list(PARAM_BOUNDS))
        lo, hi = PARAM_BOUNDS[reroll]
        setattr(child, reroll, rng.uniform(lo, hi))

    return child.clipped()
