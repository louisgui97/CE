from __future__ import annotations

import argparse
import csv
import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import t, ttest_rel

from pep309.ap2.de import CASES, DEConfig, DEResult, run_de


@dataclass(frozen=True)
class RunRecord:
    case: str
    run: int
    seed: int
    best_fitness: float
    worst_fitness: float
    best_individual: list[float]
    worst_individual: list[float]
    elapsed_seconds: float


@dataclass(frozen=True)
class GAReference:
    path: Path
    seeds: list[int]
    scores: list[float]


def load_ga_reference(path: Path, runs: int = 30) -> GAReference:
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError(f"arquivo de resultados da AP1 sem lista 'records': {path}")

    selected = [
        record
        for record in records
        if record.get("case") == "Caso 2" and isinstance(record.get("run"), int)
    ]
    by_run = {record["run"]: record for record in selected}
    expected_runs = set(range(1, runs + 1))
    if set(by_run) != expected_runs:
        raise ValueError(
            f"esperados resultados do Caso 2 da AP1 para as execucoes "
            f"1..{runs}; encontrados {len(by_run)} registros em {path}"
        )

    ordered = [by_run[index] for index in range(1, runs + 1)]
    try:
        seeds = [int(record["seed"]) for record in ordered]
        scores = [float(record["best_fitness"]) for record in ordered]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"registros invalidos para comparacao com a AP1: {path}") from error
    if not np.all(np.isfinite(scores)):
        raise ValueError(f"fitness nao finito nos resultados da AP1: {path}")
    return GAReference(path=path, seeds=seeds, scores=scores)


def run_experiment(
    seeds: list[int],
    master_seed: int,
    config: DEConfig = DEConfig(),
) -> list[RunRecord]:
    if len(seeds) < 2:
        raise ValueError("sao necessarias pelo menos duas execucoes pareadas")

    rng = np.random.default_rng(master_seed)
    records: list[RunRecord] = []
    for run_index, seed in enumerate(seeds, start=1):
        pair_results: dict[str, DEResult] = {}
        for case_index in rng.permutation(len(CASES)):
            case = CASES[int(case_index)]
            pair_results[case.name] = run_de(case, seed, config)

        for case in CASES:
            result = pair_results[case.name]
            records.append(
                RunRecord(
                    case=case.name,
                    run=run_index,
                    seed=seed,
                    best_fitness=result.best_fitness,
                    worst_fitness=result.worst_fitness,
                    best_individual=result.best_individual.tolist(),
                    worst_individual=result.worst_individual.tolist(),
                    elapsed_seconds=result.elapsed_seconds,
                )
            )
    return records


def _holm_adjust(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=np.float64)
    running_max = 0.0
    for rank, index in enumerate(order):
        corrected = min(1.0, (len(p_values) - rank) * p_values[int(index)])
        running_max = max(running_max, corrected)
        adjusted[int(index)] = running_max
    return adjusted.tolist()


def _write_csv(path: Path, records: list[RunRecord]) -> None:
    fields = [
        "case",
        "run",
        "seed",
        "best_fitness",
        "worst_fitness",
        "best_individual",
        "worst_individual",
        "elapsed_seconds",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["best_individual"] = json.dumps(row["best_individual"])
            row["worst_individual"] = json.dumps(row["worst_individual"])
            writer.writerow(row)


def _comparison(
    records: list[RunRecord], ga_scores: list[float]
) -> list[dict[str, float | str]]:
    comparisons: list[dict[str, float | str]] = []
    for case in CASES:
        scores = [
            record.best_fitness
            for record in records
            if record.case == case.name
        ]
        test = ttest_rel(scores, ga_scores, alternative="two-sided")
        differences = np.asarray(scores) - np.asarray(ga_scores)
        difference_mean = float(np.mean(differences))
        standard_error = float(
            np.std(differences, ddof=1) / np.sqrt(len(differences))
        )
        margin = float(
            t.ppf(0.975, df=len(differences) - 1) * standard_error
        )
        comparisons.append(
            {
                "case": case.name,
                "statistic": float(test.statistic),
                "p_value": float(test.pvalue),
                "difference_mean": difference_mean,
                "ci_low": difference_mean - margin,
                "ci_high": difference_mean + margin,
            }
        )
    adjusted = _holm_adjust([float(item["p_value"]) for item in comparisons])
    for item, p_adjusted in zip(comparisons, adjusted):
        item["p_holm"] = p_adjusted
    return comparisons


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa os casos da AP2 e compara seus resultados com a AP1."
    )
    parser.add_argument("--runs", type=int, default=30, help="pares de execuções")
    parser.add_argument("--seed", type=int, help="semente para aleatorizar a ordem")
    parser.add_argument(
        "--ap1-results",
        type=Path,
        default=Path("AP1") / "resultados" / "resultados.json",
        help="JSON de execuções da AP1 usado na comparação pareada",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("AP2") / "resultados",
        help="diretório de saída",
    )
    args = parser.parse_args()
    if args.runs < 2:
        parser.error("--runs deve ser pelo menos 2")

    reference = load_ga_reference(args.ap1_results, runs=args.runs)
    master_seed = secrets.randbits(64) if args.seed is None else args.seed
    records = run_experiment(reference.seeds, master_seed)
    args.output.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output / "execucoes.csv", records)
    comparisons = _comparison(records, reference.scores)
    payload = {
        "master_seed": master_seed,
        "config": asdict(DEConfig()),
        "cases": [asdict(case) for case in CASES],
        "ga_reference": {
            "path": str(reference.path),
            "case": "Caso 2",
            "seeds": reference.seeds,
            "best_fitness_per_run": reference.scores,
        },
        "comparisons": comparisons,
        "records": [asdict(record) for record in records],
    }
    (args.output / "resultados.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Experimento concluído. Dados salvos em: {args.output}")


if __name__ == "__main__":
    main()
