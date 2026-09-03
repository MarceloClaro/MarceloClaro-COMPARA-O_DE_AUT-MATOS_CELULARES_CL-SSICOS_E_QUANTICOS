"""Núcleo matemático independente de framework do experimento ECA/QCA.

Convenção canônica: célula 0 é o primeiro bit visual e o mais significativo;
o vetor conjunto usa ``x0..x(n-1), y0..y(n-1)`` e fronteira periódica.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json, math
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import numpy as np

SUPPORTED_RULES = (30, 60, 90)

@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    n_cells: int
    deterministic_state_ids: tuple[int, ...]
    noise_state_ids: tuple[int, ...]
    bitflip_probabilities: tuple[float, ...]
    base_seeds: tuple[int, ...]
    shots: int
    bootstrap_resamples: int
    benchmark_repetitions: int
    rules: tuple[int, ...] = SUPPORTED_RULES
    boundary: str = "periodic"
    def __post_init__(self):
        if self.name not in {"smoke", "paper"}: raise ValueError("profile deve ser smoke ou paper")
        if self.n_cells < 3: raise ValueError("n_cells deve ser >= 3")
        if self.boundary != "periodic": raise ValueError("fronteira deve ser periódica")
        if any(r not in range(256) for r in self.rules): raise ValueError("regra inválida")
        ids = self.deterministic_state_ids + self.noise_state_ids
        if any(i < 0 or i >= 1 << self.n_cells for i in ids): raise ValueError("state_id inválido")
        if self.shots <= 0 or self.bootstrap_resamples <= 0: raise ValueError("contagens devem ser positivas")
        if any(p < 0 or p > .5 for p in self.bitflip_probabilities): raise ValueError("p fora de [0,.5]")
        if len(set(self.base_seeds)) != len(self.base_seeds): raise ValueError("sementes repetidas")
    def to_dict(self):
        d = asdict(self)
        return {k: list(v) if isinstance(v, tuple) else v for k, v in d.items()}

PROFILE_SPECS: Mapping[str, ExperimentSpec] = {
 "smoke": ExperimentSpec("smoke",3,tuple(range(8)),(1,6),(0.,.1,.25),(20260903,20260917),512,1000,2),
 # Sementes confirmatórias congeladas após a Emenda 1 do protocolo. Elas são
 # disjuntas das sementes usadas na execução-piloto descrita em PROTOCOL.md.
 "paper": ExperimentSpec("paper",5,tuple(range(32)),(1,3,5,9,17,21,26,30),(0.,.01,.03,.05,.1,.2,.3),(104729,130363,155921,181081,206369),4096,10000,5),
}

def _bits(bits: Sequence[int], name="state"):
    b=tuple(int(x) for x in bits)
    if not b or any(x not in (0,1) for x in b): raise ValueError(f"{name} deve conter bits")
    return b
def index_from_bits(bits):
    v=0
    for b in _bits(bits,"bits"): v=(v<<1)|b
    return v
def bits_from_index(index,width):
    if width<1 or index<0 or index>=1<<width: raise ValueError("índice/largura inválido")
    return tuple((index>>s)&1 for s in range(width-1,-1,-1))
def wolfram_local(rule,left,center,right):
    if rule not in range(256): raise ValueError("rule deve estar entre 0 e 255")
    l,c,r=_bits((left,center,right),"vizinhança")
    return (rule>>(4*l+2*c+r))&1
def truth_table(rule):
    if rule not in range(256): raise ValueError("regra inválida")
    return tuple((*bits_from_index(a,3),(rule>>a)&1) for a in range(7,-1,-1))
def eca_step(state,rule,*,boundary="periodic"):
    x=_bits(state)
    if len(x)<3: raise ValueError("mínimo de três células")
    if boundary!="periodic": raise ValueError("somente fronteira periódica")
    n=len(x); return tuple(wolfram_local(rule,x[(i-1)%n],x[i],x[(i+1)%n]) for i in range(n))
def eca_evolve(initial,rule,steps,*,boundary="periodic"):
    if steps<0: raise ValueError("steps negativo")
    rows=[_bits(initial,"initial")]
    for _ in range(steps): rows.append(eca_step(rows[-1],rule,boundary=boundary))
    return np.asarray(rows,dtype=np.uint8)
def oracle_basis_output(x,rule,y=None):
    xb=_bits(x,"x"); yb=(0,)*len(xb) if y is None else _bits(y,"y")
    if len(xb)!=len(yb): raise ValueError("x/y incompatíveis")
    fx=eca_step(xb,rule); return xb,tuple(a^b for a,b in zip(yb,fx,strict=True))
def apply_reversible_oracle(amplitudes,rule,n_cells):
    v=np.asarray(amplitudes,dtype=np.complex128).reshape(-1)
    if v.size != 1<<(2*n_cells): raise ValueError("dimensão inválida")
    out=np.zeros_like(v)
    for xi in range(1<<n_cells):
        fx=index_from_bits(eca_step(bits_from_index(xi,n_cells),rule))
        for yi in range(1<<n_cells): out[(xi<<n_cells)|(yi^fx)]=v[(xi<<n_cells)|yi]
    return out
def oracle_statevector(rule,n_cells,*,initial=None,plus_input=False):
    if (initial is None)==(not plus_input): raise ValueError("use initial ou plus_input")
    v=np.zeros(1<<(2*n_cells),dtype=np.complex128)
    if plus_input:
        amp=1/math.sqrt(1<<n_cells)
        for xi in range(1<<n_cells):
            x=bits_from_index(xi,n_cells); v[(xi<<n_cells)|index_from_bits(eca_step(x,rule))]=amp
    else:
        x=_bits(initial,"initial")
        if len(x)!=n_cells: raise ValueError("initial incompatível")
        _,y=oracle_basis_output(x,rule); v[index_from_bits(x+y)]=1
    return v
def fidelity(a,b):
    a=np.asarray(a,dtype=np.complex128).reshape(-1); b=np.asarray(b,dtype=np.complex128).reshape(-1)
    if a.shape!=b.shape or np.vdot(a,a).real<=0 or np.vdot(b,b).real<=0: raise ValueError("vetores inválidos")
    return float(np.clip(abs(np.vdot(a,b))**2/(np.vdot(a,a).real*np.vdot(b,b).real),0,1))
def align_global_phase(candidate,reference):
    c=np.asarray(candidate,dtype=np.complex128).reshape(-1); r=np.asarray(reference,dtype=np.complex128).reshape(-1); z=np.vdot(r,c)
    return c.copy() if abs(z)==0 else c*np.exp(-1j*np.angle(z))
def max_phase_aligned_error(candidate,reference):
    return float(np.max(np.abs(align_global_phase(candidate,reference)-np.asarray(reference).reshape(-1))))
def output_z_expectations(statevector,n_cells):
    v=np.asarray(statevector).reshape(-1)
    if v.size!=1<<(2*n_cells): raise ValueError("dimensão inválida")
    out=np.zeros(n_cells); mask=(1<<n_cells)-1
    for idx,p in enumerate(abs(v)**2):
        yi=idx&mask
        for c in range(n_cells): out[c]+=p*(1 if ((yi>>(n_cells-1-c))&1)==0 else -1)
    return out
def von_neumann_entropy_input(statevector,n_cells):
    v=np.asarray(statevector,dtype=np.complex128).reshape(-1); d=1<<n_cells
    if v.size!=d*d: raise ValueError("dimensão inválida")
    m=v.reshape(d,d); eig=np.linalg.eigvalsh(m@m.conj().T).real; eig=eig[eig>1e-14]
    return float(max(0.,-np.sum(eig*np.log2(eig)))) if eig.size else 0.
def derive_seed(*parts,modulus=2**32-1):
    raw=json.dumps(parts,ensure_ascii=False,separators=(",",":"),default=str).encode()
    return int.from_bytes(sha256(raw).digest()[:8],"big")%modulus
def sample_output_bitflip(expected,probability,shots,simulator_seed):
    b=np.asarray(_bits(expected,"expected"),dtype=np.uint8)
    if not 0<=probability<=.5 or shots<=0: raise ValueError("parâmetros de ruído inválidos")
    flips=np.random.default_rng(int(simulator_seed)).random((shots,b.size))<probability
    return float(flips.mean()),float((~np.any(flips,axis=1)).mean())
def bootstrap_percentile_ci(values,*,resamples,seed,confidence=.95):
    x=np.asarray(values,dtype=float).reshape(-1)
    if not x.size or not np.all(np.isfinite(x)) or resamples<=0 or not 0<confidence<1: raise ValueError("bootstrap inválido")
    draw=np.random.default_rng(int(seed)).integers(0,x.size,size=(resamples,x.size)); means=x[draw].mean(axis=1); t=(1-confidence)/2
    return tuple(float(v) for v in np.quantile(means,(t,1-t)))
def sha256_file(path):
    h=sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""): h.update(chunk)
    return h.hexdigest()
def stable_json(data): return json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
def quartiles(values: Iterable[float]):
    x=np.asarray(tuple(values),dtype=float)
    if not x.size: raise ValueError("sem valores")
    return tuple(float(v) for v in np.quantile(x,(.25,.5,.75)))
