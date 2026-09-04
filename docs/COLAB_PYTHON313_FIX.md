# Correção Colab/Python 3.13 — v3.2.1

> Registro histórico: a v3.2.1 falhou em uma sessão Colab ao criar seu venv auxiliar. Use a [correção v3.2.2](COLAB_BOOTSTRAP_V322.md), que remove essa dependência. As evidências abaixo pertencem à versão anterior e não equivalem à validação da atualização.

## Diagnóstico

O erro `Esta matriz TFQ exige Python 3.11/3.12` é esperado quando o kernel fornecido pelo Colab está em Python 3.13. O TensorFlow Quantum suporta Python 3.10–3.12 e depende diretamente de Cirq; tentar forçar seus wheels no 3.13 produziria um ambiente inconsistente.

## Solução implementada

1. O kernel continua leve e permanece no Python oferecido pelo Colab.
2. O instalador procura Python 3.11/3.12 no sistema.
3. Se encontrar somente Python 3.13, cria `/content/.eca-uv-bootstrap-v321` usando o Python do kernel.
4. Instala somente `uv==0.12.9` nesse bootstrap isolado.
5. O uv baixa CPython 3.12 gerenciado para `/content/.eca-python-v321`.
6. O ambiente científico é criado em `/content/.venv-eca-v321` e recebe as versões fixadas do projeto.
7. TDD, Qiskit, PennyLane, Cirq, TensorFlow e TFQ continuam em subprocessos CPU.

Não há reinicialização do kernel, instalação de sistema, GPU, API paga ou GitHub Actions. Os diretórios desaparecem quando a VM Colab é descartada. O download exige internet e espaço temporário da própria sessão.

## Como executar após ter visto o erro antigo

1. Feche a aba antiga ou use **Arquivo → Abrir notebook → GitHub**.
2. Abra novamente o notebook da branch `main`; confirme que o cabeçalho mostra **v3.2.1**.
3. **Baixe antes quaisquer resultados ou arquivos importantes da sessão**, pois a exclusão da VM apaga seu armazenamento temporário. Depois, para evitar o checkout antigo em memória, escolha **Ambiente de execução → Desconectar e excluir ambiente de execução**.
4. Reconecte com **CPU / nenhum acelerador**.
5. Mantenha `PROFILE="smoke"` e use **Executar tudo**.
6. Na etapa 2, se não houver Python compatível no sistema, espere a mensagem `obtendo Python 3.12 gerenciado e isolado`. Ao final, `Python científico:` deve apontar para o venv separado. A etapa só avança após verificar as versões.

Se o download for interrompido, reexecute a etapa de ambiente. Caso precise descartar a VM, salve primeiro seus arquivos. Não execute as células seguintes enquanto a matriz de versões não for confirmada.

## Segurança e reprodutibilidade

- O bootstrap vem do pacote PyPI fixado `uv==0.12.9`; não executa um script remoto por pipe.
- O parâmetro `--no-bin` impede a instalação de atalhos Python fora dos diretórios isolados; o Python padrão do usuário não é substituído.
- O uv gerencia a obtenção das distribuições CPython do projeto Astral `python-build-standalone`; a versão efetivamente usada fica no manifesto.
- A versão patch efetivamente obtida (3.12.x) é registrada pelo manifesto.
- A matriz científica continua integralmente fixada em `requirements-eca-colab.txt`.
- O checkout mudou de `eca-qca-lab-v32` para `eca-qca-lab-v321`, impedindo que uma sessão antiga reutilize silenciosamente o instalador defeituoso.

## Validação da correção

Em 3 de setembro de 2026, após a alteração:

- 12 testes de UX/ambiente aprovados;
- 467 testes ECA aprovados;
- 482 testes da suíte completa aprovados;
- `smoke` aprovado, com 72 verificações de base, 81 pares de estados e 81 observáveis TFQ;
- ZIP smoke verificado: 10 artefatos científicos e 2 metadados cobertos por hash;
- 11 células executadas duas vezes no mesmo namespace, com pastas distintas.

Em 4 de setembro de 2026, após acrescentar `--no-bin` ao instalador, foram reexecutados os testes de UX/ambiente e contratos do notebook: **21 aprovados**. A geração determinística do notebook e a compilação dos arquivos Python alterados também passaram. A suíte científica completa não foi reexecutada após esse ajuste final do comando de instalação.

O ambiente local dessa validação usava Python 3.12.13. Por isso, o ramo de download a partir de um kernel 3.13 foi validado por testes isolados das decisões, comandos, diretórios e retorno do interpretador, mas **a obtenção real em uma VM Colab/Python 3.13 continua pendente da sua próxima execução**. Isso está registrado para não confundir teste unitário com validação de integração no Colab.

## Fontes técnicas

- [TensorFlow Quantum — instalação e suporte Python](https://www.tensorflow.org/quantum/install)
- [Astral uv — instalar e gerenciar versões Python](https://docs.astral.sh/uv/guides/install-python/)
- [Astral uv — métodos oficiais de instalação](https://docs.astral.sh/uv/getting-started/installation/)
