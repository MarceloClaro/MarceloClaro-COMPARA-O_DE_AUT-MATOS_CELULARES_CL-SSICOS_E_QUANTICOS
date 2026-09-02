# Protocolo científico confirmatório

## 1. Pergunta central

Como comparar, de modo reproduzível e semanticamente justo, a atualização de autômatos celulares elementares clássicos com sua incorporação reversível em circuitos quânticos implementados em diferentes frameworks?

## 2. Hipóteses e desfechos

| ID | Hipótese | Desfecho primário | Regra de decisão |
|---|---|---|---|
| H1 | A incorporação reversível preserva a atualização clássica em entradas de base | Erro máximo de probabilidade | `≤ 10⁻¹²` para Qiskit/PennyLane e `≤ 10⁻⁷` para Cirq |
| H2 | Os três SDKs implementam o mesmo estado puro | Fidelidade Qiskit–PennyLane–Cirq | `≥ 1 − 2×10⁻⁷` |
| H3 | O canal bit-flip lógico produz BER igual a `p` | BER média e IC95% bootstrap | Relatar estimativa, desvio e IC sem ajuste pós-hoc |
| H4 | O sucesso do estado completo segue `(1−p)^n` em entrada de base | Frequência de bitstring correto | Comparar estimativa e IC95% ao valor teórico |

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

## 7. Critérios de exclusão

Uma execução é excluída apenas se houver exceção, versão divergente do manifesto, amostra com forma inválida ou interrupção do runtime. A exclusão deve ser registrada com backend, chave pareada, exceção e horário; não substituir silenciosamente por zero ou `NaN`.

## 8. Reprodutibilidade e auditoria

- Executar toda a suíte TDD antes do benchmark.
- Salvar manifesto, CSVs brutos e agregados, figuras em 300 dpi e hash SHA-256 de cada artefato.
- Registrar commit Git e se o repositório estava modificado.
- Preservar dados brutos; análises derivadas devem ser regeneráveis.
- Não inserir token IBM, senha ou outra credencial no notebook.
- Escolher `smoke` ou `paper` antes de observar os resultados.

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
