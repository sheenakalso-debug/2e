from __future__ import annotations

import argparse
import sys

from .design import describe
from .evolve import GenerationStats, Objectives, evolve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paper_airplane_evolution",
        description=(
            "Evolve paper airplane designs against a simple flight simulator. "
            "Switch objectives on/off with --distance/--time/--speed; if you "
            "pass none of them, all three are used together."
        ),
    )
    parser.add_argument("--distance", action="store_true", help="optimize for glide distance")
    parser.add_argument("--time", action="store_true", help="optimize for time aloft")
    parser.add_argument("--speed", action="store_true", help="optimize for top speed")
    parser.add_argument("--population", type=int, default=40, help="population size (default 40)")
    parser.add_argument("--generations", type=int, default=25, help="number of generations (default 25)")
    parser.add_argument("--mutation-rate", type=float, default=0.15, help="mutation strength (default 0.15)")
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducibility")
    parser.add_argument("--quiet", action="store_true", help="only print the final result")
    parser.add_argument(
        "--plot",
        action="store_true",
        help="save fitness-over-generations and best-trajectory plots (requires matplotlib)",
    )
    return parser


def _maybe_plot(history: list[GenerationStats]) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("(--plot requested but matplotlib isn't installed; skipping)", file=sys.stderr)
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    gens = [s.generation for s in history]
    ax1.plot(gens, [s.best_fitness for s in history], label="best")
    ax1.plot(gens, [s.avg_fitness for s in history], label="average")
    ax1.set_xlabel("generation")
    ax1.set_ylabel("fitness")
    ax1.set_title("Fitness over generations")
    ax1.legend()

    best = history[-1].best_result
    xs = [p[0] for p in best.trajectory]
    ys = [p[1] for p in best.trajectory]
    ax2.plot(xs, ys)
    ax2.set_xlabel("distance (m)")
    ax2.set_ylabel("height (m)")
    ax2.set_title("Best flight trajectory")

    fig.tight_layout()
    fig.savefig("paper_airplane_evolution_results.png", dpi=150)
    print("Saved plot to paper_airplane_evolution_results.png")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not (args.distance or args.time or args.speed):
        objectives = Objectives(distance=True, time=True, speed=True)
        print("No objective flags given; optimizing distance + time + speed together.\n")
    else:
        objectives = Objectives(distance=args.distance, time=args.time, speed=args.speed)

    active = ", ".join(objectives.active())
    print(f"Evolving paper airplanes for: {active}")
    print(f"population={args.population} generations={args.generations} seed={args.seed}\n")

    def on_generation(stats: GenerationStats) -> None:
        if args.quiet:
            return
        r = stats.best_result
        print(
            f"gen {stats.generation:3d} | best={stats.best_fitness:6.3f} "
            f"avg={stats.avg_fitness:6.3f} | "
            f"dist={r.distance_m:5.2f}m time={r.time_aloft_s:5.2f}s "
            f"top_speed={r.top_speed_ms:5.2f}m/s"
        )

    history = evolve(
        objectives,
        population_size=args.population,
        generations=args.generations,
        mutation_rate=args.mutation_rate,
        seed=args.seed,
        on_generation=on_generation,
    )

    best = history[-1]
    r = best.best_result
    print("\n=== Best design ===")
    print(
        f"distance={r.distance_m:.2f} m  time_aloft={r.time_aloft_s:.2f} s  "
        f"top_speed={r.top_speed_ms:.2f} m/s  fitness={best.best_fitness:.3f}"
    )
    print("\nHow to fold it:")
    print(describe(best.best_genome))

    if args.plot:
        _maybe_plot(history)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
