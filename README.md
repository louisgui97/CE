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

## Testes

```powershell
python -m pytest
```
