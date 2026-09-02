"""Gera deterministicamente o notebook Iris/QML estável para Google Colab."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "Classificador_Quântico_Híbrido_de_Alta_Performance_para_Classificação_de_Dados_Iris_(Otimizado).ipynb"


def source(text: str) -> list[str]:
    return (dedent(text).strip() + "\n").splitlines(keepends=True)


def markdown(cell_id: str, text: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": cell_id,
        "metadata": {},
        "source": source(text),
    }


def code(cell_id: str, text: str, *, tags: list[str] | None = None) -> dict:
    metadata = {"tags": tags} if tags else {}
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": metadata,
        "outputs": [],
        "source": source(text),
    }


cells = [
    markdown(
        "title",
        r'''
        <a href="https://colab.research.google.com/github/MarceloClaro/MarceloClaro-COMPARA-O_DE_AUT-MATOS_CELULARES_CL-SSICOS_E_QUANTICOS/blob/main/Classificador_Qu%C3%A2ntico_H%C3%ADbrido_de_Alta_Performance_para_Classifica%C3%A7%C3%A3o_de_Dados_Iris_(Otimizado).ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Abrir no Colab"/></a>

        # Classificador híbrido quântico-clássico Iris
        ## Versão estável, reprodutível e adequada ao Google Colab

        **Objetivo:** comparar três ansätze Cirq sem vazamento de dados, otimizar apenas a arquitetura escolhida na validação e avaliar o teste uma única vez.

        > Esta versão substitui as células cumulativas que recriavam centenas de modelos Keras e derrubavam o runtime durante o COBYLA. O caminho padrão usa Cirq + regressão logística: continua sendo híbrido quântico-clássico, mas mantém consumo de memória previsível.
        ''',
    ),
    markdown(
        "project-presentation",
        r'''
        ## Apresentação do projeto

        Este projeto investiga, em escala didática e reprodutível, um **classificador híbrido quântico-clássico** aplicado ao conjunto Iris. O circuito variacional Cirq transforma quatro atributos botânicos em expectativas de Pauli-Z; uma regressão logística utiliza esses atributos quânticos para realizar a classificação binária entre *Iris setosa* e *Iris versicolor*.

        | Dimensão | Definição do projeto |
        |---|---|
        | Pergunta | Um mapa de atributos produzido por um circuito variacional pode sustentar uma classificação reproduzível sem vazamento de dados? |
        | Pipeline | Iris → normalização → VQC Cirq → quatro expectativas `⟨Zᵢ⟩` → regressão logística |
        | Comparação | Pipeline híbrido × regressão logística clássica pré-especificada |
        | Rigor | treino/validação/teste `60/20/20`, teste selado, convergência COBYLA, TDD, IC95% e hashes SHA-256 |
        | Perfis | `smoke`, para verificação rápida; `full`, para execução experimental completa |
        | Escopo | Simulação ideal de quatro qubits; não constitui demonstração de vantagem ou aceleração quântica |

        **Contribuição didática:** apresentar todo o caminho entre preparação dos dados, construção do circuito, otimização, comparação justa, incerteza estatística e auditoria dos resultados em um único ambiente Google Colab.
        ''',
    ),
    markdown(
        "author-presentation",
        r'''
        ## Autor

        <table>
          <tr>
            <td width="185" align="center">
              <a href="https://github.com/MarceloClaro" target="_blank">
                <img src="https://avatars.githubusercontent.com/u/58664974?v=4" width="150" alt="Perfil de Marcelo Claro Laranjeira no GitHub"/>
              </a>
            </td>
            <td>
              <h2>Prof. Marcelo Claro Laranjeira</h2>
              <p><strong>Professor de Geografia e Pedagogo</strong></p>
              <p><strong>GitHub:</strong> <a href="https://github.com/MarceloClaro" target="_blank">@MarceloClaro</a></p>
              <p><strong>Localização:</strong> Crateús, Ceará, Brasil</p>
              <p><strong>Projeto:</strong> <a href="https://bit.ly/geomaker" target="_blank">GeoMaker</a></p>
              <p><strong>ORCID:</strong> <a href="https://orcid.org/0000-0001-8996-2887" target="_blank">0000-0001-8996-2887</a></p>
              <p><strong>Instagram:</strong> <a href="https://www.instagram.com/marceloclaro.geomaker/" target="_blank">@marceloclaro.geomaker</a></p>
              <p><a href="https://github.com/MarceloClaro?tab=followers" target="_blank"><strong>57 seguidores</strong></a> · <a href="https://github.com/MarceloClaro?tab=following" target="_blank"><strong>65 seguindo</strong></a></p>
            </td>
          </tr>
        </table>

        <small>Contagens do GitHub informadas em 2 de setembro de 2026; esses números podem mudar. Consulte o perfil para os valores atuais.</small>
        ''',
    ),
    markdown(
        "instructions",
        r'''
        ## Como executar

        1. Em **Ambiente de execução → Alterar tipo de ambiente**, escolha **CPU / sem acelerador**. Este experimento não usa GPU.
        2. Mantenha `PROFILE = "smoke"` para a verificação rápida.
        3. Clique em **Ambiente de execução → Executar tudo**.
        4. Para o experimento completo, selecione `PROFILE = "full"` e clique novamente em **Executar tudo**.

        O notebook é reentrante: uma nova execução completa limpa apenas os objetos transitórios do próprio experimento e recebe um novo número de execução. Repetir somente a célula final reutiliza o resultado em cache e **não abre o teste novamente**. A primeira execução de uma sessão é a referência confirmatória; repetições na mesma sessão são registradas como réplicas técnicas.

        Em cada célula de código, a mensagem `GATE ...: aprovado` confirma as pós-condições. A célula de dependências pode levar alguns minutos na primeira execução, mas não reinicia o ambiente e não instala TensorFlow.

        A documentação oficial informa suporte do TensorFlow Quantum a Python 3.10–3.12. Este notebook não tenta instalar TFQ quando ele não é necessário e não imprime uma versão de Python presumida: a versão real é detectada abaixo.
        ''',
    ),
    code(
        "setup",
        r'''
        # 1. Bootstrap mínimo: não reinstala TensorFlow e não exige reinício do runtime
        import importlib.util
        import os
        import platform
        import site
        import subprocess
        import sys
        from importlib.metadata import PackageNotFoundError, version as distribution_version

        if sys.version_info[:2] < (3, 10):
            raise RuntimeError("Este notebook requer Python 3.10 ou superior.")

        # O simulador Cirq deste experimento é CPU-only; não reserva nem inicializa CUDA.
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")

        def installed_version(distribution):
            try:
                return distribution_version(distribution)
            except PackageNotFoundError:
                return None

        def numeric_version(distribution):
            try:
                parts = installed_version(distribution).split(".")
                return tuple(int(part.split("+")[0]) for part in parts[:3])
            except (AttributeError, ValueError):
                return (0, 0, 0)

        # (módulo, distribuição, requisito pip, mínimo inclusivo, major máximo exclusivo)
        dependency_contracts = (
            ("cirq", "cirq-core", "cirq-core==1.6.1", (1, 6, 1), 2),
            ("sklearn", "scikit-learn", "scikit-learn>=1.4,<2", (1, 4, 0), 2),
            ("scipy", "scipy", "scipy>=1.16,<2", (1, 16, 0), 2),
            ("matplotlib", "matplotlib", "matplotlib>=3.8,<4", (3, 8, 0), 4),
            ("pandas", "pandas", "pandas>=2.0,<3", (2, 0, 0), 3),
        )
        def contract_satisfied(module, distribution, minimum, maximum_major):
            detected = numeric_version(distribution)
            return not (
                importlib.util.find_spec(module) is None
                or detected < minimum
                or detected[0] >= maximum_major
                or (distribution == "cirq-core" and installed_version(distribution) != "1.6.1")
            )

        missing = []
        for module, distribution, requirement, minimum, maximum_major in dependency_contracts:
            if not contract_satisfied(module, distribution, minimum, maximum_major):
                missing.append(requirement)

        missing = list(dict.fromkeys(missing))

        skip_install = os.environ.get("IRIS_SKIP_INSTALL", "0") == "1"
        if missing and skip_install:
            raise RuntimeError(
                "Dependências incompatíveis e instalação desativada por IRIS_SKIP_INSTALL=1: "
                + ", ".join(missing)
            )
        if missing:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", *missing],
                    check=True,
                )
            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    "Falha ao instalar dependências. Reinicie o runtime do Colab e execute "
                    "novamente desde a primeira célula."
                ) from error

            # Alguns ambientes criam o diretório user-site durante o pip; o processo
            # corrente precisa incorporá-lo antes que a célula seguinte faça imports.
            site.addsitedir(site.getusersitepackages())
            importlib.invalidate_caches()

        remaining = [
            requirement
            for module, distribution, requirement, minimum, maximum_major in dependency_contracts
            if not contract_satisfied(module, distribution, minimum, maximum_major)
        ]
        if remaining:
            raise RuntimeError(
                "Pós-condição de dependências falhou: " + ", ".join(remaining)
                + ". Reinicie o runtime e execute novamente desde a primeira célula."
            )

        print("Python real:", platform.python_version())
        print("Plataforma:", platform.platform())
        print("Dependências instaladas ou ajustadas:", missing or "nenhuma")
        if os.environ.get("COLAB_GPU", "0") not in {"", "0"}:
            print("AVISO: GPU detectada, mas não utilizada. Prefira o runtime CPU padrão.")
        print("TFQ suportado oficialmente por versão de Python:", (3, 10) <= sys.version_info[:2] <= (3, 12))
        print("GATE SETUP: Python e contratos de dependência aprovados.")
        ''',
        tags=["setup"],
    ),
    code(
        "imports-config",
        r'''
        # 2. Imports, sementes e perfil pré-especificado
        import gc
        import hashlib
        import json
        import time
        import zipfile
        from dataclasses import asdict, dataclass
        from pathlib import Path

        import cirq
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        import scipy
        import sklearn
        import sympy
        from scipy.optimize import minimize
        from sklearn.datasets import load_iris
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import (
            accuracy_score,
            balanced_accuracy_score,
            confusion_matrix,
            f1_score,
            log_loss,
            roc_auc_score,
        )
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import MinMaxScaler, StandardScaler

        SEED = 42
        np.random.seed(SEED)

        @dataclass(frozen=True)
        class Profile:
            name: str
            cobyla_maxfun: int
            cobyla_tol: float
            cobyla_f_target: float | None
            landscape_points: int
            bootstrap_resamples: int
            noise_replicates: int

        PROFILES = {
            # Smoke: gate operacional por meta; full: convergência pelo raio da região de confiança.
            "smoke": Profile(
                "smoke", cobyla_maxfun=40, cobyla_tol=1e-2, cobyla_f_target=0.04,
                landscape_points=7, bootstrap_resamples=1_000, noise_replicates=3,
            ),
            "full": Profile(
                "full", cobyla_maxfun=160, cobyla_tol=1e-3, cobyla_f_target=None,
                landscape_points=15, bootstrap_resamples=5_000, noise_replicates=10,
            ),
        }
        PROFILE = "smoke"  # @param ["smoke", "full"]
        PROFILE = os.environ.get("IRIS_PROFILE", PROFILE)
        if PROFILE not in PROFILES:
            raise ValueError("IRIS_PROFILE deve ser 'smoke' ou 'full'.")
        SPEC = PROFILES[PROFILE]

        assert SEED >= 0
        assert SPEC.cobyla_maxfun > 0 and SPEC.cobyla_tol > 0
        assert SPEC.landscape_points >= 3 and SPEC.bootstrap_resamples >= 1_000
        assert SPEC.noise_replicates >= 3

        print("Perfil:", asdict(SPEC))
        print("Cirq:", cirq.__version__, "| NumPy:", np.__version__, "| SciPy:", scipy.__version__, "| scikit-learn:", sklearn.__version__)
        print("GATE CONFIGURAÇÃO: perfil e sementes aprovados.")
        ''',
        tags=["parameters"],
    ),
    markdown(
        "protocol",
        r'''
        ## 3. Protocolo antes dos resultados

        | Etapa | Dados permitidos | Decisão |
        |---|---|---|
        | Ajuste | treino | ajustar classificador clássico |
        | Seleção | validação | escolher arquitetura e parâmetros quânticos |
        | Robustez exploratória | validação perturbada | diagnóstico pós-seleção, sem abrir o teste |
        | Confirmação | teste | estimar desempenho uma única vez |

        Hipóteses e critérios:

        - H1: a extração retorna quatro expectativas físicas em `[-1,1]`.
        - H2: repetir com a mesma configuração produz os mesmos atributos.
        - H3: COBYLA minimiza a perda positiva e deve retornar `success=True` por meta (`smoke`) ou convergência da região de confiança (`full`).
        - H4: nenhuma escolha de arquitetura ou hiperparâmetro consulta `y_test`.
        - H5: a célula final é idempotente: uma repetição isolada reutiliza o cache sem nova abertura do teste.
        - H6: cada par `(nível de ruído, réplica)` recebe uma semente determinística e única.
        - H7: somente os artefatos pré-especificados entram no arquivo ZIP e todos têm SHA-256 verificável.

        Cada **execução completa** recebe um contador próprio. A primeira execução em uma sessão limpa é confirmatória; execuções completas adicionais no mesmo kernel são identificadas no manifesto como réplicas técnicas, preservando a transparência sem bloquear o uso didático.

        A unidade experimental é a divisão estratificada fixada pela semente. Com apenas 20 casos de teste, o intervalo de incerteza deve ser relatado e conclusões fortes devem ser evitadas.
        ''',
    ),
    code(
        "data",
        r'''
        # 4. Dados: treino/validação/teste disjuntos; scaler ajustado somente no treino
        iris = load_iris()
        mask = iris.target != 2
        X_raw = iris.data[mask].astype(np.float64)
        y = iris.target[mask].astype(np.int64)
        row_ids = np.arange(len(y))

        assert X_raw.shape == (100, 4)
        assert y.shape == (100,) and set(np.unique(y)) == {0, 1}
        assert np.isfinite(X_raw).all()

        development_ids, test_ids = train_test_split(
            row_ids, test_size=0.20, random_state=SEED, stratify=y
        )
        train_ids, validation_ids = train_test_split(
            development_ids,
            test_size=0.25,
            random_state=SEED,
            stratify=y[development_ids],
        )

        assert set(train_ids).isdisjoint(validation_ids)
        assert set(train_ids).isdisjoint(test_ids)
        assert set(validation_ids).isdisjoint(test_ids)
        assert len(train_ids) + len(validation_ids) + len(test_ids) == len(y)
        assert (len(train_ids), len(validation_ids), len(test_ids)) == (60, 20, 20)

        input_scaler = MinMaxScaler(feature_range=(0, 1), clip=True)
        X_train = input_scaler.fit_transform(X_raw[train_ids])
        X_validation = input_scaler.transform(X_raw[validation_ids])
        y_train, y_validation = y[train_ids], y[validation_ids]
        assert X_train.shape == (60, 4) and X_validation.shape == (20, 4)
        assert np.isfinite(X_train).all() and np.isfinite(X_validation).all()
        assert np.min(X_train) >= 0.0 and np.max(X_train) <= 1.0
        assert np.min(X_validation) >= 0.0 and np.max(X_validation) <= 1.0
        assert np.bincount(y_train, minlength=2).tolist() == [30, 30]
        assert np.bincount(y_validation, minlength=2).tolist() == [10, 10]

        # Uma nova passagem de "Executar tudo" começa uma execução controlada.
        previous_test_opened = bool(globals().get("TEST_OPENED", False))
        _IRIS_RUN_SEQUENCE = int(globals().get("_IRIS_RUN_SEQUENCE", 0)) + 1
        RUN_SEQUENCE = _IRIS_RUN_SEQUENCE
        _IRIS_SESSION_TEST_OPENINGS = int(globals().get("_IRIS_SESSION_TEST_OPENINGS", 0))

        # Remove somente resultados transitórios da passagem anterior para liberar memória.
        transient_names = (
            "X_test", "y_test", "X_fit", "y_fit", "fit_features", "test_features",
            "final_classifier", "classical_classifier", "test_probability",
            "test_prediction", "classical_probability", "classical_prediction",
            "test_metrics", "accuracy_ci", "log_loss_ci", "matrix", "FINAL_TEST_CACHE",
            "architecture_results", "optimization", "objective_history", "landscape_results",
            "noise_results", "noise_summary", "robustness_classifier",
            "robustness_train_features", "optimized_theta",
        )
        for transient_name in transient_names:
            globals().pop(transient_name, None)
        plt.close("all")
        gc.collect()

        # O teste permanece apenas como índices opacos até a célula confirmatória.
        TEST_OPENED = False
        TEST_OPEN_COUNT = 0
        FINAL_TEST_CACHE = None
        n_test_reserved = len(test_ids)

        split_table = pd.DataFrame({
            "partição": ["treino", "validação", "teste reservado"],
            "n": [len(y_train), len(y_validation), n_test_reserved],
            "classe_0": [int((y_train == 0).sum()), int((y_validation == 0).sum()), "selado"],
            "classe_1": [int((y_train == 1).sum()), int((y_validation == 1).sum()), "selado"],
        })
        display(split_table)
        if previous_test_opened:
            print(f"NOVA EXECUÇÃO CONTROLADA #{RUN_SEQUENCE}: estado anterior descartado.")
        else:
            print(f"EXECUÇÃO CONTROLADA #{RUN_SEQUENCE}: teste ainda não aberto.")
        print("GATE DADOS: formas, classes, partições e normalização aprovadas; teste selado.")
        ''',
        tags=["test"],
    ),
    markdown(
        "quantum-model",
        r'''
        ## 5. Modelo quântico e observáveis

        Cada camada aplica `Rx(πxᵢ)`, uma rotação treinável `Ry(θᵢ)` e uma topologia CNOT. Para cada amostra extraímos

        \[
        \phi_\theta(x)=\left(\langle Z_0\rangle,\ldots,\langle Z_3\rangle\right).
        \]

        A versão anterior usava apenas `|ψ₀|²−|ψ₁|²`, que não é a expectativa de Pauli-Z de um qubit em um estado de quatro qubits. Agora o próprio simulador calcula cada observável e um teste conhecido verifica `⟨0|Z|0⟩=1` e `⟨1|Z|1⟩=−1`.
        ''',
    ),
    code(
        "circuits",
        r'''
        # 5.1 Três ansätze comparáveis pela mesma interface
        N_QUBITS = 4
        N_LAYERS = 2

        def build_vqc(architecture: str):
            if architecture not in {"linear", "alternating", "ring"}:
                raise ValueError("Arquitetura desconhecida.")
            qubits = tuple(cirq.LineQubit.range(N_QUBITS))
            x_symbols = tuple(sympy.Symbol(f"x_{index}") for index in range(N_QUBITS))
            theta_symbols = tuple(
                sympy.Symbol(f"theta_{index}") for index in range(N_QUBITS * N_LAYERS)
            )
            circuit = cirq.Circuit()
            for layer in range(N_LAYERS):
                for index, qubit in enumerate(qubits):
                    circuit.append(cirq.rx(np.pi * x_symbols[index])(qubit))
                    circuit.append(cirq.ry(theta_symbols[layer * N_QUBITS + index])(qubit))

                if architecture == "linear":
                    pairs = ((0, 1), (1, 2), (2, 3))
                elif architecture == "ring":
                    pairs = ((0, 1), (1, 2), (2, 3), (3, 0))
                else:
                    pairs = ((0, 1), (2, 3)) if layer % 2 == 0 else ((1, 2), (3, 0))
                circuit.append(cirq.CNOT(qubits[left], qubits[right]) for left, right in pairs)
            return circuit, qubits, x_symbols, theta_symbols

        CIRCUITS = {name: build_vqc(name) for name in ("linear", "alternating", "ring")}
        circuit_signatures = set()
        for name, (circuit, qubits, x_symbols, theta_symbols) in CIRCUITS.items():
            assert len(qubits) == N_QUBITS and len(set(qubits)) == N_QUBITS
            assert len(x_symbols) == N_QUBITS
            assert len(theta_symbols) == N_QUBITS * N_LAYERS
            assert cirq.parameter_names(circuit) == {
                *(str(symbol) for symbol in x_symbols),
                *(str(symbol) for symbol in theta_symbols),
            }
            assert not circuit.has_measurements()
            circuit_signatures.add(str(circuit))
            print(f"{name}: momentos={len(circuit)}, parâmetros={len(theta_symbols)}")
            print(circuit)
        assert len(circuit_signatures) == len(CIRCUITS)
        print("GATE CIRCUITOS: topologias distintas, símbolos e qubits aprovados.")
        ''',
    ),
    code(
        "features-tests",
        r'''
        # 5.2 Extração correta, simulador reutilizado e gates TDD
        SIMULATOR = cirq.Simulator(seed=SEED)

        def quantum_features(bundle, data, theta):
            circuit, qubits, x_symbols, theta_symbols = bundle
            data = np.asarray(data, dtype=np.float64)
            theta = np.asarray(theta, dtype=np.float64)
            if data.ndim != 2 or data.shape[1] != len(x_symbols):
                raise ValueError("data deve ter forma (amostras, 4).")
            if theta.shape != (len(theta_symbols),):
                raise ValueError("Número de parâmetros incompatível.")

            observables = [cirq.Z(qubit) for qubit in qubits]
            output = np.empty((len(data), len(observables)), dtype=np.float64)
            theta_map = dict(zip(theta_symbols, theta))
            for row_index, row in enumerate(data):
                resolver = cirq.ParamResolver({**dict(zip(x_symbols, row)), **theta_map})
                values = SIMULATOR.simulate_expectation_values(
                    circuit,
                    observables=observables,
                    param_resolver=resolver,
                    qubit_order=qubits,
                )
                output[row_index] = np.real(values)
            if not np.isfinite(output).all() or (output.size and np.max(np.abs(output)) > 1 + 1e-7):
                raise FloatingPointError("Expectativas quânticas fora do domínio físico [-1, 1].")
            return output

        # Testes de observáveis conhecidos
        test_qubit = cirq.LineQubit(0)
        z_zero = SIMULATOR.simulate_expectation_values(
            cirq.Circuit(cirq.I(test_qubit)), [cirq.Z(test_qubit)]
        )[0]
        z_one = SIMULATOR.simulate_expectation_values(cirq.Circuit(cirq.X(test_qubit)), [cirq.Z(test_qubit)])[0]
        assert np.isclose(z_zero, 1.0, atol=1e-7)
        assert np.isclose(z_one, -1.0, atol=1e-7)

        rng = np.random.default_rng(SEED)
        initial_theta = rng.uniform(-np.pi, np.pi, N_QUBITS * N_LAYERS)
        probes = {
            name: quantum_features(bundle, X_train[:3], initial_theta)
            for name, bundle in CIRCUITS.items()
        }
        probe_a = probes["linear"]
        probe_b = quantum_features(CIRCUITS["linear"], X_train[:3], initial_theta)
        assert all(probe.shape == (3, 4) for probe in probes.values())
        assert all(np.isfinite(probe).all() for probe in probes.values())
        assert all(np.max(np.abs(probe)) <= 1 + 1e-7 for probe in probes.values())
        np.testing.assert_allclose(probe_a, probe_b, atol=1e-7)

        for invalid_data, invalid_theta in (
            (X_train[0], initial_theta),
            (X_train[:2, :3], initial_theta),
            (X_train[:2], initial_theta[:-1]),
        ):
            try:
                quantum_features(CIRCUITS["linear"], invalid_data, invalid_theta)
            except ValueError:
                pass
            else:
                raise AssertionError("Entrada inválida deveria produzir ValueError.")
        print("GATE TDD: observáveis, forma, limites e reprodutibilidade aprovados.")
        ''',
        tags=["test", "gate"],
    ),
    code(
        "architecture-selection",
        r'''
        # 6. Seleção de arquitetura usando somente treino e validação
        def new_classifier():
            return make_pipeline(
                StandardScaler(),
                LogisticRegression(max_iter=1_000, random_state=SEED),
            )

        architecture_rows = []
        for name, bundle in CIRCUITS.items():
            started = time.perf_counter()
            train_features = quantum_features(bundle, X_train, initial_theta)
            validation_features = quantum_features(bundle, X_validation, initial_theta)
            classifier = new_classifier()
            classifier.fit(train_features, y_train)
            validation_probability = classifier.predict_proba(validation_features)[:, 1]
            assert validation_probability.shape == (len(y_validation),)
            assert np.isfinite(validation_probability).all()
            assert np.all((validation_probability >= 0.0) & (validation_probability <= 1.0))
            architecture_rows.append({
                "architecture": name,
                "validation_log_loss": log_loss(y_validation, validation_probability, labels=[0, 1]),
                "validation_accuracy": accuracy_score(y_validation, validation_probability >= 0.5),
                "seconds": time.perf_counter() - started,
            })
            del train_features, validation_features, classifier
            gc.collect()

        architecture_results = (
            pd.DataFrame(architecture_rows)
            .sort_values(["validation_log_loss", "architecture"], kind="stable")
            .reset_index(drop=True)
        )
        assert set(architecture_results["architecture"]) == set(CIRCUITS)
        assert len(architecture_results) == 3
        assert np.isfinite(architecture_results["validation_log_loss"]).all()
        assert architecture_results["validation_accuracy"].between(0.0, 1.0).all()
        assert (architecture_results["seconds"] >= 0.0).all()
        display(architecture_results)
        best_architecture = str(architecture_results.iloc[0]["architecture"])
        best_bundle = CIRCUITS[best_architecture]
        print("Arquitetura escolhida sem consultar o teste:", best_architecture)
        print("GATE SELEÇÃO: três arquiteturas avaliadas somente na validação.")
        ''',
        tags=["gate"],
    ),
    code(
        "optimization",
        r'''
        # 7. COBYLA leve: nenhuma criação de modelo Keras dentro da função objetivo
        objective_history = []

        def validation_objective(theta, *, record=True):
            train_features = quantum_features(best_bundle, X_train, theta)
            validation_features = quantum_features(best_bundle, X_validation, theta)
            classifier = new_classifier()
            classifier.fit(train_features, y_train)
            probability = classifier.predict_proba(validation_features)[:, 1]
            value = float(log_loss(y_validation, probability, labels=[0, 1]))
            if record:
                objective_history.append(value)
            del train_features, validation_features, classifier
            return value

        initial_validation_loss = validation_objective(initial_theta, record=False)
        optimization_started = time.perf_counter()
        cobyla_options = {
            "maxiter": SPEC.cobyla_maxfun,
            "rhobeg": 0.5,
            "tol": SPEC.cobyla_tol,
            "catol": 1e-4,
        }
        if SPEC.cobyla_f_target is not None:
            cobyla_options["f_target"] = SPEC.cobyla_f_target

        optimization = minimize(
            validation_objective,
            initial_theta,
            method="COBYLA",
            bounds=[(-np.pi, np.pi)] * len(initial_theta),
            options=cobyla_options,
        )
        optimized_theta = np.asarray(optimization.x, dtype=np.float64)
        optimized_validation_loss = validation_objective(optimized_theta, record=False)
        used_initial_fallback = bool(optimized_validation_loss > initial_validation_loss)
        if optimized_validation_loss > initial_validation_loss:
            optimized_theta = initial_theta.copy()
            optimized_validation_loss = initial_validation_loss

        optimization_seconds = time.perf_counter() - optimization_started
        assert len(objective_history) == int(optimization.nfev)
        assert np.isfinite(objective_history).all()
        assert optimized_theta.shape == initial_theta.shape
        assert np.all(optimized_theta >= -np.pi - 1e-7)
        assert np.all(optimized_theta <= np.pi + 1e-7)
        optimization_record = {
            "success": bool(optimization.success),
            "status": int(optimization.status),
            "message": str(optimization.message),
            "nfev": int(optimization.nfev),
            "maxfun": SPEC.cobyla_maxfun,
            "tol": SPEC.cobyla_tol,
            "f_target": SPEC.cobyla_f_target,
            "seconds": optimization_seconds,
            "initial_validation_log_loss": float(initial_validation_loss),
            "optimizer_validation_log_loss": float(optimization.fun),
            "selected_validation_log_loss": float(optimized_validation_loss),
            "used_initial_fallback": used_initial_fallback,
        }
        print("COBYLA:", optimization_record)
        print(f"Log-loss inicial={initial_validation_loss:.6f}; selecionado={optimized_validation_loss:.6f}")
        if not optimization.success:
            raise RuntimeError(
                "GATE COBYLA FALHOU: o critério de parada não foi satisfeito. "
                "Não interprete os parâmetros como convergidos."
            )
        assert optimized_validation_loss <= initial_validation_loss + 1e-12
        assert np.isfinite(optimized_validation_loss)
        print("GATE COBYLA: parada, histórico, limites e não regressão aprovados.")
        gc.collect()
        ''',
        tags=["gate"],
    ),
    code(
        "landscape",
        r'''
        # 8. Corte unidimensional exploratório da paisagem de validação
        grid = np.linspace(-np.pi, np.pi, SPEC.landscape_points)
        landscape_loss = []
        for value in grid:
            candidate = optimized_theta.copy()
            candidate[0] = value
            landscape_loss.append(validation_objective(candidate, record=False))

        landscape_results = pd.DataFrame({
            "theta_0": grid,
            "validation_log_loss": landscape_loss,
        })
        assert len(landscape_results) == SPEC.landscape_points
        assert np.isfinite(landscape_results.to_numpy()).all()
        assert (landscape_results["validation_log_loss"] >= 0.0).all()

        fig_landscape, axis = plt.subplots(figsize=(7, 4))
        axis.plot(grid, landscape_loss, marker="o")
        axis.axvline(optimized_theta[0], color="tab:red", linestyle="--", label="θ selecionado")
        axis.set(title="Corte exploratório da perda de validação", xlabel="θ₀", ylabel="log-loss")
        axis.grid(alpha=0.25)
        axis.legend()
        fig_landscape.tight_layout()
        plt.show()
        plt.close(fig_landscape)
        print("GATE PAISAGEM: grade, finitude e perdas aprovadas.")
        ''',
    ),
    code(
        "final-test",
        r'''
        # 10. Confirmação idempotente: repetir esta célula reutiliza o cache da execução.
        def compute_final_test():
            X_test_local = input_scaler.transform(X_raw[test_ids])
            y_test_local = y[test_ids]
            assert X_test_local.shape == (n_test_reserved, N_QUBITS)
            assert y_test_local.shape == (n_test_reserved,)
            assert np.isfinite(X_test_local).all()
            assert np.min(X_test_local) >= 0.0 and np.max(X_test_local) <= 1.0
            assert np.bincount(y_test_local, minlength=2).tolist() == [10, 10]

            X_fit_local = np.vstack((X_train, X_validation))
            y_fit_local = np.concatenate((y_train, y_validation))
            fit_features_local = quantum_features(best_bundle, X_fit_local, optimized_theta)
            test_features_local = quantum_features(best_bundle, X_test_local, optimized_theta)

            final_classifier_local = new_classifier()
            final_classifier_local.fit(fit_features_local, y_fit_local)
            test_probability_local = final_classifier_local.predict_proba(test_features_local)[:, 1]
            test_prediction_local = (test_probability_local >= 0.5).astype(np.int64)
            assert np.isfinite(test_probability_local).all()
            assert np.all((test_probability_local >= 0.0) & (test_probability_local <= 1.0))
            assert set(np.unique(test_prediction_local)).issubset({0, 1})

            # Comparador clássico pré-especificado: mesma divisão e mesma família.
            classical_classifier_local = new_classifier()
            classical_classifier_local.fit(X_fit_local, y_fit_local)
            classical_probability_local = classical_classifier_local.predict_proba(X_test_local)[:, 1]
            classical_prediction_local = (classical_probability_local >= 0.5).astype(np.int64)
            assert np.isfinite(classical_probability_local).all()
            assert np.all(
                (classical_probability_local >= 0.0) & (classical_probability_local <= 1.0)
            )

            def metric_row(model_name, probability, prediction):
                return {
                    "model": model_name,
                    "accuracy": accuracy_score(y_test_local, prediction),
                    "balanced_accuracy": balanced_accuracy_score(y_test_local, prediction),
                    "f1": f1_score(y_test_local, prediction),
                    "roc_auc": roc_auc_score(y_test_local, probability),
                    "log_loss": log_loss(y_test_local, probability, labels=[0, 1]),
                }

            test_metrics_local = pd.DataFrame([
                metric_row("hybrid_cirq", test_probability_local, test_prediction_local),
                metric_row(
                    "classical_logistic_regression",
                    classical_probability_local,
                    classical_prediction_local,
                ),
            ])
            bounded_metrics = ["accuracy", "balanced_accuracy", "f1", "roc_auc"]
            assert np.isfinite(test_metrics_local.select_dtypes(include=[np.number])).all().all()
            assert all(
                test_metrics_local[column].between(0.0, 1.0).all()
                for column in bounded_metrics
            )
            assert (test_metrics_local["log_loss"] >= 0.0).all()

            bootstrap_rng = np.random.default_rng(SEED + 1)
            bootstrap_log_loss = []
            for _ in range(SPEC.bootstrap_resamples):
                sampled = bootstrap_rng.integers(0, len(y_test_local), len(y_test_local))
                bootstrap_log_loss.append(
                    log_loss(
                        y_test_local[sampled],
                        test_probability_local[sampled],
                        labels=[0, 1],
                    )
                )
            log_loss_ci_local = np.quantile(bootstrap_log_loss, [0.025, 0.975])

            # Wilson não colapsa para [1, 1] quando a amostra pequena não contém erros.
            test_size = len(y_test_local)
            correct = int(np.sum(y_test_local == test_prediction_local))
            observed_accuracy_local = correct / test_size
            z_95 = 1.959963984540054
            denominator = 1 + z_95**2 / test_size
            center = (observed_accuracy_local + z_95**2 / (2 * test_size)) / denominator
            radius = (
                z_95
                * np.sqrt(
                    observed_accuracy_local * (1 - observed_accuracy_local) / test_size
                    + z_95**2 / (4 * test_size**2)
                )
                / denominator
            )
            accuracy_ci_local = np.clip([center - radius, center + radius], 0.0, 1.0)
            matrix_local = confusion_matrix(y_test_local, test_prediction_local)

            assert accuracy_ci_local[0] <= observed_accuracy_local <= accuracy_ci_local[1]
            assert np.isfinite(log_loss_ci_local).all()
            assert log_loss_ci_local[0] <= log_loss_ci_local[1]
            return {
                "run_sequence": RUN_SEQUENCE,
                "X_test": X_test_local,
                "y_test": y_test_local,
                "X_fit": X_fit_local,
                "y_fit": y_fit_local,
                "fit_features": fit_features_local,
                "test_features": test_features_local,
                "final_classifier": final_classifier_local,
                "classical_classifier": classical_classifier_local,
                "test_probability": test_probability_local,
                "test_prediction": test_prediction_local,
                "classical_probability": classical_probability_local,
                "classical_prediction": classical_prediction_local,
                "test_metrics": test_metrics_local,
                "accuracy_ci": accuracy_ci_local,
                "log_loss_ci": log_loss_ci_local,
                "observed_accuracy": observed_accuracy_local,
                "matrix": matrix_local,
            }

        cache_valid = (
            isinstance(FINAL_TEST_CACHE, dict)
            and FINAL_TEST_CACHE.get("run_sequence") == RUN_SEQUENCE
        )
        if cache_valid:
            cache_mode = "reused_without_test_reopening"
        else:
            if TEST_OPENED:
                print("Estado legado detectado; iniciando uma nova confirmação controlada.")
            FINAL_TEST_CACHE = compute_final_test()
            _IRIS_SESSION_TEST_OPENINGS += 1
            confirmation_scope = (
                "confirmatory_first_session_run"
                if _IRIS_SESSION_TEST_OPENINGS == 1
                else "technical_rerun_same_kernel"
            )
            FINAL_TEST_CACHE["confirmation_scope"] = confirmation_scope
            FINAL_TEST_CACHE["session_test_openings"] = _IRIS_SESSION_TEST_OPENINGS
            cache_mode = "computed_once"

        X_test = FINAL_TEST_CACHE["X_test"]
        y_test = FINAL_TEST_CACHE["y_test"]
        X_fit = FINAL_TEST_CACHE["X_fit"]
        y_fit = FINAL_TEST_CACHE["y_fit"]
        fit_features = FINAL_TEST_CACHE["fit_features"]
        test_features = FINAL_TEST_CACHE["test_features"]
        final_classifier = FINAL_TEST_CACHE["final_classifier"]
        classical_classifier = FINAL_TEST_CACHE["classical_classifier"]
        test_probability = FINAL_TEST_CACHE["test_probability"]
        test_prediction = FINAL_TEST_CACHE["test_prediction"]
        classical_probability = FINAL_TEST_CACHE["classical_probability"]
        classical_prediction = FINAL_TEST_CACHE["classical_prediction"]
        test_metrics = FINAL_TEST_CACHE["test_metrics"]
        accuracy_ci = FINAL_TEST_CACHE["accuracy_ci"]
        log_loss_ci = FINAL_TEST_CACHE["log_loss_ci"]
        observed_accuracy = FINAL_TEST_CACHE["observed_accuracy"]
        matrix = FINAL_TEST_CACHE["matrix"]
        confirmation_scope = FINAL_TEST_CACHE["confirmation_scope"]
        TEST_OPENED = True
        TEST_OPEN_COUNT = 1

        assert TEST_OPEN_COUNT == 1
        assert FINAL_TEST_CACHE["run_sequence"] == RUN_SEQUENCE
        display(test_metrics)
        print(f"IC95% Wilson da acurácia híbrida: [{accuracy_ci[0]:.3f}, {accuracy_ci[1]:.3f}]")
        print(f"IC95% bootstrap do log-loss híbrido: [{log_loss_ci[0]:.4f}, {log_loss_ci[1]:.4f}]")

        fig_confusion, axis = plt.subplots(figsize=(5, 4))
        image = axis.imshow(matrix, cmap="Blues")
        for row in range(2):
            for column in range(2):
                axis.text(column, row, matrix[row, column], ha="center", va="center")
        axis.set(
            title="Matriz de confusão — teste reservado",
            xlabel="predito",
            ylabel="verdadeiro",
            xticks=[0, 1],
            yticks=[0, 1],
        )
        fig_confusion.colorbar(image, ax=axis)
        fig_confusion.tight_layout()
        plt.show()
        plt.close(fig_confusion)
        print("Modo da célula final:", cache_mode, "| escopo:", confirmation_scope)
        print("GATE TESTE FINAL: idempotência, métricas, incerteza e matriz aprovadas.")
        ''',
        tags=["confirmation"],
    ),
    code(
        "robustness",
        r'''
        # 9. Robustez exploratória na VALIDAÇÃO (não reutiliza o teste e não é ruído de hardware)
        robustness_train_features = quantum_features(best_bundle, X_train, optimized_theta)
        robustness_classifier = new_classifier()
        robustness_classifier.fit(robustness_train_features, y_train)

        noise_rows = []
        noise_levels = (0.0, 0.05, 0.10, 0.15)
        for noise_index, noise_level in enumerate(noise_levels):
            for replicate in range(SPEC.noise_replicates):
                # SeedSequence impede colisões entre pares (nível, réplica).
                noise_seed = int(
                    np.random.SeedSequence([SEED, noise_index, replicate])
                    .generate_state(1, dtype=np.uint32)[0]
                )
                noise_rng = np.random.default_rng(noise_seed)
                perturbed = np.clip(
                    X_validation + noise_rng.normal(0.0, noise_level, size=X_validation.shape),
                    0.0,
                    1.0,
                )
                perturbed_features = quantum_features(best_bundle, perturbed, optimized_theta)
                prediction = robustness_classifier.predict(perturbed_features)
                noise_rows.append({
                    "partition": "validation_post_selection",
                    "noise_level": noise_level,
                    "replicate": replicate,
                    "noise_seed": noise_seed,
                    "accuracy": accuracy_score(y_validation, prediction),
                })

        noise_results = pd.DataFrame(noise_rows)
        assert len(noise_results) == len(noise_levels) * SPEC.noise_replicates
        assert noise_results["noise_seed"].is_unique
        assert not noise_results.duplicated(["noise_level", "replicate"]).any()
        assert noise_results["accuracy"].between(0.0, 1.0).all()
        noise_summary = noise_results.groupby("noise_level", as_index=False).agg(
            accuracy_mean=("accuracy", "mean"),
            accuracy_std=("accuracy", "std"),
        )
        display(noise_summary)

        fig_noise, axis = plt.subplots(figsize=(7, 4))
        axis.errorbar(
            noise_summary["noise_level"],
            noise_summary["accuracy_mean"],
            yerr=noise_summary["accuracy_std"].fillna(0),
            marker="o",
            capsize=4,
        )
        axis.set(
            title="Robustez exploratória — validação pós-seleção",
            xlabel="desvio-padrão do ruído gaussiano",
            ylabel="acurácia",
            ylim=(0, 1.05),
        )
        axis.grid(alpha=0.25)
        fig_noise.tight_layout()
        plt.show()
        plt.close(fig_noise)
        zero_noise = noise_results.loc[noise_results["noise_level"] == 0.0, "accuracy"]
        assert zero_noise.nunique() == 1
        print("GATE ROBUSTEZ: partição, sementes únicas, réplicas e domínio aprovados.")
        del robustness_train_features, robustness_classifier
        gc.collect()
        ''',
    ),
    code(
        "artifacts",
        r'''
        # 11. Artefatos mínimos para auditoria
        output_dir = Path("/content/iris_qml_results") if Path("/content").exists() else Path("iris_qml_results")
        output_dir.mkdir(parents=True, exist_ok=True)

        architecture_path = output_dir / "architecture_validation.csv"
        landscape_path = output_dir / "landscape_validation.csv"
        noise_path = output_dir / "validation_input_noise_raw.csv"
        metrics_path = output_dir / "test_metrics.csv"
        parameters_path = output_dir / "optimized_parameters.csv"
        history_path = output_dir / "optimization_history.csv"
        manifest_path = output_dir / "manifest.json"

        architecture_results.to_csv(architecture_path, index=False)
        landscape_results.to_csv(landscape_path, index=False)
        noise_results.to_csv(noise_path, index=False)
        test_metrics.to_csv(metrics_path, index=False)
        pd.DataFrame({
            "parameter": [str(symbol) for symbol in best_bundle[3]],
            "initial_value": initial_theta,
            "selected_value": optimized_theta,
        }).to_csv(parameters_path, index=False)
        pd.DataFrame({
            "evaluation": np.arange(1, len(objective_history) + 1),
            "validation_log_loss": objective_history,
        }).to_csv(history_path, index=False)
        manifest = {
            "contract_version": "2.4.0",
            "run_sequence": int(RUN_SEQUENCE),
            "confirmation_scope": confirmation_scope,
            "session_test_openings": int(_IRIS_SESSION_TEST_OPENINGS),
            "final_cell_cache_mode": cache_mode,
            "profile": asdict(SPEC),
            "seed": SEED,
            "noise_seed_strategy": "numpy.SeedSequence([seed, noise_index, replicate])",
            "python": platform.python_version(),
            "packages": {
                "cirq": cirq.__version__,
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "scikit-learn": sklearn.__version__,
            },
            "split_sizes": {
                "train": len(y_train),
                "validation": len(y_validation),
                "test": n_test_reserved,
            },
            "selected_architecture": best_architecture,
            "initial_validation_log_loss": initial_validation_loss,
            "selected_validation_log_loss": optimized_validation_loss,
            "test_metrics": test_metrics.to_dict(orient="records"),
            "hybrid_accuracy_wilson_ci95": accuracy_ci.tolist(),
            "hybrid_log_loss_bootstrap_ci95": log_loss_ci.tolist(),
            "optimization": optimization_record,
            "test_opened_once": bool(TEST_OPENED),
            "test_open_count": int(TEST_OPEN_COUNT),
            "robustness_partition": "validation_post_selection",
        }
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Lista fechada: resíduos de execuções antigas não entram nos hashes nem no ZIP.
        artifact_paths = (
            architecture_path,
            landscape_path,
            noise_path,
            metrics_path,
            parameters_path,
            history_path,
            manifest_path,
        )
        assert all(path.is_file() and path.stat().st_size > 0 for path in artifact_paths)
        hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in artifact_paths
        }
        sha_path = output_dir / "sha256.json"
        sha_path.write_text(
            json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8"
        )
        archive_members = (*artifact_paths, sha_path)
        archive = output_dir.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in archive_members:
                bundle.write(path, arcname=path.name)

        for path in artifact_paths:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == hashes[path.name]
        with zipfile.ZipFile(archive) as bundle:
            assert sorted(bundle.namelist()) == sorted(path.name for path in archive_members)

        print("Resultados:", output_dir.resolve())
        print("Arquivo ZIP:", archive.resolve())
        print("GATE ARTEFATOS: conjunto fechado, hashes e conteúdo do ZIP aprovados.")
        print("GATE FINAL: todas as células concluídas sem recriar modelos TensorFlow em loops.")
        ''',
        tags=["artifacts", "gate"],
    ),
    markdown(
        "limits",
        r'''
        ## 12. Interpretação e limites

        - O teste contém somente 20 flores; acurácia de 100% pode ocorrer e não prova superioridade do método.
        - Este é um simulador clássico de quatro qubits, não execução em QPU e não evidência de vantagem quântica.
        - A busca compara três ansätze em uma única divisão; uma publicação exigiria validação cruzada aninhada com sementes externas.
        - O ensaio de robustez perturba a validação depois da seleção; é diagnóstico exploratório e não uma estimativa confirmatória independente.
        - O teste fica selado até a célula confirmatória; repetir apenas essa célula reutiliza o cache, enquanto uma nova execução completa é registrada como réplica técnica.
        - TFQ é uma camada TensorFlow–Cirq. A documentação oficial limita o suporte binário normal a Python 3.10–3.12; em Python 3.13 deve-se usar outro runtime ou a rota Cirq deste notebook.

        Referências: [TensorFlow Quantum — instalação](https://www.tensorflow.org/quantum/install), [Cirq](https://quantumai.google/cirq), [Iris dataset](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_iris.html).
        ''',
    ),
]

# A análise de robustez é deliberadamente anterior à única abertura confirmatória.
CELL_ORDER = (
    "title",
    "project-presentation",
    "author-presentation",
    "instructions",
    "setup",
    "imports-config",
    "protocol",
    "data",
    "quantum-model",
    "circuits",
    "features-tests",
    "architecture-selection",
    "optimization",
    "landscape",
    "robustness",
    "final-test",
    "artifacts",
    "limits",
)
cells_by_id = {cell["id"]: cell for cell in cells}
assert len(cells_by_id) == len(cells) == len(CELL_ORDER)
assert set(cells_by_id) == set(CELL_ORDER)
cells = [cells_by_id[cell_id] for cell_id in CELL_ORDER]


notebook = {
    "cells": cells,
    "metadata": {
        "colab": {
            "include_colab_link": True,
            "name": DESTINATION.name,
            "provenance": [],
        },
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

DESTINATION.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)
print(DESTINATION)
