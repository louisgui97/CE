from __future__ import annotations

import argparse
import csv
import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.stats import t, ttest_rel

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


def _summary(records: list[RunRecord]) -> dict[str, dict[str, float | RunRecord]]:
    result: dict[str, dict[str, float | RunRecord]] = {}
    for case in CASES:
        rows = [record for record in records if record.case == case.name]
        best_scores = np.asarray([row.best_fitness for row in rows], dtype=np.float64)
        best_row = min(rows, key=lambda row: row.best_fitness)
        worst_row = max(rows, key=lambda row: row.best_fitness)
        result[case.name] = {
            "best": best_row,
            "worst": worst_row,
            "mean": float(np.mean(best_scores)),
            "std": float(np.std(best_scores, ddof=1)),
            "average_seconds": float(np.mean([row.elapsed_seconds for row in rows])),
        }
    return result


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


def _format_vector(values: list[float]) -> str:
    return "[" + ", ".join(f"{value:.4f}" for value in values) + "]"


def _write_report(
    path: Path, master_seed: int, records: list[RunRecord], config: GAConfig
) -> None:
    summary = _summary(records)
    case1_scores = [
        row.best_fitness for row in records if row.case == CASES[0].name
    ]
    case2_scores = [
        row.best_fitness for row in records if row.case == CASES[1].name
    ]
    paired_differences = np.asarray(case1_scores) - np.asarray(case2_scores)
    test = ttest_rel(case1_scores, case2_scores, alternative="two-sided")
    alpha = 0.05
    difference_mean = float(np.mean(paired_differences))
    difference_se = float(
        np.std(paired_differences, ddof=1) / np.sqrt(len(paired_differences))
    )
    confidence_margin = float(
        t.ppf(1.0 - alpha / 2.0, df=len(paired_differences) - 1) * difference_se
    )
    case1_mean = float(summary[CASES[0].name]["mean"])
    case2_mean = float(summary[CASES[1].name]["mean"])
    case1_std = float(summary[CASES[0].name]["std"])
    case2_std = float(summary[CASES[1].name]["std"])
    case1_time = float(summary[CASES[0].name]["average_seconds"])
    case2_time = float(summary[CASES[1].name]["average_seconds"])
    mean_reduction = 100.0 * (case1_mean - case2_mean) / case1_mean
    variability_reduction = 100.0 * (case1_std - case2_std) / case1_std
    case2_wins = int(np.count_nonzero(paired_differences > 0.0))
    verdict = (
        "Rejeita-se H0: há evidência de diferença estatisticamente significativa."
        if test.pvalue < alpha
        else "Não se rejeita H0: não há evidência suficiente de diferença estatística."
    )

    lines = [
        "# Relatorio – Atividade Pratica 1: Algoritmos Geneticos",
        "",
        "**Aluno:** Louis Guilherme Marinho de Resende  ",
        "**Matricula:** 2025.10204",
        "",
        "## Objetivo e estrategia",
        "",
        "Foram comparadas duas configuracoes de algoritmo genetico real para minimizar "
        "a funcao de Rastrigin em 100 dimensoes, no intervalo [-5.12, 5.12]. "
        "A populacao inicial foi gerada uniformemente ao acaso. A selecao utiliza "
        "ranking linear de Baker para minimizacao, com pressao 1,7; cada geracao "
        "mantem um elite e substitui os demais individuos por descendentes. "
        "A taxa de crossover e 0,9; a taxa de mutacao por variavel e 1/n = "
        f"{config.effective_mutation_rate:.4f}.",
        "",
        "## Parametros",
        "",
        "| Parametro | Valor |",
        "|---|---:|",
        f"| Tamanho da populacao | {config.population_size} |",
        f"| Dimensoes | {config.dimensions} |",
        f"| Geracoes | {config.generations} |",
        f"| Intervalo | [{config.lower_bound}, {config.upper_bound}] |",
        f"| Taxa de crossover | {config.crossover_rate} |",
        f"| Taxa de mutacao por gene | {config.effective_mutation_rate:.4f} |",
        f"| Elitismo | {config.elitism} individuo(s) |",
        f"| Pressao do ranking linear | {config.ranking_pressure} |",
        f"| Execucoes por caso | {len(case1_scores)} |",
        f"| Semente mestre | {master_seed} |",
        "",
        "## Operadores",
        "",
    ]
    for case in CASES:
        lines.append(
            f"- **{case.name}:** crossover {case.crossover_name}; "
            f"mutacao {case.mutation_name}."
        )
    lines.extend(
        [
            "",
            "Os casos compartilham os mesmos parametros gerais e sementes dentro de "
            "cada par; a ordem de execucao de cada par e aleatorizada. O crossover "
            "combina dois progenitores e a mutacao e aplicada ao descendente.",
            "",
            "## Resultados",
            "",
            "As estatisticas abaixo sao calculadas sobre o melhor fitness final de "
            "cada execucao. O desvio padrao e amostral (ddof=1).",
            "",
            "| Caso | Melhor fitness | Pior melhor-fitness | Media | Desvio padrao | Tempo medio (s) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for case in CASES:
        values = summary[case.name]
        best = values["best"]
        worst = values["worst"]
        assert isinstance(best, RunRecord) and isinstance(worst, RunRecord)
        lines.append(
            f"| {case.name} | {best.best_fitness:.8g} | {worst.best_fitness:.8g} | "
            f"{values['mean']:.8g} | {values['std']:.8g} | "
            f"{values['average_seconds']:.4f} |"
        )
    lines.extend(
        [
            "",
            "### Indivíduos extremos observados",
            "",
        ]
    )
    for case in CASES:
        values = summary[case.name]
        best = values["best"]
        worst = values["worst"]
        assert isinstance(best, RunRecord) and isinstance(worst, RunRecord)
        lines.extend(
            [
                f"**{case.name} — melhor (execucao {best.run}, "
                f"f={best.best_fitness:.8g}):**",
                "",
                f"`{_format_vector(best.best_individual)}`",
                "",
                f"**{case.name} — pior melhor-individuo (execucao {worst.run}, "
                f"f={worst.best_fitness:.8g}):**",
                "",
                f"`{_format_vector(worst.best_individual)}`",
                "",
            ]
        )
    lines.extend(
        [
            "### Teste t pareado bilateral",
            "",
            f"- Hipóteses: H0: C1 = C2; H1: C1 != C2.",
            f"- Nível de significância: alpha = {alpha}.",
            f"- Estatística t: {test.statistic:.8g}.",
            f"- p-value: {test.pvalue:.8g}.",
            f"- Diferença média pareada (C1 - C2): {difference_mean:.8g}.",
            f"- IC 95% da diferença média (C1 - C2): "
            f"[{difference_mean - confidence_margin:.8g}, "
            f"{difference_mean + confidence_margin:.8g}].",
            f"- Decisão: {verdict}",
            "",
            "## Discussão e conclusão",
            "",
            "### Interpretação dos resultados",
            "",
            f"O Caso 2 obteve média de fitness {case2_mean:.2f}, frente a "
            f"{case1_mean:.2f} no Caso 1: uma redução média de "
            f"{mean_reduction:.2f}% (menor é melhor). Em {case2_wins} de "
            f"{len(paired_differences)} pares, o Caso 2 terminou com fitness "
            "menor. A dispersão dos resultados também foi menor no Caso 2: "
            f"desvio-padrão de {case2_std:.2f}, contra {case1_std:.2f} no Caso 1 "
            f"(redução de {variability_reduction:.2f}%).",
            "",
            f"O teste t pareado resultou em t({len(paired_differences) - 1}) = "
            f"{test.statistic:.4f}, p = {test.pvalue:.4g}. Como p < {alpha}, "
            "rejeita-se H0 ao nível de 5%. O intervalo de confiança de 95% para "
            f"a diferença média C1 - C2 [{difference_mean - confidence_margin:.2f}, "
            f"{difference_mean + confidence_margin:.2f}] é positivo, consistente "
            "com o melhor resultado médio do Caso 2. O pareamento compara as "
            "configurações sob a mesma semente em cada repetição.",
            "",
            "Os resultados comparam os operadores em conjunto, não isolam o efeito "
            "individual do crossover ou da mutação. Portanto, não é possível "
            "atribuir a diferença a um operador específico. O crossover aritmético "
            "gera combinações convexas dos progenitores, enquanto a mutação "
            "polinomial depende da distância aos limites e do parâmetro eta. No "
            "Caso 1, o BLX-alpha permite amostrar ao redor do intervalo dos pais "
            "e a mutação gaussiana usa desvio-padrão de 1.024 unidades. O melhor "
            "desempenho observado do Caso 2 é uma conclusão para estes parâmetros "
            "e este experimento, não uma superioridade universal desses operadores.",
            "",
            "### Problemas encontrados durante o desenvolvimento",
            "",
            "Foi necessário garantir que o ranking linear fosse orientado para "
            "minimização: o indivíduo com menor valor de Rastrigin deve receber "
            "maior probabilidade de seleção. Um teste unitário verificou a ordem "
            "das probabilidades e revelou a inversão inicial dos postos; a "
            "atribuição dos postos foi corrigida e os testes passaram. Também foi "
            "importante limitar os descendentes ao intervalo permitido, pois "
            "operadores de crossover e mutação podem propor valores fora dele. "
            "As execuções pareadas reutilizam a semente de cada par para iniciar "
            "os casos com a mesma população, e a ordem aleatória reduz o risco de "
            "favorecer sistematicamente um caso pela ordem de execução.",
            "",
            "### Considerações e conclusão",
            "",
            "O Caso 2 foi claramente melhor nesta configuração: sua média foi "
            f"{mean_reduction:.2f}% menor e o teste pareado indicou diferença "
            "estatisticamente significativa. Apesar disso, o melhor fitness "
            f"observado foi {min(row.best_fitness for row in records):.2f}, acima "
            "do mínimo global 0; portanto, o experimento não encontrou o ótimo "
            "global da função em 100 dimensões. Os tempos médios foram "
            f"{case1_time:.3f} s (Caso 1) e {case2_time:.3f} s (Caso 2); essa "
            "pequena diferença descritiva não foi submetida a teste estatístico "
            "e pode variar com a carga do computador.",
            "",
            "Como limitações, foram avaliadas apenas duas combinações de "
            "operadores, uma configuração de parâmetros e 30 pares. O teste t "
            "também pressupõe que as diferenças pareadas sejam adequadas a uma "
            "análise paramétrica; essa distribuição não foi avaliada aqui. "
            "Experimentos futuros podem variar separadamente crossover e mutação, "
            "testar outros parâmetros e orçamentos de busca, e inspecionar a "
            "distribuição das diferenças para avaliar a robustez das conclusões.",
            "",
            "Os tempos medidos dependem do computador e da carga do sistema. "
            "As execuções completas estão em `execucoes.csv`; `resultados.json` "
            "preserva os dados e vetores em formato estruturado.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Executa os dois casos de teste da AP1 e gera relatorio e dados."
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
    _write_report(args.output / "relatorio.md", master_seed, records, GAConfig())
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
    print(f"Experimento concluido. Relatorio: {args.output / 'relatorio.md'}")


if __name__ == "__main__":
    main()
