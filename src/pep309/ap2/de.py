from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

from pep309.objectives import rastrigin

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class DEConfig:
    population_size: int = 100
    dimensions: int = 100
    generations: int = 300
    lower_bound: float = -5.12
    upper_bound: float = 5.12
    mutation_weight: float = 0.5
    crossover_rate: float = 0.9

    def __post_init__(self) -> None:
        if self.population_size < 4:
            raise ValueError("population_size deve ser pelo menos 4")
        if self.dimensions < 1:
            raise ValueError("dimensions deve ser positivo")
        if self.generations < 0:
            raise ValueError("generations nao pode ser negativo")
        if self.lower_bound >= self.upper_bound:
            raise ValueError("lower_bound deve ser menor que upper_bound")
        if not 0.0 <= self.mutation_weight <= 2.0:
            raise ValueError("mutation_weight deve estar entre 0 e 2")
        if not 0.0 <= self.crossover_rate <= 1.0:
            raise ValueError("crossover_rate deve estar entre 0 e 1")

    @property
    def bounds(self) -> tuple[float, float]:
        return self.lower_bound, self.upper_bound


@dataclass(frozen=True)
class DECase:
    name: str
    strategy: str


@dataclass(frozen=True)
class DEResult:
    best_fitness: float
    worst_fitness: float
    best_individual: FloatArray
    worst_individual: FloatArray
    elapsed_seconds: float


CASES = (
    DECase(name="Caso 1", strategy="DE/rand/1/bin"),
    DECase(name="Caso 2", strategy="DE/best/1/bin"),
)


def binomial_crossover(
    target: FloatArray,
    donor: FloatArray,
    crossover_rate: float,
    rng: np.random.Generator,
) -> FloatArray:
    """Combine a target and donor, forcing at least one donor coordinate."""
    mask = rng.random(target.size) < crossover_rate
    mask[rng.integers(target.size)] = True
    return np.where(mask, donor, target)


def run_de(case: DECase, seed: int, config: DEConfig = DEConfig()) -> DEResult:
    if case not in CASES:
        raise ValueError(f"caso de evolucao diferencial desconhecido: {case.name}")

    rng = np.random.default_rng(seed)
    started = perf_counter()
    population = rng.uniform(
        config.lower_bound,
        config.upper_bound,
        size=(config.population_size, config.dimensions),
    )
    candidates = np.arange(config.population_size)

    for _ in range(config.generations):
        fitness = rastrigin(population)
        best_index = int(np.argmin(fitness))
        next_population = population.copy()
        next_fitness = fitness.copy()

        for target_index in range(config.population_size):
            available = candidates[candidates != target_index]
            if case.strategy == "DE/rand/1/bin":
                r1, r2, r3 = rng.choice(available, size=3, replace=False)
                base = population[r1]
                difference = population[r2] - population[r3]
            else:
                r1, r2 = rng.choice(available, size=2, replace=False)
                base = population[best_index]
                difference = population[r1] - population[r2]

            donor = np.clip(
                base + config.mutation_weight * difference,
                config.lower_bound,
                config.upper_bound,
            )
            trial = binomial_crossover(
                population[target_index], donor, config.crossover_rate, rng
            )
            trial_fitness = float(rastrigin(trial))
            if trial_fitness <= fitness[target_index]:
                next_population[target_index] = trial
                next_fitness[target_index] = trial_fitness

        population = next_population
        fitness = next_fitness

    best_index = int(np.argmin(fitness))
    worst_index = int(np.argmax(fitness))
    elapsed = perf_counter() - started
    return DEResult(
        best_fitness=float(fitness[best_index]),
        worst_fitness=float(fitness[worst_index]),
        best_individual=population[best_index].copy(),
        worst_individual=population[worst_index].copy(),
        elapsed_seconds=elapsed,
    )
