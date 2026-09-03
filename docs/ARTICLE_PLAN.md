# Plano de artigo — benchmark reprodutível ECA/QCA

## Lacuna e contribuição

A literatura e os tutoriais nem sempre separam: atualização ECA irreversível; incorporação unitária com ancila; replicação entre SDKs; e integração TFQ–Cirq. O artigo propõe uma metodologia aberta com convenção explícita de qubits, bases exaustivas, superposição sensível a fase, unidade experimental independente, gate de evidência e pacote auditável — sem alegar vantagem quântica.

## Perguntas de pesquisa

| ID | Pergunta | Evidência |
|---|---|---|
| RQ1 | `U_F` recupera a etapa ECA em todas as bases estudadas? | Erro máximo de probabilidade |
| RQ2 | Qiskit, PennyLane e Cirq geram o mesmo estado? | Fidelidade e erro alinhado em fase |
| RQ3 | TFQ preserva as expectativas dos circuitos Cirq? | Erro em `⟨Zᵢ⟩` |
| RQ4 | O bit-flip reproduz BER `p` e sucesso `(1-p)^n`? | Média e IC95% de unidades independentes |
| RQ5 | Qual o custo descritivo das pilhas fixadas? | Mediana/IQR após warm-up |

## Plano confirmatório

Congelar commit, `PROTOCOL.md`, perfil `paper`, versões e análise antes da coleta. Unidade de ruído: `(regra, estado, p, semente-base)`. Os SDKs usam números aleatórios comuns dentro da unidade pareada e fluxo SHA-256 distinto entre unidades. Shots estimam a distribuição, não são réplicas.

RQ1–RQ3 são verificações determinísticas, sem p-valores. Em RQ4, agregar por unidade, relatar IC95% bootstrap e decidir compatibilidade por banda simultânea Bonferroni–Hoeffding com `α_F=0,05`. Não se exige que a teoria caia em todos os IC95% pontuais, pois isso inflaria o falso bloqueio familiar. Em RQ5, não remover outliers; excluir apenas o warm-up pré-declarado. Mudança pós-registro exige emenda datada, sementes disjuntas e nova coleta.

## Estrutura IMRaD

1. **Introdução:** irreversibilidade, QCA reversível, reprodutibilidade e lacuna.
2. **Métodos:** `f_r`, `F_r`, `U_F`, ordem canônica, síntese, TFQ, perfis, sementes e estatística.
3. **Resultados:** rastreabilidade, erros/fidelidade, entropia, ruído com IC e tempos.
4. **Discussão:** significado da equivalência, endianness, dependência TFQ–Cirq e validades.

Figuras mínimas: arquitetura/gates; BER e sucesso; microbenchmark. Tabelas mínimas: requisitos/RQs; versões; paridade; ameaças à validade.

## Antes da submissão

- executar `paper` em ambiente limpo e arquivar bundle/commit/logs com DOI;
- ampliar e documentar a busca bibliográfica por pares;
- disponibilizar dados brutos, código e política de exclusão;
- verificar escopo, ética, dados, uso de IA e Qualis vigente na área CAPES.

Rigor compatível com avaliação exigente não garante aceite nem classificação A1; isso depende do ciclo, área e decisão editorial.
