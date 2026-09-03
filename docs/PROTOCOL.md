# Protocolo científico confirmatório

## 1. Pergunta central

Como comparar, de modo reproduzível e semanticamente justo, a atualização de autômatos celulares elementares clássicos com sua incorporação reversível em circuitos quânticos implementados em diferentes frameworks?

## 2. Hipóteses e desfechos

| ID | Hipótese | Desfecho primário | Regra de decisão |
|---|---|---|---|
| H1 | A incorporação reversível preserva a atualização clássica em entradas de base | Erro máximo de probabilidade | `≤ 10⁻¹²` para Qiskit/PennyLane e `≤ 10⁻⁷` para Cirq |
| H2 | Os três SDKs implementam o mesmo estado puro | Fidelidade Qiskit–PennyLane–Cirq | `≥ 1 − 2×10⁻⁷` |
| H3 | O canal bit-flip lógico é compatível com BER `p` | BER média e IC95% bootstrap | Desvio dentro da banda simultânea Bonferroni–Hoeffding |
| H4 | O sucesso completo é compatível com `(1−p)^n` em entrada de base | Frequência de bitstring correto | Desvio dentro da banda simultânea Bonferroni–Hoeffding |

A entropia de emaranhamento em `|+〉ⁿ|0〉ⁿ` e os tempos dos simuladores são desfechos secundários ou exploratórios.

## 3. Casos estudados

- Regra 30: não linear e associada a comportamento clássico complexo.
- Regra 60: atualização XOR entre esquerda e centro.
- Regra 90: atualização XOR entre esquerda e direita.
- Fronteira periódica.
- Perfil `smoke`: diagnóstico rápido, não publicável isoladamente.
- Perfil `paper`: `n=5`, todos os 32 estados na validação determinística; oito estados pré-fixados no ensaio de ruído, 4.096 shots, cinco sementes-base e 10.000 reamostragens bootstrap.

## 4. Pareamento, sementes e ordem

Cada combinação `(regra, estado inicial, p, semente-base)` é executada em todos os backends. Essa chave é a unidade de pareamento.

Uma semente de simulador deve ser derivada de modo determinístico por SHA-256 dessa chave. Isso evita reutilizar o mesmo fluxo pseudoaleatório em estados ou regras distintos. O valor derivado deve ser idêntico entre frameworks e registrado junto à semente-base.

Os três SDKs recebem números aleatórios comuns dentro da unidade pareada; o fluxo muda entre unidades. TFQ não participa como backend de ruído independente.

A ordem de backends pode permanecer fixa para depuração, com warm-up separado. Em um estudo de desempenho dedicado, a ordem deve ser randomizada por réplica e registrada.

## 5. Ruído

O canal primário é bit-flip independente somente no registrador de saída:

\[
\mathcal{E}_p(\rho)=(1-p)\rho+pX\rho X,\qquad 0\le p\le 0{,}5.
\]

Essa escolha evita comparar parâmetros com significados diferentes em canais depolarizantes dos SDKs. Ruído de portas nativas e modelos de hardware ficam para extensão separada e não devem ser misturados ao desfecho primário.

## 6. Estatística

1. H1 e H2 são verificações determinísticas e exaustivas; não se aplica teste de significância.
2. Para H3 e H4, cada linha `(estado, semente-base)` gera uma estimativa; os IC95% são obtidos por bootstrap percentil dessas réplicas.
3. Shots dentro da mesma execução estimam a distribuição, mas não são tratados como réplicas experimentais independentes.
4. Relatar estimativa, limites inferior e superior, número de estados, número de sementes, total de shots e valor teórico.
5. Não remover outliers de tempo. Relatar mediana e IQR após um warm-up.
6. Não escolher regras, níveis de ruído ou backends depois de observar os resultados.
7. `smoke` não decide H3/H4; somente `paper`, pré-especificado e com gates aprovados, habilita essas decisões.
8. Os IC95% bootstrap são estimativas descritivas, não um conjunto de testes simultâneos. Para H3/H4, sejam `K` todas as verificações BER e sucesso planejadas e `N` o número de ensaios Bernoulli no estrato. A meia largura simultânea é

   \[
   \varepsilon_N=\sqrt{\frac{\log(2K/\alpha_F)}{2N}},\qquad \alpha_F=0{,}05.
   \]

   A hipótese operacional passa quando `|estimativa − teoria| ≤ ε_N` em todos os estratos. Pela desigualdade de Hoeffding e pela união de Bonferroni, a probabilidade de ao menos uma rejeição puramente amostral é limitada por `α_F`, sem aproximação normal. Isso demonstra compatibilidade dentro da resolução planejada, não igualdade matemática do canal.

## 7. Critérios de exclusão

Uma execução é excluída apenas se houver exceção, versão divergente do manifesto, amostra com forma inválida ou interrupção do runtime. A exclusão deve ser registrada com backend, chave pareada, exceção e horário; não substituir silenciosamente por zero ou `NaN`.

## 8. Reprodutibilidade e auditoria

- Executar toda a suíte TDD antes do benchmark.
- Salvar manifesto, CSVs brutos e agregados, figuras em 300 dpi e hash SHA-256 de cada artefato.
- Registrar commit Git e se o repositório estava modificado.
- Preservar dados brutos; análises derivadas devem ser regeneráveis.
- Não inserir token IBM, senha ou outra credencial no notebook.
- Escolher `smoke` ou `paper` antes de observar os resultados.
- Executar TFQ em subprocesso CPU com `TF_USE_LEGACY_KERAS=1`.

### 8.1 Falhas do Colab e reentrância

HTTP 502 em `prod.colab.dev/api/kernelspecs`, antes do kernel, é falha de infraestrutura e não dado experimental. Substitua a sessão e recomece da primeira célula. O notebook não usa bloqueio global de abertura do teste e pode repetir **Executar tudo**.

## 9. Comparações permitidas

- Referência clássica × cada implementação quântica em base.
- Qiskit × PennyLane × Cirq por fidelidade do estado canônico.
- TFQ × Cirq somente como validação da camada de integração.
- BER observada × `p` teórico.
- Sucesso exato observado × `(1−p)^n`.
- Tempos entre simuladores apenas como descrição do runtime atual.

## 10. Linguagem permitida nas conclusões

Permitido: “as implementações apresentaram equivalência no domínio testado”; “o simulador X teve menor mediana neste ambiente”; “a entropia indica emaranhamento entre registros”.

Não permitido sem novo protocolo: “o computador quântico foi mais rápido”; “houve supremacia ou vantagem quântica”; “o resultado prova comportamento de uma QCA física”; “TFQ confirmou Cirq de forma independente”.

## 11. Extensão futura para QPU

Uma execução em hardware deve pré-especificar backend e calibração, mapeamento de qubits, semente de transpilation, shots, circuitos de calibração de leitura, modelo nulo, repetição temporal e política de mitigação. Resultados brutos e mitigados devem ser relatados separadamente na sequência ideal → shots → ruído → QPU.

## 12. Registro de emendas

**Emenda 1 — 2026-09-03, antes da coleta confirmatória definitiva.** Uma execução-piloto de engenharia revelou que exigir cobertura simultânea por todos os IC95% bootstrap pontuais era um critério de decisão inválido por multiplicidade. Essa execução foi classificada como piloto e excluída da confirmação. Antes de abrir os novos resultados, o critério foi substituído pela banda Bonferroni–Hoeffding acima e todas as cinco sementes do perfil `paper` foram trocadas por um conjunto disjunto (`104729`, `130363`, `155921`, `181081`, `206369`). Qualquer nova mudança exige outra emenda, novas sementes e nova coleta.

## 13. Referências essenciais

- WOLFRAM, S. Statistical mechanics of cellular automata. *Reviews of Modern Physics*, 55, 601–644, 1983. DOI: [10.1103/RevModPhys.55.601](https://doi.org/10.1103/RevModPhys.55.601).
- SCHUMACHER, B.; WERNER, R. F. Reversible quantum cellular automata. 2004. [arXiv:quant-ph/0405174](https://arxiv.org/abs/quant-ph/0405174).
- PÉREZ-DELGADO, C. A.; CHEUNG, D. Local unitary quantum cellular automata. *Physical Review A*, 76, 032320, 2007. DOI: [10.1103/PhysRevA.76.032320](https://doi.org/10.1103/PhysRevA.76.032320).
- FARRELLY, T. A review of quantum cellular automata. *Quantum*, 4, 368, 2020. DOI: [10.22331/q-2020-11-30-368](https://doi.org/10.22331/q-2020-11-30-368).
- JAVADI-ABHARI, A. et al. Quantum computing with Qiskit. 2024. [arXiv:2405.08810](https://arxiv.org/abs/2405.08810).
- BERGHOLM, V. et al. PennyLane: automatic differentiation of hybrid quantum-classical computations. [arXiv:1811.04968](https://arxiv.org/abs/1811.04968).
- BROUGHTON, M. et al. TensorFlow Quantum: a software framework for quantum machine learning. [arXiv:2003.02989](https://arxiv.org/abs/2003.02989).
