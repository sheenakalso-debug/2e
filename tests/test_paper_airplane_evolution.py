import random

from paper_airplane_evolution.design import describe
from paper_airplane_evolution.evolve import Objectives, evolve, fitness
from paper_airplane_evolution.genome import (
    PARAM_BOUNDS,
    crossover,
    mutate,
    random_genome,
)
from paper_airplane_evolution.simulator import simulate_flight


def test_random_genome_within_bounds():
    rng = random.Random(0)
    for _ in range(50):
        genome = random_genome(rng)
        for name, (lo, hi) in PARAM_BOUNDS.items():
            assert lo <= getattr(genome, name) <= hi


def test_mutate_stays_within_bounds():
    rng = random.Random(1)
    genome = random_genome(rng)
    for _ in range(50):
        genome = mutate(genome, rng, rate=0.5)
        for name, (lo, hi) in PARAM_BOUNDS.items():
            assert lo <= getattr(genome, name) <= hi


def test_crossover_gene_comes_from_a_parent():
    rng = random.Random(2)
    a = random_genome(rng)
    b = random_genome(rng)
    child = crossover(a, b, rng)
    for name in PARAM_BOUNDS:
        assert getattr(child, name) in (getattr(a, name), getattr(b, name))


def test_simulate_flight_returns_sane_result():
    rng = random.Random(3)
    genome = random_genome(rng)
    result = simulate_flight(genome)
    assert result.distance_m >= 0
    assert result.time_aloft_s > 0
    assert result.top_speed_ms > 0
    assert len(result.trajectory) >= 2


def test_objectives_toggle_changes_fitness():
    rng = random.Random(4)
    genome = random_genome(rng)
    result = simulate_flight(genome)

    distance_only = fitness(result, Objectives(distance=True, time=False, speed=False))
    time_only = fitness(result, Objectives(distance=False, time=True, speed=False))
    all_off = fitness(result, Objectives(distance=False, time=False, speed=False))

    assert all_off == 0.0
    assert distance_only != time_only or result.distance_m == result.time_aloft_s


def test_evolution_improves_or_matches_first_generation():
    history = evolve(
        Objectives(distance=True, time=True, speed=True),
        population_size=20,
        generations=10,
        seed=42,
    )
    assert len(history) == 10
    # Elitism guarantees fitness never regresses generation to generation.
    for prev, cur in zip(history, history[1:]):
        assert cur.best_fitness >= prev.best_fitness - 1e-9
    assert history[-1].best_fitness >= history[0].best_fitness


def test_describe_produces_readable_instructions():
    rng = random.Random(5)
    genome = random_genome(rng)
    text = describe(genome)
    assert "Wings" in text
    assert "Nose" in text
    assert "Trim" in text
