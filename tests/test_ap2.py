import json

import numpy as np
import pytest

from pep309.ap2.de import CASES, DEConfig, binomial_crossover, run_de
from pep309.ap2.experiment import load_ga_reference, run_experiment
from pep309.objectives import rastrigin


@pytest.mark.parametrize("case", CASES)
def test_de_returns_feasible_individuals(case) -> None:
    config = DEConfig(population_size=8, dimensions=4, generations=3)
    result = run_de(case, seed=42, config=config)
    assert result.best_fitness <= result.worst_fitness
    assert result.best_individual.shape == (4,)
    assert np.all(result.best_individual >= config.lower_bound)
    assert np.all(result.best_individual <= config.upper_bound)


def test_binomial_crossover_forces_donor_coordinate() -> None:
    target = np.zeros(5)
    donor = np.ones(5)
    child = binomial_crossover(
        target, donor, crossover_rate=0.0, rng=np.random.default_rng(17)
    )
    assert np.count_nonzero(child == 1.0) == 1


def test_de_cases_are_reproducible_and_share_initial_population() -> None:
    config = DEConfig(population_size=8, dimensions=3, generations=1)
    first = run_de(CASES[0], seed=91, config=config)
    second = run_de(CASES[1], seed=91, config=config)
    assert rastrigin(
        np.random.default_rng(91).uniform(
            config.lower_bound,
            config.upper_bound,
            size=(config.population_size, config.dimensions),
        )
    ).min() >= first.best_fitness
    assert first.best_fitness == run_de(CASES[0], seed=91, config=config).best_fitness
    assert second.best_fitness == run_de(CASES[1], seed=91, config=config).best_fitness


def test_experiment_pairs_cases_on_each_seed() -> None:
    config = DEConfig(population_size=6, dimensions=2, generations=1)
    records = run_experiment([11, 22], master_seed=7, config=config)
    assert len(records) == 4
    for run, seed in ((1, 11), (2, 22)):
        pair = [record for record in records if record.run == run]
        assert {record.case for record in pair} == {case.name for case in CASES}
        assert {record.seed for record in pair} == {seed}


def test_load_ga_reference_selects_ap1_case_two(tmp_path) -> None:
    path = tmp_path / "ap1.json"
    path.write_text(
        json.dumps(
            {
                "records": [
                    {"case": "Caso 2", "run": 1, "seed": 101, "best_fitness": 9.0},
                    {"case": "Caso 1", "run": 1, "seed": 101, "best_fitness": 99.0},
                    {"case": "Caso 2", "run": 2, "seed": 202, "best_fitness": 8.0},
                ]
            }
        ),
        encoding="utf-8",
    )
    reference = load_ga_reference(path, runs=2)
    assert reference.seeds == [101, 202]
    assert reference.scores == [9.0, 8.0]


def test_config_rejects_population_too_small() -> None:
    with pytest.raises(ValueError, match="population_size"):
        DEConfig(population_size=3)
