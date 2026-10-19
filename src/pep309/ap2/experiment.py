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


def _summary(records: list[RunRecord]) -> dict[str, dict[str, float | RunRecord]]:
    result: dict[str, dict[str, float | RunRecord]] = {}
    for case in CASES:
        rows = [record for record in records if record.case == case.name]
        scores = np.asarray([row.best_fitness for row in rows], dtype=np.float64)
        result[case.name] = {
            "best": min(rows, key=lambda row: row.best_fitness),
            "worst": max(rows, key=lambda row: row.best_fitness),
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores, ddof=1)),
            "average_seconds": float(
                np.mean([row.elapsed_seconds for row in rows])
            ),
        }
    return result


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


def _format_vector(values: list[float]) -> str:
    return "[" + ", ".join(f"{value:.4f}" for value in values) + "]"


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


def _write_report(
    path: Path,
    records: list[RunRecord],
    config: DEConfig,
    reference: GAReference,
    master_seed: int,
) -> dict[str, Any]:
    summary = _summary(records)
    comparisons = _comparison(records, reference.scores)
    best_de_case = min(CASES, key=lambda case: float(summary[case.name]["mean"]))
    best_de = min(records, key=lambda row: row.best_fitness)
    best_ga_index = int(np.argmin(reference.scores))
    best_ga = reference.scores[best_ga_index]
    alpha = 0.05

    lines = [
        "# Relatório – Atividade Prática 2: Evolução Diferencial",
        "",
        "**Aluno:** Louis Guilherme Marinho de Resende  ",
        "**Matrícula:** 2025.10204",
        "",
        "## Estratégia e parâmetros",
        "",
        "Foi implementada Evolução Diferencial com representação real, população "
        "inicial uniforme no intervalo viável e seleção gulosa: cada vetor "
        "experimental substitui seu alvo somente quando apresenta fitness menor "
        "ou igual. Ambos os casos usam os mesmos parâmetros; a estratégia de "
        "perturbação é a diferença entre eles.",
        "",
        "| Parâmetro | Valor |",
        "|---|---:|",
        f"| Tamanho da população (Np) | {config.population_size} |",
        f"| Dimensões (n) | {config.dimensions} |",
        f"| Gerações máximas | {config.generations} |",
        f"| Intervalo | [{config.lower_bound}, {config.upper_bound}] |",
        f"| Peso de mutação (F) | {config.mutation_weight} |",
        f"| Taxa de crossover (Cr) | {config.crossover_rate} |",
        f"| Execuções por caso | {len(reference.seeds)} |",
        f"| Semente da ordem de execução | {master_seed} |",
        "",
        "## Casos de teste e operadores",
        "",
        "- **Caso 1 — DE/rand/1/bin:** o vetor doador é `x_r1 + F (x_r2 - x_r3)`, "
        "com três índices distintos entre si e diferentes do alvo.",
        "- **Caso 2 — DE/best/1/bin:** o vetor doador é "
        "`x_best + F (x_r1 - x_r2)`, com índices distintos e diferentes do alvo.",
        "",
        "Nos dois casos, o crossover binomial combina alvo e doador, forçando "
        "pelo menos uma coordenada do doador. Valores fora do domínio são "
        "projetados nos limites por clipping. A seleção mantém o melhor entre "
        "alvo e vetor experimental.",
        "",
        "## Resultados",
        "",
        "As estatísticas são calculadas sobre o melhor fitness final de cada "
        "execução; o desvio-padrão é amostral.",
        "",
        "| Caso | Melhor fitness | Pior melhor-fitness | Média | Desvio-padrão | Tempo médio (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for case in CASES:
        values = summary[case.name]
        best = values["best"]
        worst = values["worst"]
        assert isinstance(best, RunRecord) and isinstance(worst, RunRecord)
        lines.append(
            f"| {case.name} ({case.strategy}) | {best.best_fitness:.8g} | "
            f"{worst.best_fitness:.8g} | {values['mean']:.8g} | "
            f"{values['std']:.8g} | {values['average_seconds']:.4f} |"
        )
    lines.extend(["", "### Indivíduos extremos", ""])
    for case in CASES:
        values = summary[case.name]
        best = values["best"]
        worst = values["worst"]
        assert isinstance(best, RunRecord) and isinstance(worst, RunRecord)
        lines.extend(
            [
                f"**{case.name} — melhor (execução {best.run}, "
                f"f={best.best_fitness:.8g}):**",
                "",
                f"`{_format_vector(best.best_individual)}`",
                "",
                f"**{case.name} — pior melhor-indivíduo (execução {worst.run}, "
                f"f={worst.best_fitness:.8g}):**",
                "",
                f"`{_format_vector(worst.best_individual)}`",
                "",
            ]
        )
    lines.extend(
        [
            "### Teste t pareado entre os casos de DE",
            "",
            f"Os mesmos {len(reference.seeds)} valores de semente foram usados nos "
            "dois casos, formando pares por execução. Hipóteses: H0: C1 = C2; "
            "H1: C1 != C2. Teste bilateral, com α = 0,05:",
            "",
            f"| Comparação (C1 − C2) | t({len(reference.seeds) - 1}) | "
            "p-value | Diferença média |",
            "|---|---:|---:|---:|",
        ]
    )
    case1_scores = [
        row.best_fitness for row in records if row.case == CASES[0].name
    ]
    case2_scores = [
        row.best_fitness for row in records if row.case == CASES[1].name
    ]
    de_test = ttest_rel(case1_scores, case2_scores, alternative="two-sided")
    lines.append(
        f"| Caso 1 − Caso 2 | {de_test.statistic:.6g} | "
        f"{de_test.pvalue:.6g} | "
        f"{np.mean(np.asarray(case1_scores) - np.asarray(case2_scores)):.6g} |"
    )
    de_verdict = (
        "Rejeita-se H0: há evidência de diferença estatisticamente significativa."
        if de_test.pvalue < alpha
        else "Não se rejeita H0: não há evidência suficiente de diferença estatística."
    )
    lines.extend(
        [
            "",
            f"Decisão: {de_verdict}",
            "",
            "## Comparação com o algoritmo genético da AP1",
            "",
            f"A referência é o **Caso 2 da AP1** (crossover aritmético e mutação "
            f"polinomial), que apresentou a menor média entre as duas "
            f"configurações genéticas: {np.mean(reference.scores):.8g}. As "
            "execuções do DE foram pareadas pelo mesmo número de semente usado "
            "na AP1, mantendo a população inicial aleatória comparável. A "
            f"comparação testa H0: média(DE) = média(AP1) contra H1: médias "
            f"diferentes, usando os {len(reference.seeds)} melhores fitness por "
            "execução; comparar apenas os dois melhores indivíduos isolados não "
            "permitiria um teste de significância.",
            "",
            f"O melhor fitness individual encontrado pelo DE foi "
            f"{best_de.best_fitness:.8g} ({best_de.case}, execução {best_de.run}); "
            f"na referência da AP1 foi {best_ga:.8g} (Caso 2, execução "
            f"{best_ga_index + 1}). Assim, o melhor valor observado pelo DE foi "
            f"{best_de.best_fitness / best_ga:.2f} vezes maior (pior, pois o "
            "problema é de minimização). Esses extremos são uma comparação descritiva; "
            f"a significância é avaliada sobre os {len(reference.seeds)} pares.",
            "",
            f"| DE vs. AP1 Caso 2 | Média DE | Média AP1 | "
            f"t({len(reference.seeds) - 1}) | p-value | p Holm | "
            "Diferença média (DE − AP1) |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in comparisons:
        case = next(case for case in CASES if case.name == item["case"])
        values = summary[case.name]
        mean = float(values["mean"])
        mean_ga = float(np.mean(reference.scores))
        lines.append(
            f"| {case.name} ({case.strategy}) | {mean:.8g} | {mean_ga:.8g} | "
            f"{float(item['statistic']):.6g} | {float(item['p_value']):.6g} | "
            f"{float(item['p_holm']):.6g} | "
            f"{float(item['difference_mean']):.8g} |"
        )
    lines.extend(
        [
            "",
            "Foi aplicado o ajuste de Holm às duas comparações com a AP1 para "
            "controlar o erro familiar. Com α = 0,05, "
            + "; ".join(
                f"{item['case']}: "
                + (
                    "rejeita-se H0"
                    if float(item["p_holm"]) < alpha
                    else "não se rejeita H0"
                )
                + f" (p ajustado = {float(item['p_holm']):.6g})"
                for item in comparisons
            )
            + ".",
            "",
            "## Discussão e conclusão",
            "",
            f"A configuração DE com menor média foi **{best_de_case.name} "
            f"({best_de_case.strategy})**, com média "
            f"{float(summary[best_de_case.name]['mean']):.2f} e desvio-padrão "
            f"{float(summary[best_de_case.name]['std']):.2f}. O teste t entre "
            f"os casos de DE resultou em p = {de_test.pvalue:.4g}; "
            + (
                "a diferença entre essas estratégias é estatisticamente "
                "significativa a 5%."
                if de_test.pvalue < alpha
                else "não foi detectada diferença estatisticamente significativa "
                "entre essas estratégias a 5%."
            ),
            "",
            "A comparação com a AP1 deve ser interpretada em conjunto com as "
            "médias, os p-values ajustados e os melhores indivíduos. Um p-value "
            "acima do nível adotado significa que não se rejeita H0; não prova "
            "que os algoritmos sejam equivalentes. Os valores de p avaliam as "
            "configurações completas testadas, não um operador isolado.",
            "",
            f"A busca não atingiu o mínimo global 0: o melhor fitness obtido foi "
            f"{best_de.best_fitness:.2f}. Os resultados "
            "dependem de Np, F, Cr, do tratamento dos limites e do orçamento de "
            "300 gerações. Também se utilizou apenas uma combinação de F e Cr "
            f"para cada estratégia e {len(reference.seeds)} execuções. "
            "Uma investigação mais ampla "
            "poderia variar esses parâmetros, aumentar o número de repetições e "
            "inspecionar a distribuição das diferenças pareadas.",
            "",
            "### Desafios de implementação",
            "",
            "A mutação diferencial pode propor coordenadas fora do intervalo "
            "permitido; foi adotado clipping para manter cada indivíduo factível. "
            "No crossover binomial, foi necessário garantir que ao menos uma "
            "coordenada viesse do vetor doador, inclusive quando Cr é zero. Para "
            "a comparação entre atividades, os experimentos reutilizam as mesmas "
            "sementes e, portanto, as mesmas populações iniciais; a ordem dos "
            "casos de DE é aleatorizada em cada par.",
            "",
            "## Reprodutibilidade",
            "",
            f"Resultados da AP1 lidos de `{reference.path}`. O CSV contém as "
            "execuções individuais; o JSON preserva sementes, configurações, "
            "indivíduos extremos e testes estatísticos.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "de_case_test": {
            "statistic": float(de_test.statistic),
            "p_value": float(de_test.pvalue),
            "degrees_of_freedom": len(case1_scores) - 1,
        },
        "ga_comparisons": comparisons,
    }


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
    comparisons = _write_report(
        args.output / "relatorio.md",
        records,
        DEConfig(),
        reference,
        master_seed,
    )
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
    print(f"Experimento concluído. Relatório: {args.output / 'relatorio.md'}")


if __name__ == "__main__":
    main()
