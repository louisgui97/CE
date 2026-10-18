# PEP309 – Computação Evolucionária

Repositório das atividades práticas da disciplina PEP309. Cada atividade pode
abordar diferentes métodos de computação evolucionária, problemas, operadores e
protocolos experimentais. O código e as instruções específicos de cada atividade
ficam organizados sem pressupor que todas usem o mesmo algoritmo.

## Identificação

- **Aluno:** Louis Guilherme Marinho de Resende
- **Matrícula:** 2025.10204

## Organização

- `AP<n>/`: enunciado, dados de entrada, resultados e relatório da atividade.
- `src/pep309/ap<n>/`: implementação e ferramentas específicas da atividade,
  quando aplicável.
- `tests/`: testes automatizados do código.

Uma atividade que não precise de código Python pode manter seus materiais e
relatório em `AP<n>/` sem criar módulos ou testes. Para novas implementações,
use um módulo próprio da atividade e registre aqui as instruções de instalação
e execução pertinentes, sem alterar os comandos das atividades anteriores.

## Ambiente Python

As implementações Python deste repositório requerem Python 3.10 ou superior.
Crie um ambiente virtual e instale o projeto e as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Atividade prática 1 – Algoritmos Genéticos

O enunciado está em
[AP1/PEP309-2026-02-assignment-001-ga.pdf](AP1/PEP309-2026-02-assignment-001-ga.pdf).
Esta atividade implementa um algoritmo genético real para minimizar a função de
Rastrigin e compara dois conjuntos de operadores.

Execute o experimento com semente aleatória:

```powershell
python -m pep309.ap1 --output AP1\resultados
```

Para reproduzir os resultados entregues:

```powershell
python -m pep309.ap1 --seed 309 --output AP1\resultados
```

O diretório `AP1/resultados/` contém o relatório, os dados de cada execução em
CSV e os resultados estruturados em JSON. Revise o relatório e seus resultados
antes de entregar.

## Testes

Para executar os testes automatizados:

```powershell
python -m pytest
```
