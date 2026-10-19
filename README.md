# PEP309 – Computação Evolucionária

Implementações, experimentos e relatórios das atividades práticas da disciplina.

**Aluno:** Louis Guilherme Marinho de Resende · **Matrícula:** 2025.10204

## Estrutura

- `AP<n>/`: enunciado, resultados e relatório de cada atividade.
- `src/pep309/ap<n>/`: implementação específica, quando houver.
- `tests/`: testes automatizados.

Cada atividade pode usar um método evolucionário diferente; seus comandos,
parâmetros e resultados ficam documentados na respectiva seção abaixo.

## Preparação

Requer Python 3.10 ou superior:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Atividades

### AP1 – Algoritmos Genéticos

Enunciado: [AP1/PEP309-2026-02-assignment-001-ga.pdf](AP1/PEP309-2026-02-assignment-001-ga.pdf).

```powershell
python -m pep309.ap1 --seed 309 --output AP1\resultados
```

### AP2 – Evolução Diferencial

Enunciado: [AP2/PEP309-2026-02-assignment-002-de.pdf](AP2/PEP309-2026-02-assignment-002-de.pdf).
O experimento pareia as sementes com a AP1 e compara os dois casos de DE com o
Caso 2 do algoritmo genético.

```powershell
python -m pep309.ap2 --seed 309 --output AP2\resultados
```

Sem `--seed`, a AP1 usa sementes aleatórias e a ordem dos casos é aleatorizada;
na AP2, as sementes continuam pareadas com a AP1 e apenas a ordem dos casos
muda. Relatórios e dados ficam no diretório informado.

## Testes

```powershell
python -m pytest
```
