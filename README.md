# Laboratório ECA/QCA multiframework

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/blob/main/COMPARA%C3%87%C3%83O_DE_AUT%C3%94MATOS_CELULARES_CL%C3%81SSICOS_E_QUANTICOS_Performance%2C_robustez_ao_ru%C3%ADdo_e_aplica%C3%A7%C3%B5es_.ipynb)
[![Validação](https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/actions/workflows/eca-confirmatory.yml/badge.svg)](https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/actions/workflows/eca-confirmatory.yml)

Experimento científico-didático que compara as regras ECA 30, 60 e 90 com sua incorporação reversível em **Qiskit, PennyLane e Cirq**. O **TensorFlow Quantum** é tratado corretamente como integração TensorFlow–Cirq, não como quarta implementação independente.

> Não se alega vantagem, supremacia ou aceleração quântica. Os tempos são microbenchmarks de simuladores clássicos.

## Autor

### Marcelo Claro Laranjeira — [@MarceloClaro](https://github.com/MarceloClaro)

Professor de Geografia e Pedagogo, pesquisador em cultura maker, educação e tecnologias computacionais.

- Crateús, Ceará, Brasil
- [GeoMaker](https://bit.ly/geomaker)
- [ORCID 0000-0001-8996-2887](https://orcid.org/0000-0001-8996-2887)
- [Instagram @marceloclaro.geomaker](https://www.instagram.com/marceloclaro.geomaker/)
- [Seguidores](https://github.com/MarceloClaro?tab=followers) · [Seguindo](https://github.com/MarceloClaro?tab=following)

As contagens sociais mudam; os links são preferíveis a números estáticos em metadados científicos.

## Modelo correto

Como uma regra ECA pode ser irreversível, `|x⟩→|F(x)⟩` não é unitária em geral. O laboratório preserva a entrada:

$$U_F|x\rangle|y\rangle=|x\rangle|y\oplus F(x)\rangle.$$

Isso é uma incorporação reversível de uma etapa ECA, não uma QCA física infinita completa.

## Implementação e evidência

| Eixo | Conteúdo |
|---|---|
| Clássico | Regras 30, 60 e 90; atualização síncrona; fronteira periódica |
| Ideal | Enumeração de bases, superposição, fidelidade, fase e entropia `x|y` |
| Frameworks | Três sínteses independentes: Qiskit, PennyLane e Cirq |
| TFQ | Expectativas `⟨Zᵢ⟩` dos circuitos Cirq em processo isolado |
| Ruído | Bit-flip lógico no registro de saída; BER e sucesso exato |
| Estatística | Unidades independentes, IC95% bootstrap e banda simultânea Bonferroni–Hoeffding |
| Desempenho | Warm-up excluído; ordem randomizada; mediana e IQR |
| Auditoria | Manifesto, CSVs, figuras 300 dpi, ZIP e SHA-256 |

O gate obrigatório é: ECA clássico → bases nos três SDKs → coerência → TFQ×Cirq → ruído → microbenchmark. Shots não são tratados como réplicas independentes.

## Executar no Colab

1. Abra o badge.
2. Selecione **CPU / sem acelerador**.
3. Mantenha `PROFILE="smoke"`.
4. Clique em **Ambiente de execução → Executar tudo**.

O notebook tem 21 células, 11 de código curto, e é reentrante. Não existe o antigo bloqueio `TEST_OPENED`; repetir **Executar tudo** no mesmo kernel é válido. TensorFlow/TFQ roda em subprocesso, reduzindo estado residual e memória no kernel principal.

### As duas ressalvas solucionadas

- HTTP `502` em `prod.colab.dev/api/kernelspecs` acontece antes do Python: é falha da VM/proxy do Colab. Desconecte a sessão, reconecte uma VM CPU e execute desde o início.
- Se `pip` for interrompido, descarte a VM parcialmente instalada e reconecte. Não continue células fora de ordem.

## Perfis congelados

| Parâmetro | `smoke` | `paper` |
|---|---:|---:|
| Células | 3 | 5 |
| Estados determinísticos | 8 | 32 |
| Estados de ruído | 2 | 8 |
| Níveis de bit-flip | 3 | 7 |
| Sementes-base | 2 | 5 |
| Shots | 512 | 4.096 |
| Bootstrap | 1.000 | 10.000 |

`smoke` é diagnóstico. Apenas `paper`, escolhido antes dos resultados e com gates aprovados, pode decidir H3/H4.

## Ambiente unificado

NumPy 2.0.2; Qiskit 2.5.2; Aer 0.17.2; PennyLane 0.45.1; Cirq Core 1.5.0; TensorFlow 2.18.1; TF-Keras 2.18.0; TFQ 0.7.6; pyparsing 3.2.5. TFQ fixa Cirq 1.5.0 e exige a linha legada TF-Keras; `TF_USE_LEGACY_KERAS=1` é definido antes do import.

## Execução local

```bash
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements-eca-colab.txt
python -m pytest -q tests/test_eca_*.py
python scripts/run_eca_experiment.py --profile smoke --output-dir eca_qca_results
python scripts/verify_eca_bundle.py eca_qca_results
```

## Pesquisa e artigo

- [SDD e rastreabilidade](docs/SDD.md)
- [Protocolo confirmatório](docs/PROTOCOL.md)
- [Plano do artigo e lacuna](docs/ARTICLE_PLAN.md)
- [Relatório de validação](docs/ECA_VALIDATION.md)

Validação v3.1: **425 testes aprovados**, execução integral reentrante e perfil confirmatório `paper` aprovado em H1–H4 com 840 unidades independentes de ruído. O protocolo registra a emenda, o commit congelado e a separação entre piloto e confirmação.

Rigor aumenta a publicabilidade, mas não garante Qualis A1 ou aceite. A área CAPES, o ciclo de avaliação e o periódico devem ser verificados na submissão.

Referências centrais: Wolfram (1983), Schumacher–Werner (2004), Pérez-Delgado–Cheung (2007), Qiskit, PennyLane e TFQ. DOIs, fontes e limites estão no protocolo e no SDD.

Código sob [GPL-3.0](LICENSE); citação em [CITATION.cff](CITATION.cff).
