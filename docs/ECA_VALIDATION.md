# Validação do laboratório ECA/QCA v3.1

Data da validação: **2026-09-03**.

## Proveniência confirmatória

O código, o perfil `paper`, a Emenda 1, as cinco novas sementes e a regra simultânea Bonferroni–Hoeffding foram congelados localmente no commit `ae8e4ab0cc046490803b7337d95d5b02ab544787`, árvore Git `610f4ba6eaa3ee44a2987a3b1d222fcc059b98f6`, antes da execução confirmatória definitiva. O manifesto registra esse commit, a branch `main` e `dirty=false`. A mesma árvore foi publicada no GitHub como commit `2fafcec2f454943a4c82c636cbc2c28fcd2110f6`, seguida do relatório pós-coleta em `7f00b2f387b8aeb6d10b272ab71d1316e0767dfc`. Os resultados e sementes da execução-piloto não foram reutilizados.

Sementes confirmatórias: `104729`, `130363`, `155921`, `181081`, `206369`. Critérios: regras 30/60/90; involução de `U_F`; bases exaustivas; fidelidade `≥1−2×10⁻⁷`; TFQ×Cirq `≤2×10⁻⁵`; sementes independentes; dez artefatos SHA-256; notebook de 21 células/11 códigos e execução reentrante.

## Resultado

- TDD: **425 testes aprovados** em 3,31 s.
- `smoke`: portão técnico aprovado; H1 e H2 aprovadas; H3/H4 corretamente não avaliadas nesse perfil.
- `paper`: portão técnico aprovado; **H1, H2, H3 e H4 aprovadas**.
- Auditoria: **10/10 artefatos** verificados por SHA-256 em cada perfil.
- TFQ disponível e validado como integração TensorFlow–Cirq, não como quarto backend independente.

| Métrica | `smoke` | `paper` |
|---|---:|---:|
| Paridades em base computacional | 72 | 288 |
| Comparações de vetores de estado | 81 | 297 |
| Verificações de estados coerentes | 9 | 9 |
| Observáveis TFQ×Cirq | 81 | 495 |
| Registros de ruído | 108 | 2.520 |
| Unidades independentes de ruído | 36 | 840 |
| Registros de benchmark | 36 | 360 |
| Fidelidade mínima entre frameworks | 0,9999999999999998 | 0,9999999999999999 |
| Maior erro de probabilidade em base | 5,77 × 10⁻¹⁵ | 9,77 × 10⁻¹⁵ |
| Maior erro alinhado por fase | 2,89 × 10⁻¹⁵ | 4,88 × 10⁻¹⁵ |
| Maior erro de observável TFQ | 1,20 × 10⁻¹³ | 1,23 × 10⁻¹³ |

No perfil `paper`, o maior desvio BER foi `6,76×10⁻⁴`, ou 29,65% da respectiva meia largura simultânea; o maior desvio de sucesso exato foi `2,86×10⁻³`, ou 56,14% da meia largura. Portanto, todos os 126 cheques planejados ficaram dentro das bandas com `α_F=0,05`. Isso sustenta compatibilidade na resolução amostral declarada, não igualdade matemática.

Hashes dos bundles: `361aac11f6de4ccaa7e4400abf3be3384b4898259571ec3ac96b8ebcccf5df18` (`smoke`) e `4b273e6a490dfec56d87a892f3f18eca6e53295c75945bb417660afba9d7800b` (`paper`).

## Notebook e ambiente

- Estrutura: **21 células**, sendo **11 de código**, com projeto, autoria e ORCID.
- Duas execuções integrais consecutivas no mesmo processo concluíram sem `TEST_OPENED`: 13,34 s e 10,28 s.
- Cada execução interna repetiu os 425 testes; pico de memória residente: **482.272 KiB** (aprox. 471 MiB).
- Matriz: Python 3.12; Qiskit 2.5.2; Qiskit Aer 0.17.2; PennyLane 0.45.1; Cirq Core 1.5.0; TensorFlow 2.18.1; TF-Keras 2.18.0; TensorFlow Quantum 0.7.6.
- Execução em CPU e TFQ isolado em subprocesso, reduzindo conflitos de ABI e estado residual no kernel do Colab.

## Limitações

- `U_F` não é uma QCA física infinita completa.
- TFQ reutiliza Cirq.
- O canal é lógico, não um modelo de dispositivo.
- Tempos de simulador não demonstram vantagem quântica.
- `smoke` não decide H3/H4; isso cabe ao perfil `paper` congelado.
