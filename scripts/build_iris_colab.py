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

        1. Use **Ambiente de execução → Desconectar e excluir ambiente de execução** para remover objetos da versão antiga.
        2. Abra novamente este notebook a partir do GitHub.
        3. Execute **uma célula por vez** na primeira tentativa.
        4. Mantenha `PROFILE = "smoke"`. Depois que ele terminar, **reinicie o runtime**, selecione `"full"` e execute novamente desde o início.

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
        import subprocess
        import sys
        from importlib.metadata import PackageNotFoundError, version as distribution_version

        missing = []
        requirements = {
            "cirq": "cirq-core==1.6.1",
            "sklearn": "scikit-learn>=1.4,<2",
            "scipy": "scipy>=1.16,<2",
            "matplotlib": "matplotlib>=3.8,<4",
            "pandas": "pandas>=2.0,<3",
        }
        for module, requirement in requirements.items():
            if importlib.util.find_spec(module) is None:
                missing.append(requirement)

        def installed_version(distribution):
            try:
                return distribution_version(distribution)
            except PackageNotFoundError:
                return None

        def major_minor(distribution):
            try:
                return tuple(int(part) for part in installed_version(distribution).split(".")[:2])
            except (AttributeError, ValueError):
                return (0, 0)

        if importlib.util.find_spec("cirq") is not None and installed_version("cirq-core") != "1.6.1":
            missing.append("cirq-core==1.6.1")
        if importlib.util.find_spec("scipy") is not None and major_minor("scipy") < (1, 16):
            missing.append("scipy>=1.16,<2")
        missing = list(dict.fromkeys(missing))

        if missing and os.environ.get("IRIS_SKIP_INSTALL", "0") != "1":
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", *missing], check=True)

        print("Python real:", platform.python_version())
        print("Plataforma:", platform.platform())
        print("Dependências instaladas ou ajustadas:", missing or "nenhuma")
        print("TFQ suportado oficialmente por versão de Python:", (3, 10) <= sys.version_info[:2] <= (3, 12))
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

        print("Perfil:", asdict(SPEC))
        print("Cirq:", cirq.__version__, "| NumPy:", np.__version__, "| SciPy:", scipy.__version__, "| scikit-learn:", sklearn.__version__)
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
        - H5: um gate de estado impede que o conjunto de teste seja aberto duas vezes no mesmo runtime.

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

        input_scaler = MinMaxScaler(feature_range=(0, 1), clip=True)
        X_train = input_scaler.fit_transform(X_raw[train_ids])
        X_validation = input_scaler.transform(X_raw[validation_ids])
        y_train, y_validation = y[train_ids], y[validation_ids]

        # O teste permanece apenas como índices opacos até a célula confirmatória.
        if globals().get("TEST_OPENED", False):
            raise RuntimeError("O teste já foi aberto. Reinicie o runtime para uma nova execução.")
        TEST_OPENED = False
        n_test_reserved = len(test_ids)

        split_table = pd.DataFrame({
            "partição": ["treino", "validação", "teste reservado"],
            "n": [len(y_train), len(y_validation), n_test_reserved],
            "classe_0": [int((y_train == 0).sum()), int((y_validation == 0).sum()), "selado"],
            "classe_1": [int((y_train == 1).sum()), int((y_validation == 1).sum()), "selado"],
        })
        display(split_table)
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
        for name, (circuit, _, _, theta_symbols) in CIRCUITS.items():
            print(f"{name}: momentos={len(circuit)}, parâmetros={len(theta_symbols)}")
            print(circuit)
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
        probe_a = quantum_features(CIRCUITS["linear"], X_train[:3], initial_theta)
        probe_b = quantum_features(CIRCUITS["linear"], X_train[:3], initial_theta)
        assert probe_a.shape == (3, 4)
        assert np.isfinite(probe_a).all()
        assert np.max(np.abs(probe_a)) <= 1 + 1e-7
        np.testing.assert_allclose(probe_a, probe_b, atol=1e-7)
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
            architecture_rows.append({
                "architecture": name,
                "validation_log_loss": log_loss(y_validation, validation_probability, labels=[0, 1]),
                "validation_accuracy": accuracy_score(y_validation, validation_probability >= 0.5),
                "seconds": time.perf_counter() - started,
            })
            del train_features, validation_features, classifier
            gc.collect()

        architecture_results = pd.DataFrame(architecture_rows).sort_values("validation_log_loss")
        display(architecture_results)
        best_architecture = str(architecture_results.iloc[0]["architecture"])
        best_bundle = CIRCUITS[best_architecture]
        print("Arquitetura escolhida sem consultar o teste:", best_architecture)
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
        if optimized_validation_loss > initial_validation_loss:
            optimized_theta = initial_theta.copy()
            optimized_validation_loss = initial_validation_loss

        optimization_seconds = time.perf_counter() - optimization_started
        optimization_record = {
            "success": bool(optimization.success),
            "status": int(optimization.status),
            "message": str(optimization.message),
            "nfev": int(optimization.nfev),
            "maxfun": SPEC.cobyla_maxfun,
            "tol": SPEC.cobyla_tol,
            "f_target": SPEC.cobyla_f_target,
            "seconds": optimization_seconds,
        }
        print("COBYLA:", optimization_record)
        print(f"Log-loss inicial={initial_validation_loss:.6f}; selecionado={optimized_validation_loss:.6f}")
        if not optimization.success:
            raise RuntimeError(
                "GATE COBYLA FALHOU: o critério de parada não foi satisfeito. "
                "Não interprete os parâmetros como convergidos."
            )
        assert optimized_validation_loss <= initial_validation_loss + 1e-12
        print("GATE COBYLA: critério de parada satisfeito.")
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

        fig_landscape, axis = plt.subplots(figsize=(7, 4))
        axis.plot(grid, landscape_loss, marker="o")
        axis.axvline(optimized_theta[0], color="tab:red", linestyle="--", label="θ selecionado")
        axis.set(title="Corte exploratório da perda de validação", xlabel="θ₀", ylabel="log-loss")
        axis.grid(alpha=0.25)
        axis.legend()
        fig_landscape.tight_layout()
        plt.show()
        plt.close(fig_landscape)
        ''',
    ),
    code(
        "final-test",
        r'''
        # 9. Confirmação: ajuste final em treino+validação e uma única abertura do teste
        if TEST_OPENED:
            raise RuntimeError("O teste já foi aberto. Reinicie o runtime antes de repetir a confirmação.")
        X_test = input_scaler.transform(X_raw[test_ids])
        y_test = y[test_ids]
        TEST_OPENED = True

        X_fit = np.vstack((X_train, X_validation))
        y_fit = np.concatenate((y_train, y_validation))
        fit_features = quantum_features(best_bundle, X_fit, optimized_theta)
        test_features = quantum_features(best_bundle, X_test, optimized_theta)

        final_classifier = new_classifier()
        final_classifier.fit(fit_features, y_fit)
        test_probability = final_classifier.predict_proba(test_features)[:, 1]
        test_prediction = (test_probability >= 0.5).astype(np.int64)

        # Comparador clássico pré-especificado: mesma divisão e mesma família de classificador.
        classical_classifier = new_classifier()
        classical_classifier.fit(X_fit, y_fit)
        classical_probability = classical_classifier.predict_proba(X_test)[:, 1]
        classical_prediction = (classical_probability >= 0.5).astype(np.int64)

        def metric_row(model_name, probability, prediction):
            return {
                "model": model_name,
                "accuracy": accuracy_score(y_test, prediction),
                "balanced_accuracy": balanced_accuracy_score(y_test, prediction),
                "f1": f1_score(y_test, prediction),
                "roc_auc": roc_auc_score(y_test, probability),
                "log_loss": log_loss(y_test, probability, labels=[0, 1]),
            }

        final_metrics = metric_row("hybrid_cirq", test_probability, test_prediction)
        classical_metrics = metric_row(
            "classical_logistic_regression", classical_probability, classical_prediction
        )
        test_metrics = pd.DataFrame([final_metrics, classical_metrics])

        bootstrap_rng = np.random.default_rng(SEED + 1)
        bootstrap_log_loss = []
        for _ in range(SPEC.bootstrap_resamples):
            sampled = bootstrap_rng.integers(0, len(y_test), len(y_test))
            bootstrap_log_loss.append(
                log_loss(y_test[sampled], test_probability[sampled], labels=[0, 1])
            )
        log_loss_ci = np.quantile(bootstrap_log_loss, [0.025, 0.975])

        # Wilson não colapsa para [1, 1] quando a amostra pequena não contém erros.
        test_size = len(y_test)
        correct = int(np.sum(y_test == test_prediction))
        observed_accuracy = correct / test_size
        z_95 = 1.959963984540054
        denominator = 1 + z_95**2 / test_size
        center = (observed_accuracy + z_95**2 / (2 * test_size)) / denominator
        radius = (
            z_95
            * np.sqrt(
                observed_accuracy * (1 - observed_accuracy) / test_size
                + z_95**2 / (4 * test_size**2)
            )
            / denominator
        )
        accuracy_ci = np.clip([center - radius, center + radius], 0.0, 1.0)

        display(test_metrics)
        print(f"IC95% Wilson da acurácia híbrida: [{accuracy_ci[0]:.3f}, {accuracy_ci[1]:.3f}]")
        print(f"IC95% bootstrap do log-loss híbrido: [{log_loss_ci[0]:.4f}, {log_loss_ci[1]:.4f}]")
        assert accuracy_ci[0] <= observed_accuracy <= accuracy_ci[1]

        matrix = confusion_matrix(y_test, test_prediction)
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
        ''',
        tags=["confirmation"],
    ),
    code(
        "robustness",
        r'''
        # 10. Robustez exploratória na VALIDAÇÃO (não reutiliza o teste e não é ruído de hardware)
        robustness_train_features = quantum_features(best_bundle, X_train, optimized_theta)
        robustness_classifier = new_classifier()
        robustness_classifier.fit(robustness_train_features, y_train)

        noise_rows = []
        for noise_level in (0.0, 0.05, 0.10, 0.15):
            for replicate in range(SPEC.noise_replicates):
                noise_rng = np.random.default_rng(SEED + 1_000 * replicate + int(noise_level * 10_000))
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
                    "accuracy": accuracy_score(y_validation, prediction),
                })

        noise_results = pd.DataFrame(noise_rows)
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

        architecture_results.to_csv(output_dir / "architecture_validation.csv", index=False)
        noise_results.to_csv(output_dir / "validation_input_noise_raw.csv", index=False)
        test_metrics.to_csv(output_dir / "test_metrics.csv", index=False)
        manifest = {
            "profile": asdict(SPEC),
            "seed": SEED,
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
            "robustness_partition": "validation_post_selection",
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        artifact_paths = sorted(output_dir.glob("*"))
        hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in artifact_paths
            if path.is_file() and path.name != "sha256.json"
        }
        (output_dir / "sha256.json").write_text(
            json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8"
        )
        archive = output_dir.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(output_dir.glob("*")):
                bundle.write(path, arcname=path.name)

        print("Resultados:", output_dir.resolve())
        print("Arquivo ZIP:", archive.resolve())
        print("GATE FINAL: notebook concluído sem recriar modelos TensorFlow em loops.")
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
        - O teste fica selado até a célula confirmatória e um gate impede sua segunda abertura no mesmo runtime.
        - TFQ é uma camada TensorFlow–Cirq. A documentação oficial limita o suporte binário normal a Python 3.10–3.12; em Python 3.13 deve-se usar outro runtime ou a rota Cirq deste notebook.

        Referências: [TensorFlow Quantum — instalação](https://www.tensorflow.org/quantum/install), [Cirq](https://quantumai.google/cirq), [Iris dataset](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_iris.html).
        ''',
    ),
]


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
