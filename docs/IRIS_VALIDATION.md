# Relatório de validação — classificador híbrido Iris

**Data:** 2 de setembro de 2026  
**Escopo:** notebook Cirq + regressão logística para Google Colab  
**SHA-256 do notebook:** `1c86caafb5d50c51b5cc44140e1366421795c7f4c5f958af2065bd5457d6b1e3`

## Decisão de validação

O notebook está **aprovado para execução didática e experimental no Colab**. As duas ressalvas identificadas na revisão anterior foram transformadas em gates verificáveis:

1. COBYLA somente libera a continuação quando `optimization.success` é verdadeiro;
2. o teste permanece selado até a confirmação e não é reutilizado no ensaio de robustez.

Essa aprovação não representa evidência de vantagem quântica nem validação confirmatória para publicação. O conjunto binário contém apenas 100 observações e a confirmação usa 20 casos.

## Rastreabilidade das correções

| Requisito | Implementação | Teste de aceitação | Resultado |
|---|---|---|---|
| IRIS-CNV-01 | `smoke`: meta pré-especificada `log-loss ≤ 0,04` | COBYLA retorna `success=True` | Aprovado em 10 avaliações |
| IRIS-CNV-02 | `full`: `tol=10⁻³`, limite de 160 avaliações | término pela redução do raio da região de confiança | Aprovado em 94 avaliações |
| IRIS-CNV-03 | registro de `status`, mensagem, avaliações e tolerância | presença no `manifest.json` | Aprovado |
| IRIS-BLD-01 | `X_test` e `y_test` só são materializados em `final-test` | análise AST das células | Aprovado |
| IRIS-BLD-02 | flag `TEST_OPENED` | segunda execução de `final-test` deve falhar | Aprovado |
| IRIS-RBS-01 | perturbação somente de `X_validation` | ausência de `X_test` na célula de robustez | Aprovado |
| IRIS-REP-01 | gerador determinístico | dois builds produzem o mesmo SHA-256 | Aprovado |
| IRIS-INT-01 | hashes dos CSVs e manifesto | recálculo e comparação | Aprovado |
| IRIS-DOC-01 | apresentação do projeto e identificação do autor | teste dos conteúdos, links e ORCID | Aprovado |

## Ambiente e resultados observados

| Item | Resultado |
|---|---:|
| Python | 3.12.13 |
| Cirq | 1.6.1 |
| SciPy | 1.17.0 |
| scikit-learn | 1.8.0 |
| Testes estáticos | 9/9 aprovados |
| Tempo `smoke` | 7,6 s |
| Tempo `full` | 25,7 s |
| Pico de memória `full` | 206,6 MiB |
| COBYLA `full` | `success=True`, 94 avaliações |
| Log-loss de validação inicial → final | 0,04920 → 0,02943 |
| Acurácia híbrida no teste | 1,000 |
| IC95% de Wilson da acurácia | [0,839; 1,000] |
| Log-loss híbrido no teste | 0,02162 |
| Log-loss do baseline clássico | 0,02556 |

Os tempos excluem o download inicial de dependências e dependem do hardware. O empate de acurácia entre o modelo híbrido e o baseline clássico impede qualquer conclusão de superioridade quântica.

## Procedimento de reprodução

No Colab:

1. desconectar e excluir o runtime antigo;
2. executar o perfil `smoke` desde a primeira célula;
3. verificar os gates `TDD`, `COBYLA` e `FINAL`;
4. reiniciar o runtime;
5. selecionar `full` e executar novamente desde o início;
6. baixar `iris_qml_results.zip` e conferir `sha256.json`.

Para validar o contrato estrutural do repositório:

```bash
python scripts/build_iris_colab.py
python -m unittest -v tests/test_iris_notebook.py
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
