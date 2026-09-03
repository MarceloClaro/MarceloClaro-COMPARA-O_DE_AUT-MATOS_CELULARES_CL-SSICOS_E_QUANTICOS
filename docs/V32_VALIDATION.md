# Validação técnica v3.2 — 3 de setembro de 2026

**463 testes ECA aprovados; 478 testes na suíte completa.** Os perfis smoke e paper foram executados localmente com os SDKs reais. As 11 células de código passaram duas vezes no mesmo namespace Python, com pastas diferentes. **Não se comprovou execução em kernel Colab/Jupyter nesta revisão.**

Esta é uma reprodução de engenharia pós-coleta: preserva o desenho e as sementes da Emenda 1. Não é uma confirmação independente, prova de novidade ou garantia de aceite editorial.

## 1. Código e rastreabilidade

- Commit local congelado antes da revalidação: `d2a734b4492c79474e20415f2dfca6022c58fab3`.
- [Commit equivalente publicado](https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/commit/40284806648a7ed914ed131360bf505318df6f32): `40284806648a7ed914ed131360bf505318df6f32`.
- Árvore Git idêntica nos dois commits: `a76b54670ec6d1400ced032451c2fd92b1a1015b`.
- Os manifestos registram o commit local, essa árvore e `dirty=false`. A publicação do relatório acrescenta documentação/evidências, sem alterar o código validado.
- Ambiente: Linux x86_64, Python 3.12.13; matriz fixada em requirements-eca-colab.txt. `pip check` não apontou incompatibilidades.

## 2. Correções comprovadas por regressão

| Problema | Correção e teste |
|---|---|
| Frações e strings convertidas silenciosamente em bits | Núcleo e três adaptadores rejeitam entradas que não são bits inteiros |
| Referência analítica rotulada como Cirq | TFQ é comparado ao simulador Cirq real e à referência analítica; um comparador deliberadamente errado falha |
| H3/H4 habilitadas com gate TFQ incompleto | Flags confirmatórias dependem de todos os gates |
| Relatório em disco divergente do ZIP | Relatório imutável; hash do ZIP em recibo externo |
| Metadados fora da verificação de hashes | Manifesto e relatório incluídos nos checksums; adulteração é detectada |
| ZIP aceitando nomes inesperados | Conjunto fechado, sem extração; membros extras/duplicados são rejeitados |
| Resultados sobrescritos | Coleta recusa pasta com artefatos anteriores; notebook separa execuções |
| UI carregando a pilha científica | Etapas em subprocessos; teste verifica ausência dos SDKs no processo da interface |
| Smoke apresentado como confirmação | Painel mostra H3/H4 não avaliadas |
| Ruído parecendo independente por SDK | CSV/manifesto/protocolo identificam o canal NumPy compartilhado |

Os testes de regressão foram introduzidos antes das respectivas correções, com falhas observadas, e depois passaram. [Log ECA](../validation/v3.2/pytest_eca.txt) · [Resumo da suíte completa](../validation/v3.2/evidence_index.json).

## 3. Resultados reproduzidos

| Indicador | smoke | paper |
|---|---:|---:|
| Verificações de base por SDK | 72 | 288 |
| Comparações de pares de vetores | 81 | 297 |
| Casos coerentes por SDK | 9 | 9 |
| Observáveis TFQ comparados | 81 | 495 |
| Linhas de ruído pareadas | 108 | 2.520 |
| Unidades / fluxos distintos | 36 / 36 | 840 / 840 |
| Execuções nativas de ruído por SDK | 0 | 0 |
| Observações de microbenchmark | 36 | 360 |
| Fidelidade mínima entre SDKs | 0,9999999999999998 | 0,9999999999999999 |
| Maior erro de probabilidade | 5,7732 × 10⁻¹⁵ | 9,7700 × 10⁻¹⁵ |
| Maior erro TFQ × Cirq | 1,1990 × 10⁻¹³ | 1,2262 × 10⁻¹³ |
| Gate técnico | Aprovado | Aprovado |
| H3/H4 | Não avaliadas | Compatíveis com as bandas planejadas |

Em paper, H1–H4 passam seus critérios operacionais. Isso verifica o baseline no domínio definido; o ensaio de ruído valida um amostrador do canal de saída, não fidelidade de ruído nativo nem comportamento de QPU. Não se somam as etiquetas pareadas como novas réplicas.

[Relatório smoke](../validation/v3.2/smoke_report.json) · [Relatório paper](../validation/v3.2/paper_report.json).

## 4. Notebook: resultado e ressalva obrigatória

O notebook contém 21 células, sendo 11 de código. O modo explícito namespace executou todas duas vezes, no mesmo processo, com 463 testes ECA em cada passagem. As pastas são distintas; não houve SDK científico importado no processo da interface. Tempos locais: aproximadamente 23,0 s e 22,5 s, **sem instalar dependências do zero**. Esses tempos não são previsão para Colab.

[Relatório célula a célula](../validation/v3.2/notebook_validation.json) · [Passagem 1](../validation/v3.2/notebook_run1.txt) · [Passagem 2](../validation/v3.2/notebook_run2.txt).

A tentativa de iniciar kernel Jupyter real foi bloqueada pelo ambiente de validação: `Operation not permitted` na resolução/comunicação de interfaces, seguida de `Kernel died before replying to kernel_info`. A falha foi preservada em [jupyter_attempt_failed.json](../validation/v3.2/jupyter_attempt_failed.json); ocorreu antes da execução de qualquer célula. Não houve tentativa de contornar a restrição.

Portanto permanecem **pendentes**: instalação isolada em uma VM Colab limpa, execução via kernel Colab, renderização/interações do frontend e download pelo navegador. O modo namespace testa o Python, não essas integrações. Capa e quatro figuras produzidas foram inspecionadas visualmente como arquivos locais.

## 5. Como reproduzir

Com a matriz instalada em venv Python 3.12:

```bash
python scripts/validate_eca_all.py --profile paper --notebook --notebook-executor namespace
python -m pytest -q tests
```

Para testar o kernel Jupyter em um ambiente que o permita:

```bash
python scripts/validate_eca_all.py --profile smoke --notebook
```

Para validar a integração Google, abra o notebook pelo botão do README em uma sessão Colab CPU limpa e use Executar tudo. Um HTTP 502 anterior ao kernel é indisponibilidade de infraestrutura; não há correção executável em uma célula que ainda não pode rodar.

## 6. Pacotes de evidência e integridade

- [ZIP smoke](../validation/v3.2/eca_qca_smoke_bundle.zip) — SHA-256 `b6a39864b36d1a709565fa3ed053d63ccc9399262e821dd582887b216e686692`.
- [ZIP paper](../validation/v3.2/eca_qca_paper_bundle.zip) — SHA-256 `1ae12f1ed2d2eed90392c17387214f93f503ccb2dce928ca1dfed88da212b4dc`.

Cada ZIP passou pelo verificador: **10 artefatos científicos + 2 JSONs de metadados por hash**, em um conjunto de 13 membros incluindo o arquivo de checksums. Os ZIPs contêm os CSVs brutos, agregados e duas figuras em 300 dpi. O relatório interno é idêntico ao externo. Hashes verificam integridade contra uma referência; não substituem auditoria científica ou autenticação de autoria.

## 7. Custos e GitHub Actions

O único workflow ativo foi movido para docs/workflows/eca-confirmatory.yml.example, e o badge de CI foi removido. Esse exemplo não executa no GitHub Actions. A validação é manual/local ou no Colab; não se chama API paga nem QPU. Nenhuma configuração de cobrança foi modificada, e a remoção não cancela débitos ou assinaturas preexistentes. Colab gratuito continua sujeito aos limites do provedor.
