from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
Operator = Callable[[FloatArray, FloatArray, np.random.Generator, "GAConfig"], FloatArray]


@dataclass(frozen=True)
class GAConfig:
    population_size: int = 100
    dimensions: int = 100
    generations: int = 300
    lower_bound: float = -5.12
    upper_bound: float = 5.12
    crossover_rate: float = 0.9
    mutation_rate: float | None = None
    elitism: int = 1
    ranking_pressure: float = 1.7
    blx_alpha: float = 0.5
    gaussian_sigma_fraction: float = 0.1
    polynomial_eta: float = 20.0

    def __post_init__(self) -> None:
        if self.population_size < 2:
            raise ValueError("population_size deve ser pelo menos 2")
        if self.dimensions < 1:
            raise ValueError("dimensions deve ser positivo")
        if self.generations < 0:
            raise ValueError("generations nao pode ser negativo")
        if self.lower_bound >= self.upper_bound:
            raise ValueError("lower_bound deve ser menor que upper_bound")
        if not 0.0 <= self.crossover_rate <= 1.0:
            raise ValueError("crossover_rate deve estar entre 0 e 1")
        if self.mutation_rate is not None and not 0.0 <= self.mutation_rate <= 1.0:
            raise ValueError("mutation_rate deve estar entre 0 e 1")
        if not 0 <= self.elitism < self.population_size:
            raise ValueError("elitism deve estar entre 0 e population_size - 1")
        if not 1.0 <= self.ranking_pressure <= 2.0:
            raise ValueError("ranking_pressure deve estar entre 1 e 2")
        if self.blx_alpha < 0.0:
            raise ValueError("blx_alpha nao pode ser negativo")
        if self.gaussian_sigma_fraction <= 0.0:
            raise ValueError("gaussian_sigma_fraction deve ser positivo")
        if self.polynomial_eta <= 0.0:
            raise ValueError("polynomial_eta deve ser positivo")

    @property
    def effective_mutation_rate(self) -> float:
        return self.mutation_rate if self.mutation_rate is not None else 1.0 / self.dimensions

    @property
    def bounds(self) -> tuple[float, float]:
        return self.lower_bound, self.upper_bound


@dataclass(frozen=True)
class GeneticCase:
    name: str
    crossover_name: str
    mutation_name: str
    crossover: Operator
    mutation: Operator


@dataclass(frozen=True)
class RastriginResult:
    best_fitness: float
    worst_fitness: float
    best_individual: FloatArray
    worst_individual: FloatArray
    elapsed_seconds: float


def rastrigin(individuals: FloatArray) -> FloatArray:
    """Evaluate Rastrigin for one vector or a matrix of individuals."""
    values = np.asarray(individuals, dtype=np.float64)
    if values.ndim not in (1, 2):
        raise ValueError("individuals deve ser um vetor ou uma matriz")
    if values.shape[-1] < 1:
        raise ValueError("cada individuo deve ter ao menos uma variavel")
    return 10.0 * values.shape[-1] + np.sum(
        values**2 - 10.0 * np.cos(2.0 * np.pi * values), axis=-1
    )


def linear_ranking_probabilities(fitness: FloatArray, pressure: float) -> FloatArray:
    """Return Baker linear-ranking probabilities for a minimization problem."""
    values = np.asarray(fitness, dtype=np.float64)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("fitness deve conter ao menos dois valores em um vetor")
    if not 1.0 <= pressure <= 2.0:
        raise ValueError("pressure deve estar entre 1 e 2")

    order = np.argsort(values, kind="stable")
    ranks = np.empty(values.size, dtype=np.float64)
    ranks[order] = np.arange(values.size, 0, -1, dtype=np.float64)
    probabilities = (
        (2.0 - pressure) / values.size
        + 2.0 * (pressure - 1.0) * (ranks - 1.0) / (values.size * (values.size - 1))
    )
    return probabilities / probabilities.sum()


def blx_alpha_crossover(
    parent1: FloatArray, parent2: FloatArray, rng: np.random.Generator, config: GAConfig
) -> FloatArray:
    """Blend two parents using BLX-alpha, then enforce the feasible interval."""
    low = np.minimum(parent1, parent2)
    high = np.maximum(parent1, parent2)
    interval = high - low
    child = rng.uniform(
        low - config.blx_alpha * interval,
        high + config.blx_alpha * interval,
    )
    return np.clip(child, *config.bounds)


def arithmetic_crossover(
    parent1: FloatArray, parent2: FloatArray, rng: np.random.Generator, config: GAConfig
) -> FloatArray:
    """Create a convex, gene-wise arithmetic combination of two parents."""
    weights = rng.random(parent1.shape)
    child = weights * parent1 + (1.0 - weights) * parent2
    return np.clip(child, *config.bounds)


def gaussian_mutation(
    individual: FloatArray, rng: np.random.Generator, config: GAConfig
) -> FloatArray:
    child = individual.copy()
    mask = rng.random(child.shape) < config.effective_mutation_rate
    sigma = config.gaussian_sigma_fraction * (config.upper_bound - config.lower_bound)
    child[mask] += rng.normal(0.0, sigma, size=int(mask.sum()))
    return np.clip(child, *config.bounds)


def polynomial_mutation(
    individual: FloatArray, rng: np.random.Generator, config: GAConfig
) -> FloatArray:
    child = individual.copy()
    mask = rng.random(child.shape) < config.effective_mutation_rate
    selected = np.flatnonzero(mask)
    if selected.size == 0:
        return child

    lower, upper = config.bounds
    span = upper - lower
    values = child[selected]
    delta1 = (values - lower) / span
    delta2 = (upper - values) / span
    random_values = rng.random(selected.size)
    mutation_power = 1.0 / (config.polynomial_eta + 1.0)
    delta = np.empty(selected.size, dtype=np.float64)

    lower_half = random_values <= 0.5
    xy = 1.0 - delta1[lower_half]
    value = 2.0 * random_values[lower_half] + (
        1.0 - 2.0 * random_values[lower_half]
    ) * xy ** (config.polynomial_eta + 1.0)
    delta[lower_half] = value**mutation_power - 1.0

    upper_half = ~lower_half
    xy = 1.0 - delta2[upper_half]
    value = 2.0 * (1.0 - random_values[upper_half]) + (
        2.0 * random_values[upper_half] - 1.0
    ) * xy ** (config.polynomial_eta + 1.0)
    delta[upper_half] = 1.0 - value**mutation_power

    child[selected] = np.clip(values + delta * span, lower, upper)
    return child


CASES = (
    GeneticCase(
        name="Caso 1",
        crossover_name="BLX-alpha (alpha=0.5)",
        mutation_name="Gaussiana (sigma=10% do intervalo)",
        crossover=blx_alpha_crossover,
        mutation=gaussian_mutation,
    ),
    GeneticCase(
        name="Caso 2",
        crossover_name="Aritmetico (pesos por gene)",
        mutation_name="Polinomial (eta=20)",
        crossover=arithmetic_crossover,
        mutation=polynomial_mutation,
    ),
)


def run_ga(
    case: GeneticCase,
    seed: int,
    config: GAConfig = GAConfig(),
) -> RastriginResult:
    rng = np.random.default_rng(seed)
    started = perf_counter()
    population = rng.uniform(
        config.lower_bound,
        config.upper_bound,
        size=(config.population_size, config.dimensions),
    )

    for _ in range(config.generations):
        fitness = rastrigin(population)
        probabilities = linear_ranking_probabilities(fitness, config.ranking_pressure)
        order = np.argsort(fitness, kind="stable")
        next_population = np.empty_like(population)
        if config.elitism:
            next_population[: config.elitism] = population[order[: config.elitism]]

        for index in range(config.elitism, config.population_size):
            first = population[rng.choice(config.population_size, p=probabilities)]
            second = population[rng.choice(config.population_size, p=probabilities)]
            if rng.random() < config.crossover_rate:
                child = case.crossover(first, second, rng, config)
            else:
                child = first.copy()
            next_population[index] = case.mutation(child, rng, config)
        population = next_population

    final_fitness = rastrigin(population)
    best_index = int(np.argmin(final_fitness))
    worst_index = int(np.argmax(final_fitness))
    elapsed = perf_counter() - started
    return RastriginResult(
        best_fitness=float(final_fitness[best_index]),
        worst_fitness=float(final_fitness[worst_index]),
        best_individual=population[best_index].copy(),
        worst_individual=population[worst_index].copy(),
        elapsed_seconds=elapsed,
    )
