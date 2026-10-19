from __future__ import annotations

import argparse
import csv
import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from pep309.ap1.ga import CASES, GAConfig, RastriginResult, run_ga


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


def run_experiment(
    runs: int = 30, seed: int | None = None, config: GAConfig = GAConfig()
) -> tuple[int, list[RunRecord]]:
    if runs < 2:
        raise ValueError("runs deve ser pelo menos 2 para o teste t pareado")

    master_seed = secrets.randbits(64) if seed is None else seed
    rng = np.random.default_rng(master_seed)
    records: list[RunRecord] = []

    for run_index in range(1, runs + 1):
        pair_seed = int(rng.integers(0, np.iinfo(np.uint32).max, dtype=np.uint32))
        execution_order = rng.permutation(len(CASES))
        pair_results: dict[str, RastriginResult] = {}
        for case_index in execution_order:
            case = CASES[int(case_index)]
            pair_results[case.name] = run_ga(case, pair_seed, config)

        for case in CASES:
            result = pair_results[case.name]
            records.append(
                RunRecord(
                    case=case.name,
                    run=run_index,
                    seed=pair_seed,
                    best_fitness=result.best_fitness,
                    worst_fitness=result.worst_fitness,
                    best_individual=result.best_individual.tolist(),
                    worst_individual=result.worst_individual.tolist(),
                    elapsed_seconds=result.elapsed_seconds,
                )
            )

    return master_seed, records


def _write_csv(path: Path, records: list[RunRecord]) -> None:
    fieldnames = [
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
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["best_individual"] = json.dumps(row["best_individual"])
            row["worst_individual"] = json.dumps(row["worst_individual"])
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa os dois casos de teste da AP1 e salva os dados."
    )
    parser.add_argument("--runs", type=int, default=30, help="pares de execucoes (padrao: 30)")
    parser.add_argument("--seed", type=int, help="semente mestre para reproducibilidade")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("AP1") / "resultados",
        help="diretorio de saida (padrao: AP1/resultados)",
    )
    args = parser.parse_args()

    master_seed, records = run_experiment(runs=args.runs, seed=args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output / "execucoes.csv", records)
    payload = {
        "master_seed": master_seed,
        "config": asdict(GAConfig()),
        "cases": [
            {
                "name": case.name,
                "crossover": case.crossover_name,
                "mutation": case.mutation_name,
            }
            for case in CASES
        ],
        "records": [asdict(record) for record in records],
    }
    (args.output / "resultados.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Experimento concluido. Dados salvos em: {args.output}")


if __name__ == "__main__":
    main()
