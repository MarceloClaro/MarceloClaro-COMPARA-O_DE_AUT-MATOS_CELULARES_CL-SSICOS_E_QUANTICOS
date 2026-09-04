# Colab v3.2.2 — bootstrap independente do Python do kernel

## O que o erro demonstra

O traceback fornecido pelo autor identifica Python 3.13 e falha de código 1 ao executar `python -m venv` na preparação do uv. A v3.2.1 ainda dependia, portanto, da capacidade do Python hospedeiro de criar um venv com pip. Essa premissa do instalador estava inadequada.

A documentação do Python informa que `venv` chama `ensurepip` por padrão. A indisponibilidade de `ensurepip` é uma causa possível, mas **a mensagem recebida não contém stdout/stderr para confirmar a causa específica**. A correção remove essa dependência em vez de presumir que basta trocar um pacote científico.

## Arquitetura corrigida

1. O kernel continua no Python fornecido pelo Colab e importa apenas bibliotecas leves.
2. O código baixa um wheel oficial `uv==0.12.9`, compatível com Linux x86_64, por HTTPS. A URL e seu SHA-256 estão fixados no código, não são obtidos de uma resposta mutável durante a execução.
3. Confere o SHA-256 antes de ler ou executar o binário. Lê apenas o membro `uv-0.12.9.data/scripts/uv`; não extrai caminhos arbitrários do ZIP. Há limites de tamanho.
4. Confirma a versão do executável e publica atomicamente o bootstrap em `/content/.eca-uv-bootstrap-v322`, com recibo de integridade. Não usa pip, venv ou ensurepip do kernel, nem instala pacotes no ambiente da interface.
5. Reutiliza Python 3.11/3.12 do sistema quando disponível; caso contrário, uv obtém CPython 3.12 gerenciado em `/content/.eca-python-v322`, com `--no-bin`.
6. `uv venv --python ... --no-python-downloads` cria `/content/.venv-eca-v322`. O uv instala `pip==26.2.1` somente nesse venv; o pip científico instala a matriz original e executa `pip check`.
7. Reentradas conferem integridade e versões. A célula de fonte carrega explicitamente o módulo do checkout `/content/eca-qca-lab-v322`, mesmo se o módulo anterior ainda existir na sessão.

Não se exige GPU, API paga, Actions ou instalação de sistema. Não se desativa a validação TLS. O código não apaga checkouts antigos, resultados ou diretórios não reconhecidos. Hashes verificam integridade em relação aos valores publicados, não validade científica.

## Como executar

Abra o notebook da branch `main` e confirme **v3.2.2** no cabeçalho. Selecione **CPU / nenhum acelerador**, mantenha `PROFILE="smoke"` e use **Executar tudo**. Não é necessário excluir uma sessão que ainda funciona para aplicar esta atualização; o novo checkout e o carregamento do módulo estão separados da v3.2.1.

Na primeira execução, aguarde as mensagens de obtenção do uv, Python gerenciado (se necessário), criação do ambiente científico e instalação da matriz. Só avance quando aparecer `Python científico:` e a confirmação das versões. Downloads dependem da rede e dos recursos temporários da sessão.

Se houver falha, preserve a mensagem completa: a v3.2.2 inclui a saída do comando, sem ocultá-la atrás de um simples `CalledProcessError`. Não comente os testes nem altere tolerâncias. HTTP 502 de um kernel inacessível é uma falha de infraestrutura separada; antes de descartar uma VM, baixe seus arquivos importantes.

## Validação e limites

O ciclo TDD começou com 10 testes de regressão falhando e 1 contrato pré-existente preservado. Após a implementação e a ampliação da cobertura, os **35 testes de bootstrap, UX e estrutura** passaram. O desenho científico, as regras, os circuitos, os perfis, as sementes e as tolerâncias não foram alterados.

Em 4 de setembro de 2026, a instalação foi executada do zero em Linux x86_64 a partir de **Python 3.13.14 com `-S`**. O PATH foi limitado ao diretório desse interpretador gerenciado, que não continha Python 3.11/3.12. O ensaio bloqueou importações de pip, venv e ensurepip no hospedeiro e chamadas de instalação por módulo no próprio Python hospedeiro.

Foram baixados de fato o wheel uv e **Python 3.12.14**, criado o ambiente científico e instalada a matriz integral. `pip check` passou. A segunda chamada reutilizou o mesmo ambiente, sem instalação adicional. O processo levou aproximadamente **228 segundos neste ambiente local**; esse tempo não é uma previsão para Colab. A suíte completa passou com **496 testes**.

[Registro dos comandos e versões da instalação](../validation/v3.2.2/installation.json) · [Recibo do binário uv](../validation/v3.2.2/uv_receipt.json) · [Log da suíte completa](../validation/v3.2.2/pytest_all.txt).

O [índice de evidências](../validation/v3.2.2/evidence_index.json) registra os SHA-256 dos arquivos de instalação validados. O [snapshot de pacotes](../validation/v3.2.2/environment_freeze.txt) inclui as dependências transitivas efetivamente instaladas; é um registro desta execução, não um lockfile universal para outras plataformas. A validação ocorreu no worktree antes do commit de publicação, condição explicitada no índice.

No ambiente recém-instalado, a validação científica `smoke` também passou:

| Verificação | Resultado observado |
|---|---|
| Suíte ECA (subconjunto dos 496 testes) | 481 aprovados |
| Bases / pares de vetores / observáveis TFQ | 72 / 81 / 81 aprovados |
| ZIP | 10 artefatos científicos e 2 metadados verificados por hash |
| Código do notebook | 11 células executadas duas vezes no mesmo namespace Python |
| Reentrada | Pastas de resultados distintas; nenhum SDK científico no processo da interface |
| Hipóteses H3/H4 | Não avaliadas: perfil smoke, não confirmação independente |

[Log ECA](../validation/v3.2.2/pytest_eca.txt) · [Relatório smoke](../validation/v3.2.2/smoke_report.json) · [Registro célula a célula](../validation/v3.2.2/notebook_validation.json).

**Limitação:** o ensaio foi local, não dentro de uma VM Google Colab. Assim, comprova a instalação real sob as condições descritas, mas não valida a infraestrutura Google, a interface do navegador ou a disponibilidade de rede de outra sessão. O Python hospedeiro também não é a distribuição exata `/usr/bin/python3` fornecida pelo Colab.

## Reprodução do ensaio de instalação

Em Linux x86_64, com Python 3.13 disponível, use um diretório de saída novo:

```bash
python3.13 -S scripts/validate_eca_bootstrap.py \
  --output-dir /tmp/eca-v322-ensaio-01 \
  --allow-download --hide-system-python
```

O comando baixa as dependências e exige espaço temporário; o relatório `installation.json` distingue explicitamente execução local de Colab. `--hide-system-python` limita PATH ao diretório do hospedeiro: para reproduzir o fallback, esse diretório não deve conter também Python 3.11/3.12. O script recusa sobrescrever um diretório de ensaio existente.

## Fontes primárias

- [Python 3.13 — venv e sua dependência padrão de ensurepip](https://docs.python.org/3.13/library/venv.html).
- [Astral — instalação de uv e distribuição oficial no PyPI](https://docs.astral.sh/uv/getting-started/installation/).
- [PyPI — uv 0.12.9 e arquivos de distribuição](https://pypi.org/project/uv/0.12.9/#files).
- [Astral — comandos uv venv e uv pip](https://docs.astral.sh/uv/reference/cli/).
- [TensorFlow Quantum — instalação e compatibilidade Python](https://www.tensorflow.org/quantum/install).
