"""Genome representation for a paper airplane.

Each gene is a continuous (or small integer) parameter that a real paper
airplane fold actually controls. There's no "correct" paper airplane
encoded here -- the genome just exposes the handful of fold choices that
matter aerodynamically, and evolution is left to discover which
combinations work for whichever objectives are switched on.

Fairness / buildability
------------------------
Every genome is built from the *same single sheet* of standard printer
paper (A4). That's what keeps evolution honest:

- **Fair**: no design can carry more material (and therefore more lift
  surface or more mass) than any other -- they all share one fixed sheet
  area and one fixed sheet mass.
- **No impossible folds**: per-gene bounds keep individual dimensions
  within what a sheet that size can actually produce (a wingspan can't
  exceed the sheet's diagonal, a fuselage can't exceed its long edge, a
  nose can't be folded more times than paper realistically allows), and
  ``Genome.repaired()`` additionally scales down paper-consuming
  dimensions together whenever a combination would need more flat area
  than one sheet provides.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, fields

# A4 printer paper. Change these if you'd rather evolve planes folded from
# US Letter or any other fixed sheet size.
PAPER_WIDTH_M = 0.210
PAPER_HEIGHT_M = 0.297
PAPER_DIAGONAL_M = math.hypot(PAPER_WIDTH_M, PAPER_HEIGHT_M)
PAPER_AREA_M2 = PAPER_WIDTH_M * PAPER_HEIGHT_M
USABLE_AREA_M2 = PAPER_AREA_M2 * 0.85  # ~15% lost to overlaps/trim when folding
PAPER_GRAMMAGE_KGM2 = 0.080            # standard 80 gsm printer paper
OVERLAP_FACTOR = 1.3                   # folded structure is multiply-layered

# name -> (low, high). Order here defines crossover/mutation iteration order.
PARAM_BOUNDS: dict[str, tuple[float, float]] = {
    "wingspan_m": (0.08, 0.32),          # tip-to-tip span (a diagonal fold can exceed one paper edge)
    "wing_chord_m": (0.03, 0.14),        # wing depth (front to back)
    "fuselage_length_m": (0.12, PAPER_HEIGHT_M),  # body spine, can't exceed the sheet's long edge
    "fuselage_width_m": (0.015, 0.05),   # body spine width
    "nose_weight": (0.0, 1.0),           # fraction of the fold concentrated at the nose (shifts CG; the sheet's total mass is fixed, see mass_kg())
    "dihedral_deg": (0.0, 30.0),         # wingtip fold-up angle (roll stability)
    "nose_angle_deg": (10.0, 60.0),      # nose taper: low = sharp dart, high = blunt
    "trim_deg": (-5.0, 15.0),            # trailing-edge flap bend (sets cruise AoA)
    "fold_layers": (1.0, 4.0),           # nose fold count -- paper can't realistically be folded more than this
    "wing_sweep_deg": (0.0, 45.0),       # wing sweep back from the fuselage
    "tail_fin_height_m": (0.0, 0.04),    # vertical tail fin, for yaw stability
}


@dataclass
class Genome:
    wingspan_m: float
    wing_chord_m: float
    fuselage_length_m: float
    fuselage_width_m: float
    nose_weight: float
    dihedral_deg: float
    nose_angle_deg: float
    trim_deg: float
    fold_layers: float
    wing_sweep_deg: float
    tail_fin_height_m: float

    def clipped(self) -> "Genome":
        values = {}
        for f in fields(self):
            lo, hi = PARAM_BOUNDS[f.name]
            values[f.name] = min(hi, max(lo, getattr(self, f.name)))
        return Genome(**values)

    def copy(self) -> "Genome":
        return Genome(**{f.name: getattr(self, f.name) for f in fields(self)})

    def paper_area_m2(self) -> float:
        """Flat paper area this design's wings + fuselage + tail occupy."""
        wing_area = self.wingspan_m * self.wing_chord_m
        fuselage_area = self.fuselage_length_m * self.fuselage_width_m
        tail_area = 0.5 * self.tail_fin_height_m * (self.fuselage_width_m * 2)
        return wing_area + fuselage_area + tail_area

    def mass_kg(self) -> float:
        """Folding doesn't discard paper -- whatever isn't wing, fuselage
        or tail is folded up inside the structure rather than thrown away.
        So every design carries the same, fixed sheet mass; no genome can
        add or shed weight from nowhere.
        """
        return PAPER_AREA_M2 * PAPER_GRAMMAGE_KGM2 * OVERLAP_FACTOR

    def is_buildable(self) -> bool:
        return self.paper_area_m2() <= USABLE_AREA_M2 + 1e-9

    def repaired(self) -> "Genome":
        """Scale paper-consuming dimensions down until the design fits on
        one sheet, then re-clip each gene to its own bounds. Wings are
        trimmed last/most since they have the most slack in their bounds,
        which guarantees this converges (the fuselage/tail minimums alone
        are always well under the sheet budget).
        """
        genome = self.clipped()
        for _ in range(3):
            area = genome.paper_area_m2()
            if area <= USABLE_AREA_M2:
                return genome
            scale = math.sqrt(USABLE_AREA_M2 / area)
            genome.wingspan_m *= scale
            genome.wing_chord_m *= scale
            genome.fuselage_length_m *= scale
            genome.fuselage_width_m *= scale
            genome.tail_fin_height_m *= scale
            genome = genome.clipped()

        span_lo, _ = PARAM_BOUNDS["wingspan_m"]
        chord_lo, _ = PARAM_BOUNDS["wing_chord_m"]
        while genome.paper_area_m2() > USABLE_AREA_M2 and genome.wingspan_m > span_lo:
            genome.wingspan_m = max(span_lo, genome.wingspan_m * 0.95)
            genome.wing_chord_m = max(chord_lo, genome.wing_chord_m * 0.95)
        return genome


def random_genome(rng: random.Random) -> Genome:
    values = {name: rng.uniform(lo, hi) for name, (lo, hi) in PARAM_BOUNDS.items()}
    return Genome(**values).repaired()


def crossover(a: Genome, b: Genome, rng: random.Random) -> Genome:
    """Uniform crossover: each gene independently comes from a or b."""
    values = {}
    for name in PARAM_BOUNDS:
        values[name] = getattr(a, name) if rng.random() < 0.5 else getattr(b, name)
    return Genome(**values).repaired()


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

    return child.repaired()
