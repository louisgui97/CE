import numpy as np
import pytest

from pep309.ap1.ga import (
    CASES,
    GAConfig,
    arithmetic_crossover,
    blx_alpha_crossover,
    linear_ranking_probabilities,
    polynomial_mutation,
    rastrigin,
    run_ga,
)
from pep309.ap1.experiment import run_experiment


def test_rastrigin_global_minimum_and_batch() -> None:
    assert rastrigin(np.zeros(100)) == pytest.approx(0.0)
    batch = rastrigin(np.array([[0.0, 0.0], [1.0, 1.0]]))
    np.testing.assert_allclose(batch, [0.0, 2.0])


def test_linear_ranking_favors_best_for_minimization() -> None:
    probabilities = linear_ranking_probabilities(np.array([0.0, 1.0, 2.0]), 1.7)
    assert probabilities.sum() == pytest.approx(1.0)
    assert probabilities[0] > probabilities[1] > probabilities[2]


@pytest.mark.parametrize("crossover", [blx_alpha_crossover, arithmetic_crossover])
def test_crossovers_return_feasible_child(crossover) -> None:
    config = GAConfig(dimensions=3)
    rng = np.random.default_rng(19)
    parent1 = np.array([-5.0, 0.0, 5.0])
    parent2 = np.array([5.0, 1.0, -5.0])
    child = crossover(parent1, parent2, rng, config)
    assert child.shape == parent1.shape
    assert np.all(child >= config.lower_bound)
    assert np.all(child <= config.upper_bound)


def test_polynomial_mutation_remains_in_bounds() -> None:
    config = GAConfig(dimensions=20, mutation_rate=1.0)
    child = polynomial_mutation(
        np.full(20, config.upper_bound), np.random.default_rng(3), config
    )
    assert np.all(child >= config.lower_bound)
    assert np.all(child <= config.upper_bound)


@pytest.mark.parametrize("case", CASES)
def test_ga_returns_feasible_individuals(case) -> None:
    config = GAConfig(population_size=8, dimensions=4, generations=3)
    result = run_ga(case, seed=42, config=config)
    assert result.best_fitness <= result.worst_fitness
    assert result.best_individual.shape == (4,)
    assert np.all(result.best_individual >= config.lower_bound)
    assert np.all(result.best_individual <= config.upper_bound)


def test_experiment_pairs_seeds_and_returns_all_cases() -> None:
    config = GAConfig(population_size=6, dimensions=2, generations=1)
    master_seed, records = run_experiment(runs=2, seed=11, config=config)
    assert master_seed == 11
    assert len(records) == 4
    for run in (1, 2):
        pair = [record for record in records if record.run == run]
        assert len({record.case for record in pair}) == 2
        assert len({record.seed for record in pair}) == 1


def test_config_rejects_invalid_ranking_pressure() -> None:
    with pytest.raises(ValueError, match="ranking_pressure"):
        GAConfig(ranking_pressure=2.1)
