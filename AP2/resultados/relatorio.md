# Relatório – Atividade Prática 2: Evolução Diferencial

**Aluno:** Louis Guilherme Marinho de Resende  
**Matrícula:** 2025.10204

## Estratégia e parâmetros

Foi implementada Evolução Diferencial com representação real, população inicial uniforme no intervalo viável e seleção gulosa: cada vetor experimental substitui seu alvo somente quando apresenta fitness menor ou igual. Ambos os casos usam os mesmos parâmetros; a estratégia de perturbação é a diferença entre eles.

| Parâmetro | Valor |
|---|---:|
| Tamanho da população (Np) | 100 |
| Dimensões (n) | 100 |
| Gerações máximas | 300 |
| Intervalo | [-5.12, 5.12] |
| Peso de mutação (F) | 0.5 |
| Taxa de crossover (Cr) | 0.9 |
| Execuções por caso | 30 |
| Semente da ordem de execução | 309 |

## Casos de teste e operadores

- **Caso 1 — DE/rand/1/bin:** o vetor doador é `x_r1 + F (x_r2 - x_r3)`, com três índices distintos entre si e diferentes do alvo.
- **Caso 2 — DE/best/1/bin:** o vetor doador é `x_best + F (x_r1 - x_r2)`, com índices distintos e diferentes do alvo.

Nos dois casos, o crossover binomial combina alvo e doador, forçando pelo menos uma coordenada do doador. Valores fora do domínio são projetados nos limites por clipping. A seleção mantém o melhor entre alvo e vetor experimental.

## Resultados

As estatísticas são calculadas sobre o melhor fitness final de cada execução; o desvio-padrão é amostral.

| Caso | Melhor fitness | Pior melhor-fitness | Média | Desvio-padrão | Tempo médio (s) |
|---|---:|---:|---:|---:|---:|
| Caso 1 (DE/rand/1/bin) | 880.91967 | 1015.3016 | 960.05096 | 28.733157 | 1.1930 |
| Caso 2 (DE/best/1/bin) | 488.56994 | 694.05886 | 607.93168 | 55.669071 | 1.1712 |

### Indivíduos extremos

**Caso 1 — melhor (execução 10, f=880.91967):**

`[0.0387, 0.9240, 0.2793, 3.0691, 0.9714, 0.0852, -0.0346, -1.5768, -3.1269, -1.5346, 0.9547, 0.8902, 0.6835, 0.1418, -1.0798, -0.1267, 1.9243, 1.1007, 1.5836, 1.4280, 1.1347, -2.0101, -1.1009, -2.9468, 0.8747, 0.3017, 1.8848, 0.0117, 1.8201, 0.2017, -2.0535, 3.1018, 1.1199, -1.3025, 0.6478, 0.9310, -4.4844, -0.2728, 1.9470, 2.1643, -1.2783, -0.3752, 1.0685, -0.0676, -1.1041, 1.2146, 0.0933, 0.9483, 1.1531, 0.3469, 2.1431, -0.6962, -0.3199, -4.7546, -1.8763, 1.1070, -2.9842, 0.5563, 0.9992, 0.1087, -2.7842, -0.0663, -0.5948, -0.8829, 1.7234, 1.1604, -0.8488, -0.8792, -0.1660, 0.0737, -0.1583, -3.0335, 1.0514, 0.4613, 1.8375, 1.2023, 1.2949, 0.8067, -1.8886, 3.1698, 0.1730, -0.0447, -0.8141, -0.4344, -0.3814, 2.3217, 0.5050, -1.9601, -0.0110, -1.0704, 0.9205, -0.6436, -1.2521, -1.5932, 0.0287, 1.7734, 0.8910, 2.2121, 2.0103, 2.8598]`

**Caso 1 — pior melhor-indivíduo (execução 4, f=1015.3016):**

`[-0.0564, -1.1848, -0.1936, -0.0144, 0.1077, -1.4614, 1.1945, -0.7428, -0.0395, 2.5332, -0.6694, 0.5347, -2.1086, -2.5217, -2.9226, 1.6474, 0.0412, -0.9472, -0.8684, -1.7889, 1.2556, -2.4211, -0.6842, -0.6069, -1.2167, 0.2774, 0.3715, -0.1434, 0.9435, -1.0401, 0.6065, -1.5751, -0.1829, 0.3063, 3.1884, 0.1681, 1.0381, 0.4407, -1.4570, 0.0633, -1.4482, -0.9801, -0.1453, -0.5961, -0.9868, 2.7685, 1.9295, -1.3784, 0.9351, 0.1373, -2.1116, 3.1525, -1.2757, 0.3941, 1.0833, -0.5274, -0.6422, -0.3504, 0.9491, -1.4460, -1.9142, -0.6270, 1.1785, 0.6568, -2.1120, 1.7118, 0.1241, -1.1339, -0.1210, -0.2939, 1.0659, -0.5394, 0.9247, 1.1850, -3.0264, -0.7521, 0.3586, -3.1482, 1.0006, -0.0840, 1.8351, -0.2645, 0.5959, -1.8126, -1.0334, -4.1950, 1.1423, 0.7802, -2.1036, -0.3460, -0.0378, -1.8293, 0.9852, 2.6520, -1.8637, -1.7397, 1.0266, 0.0568, 0.1988, -0.2816]`

**Caso 2 — melhor (execução 28, f=488.56994):**

`[1.1981, 0.0475, -1.0329, -0.2013, -0.8633, 0.8732, 0.9143, -2.0781, 0.9493, 2.9792, 0.9038, 0.9983, 0.0169, 0.0456, -1.0231, 0.9258, -1.0139, -1.1299, -1.2665, -0.9856, 0.0301, 0.2425, -0.9639, -0.1025, -1.0699, 1.9793, 0.1226, -0.1683, 0.8351, 0.6893, 2.0369, -0.9673, 0.0765, -0.9284, 2.9818, -2.9666, 2.8946, -0.2169, -3.0420, -0.0290, -0.0658, 1.9677, -1.7539, 0.0679, 0.9787, 3.0238, 1.9906, -0.9613, 0.8671, 0.6307, 1.9378, -1.1161, -0.4351, 1.0057, 1.9376, -0.8122, 1.9453, 0.0030, -0.9231, 0.0340, -0.1529, 0.9644, -2.0589, -0.1166, 0.9572, -0.8508, -2.6969, -1.9618, -0.8641, -0.9927, -1.0031, -2.8700, 0.9914, 0.9577, 1.8388, -2.0132, -2.8507, -1.9666, 1.3591, -3.0227, 0.9637, -0.2043, -0.9104, 3.0882, 0.0278, 1.9351, -3.0602, -1.0241, 0.9939, -0.0042, -0.7186, 0.2242, 2.0139, 1.9873, -1.1042, 1.9751, -1.9782, -0.6929, 0.9906, 0.9209]`

**Caso 2 — pior melhor-indivíduo (execução 18, f=694.05886):**

`[3.3822, -1.1564, 1.0410, -1.1216, 2.0739, 1.8959, 1.9676, 0.9766, -0.0793, 1.0680, 1.9466, -0.0980, -3.0239, 3.0583, -2.0810, 1.3019, 1.9075, -4.0650, 3.9455, -1.7551, -0.9348, -2.2196, 2.8520, -1.0557, -0.1309, 4.1113, -0.0977, 0.0435, -3.1769, -0.0927, 1.8586, 1.0290, -0.8721, -0.9190, 3.0750, -2.0448, -0.1020, -0.2441, -1.9464, -0.0270, -1.1325, 0.0061, -2.7079, 0.0652, 1.0497, -3.7652, -0.9729, -4.5370, 0.9721, -2.0593, -3.0093, 1.0179, 1.0025, -2.0031, 0.9731, 1.9028, 0.9203, -1.9498, -0.5136, 0.1503, 0.7388, -3.9699, -4.0504, -0.9713, 2.0675, -1.7073, -3.0894, 0.8241, -1.0630, 2.9773, -3.0297, 1.9381, -0.9066, 1.0528, 2.9778, -3.0396, 2.9230, -1.0827, -0.1921, 3.1263, 1.9041, 1.0127, -1.0375, 1.7856, 0.9276, -1.1467, 0.1336, 0.9636, 4.0319, 2.0489, 0.8825, 2.7173, -0.2107, 1.0479, -0.9928, -0.9502, -1.0052, 2.8088, 1.1558, -1.0621]`

### Teste t pareado entre os casos de DE

Os mesmos 30 valores de semente foram usados nos dois casos, formando pares por execução. Hipóteses: H0: C1 = C2; H1: C1 != C2. Teste bilateral, com α = 0,05:

| Comparação (C1 − C2) | t(29) | p-value | Diferença média |
|---|---:|---:|---:|
| Caso 1 − Caso 2 | 34.341 | 4.84326e-25 | 352.119 |

Decisão: Rejeita-se H0: há evidência de diferença estatisticamente significativa.

## Comparação com o algoritmo genético da AP1

A referência é o **Caso 2 da AP1** (crossover aritmético e mutação polinomial), que apresentou a menor média entre as duas configurações genéticas: 101.60758. As execuções do DE foram pareadas pelo mesmo número de semente usado na AP1, mantendo a população inicial aleatória comparável. A comparação testa H0: média(DE) = média(AP1) contra H1: médias diferentes, usando os 30 melhores fitness por execução; comparar apenas os dois melhores indivíduos isolados não permitiria um teste de significância.

O melhor fitness individual encontrado pelo DE foi 488.56994 (Caso 2, execução 28); na referência da AP1 foi 78.508436 (Caso 2, execução 19). Assim, o melhor valor observado pelo DE foi 6.22 vezes maior (pior, pois o problema é de minimização). Esses extremos são uma comparação descritiva; a significância é avaliada sobre os 30 pares.

| DE vs. AP1 Caso 2 | Média DE | Média AP1 | t(29) | p-value | p Holm | Diferença média (DE − AP1) |
|---|---:|---:|---:|---:|---:|---:|
| Caso 1 (DE/rand/1/bin) | 960.05096 | 101.60758 | 130.747 | 9.65836e-42 | 1.93167e-41 | 858.44338 |
| Caso 2 (DE/best/1/bin) | 607.93168 | 101.60758 | 51.3088 | 5.12206e-30 | 5.12206e-30 | 506.3241 |

Foi aplicado o ajuste de Holm às duas comparações com a AP1 para controlar o erro familiar. Com α = 0,05, Caso 1: rejeita-se H0 (p ajustado = 1.93167e-41); Caso 2: rejeita-se H0 (p ajustado = 5.12206e-30).

## Discussão e conclusão

A configuração DE com menor média foi **Caso 2 (DE/best/1/bin)**, com média 607.93 e desvio-padrão 55.67. O teste t entre os casos de DE resultou em p = 4.843e-25; a diferença entre essas estratégias é estatisticamente significativa a 5%.

A comparação com a AP1 deve ser interpretada em conjunto com as médias, os p-values ajustados e os melhores indivíduos. Um p-value acima do nível adotado significa que não se rejeita H0; não prova que os algoritmos sejam equivalentes. Os valores de p avaliam as configurações completas testadas, não um operador isolado.

A busca não atingiu o mínimo global 0: o melhor fitness obtido foi 488.57. Os resultados dependem de Np, F, Cr, do tratamento dos limites e do orçamento de 300 gerações. Também se utilizou apenas uma combinação de F e Cr para cada estratégia e 30 execuções. Uma investigação mais ampla poderia variar esses parâmetros, aumentar o número de repetições e inspecionar a distribuição das diferenças pareadas.

### Desafios de implementação

A mutação diferencial pode propor coordenadas fora do intervalo permitido; foi adotado clipping para manter cada indivíduo factível. No crossover binomial, foi necessário garantir que ao menos uma coordenada viesse do vetor doador, inclusive quando Cr é zero. Para a comparação entre atividades, os experimentos reutilizam as mesmas sementes e, portanto, as mesmas populações iniciais; a ordem dos casos de DE é aleatorizada em cada par.

## Reprodutibilidade

Resultados da AP1 lidos de `AP1\resultados\resultados.json`. O CSV contém as execuções individuais; o JSON preserva sementes, configurações, indivíduos extremos e testes estatísticos.
