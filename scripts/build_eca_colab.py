#!/usr/bin/env python3
"""Gera deterministicamente o notebook Colab ECA/QCA — UI leve, SDKs isolados."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "COMPARAÇÃO_DE_AUTÔMATOS_CELULARES_CLÁSSICOS_E_QUANTICOS_Performance,_robustez_ao_ruído_e_aplicações_.ipynb"
REPO = "MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS"


def m(text, id):
    return {"cell_type": "markdown", "id": id, "metadata": {}, "source": text.strip().splitlines(keepends=True)}


def c(text, id):
    return {"cell_type": "code", "execution_count": None, "id": id, "metadata": {},
            "outputs": [], "source": text.strip().splitlines(keepends=True)}


def build():
    cells = [
        m(r'''![Autômatos celulares: do padrão à prova. Padrão da regra 30 calculado com 81 células e 40 passos.](https://raw.githubusercontent.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/main/assets/eca-cover.png)

# Autômatos celulares · do padrão à prova
### Laboratório científico-didático · v3.2.1 · CPU

**MARCELO CLARO LARANJEIRA** · [@MarceloClaro](https://github.com/MarceloClaro)<br>
Professor de Geografia e Pedagogo · Crateús, Ceará, Brasil<br>
[GeoMaker](https://bit.ly/geomaker) · [ORCID 0000-0001-8996-2887](https://orcid.org/0000-0001-8996-2887) · [Instagram](https://www.instagram.com/marceloclaro.geomaker/)

**A pergunta que guia o laboratório:** como representar uma dinâmica clássica possivelmente irreversível sem apagar informação em um circuito unitário?

Você vai **ler padrões → construir o modelo → testar equivalência → interpretar incerteza → exportar evidências**. Os três SDKs são Qiskit, PennyLane e Cirq. TFQ integra TensorFlow–Cirq e **não é uma quarta implementação independente**.

> Escopo: incorporação reversível de uma etapa ECA finita. Não é uma demonstração de vantagem quântica nem uma QCA física infinita completa.''', "title"),
        m('''## Comece aqui
1. Selecione **CPU / nenhum acelerador** no Colab.
2. Mantenha o perfil **smoke** abaixo e use **Ambiente de execução → Executar tudo**.
3. Aguarde a instalação isolada. Ao final, veja o painel e guarde o ZIP.

**Aprendizagem:** siga os mapas, tabelas e exercícios. **Pesquisa:** leia o [protocolo](https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/blob/main/docs/PROTOCOL.md) antes de escolher **paper**. Reexecutar uma semente reproduz a mesma unidade; não cria uma nova réplica.

**Sem serviço pago obrigatório:** não usa GPU, API paga ou GitHub Actions. Colab gratuito tem limites variáveis de recursos e duração; não há garantia de disponibilidade. Esta configuração não altera cobranças anteriores de nenhuma conta.

**Erro 502 antes da primeira saída Python?** O kernel/servidor não ficou acessível. Desconecte e exclua o ambiente de execução; reconecte uma sessão CPU. Nenhuma célula Python consegue corrigir um proxy indisponível. Não compartilhe URLs com tokens de autenticação.''', "before"),
        c('''import os, sys, json, uuid
from datetime import datetime, timezone
from pathlib import Path

PROFILE = os.environ.get("ECA_PROFILE", "smoke").strip().lower()  # smoke ou paper
AUTO_DOWNLOAD = False  # True para baixar automaticamente o ZIP no Colab
if PROFILE not in {"smoke", "paper"}:
    raise ValueError("Escolha smoke ou paper antes de executar.")
IN_COLAB = "google.colab" in sys.modules or bool(os.environ.get("COLAB_RELEASE_TAG"))
RUN_NUMBER = int(globals().get("ECA_RUN_STATE", {}).get("run_number", 0)) + 1
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
OUTPUT_BASE = Path(os.environ.get("ECA_OUTPUT_DIR", "/content/eca_qca_results" if IN_COLAB else "eca_qca_results")).resolve()
OUTPUT_DIR = OUTPUT_BASE / PROFILE / RUN_ID
print(f"Perfil: {PROFILE} | CPU | execução {RUN_NUMBER}\\nPasta exclusiva: {OUTPUT_DIR}")''', "config"),
        m('''## 1 · Fonte rastreável
O checkout local é reutilizado; no Colab, um clone separado é criado uma vez. Não se sobrescrevem alterações locais e não se atualiza o código silenciosamente entre execuções. O manifesto registrará o commit e a árvore Git efetivamente utilizados.''', "source-md"),
        c('''import subprocess
REPOSITORY = "https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS.git"
PROJECT_ROOT = Path.cwd()
if not (PROJECT_ROOT / "scripts/eca_colab_support.py").is_file():
    PROJECT_ROOT = Path("/content/eca-qca-lab-v321") if IN_COLAB else Path.cwd() / "eca-qca-lab-v321"
    if not PROJECT_ROOT.exists():
        subprocess.run(["git", "clone", "--depth", "1", "--branch", "main", REPOSITORY, str(PROJECT_ROOT)], check=True, timeout=180)
if not (PROJECT_ROOT / "scripts/eca_colab_support.py").is_file():
    raise FileNotFoundError("Checkout incompleto. Abra a versão atual do notebook ou use uma nova sessão.")
sys.path.insert(0, str(PROJECT_ROOT / "scripts")) if str(PROJECT_ROOT / "scripts") not in sys.path else None
print("Código:", PROJECT_ROOT)
print("Commit:", subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True).strip())''', "source"),
        m('''## 2 · Ambiente isolado, interface leve
**A instalação não altera o Python do kernel Colab.** As bibliotecas científicas ficam em um ambiente virtual; cada etapa roda em **processo isolado**, usando CPU e um número limitado de threads. TFQ tem um subprocesso próprio.

A matriz TFQ exige Python **3.11 ou 3.12**. Se o Colab estiver em **Python 3.13**, o instalador obtém um **Python 3.12 gerenciado** dentro de `/content`, cria o venv científico a partir dele e mantém o kernel atual. O bootstrap `uv` também fica isolado e fixado por versão. A primeira execução baixa o interpretador e as bibliotecas e pode levar vários minutos; as seguintes verificam e reutilizam o ambiente.''', "env-md"),
        c('''from eca_colab_support import ensure_environment, cpu_environment, read_pins, run_json, table_html, report_html
ENV_DIR = (Path("/content") if IN_COLAB else PROJECT_ROOT) / ".venv-eca-v321"
PYTHON = ensure_environment(PROJECT_ROOT, ENV_DIR, allow_install=IN_COLAB or os.environ.get("ECA_ALLOW_INSTALL") == "1", reuse_current=not IN_COLAB)
print("Python científico:", PYTHON)
print("Versões verificadas:", json.dumps(read_pins(PROJECT_ROOT / "requirements-eca-colab.txt"), ensure_ascii=False))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)''', "install"),
        c('''from IPython.display import display, HTML, Image, FileLink
from html import escape

def show_stage(stage):
    data = run_json(PYTHON, PROJECT_ROOT, "eca_didactic.py",
                    ["--stage", stage, "--profile", PROFILE, "--output-dir", str(OUTPUT_DIR / "didactic")])
    display(HTML("<h3>" + escape(data["title"]) + "</h3>" + table_html(data["rows"])))
    for filename in data["images"]:
        display(Image(filename=filename, width=1050))
    if data.get("interpretation"):
        display(HTML("<p><strong>Como interpretar:</strong> " + escape(data["interpretation"]) + "</p>"))
    return data

SPEC_VIEW = show_stage("spec")
print("As ilustrações didáticas ficam separadas dos dados experimentais.")''', "imports"),
        m('''## 3 · TDD: a execução só avança se os contratos passarem
Os testes cobrem numeração de Wolfram, sincronia, fronteira periódica, reversibilidade, ordem dos qubits, três SDKs, integração TFQ, estatística e integridade dos artefatos.

**Leia o resultado:** uma falha bloqueia o experimento. Não comente testes nem mude tolerâncias para obter aprovação. O número de testes é calculado na execução, não impresso como resultado fixo.''', "tdd-md"),
        c('''tests = sorted(str(p) for p in (PROJECT_ROOT / "tests").glob("test_eca_*.py"))
tested = subprocess.run([PYTHON, "-m", "pytest", "-q", *tests], cwd=PROJECT_ROOT,
                        env=cpu_environment(), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
print(tested.stdout)
if tested.returncode:
    raise AssertionError("TDD falhou: corrija a causa antes de coletar resultados.")''', "tdd"),
        m(r'''## 4 · Observe: de uma regra local ao padrão global
Cada célula lê a vizinhança **esquerda, centro, direita**; todas são atualizadas simultaneamente:

$$f_r(l,c,d)=\left(r\gg(4l+2c+d)\right)\ \&\ 1.$$

A tabela segue a ordem **111 → 000** de Wolfram. Nos mapas, a posição é horizontal e o tempo cresce para baixo. A fronteira periódica conecta a última célula à primeira.

**Antes de executar:** você espera que 60 e 90 produzam o mesmo padrão a partir de uma única célula ativa?''', "classic-md"),
        c('''CLASSIC_VIEW = show_stage("classic")''', "classic"),
        m(r'''## 5 · Modele: preservar informação para poder inverter
Uma função que envia entradas diferentes à mesma saída não pode, sozinha, ser uma transformação unitária no mesmo espaço. Adicionamos um registro de saída:

$$U_F|x\rangle|y\rangle=|x\rangle|y\oplus F(x)\rangle.$$

**Entrada:** $x$ é preservado. **Saída:** $y$ recebe XOR com $F(x)$. **Inversão:** repetir o mesmo XOR desfaz a operação, logo $U_F^2=I$.

A tabela a seguir usa $x=001$ e $y=000$ e compara três sínteses de circuito com uma referência matemática independente dos SDKs.''', "oracle-md"),
        c('''ORACLE_VIEW = show_stage("oracle")''', "oracle"),
        m(r'''## 6 · Investigue: superposição, fase e emaranhamento
Preparamos $|+\rangle^{\otimes n}|0\rangle^{\otimes n}$, e não apenas estados de base. Isso permite que a comparação de amplitudes detecte erros relativos de fase.

**Como interpretar:** as matrizes abaixo mostram $P(x,y)$; elas não mostram fase. A fidelidade compara os estados completos, descontada a fase global. A entropia de von Neumann quantifica o emaranhamento entre os registros de entrada e saída neste estado puro. Entropia positiva **não implica aceleração**.''', "coherent-md"),
        c('''COHERENT_VIEW = show_stage("coherent")''', "coherent"),
        m(r'''## 7 · Meça: ruído, incerteza e custo de simulação
O fluxo obrigatório é: **bases → coerência → TFQ×Cirq → ruído → microbenchmark**.

| Medida | O que significa | O que não conclui |
|---|---|---|
| BER | Fração média de bits alterados | Qualidade de hardware real |
| Sucesso exato | Fração de saídas inteiramente corretas | Vantagem quântica |
| IC95% bootstrap | Incerteza por reamostragem de unidades | Probabilidade de a hipótese ser verdadeira |
| Mediana e IQR | Tempo e dispersão dos simuladores | Aceleração de um computador quântico |

**Modelo de ruído explícito:** bit-flips independentes na saída, amostrados em NumPy. A mesma realização é associada aos três SDKs já validados: são **medidas pareadas de um canal comum**, não três simulações nativas de ruído. Unidade experimental: *(regra, estado, p, semente)*. Não triplique o tamanho amostral pelas etiquetas dos SDKs.

**Previsões:** $\mathrm{BER}=p$ e $P(\mathrm{saída\ exata})=(1-p)^n$. O bootstrap é descritivo; H3/H4 usam bandas simultâneas **Bonferroni–Hoeffding**. Apenas **paper** com todos os gates pode avaliá-las. O perfil smoke não é confirmação de artigo.

O benchmark exclui warm-up, randomiza a ordem e mede construção + execução do simulador, sem custo de importação.''', "run-md"),
        c('''if (OUTPUT_DIR / "bundle_receipt.json").is_file():
    receipt = json.loads((OUTPUT_DIR / "bundle_receipt.json").read_text())
    run_json(PYTHON, PROJECT_ROOT, "verify_eca_bundle.py", [str(OUTPUT_DIR)])
    REPORT = {**json.loads((OUTPUT_DIR / "validation_report.json").read_text()), **receipt}
    print("Resultado existente verificado e reutilizado. Executar tudo inicia outra pasta.")
else:
    REPORT = run_json(PYTHON, PROJECT_ROOT, "run_eca_experiment.py",
                      ["--profile", PROFILE, "--output-dir", str(OUTPUT_DIR)], timeout=1200)
if not REPORT["technical_gate_passed"]:
    raise AssertionError("Gate técnico falhou.")
display(HTML(report_html(REPORT)))
for filename in ("figure_noise.png", "figure_benchmark.png"):
    display(Image(filename=str(OUTPUT_DIR / filename), width=1050))''', "run"),
        c('''VERIFICATION = run_json(PYTHON, PROJECT_ROOT, "verify_eca_bundle.py", [REPORT["bundle"]])
display(HTML("<h3>Pacote íntegro</h3>" + table_html([VERIFICATION])))
print("ZIP:", REPORT["bundle"])
print("SHA-256 do ZIP:", REPORT["bundle_sha256"])
print("Ilustrações didáticas:", OUTPUT_DIR / "didactic")
if IN_COLAB:
    print("Baixe o ZIP pelo painel Arquivos (pasta acima), ou ative AUTO_DOWNLOAD e reexecute esta célula.")
    if AUTO_DOWNLOAD:
        from google.colab import files
        files.download(REPORT["bundle"])
else:
    display(FileLink(REPORT["bundle"]))
print("SHA-256 verifica integridade; não prova autoria nem validade científica.")''', "artifacts"),
        m(r'''## 8 · Aprenda, explique, reproduza

### Exercícios progressivos

1. **Ler:** obtenha os oito bits da regra 30 na ordem 111 → 000.
2. **Aplicar:** para a regra 90 e o estado periódico 001, calcule a próxima linha.
3. **Demonstrar:** encontre uma colisão da regra 30 com três células; explique por que preservar $x$ resolve a reversibilidade.
4. **Analisar:** dois vetores com as mesmas probabilidades podem ter fidelidade menor que 1? Dê um exemplo.
5. **Quantificar:** para $n=5$ e $p=0{,}1$, calcule BER e sucesso exato teóricos.
6. **Auditar:** os três registros de um mesmo canal/estado/semente são três réplicas independentes? Como checar um ZIP?
7. **Pesquisar:** o que falta para estudar ruído por porta em hardware real?

<details>
<summary><strong>Gabarito comentado — abra depois de tentar</strong></summary>

1. **00011110**: essa sequência binária corresponde ao inteiro 30.
2. **110**: na regra 90, a nova célula é esquerda XOR direita.
3. **000 e 111 vão para 000**. O mapeamento simples colide; no oráculo, as entradas continuam distinguíveis em x. Aplicar XOR duas vezes cancela F(x).
4. **Sim:** (|0⟩+|1⟩)/√2 e (|0⟩−|1⟩)/√2 têm as mesmas probabilidades e fidelidade zero.
5. **BER = 0,1; sucesso = 0,9⁵ = 0,59049.** São métricas diferentes.
6. **Não:** são observações pareadas do mesmo fluxo aleatório. Rode o verificador e confira os hashes. Integridade não substitui revisão metodológica.
7. **Um protocolo novo:** localização dos canais, taxas calibradas, backend físico, transpilações, orçamento e hipóteses apropriadas. O modelo de saída deste notebook não responde a essa pergunta.

</details>

### Limites e próximo passo científico

Este laboratório fornece um **baseline reprodutível**, não comprova novidade bibliográfica nem garante Qualis A1. Repetir paper com sementes congeladas é reprodução técnica. Novas hipóteses exigem protocolo, análise da literatura, planejamento amostral e novos dados antes de qualquer conclusão.

[Especificação SDD](https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/blob/main/docs/SDD.md) · [Protocolo](https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/blob/main/docs/PROTOCOL.md) · [Plano do artigo](https://github.com/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/blob/main/docs/ARTICLE_PLAN.md)

**Como citar:** use o arquivo CITATION.cff e o commit do manifesto. Autoria do projeto: **MARCELO CLARO LARANJEIRA**, Professor de Geografia e Pedagogo.''', "exercises"),
        c('''ECA_RUN_STATE = {"status": "completed", "profile": PROFILE, "run_number": RUN_NUMBER,
                 "run_id": RUN_ID, "output_dir": str(OUTPUT_DIR),
                 "technical_gate_passed": bool(REPORT["technical_gate_passed"]),
                 "bundle_sha256": REPORT["bundle_sha256"]}
print("Execução concluída:", json.dumps(ECA_RUN_STATE, ensure_ascii=False, indent=2))
print("Você pode repetir Executar tudo: uma nova pasta preservará esta execução.")''', "final"),
    ]
    assert len(cells) == 21 and sum(x["cell_type"] == "code" for x in cells) == 11
    return {"cells": cells, "metadata": {
        "accelerator": "CPU", "colab": {"name": NB.name, "provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"}},
        "nbformat": 4, "nbformat_minor": 5}


def text():
    return json.dumps(build(), ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    wanted = text()
    if args.check:
        raise SystemExit(0 if NB.is_file() and NB.read_text() == wanted else 1)
    NB.write_text(wanted, encoding="utf-8")
    print(NB)
