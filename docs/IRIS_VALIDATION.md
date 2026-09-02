# Relatório de validação — classificador híbrido Iris

**Data:** 2 de setembro de 2026  
**Escopo:** notebook Cirq + regressão logística para Google Colab  
**SHA-256 do notebook:** `c5f12d49ed94e4c216fac8075b6de02d5076be5b12daf8e99072818cb59ffe3e`

## Decisão de validação

O notebook está **aprovado para execução didática e experimental no Colab**. As duas ressalvas identificadas na revisão anterior foram transformadas em gates verificáveis:

1. COBYLA somente libera a continuação quando `optimization.success` é verdadeiro;
2. o teste permanece selado até a confirmação e não é reutilizado no ensaio de robustez.

A revisão célula a célula também corrigiu quatro falhas operacionais adicionais: atualização do `user-site` após instalação no mesmo processo, chamada incompatível da API de medição do Cirq 1.6.1, colisões entre sementes de ruído e inclusão de resíduos de execuções antigas no ZIP.

Essa aprovação não representa evidência de vantagem quântica nem validação confirmatória para publicação. O conjunto binário contém apenas 100 observações e a confirmação usa 20 casos.

## Diagnóstico do registro de execução fornecido

| Evidência observada na versão antiga | Defeito | Solução validada |
|---|---|---|
| TensorFlow 2.20 carregado embora TFQ estivesse indisponível | consumo de memória sem contribuição ao circuito Cirq | rota leve Cirq + regressão logística, sem importar TensorFlow/Keras |
| nomes `functional_258` e `dropout_147` | criação cumulativa de muitos modelos Keras no mesmo runtime | classificador pequeno e descartável; nenhum grafo Keras no objetivo COBYLA |
| atributos quânticos com forma `(70, 1)` para quatro qubits | observável reduzido incorretamente a um escalar | quatro expectativas `⟨Zᵢ⟩`, forma `(n, 4)`, testadas nos estados `|0⟩` e `|1⟩` |
| divisão apenas `70/30` e escolha da arquitetura pela acurácia de teste | vazamento confirmatório | partições estratificadas `60/20/20`; arquitetura e parâmetros usam somente validação |
| saída interrompida imediatamente após “Otimizando ... COBYLA” | forte indício de encerramento do kernel por pressão acumulada de memória, não exceção Python registrada | objetivo sem modelos Keras, limite explícito de avaliações e pico medido de 206,93 MiB |

O registro não contém uma mensagem do sistema operacional, portanto a causa exata da desconexão antiga não pode ser provada apenas pelo texto. A numeração cumulativa dos objetos Keras e o ponto da interrupção, porém, são consistentes com esgotamento do runtime; a reprodução corrigida elimina esse mecanismo e conclui os dois perfis.

## Rastreabilidade das correções

| Requisito | Implementação | Teste de aceitação | Resultado |
|---|---|---|---|
| IRIS-CNV-01 | `smoke`: meta pré-especificada `log-loss ≤ 0,04` | COBYLA retorna `success=True` | Aprovado em 10 avaliações |
| IRIS-CNV-02 | `full`: `tol=10⁻³`, limite de 160 avaliações | término pela redução do raio da região de confiança | Aprovado em 94 avaliações |
| IRIS-CNV-03 | registro de `status`, mensagem, avaliações e tolerância | presença no `manifest.json` | Aprovado |
| IRIS-BLD-01 | `X_test` e `y_test` só são materializados em `final-test` | análise AST das células | Aprovado |
| IRIS-BLD-02 | cache por número de execução | repetir `final-test` não incrementa aberturas nem altera métricas | Aprovado |
| IRIS-BLD-03 | limpeza transitória + `_IRIS_RUN_SEQUENCE` | duas passagens completas no mesmo kernel | Aprovado: 22/22 células |
| IRIS-RBS-01 | perturbação somente de `X_validation` | ausência de `X_test` na célula de robustez | Aprovado |
| IRIS-RBS-02 | `SeedSequence([seed, nível, réplica])` | unicidade das sementes em todas as réplicas | Aprovado |
| IRIS-REP-01 | gerador determinístico | dois builds produzem o mesmo SHA-256 | Aprovado |
| IRIS-INT-01 | hashes dos CSVs e manifesto | recálculo e comparação | Aprovado |
| IRIS-INT-02 | lista fechada de membros do ZIP | arquivo residual não pode entrar no pacote | Aprovado |
| IRIS-DOC-01 | apresentação do projeto e identificação do autor | teste dos conteúdos, links e ORCID | Aprovado |

## Auditoria de cada célula de código

Execução `full` limpa, na ordem efetiva do notebook:

| Nº | ID da célula | Contrato principal | Tempo (s) | Pico RSS (MiB) | Resultado |
|---:|---|---|---:|---:|---|
| 1 | `setup` | Python, versões e pós-instalação importável | 0,045 | 15,8 | Aprovado |
| 2 | `imports-config` | imports, semente e perfil imutável | 1,548 | 195,2 | Aprovado |
| 3 | `data` | forma, balanceamento, disjunção, limpeza e teste selado | 0,099 | 196,0 | Aprovado |
| 4 | `circuits` | 4 qubits, 8 parâmetros, 3 topologias sem medição | 0,030 | 197,7 | Aprovado |
| 5 | `features-tests` | observáveis físicos, erros de forma e determinismo | 0,031 | 198,2 | Aprovado |
| 6 | `architecture-selection` | três ansätze e seleção só na validação | 0,849 | 199,1 | Aprovado |
| 7 | `optimization` | histórico finito, limites e `success=True` | 16,129 | 200,0 | Aprovado |
| 8 | `landscape` | grade completa e perdas finitas | 2,666 | 202,2 | Aprovado |
| 9 | `robustness` | validação apenas e sementes únicas | 1,846 | 204,6 | Aprovado |
| 10 | `final-test` | cache idempotente, métricas e IC95% | 3,359 | 206,1 | Aprovado |
| 11 | `artifacts` | lista fechada, hashes e ZIP exato | 0,007 | 206,6 | Aprovado |

As sete células Markdown também foram verificadas quanto a ordem, apresentação, instruções, protocolo, equações e limites. Todas as 18 células têm identificadores únicos; as 11 células executáveis estão sem outputs persistidos e encerram com um gate explícito.

## Ambiente e resultados observados

| Item | Resultado |
|---|---:|
| Python | 3.12.13 |
| Cirq | 1.6.1 |
| SciPy | 1.17.0 |
| scikit-learn | 1.8.0 |
| Testes estáticos | 15/15 aprovados |
| Células executáveis `smoke` | 11/11 aprovadas |
| Células executáveis `full` | 11/11 aprovadas |
| Duas passagens `smoke` no mesmo kernel | 22/22 aprovadas em 13,46 s |
| Idempotência da célula final | aprovada nas duas passagens; nenhuma reabertura |
| Tempo `full` | 26,60 s |
| Pico de memória `full` | 208,11 MiB |
| COBYLA `full` | `success=True`, 94 avaliações |
| Log-loss de validação inicial → final | 0,04920 → 0,02943 |
| Acurácia híbrida no teste | 1,000 |
| IC95% de Wilson da acurácia | [0,839; 1,000] |
| Log-loss híbrido no teste | 0,02162 |
| Log-loss do baseline clássico | 0,02556 |

Os tempos excluem o download inicial de dependências e dependem do hardware. O empate de acurácia entre o modelo híbrido e o baseline clássico impede qualquer conclusão de superioridade quântica.

## Procedimento de reprodução

No Colab:

1. selecionar o runtime padrão CPU, sem GPU;
2. manter `PROFILE = "smoke"` e clicar em **Executar tudo**;
3. verificar os gates `TDD`, `COBYLA`, `TESTE FINAL` e `ARTEFATOS`;
4. opcionalmente selecionar `full` e clicar novamente em **Executar tudo**;
5. baixar `iris_qml_results.zip` e conferir `sha256.json`.

A primeira passagem no kernel recebe o escopo `confirmatory_first_session_run`. Passagens completas posteriores recebem `technical_rerun_same_kernel`. Repetir apenas `final-test` produz `reused_without_test_reopening` e conserva o contador de abertura.

Para validar o contrato estrutural do repositório:

```bash
python scripts/build_iris_colab.py
python -m unittest -v tests/test_iris_notebook.py
python scripts/validate_iris_notebook.py --profile smoke --repeat-run-all --allow-install --report iris_smoke_report.json
```

## Limites científicos remanescentes

- a robustez na validação é pós-seleção e permanece exploratória;
- uma conclusão confirmatória requer validação cruzada aninhada e sementes externas;
- Setosa × Versicolor é um problema simples e não representa desempenho geral em QML;
- simulação ideal de quatro qubits não representa execução em hardware quântico;
- o protocolo não autoriza alegações de aceleração, supremacia ou vantagem quântica.

## Referências

- ZHANG, Z. *PRIMA: Reference Implementation for Powell's Methods with Modernization and Amelioration*. Zenodo, 2023. DOI: [10.5281/zenodo.8052654](https://doi.org/10.5281/zenodo.8052654).
- SCIPY COMMUNITY. *minimize(method='COBYLA')*. SciPy API Reference. Disponível em: <https://docs.scipy.org/doc/scipy/reference/optimize.minimize-cobyla.html>. Acesso em: 2 set. 2026.
- GOOGLE QUANTUM AI. *Cirq documentation*. Disponível em: <https://quantumai.google/cirq>. Acesso em: 2 set. 2026.
