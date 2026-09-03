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

Cada combinação `(regra, estado inicial, p, semente-base)` define uma unidade de ruído. Uma realização NumPy é associada às etiquetas dos três backends cuja equivalência ideal foi validada. Não há três execuções nativas de canal por unidade.

Uma semente de simulador deve ser derivada de modo determinístico por SHA-256 dessa chave. Isso evita reutilizar o mesmo fluxo pseudoaleatório em estados ou regras distintos. O valor derivado deve ser idêntico entre frameworks e registrado junto à semente-base.

As três linhas pareadas recebem os mesmos BER e sucesso exato, porque representam a mesma realização do canal lógico. O fluxo muda entre unidades. TFQ não participa como backend de ruído independente. Em `paper`, 2.520 linhas representam 840 unidades/fluxos, não 2.520 réplicas independentes.

A ordem dos backends no microbenchmark implementado é randomizada por réplica e registrada; o warm-up é separado. A medida inclui construção e simulação, mas não importação dos SDKs nem inicialização do processo TFQ.

## 5. Ruído

O canal primário é bit-flip independente somente no registrador de saída:

\[
\mathcal{E}_p(\rho)=(1-p)\rho+pX\rho X,\qquad 0\le p\le 0{,}5.
\]

Essa escolha evita comparar parâmetros com significados diferentes em canais depolarizantes dos SDKs. Ruído de portas nativas e modelos de hardware ficam para extensão separada e não devem ser misturados ao desfecho primário.

Nas entradas de base, amostrar flips Bernoulli independentes em NumPy reproduz a distribuição de medição desse canal na saída ideal. O ensaio mede o amostrador e as previsões analíticas, **não** a implementação de ruído nativo de cada SDK, nem a evolução de estados em superposição sob ruído. Isso é uma limitação de construto, não uma evidência de independência entre frameworks.

## 6. Estatística

1. H1 enumera todos os estados de entrada `x` do domínio, com `y=0`; H2 compara essas saídas e a superposição uniforme especificada. Não se aplica teste de significância. Não se alega tomografia exaustiva do operador em todos os estados conjuntos.
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

   No desenho congelado, `K=126` no perfil paper inclui as etiquetas pareadas; a união continua válida sob dependência, mas é conservadora. `N` conta flips de bits para BER e shots para sucesso exato sob o modelo Bernoulli independente, não réplicas de hardware. O bootstrap reamostra unidades; suas sementes por etiqueta foram preservadas. A figura v3.2 exibe somente o representante Qiskit do canal comum, por regra, sem fazer média de ICs entre etiquetas.

## 7. Critérios de exclusão

Uma execução é excluída apenas se houver exceção, versão divergente do manifesto, amostra com forma inválida ou interrupção do runtime. A exclusão deve ser registrada com backend, chave pareada, exceção e horário; não substituir silenciosamente por zero ou `NaN`.

## 8. Reprodutibilidade e auditoria

- Executar toda a suíte TDD antes do benchmark.
- Salvar manifesto, CSVs brutos e agregados, figuras em 300 dpi e hash SHA-256 de cada artefato.
- Registrar commit Git e se o repositório estava modificado.
- No esquema 3.2, registrar também a árvore Git; verificar hashes dos 10 artefatos e dos dois JSONs de metadados. O recibo do ZIP é externo e o relatório arquivado é idêntico ao relatório em disco.
- Preservar dados brutos; análises derivadas devem ser regeneráveis.
- Não inserir token IBM, senha ou outra credencial no notebook.
- Escolher `smoke` ou `paper` antes de observar os resultados.
- Executar TFQ em subprocesso CPU com `TF_USE_LEGACY_KERAS=1`.

### 8.1 Falhas do Colab e reentrância

HTTP 502 em `prod.colab.dev/api/kernelspecs`, antes do kernel, é falha de infraestrutura e não dado experimental. Substitua a sessão e recomece da primeira célula. O notebook não usa bloqueio global de abertura do teste e pode repetir **Executar tudo**.

A v3.2 usa um venv científico separado do kernel da interface, com processos CPU. Cada execução recebe uma pasta própria; resultados completos não são sobrescritos. A validação em namespace Python é explicitamente distinta da execução em kernel Jupyter/Colab. Uma falha de permissão ao iniciar Jupyter não pode ser registrada como teste de notebook aprovado.

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

**Errata de implementação e transparência v3.2 — 2026-09-03, pós-coleta.** A descrição anterior sugeria execuções nativas de ruído; o código já usava uma amostra NumPy comum. A presente versão corrige a descrição e adiciona identificação de unidade, amostrador e pareamento. Corrige também o campo que chamava a referência analítica de Cirq: agora os dois comparadores são calculados e registrados separadamente. Foram corrigidos o gate incompleto de TFQ, a validação de bits e a consistência do ZIP. Melhorias de UX/isolamento não alteram hipóteses, estados, probabilidades, sementes ou critérios da Emenda 1. As execuções desta versão são **reproduções técnicas pós-coleta**, não uma confirmação nova. Uma mudança de hipótese/desenho ou nova inferência exigirá protocolo próprio e dados novos.

## 13. Referências essenciais

- WOLFRAM, S. Statistical mechanics of cellular automata. *Reviews of Modern Physics*, 55, 601–644, 1983. DOI: [10.1103/RevModPhys.55.601](https://doi.org/10.1103/RevModPhys.55.601).
- SCHUMACHER, B.; WERNER, R. F. Reversible quantum cellular automata. 2004. [arXiv:quant-ph/0405174](https://arxiv.org/abs/quant-ph/0405174).
- PÉREZ-DELGADO, C. A.; CHEUNG, D. Local unitary quantum cellular automata. *Physical Review A*, 76, 032320, 2007. DOI: [10.1103/PhysRevA.76.032320](https://doi.org/10.1103/PhysRevA.76.032320).
- FARRELLY, T. A review of quantum cellular automata. *Quantum*, 4, 368, 2020. DOI: [10.22331/q-2020-11-30-368](https://doi.org/10.22331/q-2020-11-30-368).
- JAVADI-ABHARI, A. et al. Quantum computing with Qiskit. 2024. [arXiv:2405.08810](https://arxiv.org/abs/2405.08810).
- BERGHOLM, V. et al. PennyLane: automatic differentiation of hybrid quantum-classical computations. [arXiv:1811.04968](https://arxiv.org/abs/1811.04968).
- BROUGHTON, M. et al. TensorFlow Quantum: a software framework for quantum machine learning. [arXiv:2003.02989](https://arxiv.org/abs/2003.02989).
