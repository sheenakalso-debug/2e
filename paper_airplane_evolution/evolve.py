"""Genetic algorithm that evolves paper airplane genomes against whichever
objectives (distance, time aloft, speed) are switched on.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .genome import Genome, crossover, mutate, random_genome
from .simulator import FlightResult, simulate_flight

# Rough normalizers so distance (meters), time (seconds) and speed (m/s)
# contribute comparably when several objectives are switched on together.
_NORMALIZERS = {"distance": 10.0, "time": 2.0, "speed": 8.0}


@dataclass
class Objectives:
    distance: bool = True
    time: bool = True
    speed: bool = True

    def active(self) -> list[str]:
        return [name for name in ("distance", "time", "speed") if getattr(self, name)]


def fitness(result: FlightResult, objectives: Objectives) -> float:
    active = objectives.active()
    if not active:
        return 0.0
    total = 0.0
    if objectives.distance:
        total += result.distance_m / _NORMALIZERS["distance"]
    if objectives.time:
        total += result.time_aloft_s / _NORMALIZERS["time"]
    if objectives.speed:
        total += result.top_speed_ms / _NORMALIZERS["speed"]
    return total / len(active)


@dataclass
class GenerationStats:
    generation: int
    best_fitness: float
    avg_fitness: float
    best_genome: Genome
    best_result: FlightResult


def _tournament_select(
    pop: list[Genome], scores: list[float], rng: random.Random, k: int = 3
) -> Genome:
    contenders = rng.sample(range(len(pop)), k)
    winner = max(contenders, key=lambda i: scores[i])
    return pop[winner]


def evolve(
    objectives: Objectives,
    population_size: int = 40,
    generations: int = 25,
    mutation_rate: float = 0.15,
    elite_count: int = 2,
    seed: int | None = None,
    on_generation=None,
) -> list[GenerationStats]:
    rng = random.Random(seed)
    population = [random_genome(rng) for _ in range(population_size)]
    history: list[GenerationStats] = []

    for gen in range(generations):
        results = [simulate_flight(g) for g in population]
        scores = [fitness(r, objectives) for r in results]

        best_idx = max(range(len(population)), key=lambda i: scores[i])
        stats = GenerationStats(
            generation=gen,
            best_fitness=scores[best_idx],
            avg_fitness=sum(scores) / len(scores),
            best_genome=population[best_idx].copy(),
            best_result=results[best_idx],
        )
        history.append(stats)
        if on_generation is not None:
            on_generation(stats)

        ranked = sorted(range(len(population)), key=lambda i: scores[i], reverse=True)
        elites = [population[i].copy() for i in ranked[:elite_count]]

        next_population = list(elites)
        while len(next_population) < population_size:
            parent_a = _tournament_select(population, scores, rng)
            parent_b = _tournament_select(population, scores, rng)
            child = crossover(parent_a, parent_b, rng)
            child = mutate(child, rng, rate=mutation_rate)
            next_population.append(child)

        population = next_population

    return history
