"""Implementações equivalentes em Qiskit, PennyLane e Cirq; TFQ é integração."""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
from typing import Mapping, Sequence
import numpy as np
from .core import truth_table

BACKENDS=("qiskit","pennylane","cirq")
def _request(rule,n,initial,plus):
    if n<3 or rule not in range(256): raise ValueError("regra/tamanho inválido")
    if plus==(initial is not None): raise ValueError("use initial ou plus_input")
    if initial is None:return None
    b=tuple(int(x) for x in initial)
    if len(b)!=n or any(x not in (0,1) for x in b): raise ValueError("initial inválido")
    return b
def _mins(rule): return tuple(row[:3] for row in truth_table(rule) if row[3])
def _near(i,n): return ((i-1)%n,i,(i+1)%n)

def build_qiskit_circuit(rule,n_cells,*,initial=None,plus_input=False):
    bits=_request(rule,n_cells,initial,plus_input)
    from qiskit import QuantumCircuit
    qc=QuantumCircuit(2*n_cells,name=f"UF_{rule}")
    for q in range(n_cells):
        if plus_input: qc.h(q)
        elif bits[q]: qc.x(q)
    for cell in range(n_cells):
        controls=list(_near(cell,n_cells)); target=n_cells+cell
        for pattern in _mins(rule):
            zeros=[q for q,v in zip(controls,pattern,strict=True) if not v]
            for q in zeros: qc.x(q)
            qc.mcx(controls,target)
            for q in reversed(zeros): qc.x(q)
    return qc
def qiskit_statevector(rule,n_cells,*,initial=None,plus_input=False):
    from qiskit.quantum_info import Statevector
    v=np.asarray(Statevector.from_instruction(build_qiskit_circuit(rule,n_cells,initial=initial,plus_input=plus_input)).data,dtype=np.complex128)
    return v.reshape((2,)*(2*n_cells)).transpose(tuple(reversed(range(2*n_cells)))).reshape(-1)

def build_pennylane_qnode(rule,n_cells,*,initial=None,plus_input=False):
    bits=_request(rule,n_cells,initial,plus_input); import pennylane as qml
    dev=qml.device("default.qubit",wires=list(range(2*n_cells)),shots=None)
    @qml.qnode(dev,interface=None,diff_method=None)
    def circuit():
        for q in range(n_cells):
            if plus_input:qml.Hadamard(q)
            elif bits[q]:qml.PauliX(q)
        for cell in range(n_cells):
            controls=list(_near(cell,n_cells)); target=n_cells+cell
            for pattern in _mins(rule):
                zeros=[q for q,v in zip(controls,pattern,strict=True) if not v]
                for q in zeros:qml.PauliX(q)
                qml.MultiControlledX(wires=controls+[target])
                for q in reversed(zeros):qml.PauliX(q)
        return qml.state()
    return circuit
def pennylane_statevector(rule,n_cells,*,initial=None,plus_input=False):
    return np.asarray(build_pennylane_qnode(rule,n_cells,initial=initial,plus_input=plus_input)(),dtype=np.complex128).reshape(-1)

def build_cirq_circuit(rule,n_cells,*,initial=None,plus_input=False):
    bits=_request(rule,n_cells,initial,plus_input); import cirq
    q=list(cirq.LineQubit.range(2*n_cells)); c=cirq.Circuit()
    if plus_input:c.append(cirq.H(q[i]) for i in range(n_cells))
    else:c.append(cirq.X(q[i]) for i,b in enumerate(bits) if b)
    for cell in range(n_cells):
        controls=list(_near(cell,n_cells)); target=n_cells+cell
        for pattern in _mins(rule):
            zeros=[i for i,v in zip(controls,pattern,strict=True) if not v]
            c.append(cirq.X(q[i]) for i in zeros)
            c.append(cirq.X(q[target]).controlled_by(*(q[i] for i in controls)))
            c.append(cirq.X(q[i]) for i in reversed(zeros))
    return c
def cirq_statevector(rule,n_cells,*,initial=None,plus_input=False):
    import cirq
    q=list(cirq.LineQubit.range(2*n_cells)); c=build_cirq_circuit(rule,n_cells,initial=initial,plus_input=plus_input)
    return np.asarray(cirq.Simulator(dtype=np.complex128).simulate(c,qubit_order=q).final_state_vector,dtype=np.complex128)
ADAPTERS:Mapping[str,object]={"qiskit":qiskit_statevector,"pennylane":pennylane_statevector,"cirq":cirq_statevector}
def statevector(backend,rule,n_cells,*,initial=None,plus_input=False):
    if backend not in ADAPTERS:raise ValueError(f"backend inválido: {backend}")
    return ADAPTERS[backend](rule,n_cells,initial=initial,plus_input=plus_input)

def tfq_batch_expectations(cases:Sequence[dict],timeout=600):
    if not cases:return []
    env=os.environ.copy(); env.update(TF_USE_LEGACY_KERAS="1",TF_CPP_MIN_LOG_LEVEL="3",CUDA_VISIBLE_DEVICES="-1")
    root=str(Path(__file__).resolve().parents[1]); env["PYTHONPATH"]=root+((os.pathsep+env["PYTHONPATH"]) if env.get("PYTHONPATH") else "")
    p=subprocess.run([sys.executable,"-m","eca_qca_lab.tfq_worker"],input=json.dumps(list(cases)),text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=timeout)
    marker="TFQ_RESULT_JSON="; pos=p.stdout.rfind(marker)
    if p.returncode or pos<0:raise RuntimeError("worker TFQ falhou: "+(p.stderr or p.stdout)[-4000:])
    result=json.loads(p.stdout[pos+len(marker):].strip())
    if len(result)!=len(cases):raise RuntimeError("resposta TFQ incompatível")
    return result
