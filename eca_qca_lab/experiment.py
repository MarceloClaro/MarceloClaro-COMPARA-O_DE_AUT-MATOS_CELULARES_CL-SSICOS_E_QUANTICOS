"""Orquestra os gates, estatística e artefatos auditáveis do laboratório."""
from __future__ import annotations
from collections import defaultdict
import csv,itertools,json,os,platform,subprocess,sys,time,zipfile
from datetime import datetime,timezone
import importlib.metadata
from pathlib import Path
import numpy as np
from .adapters import BACKENDS,statevector,tfq_batch_expectations
from .core import *

PRIMARY_ARTIFACTS=("basis_parity.csv","statevector_parity.csv","coherent_states.csv","tfq_integration.csv","noise_raw.csv","noise_summary.csv","benchmark_raw.csv","benchmark_summary.csv","figure_noise.png","figure_benchmark.png")
SCHEMA_VERSION="3.2"
FAMILYWISE_ALPHA=.05
def _csv(path,rows):
    if not rows:raise ValueError(f"sem linhas: {path}")
    fields=[]
    for row in rows:
        for k in row:
            if k not in fields:fields.append(k)
    def cv(v):
        if isinstance(v,(tuple,list,dict)):return json.dumps(v,ensure_ascii=False,separators=(",",":"))
        if isinstance(v,(bool,np.bool_)):return str(bool(v)).lower()
        if isinstance(v,np.generic):return v.item()
        return v
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in rows:w.writerow({k:cv(row.get(k,"")) for k in fields})
def _versions():
    names={"numpy":"numpy","qiskit":"qiskit","qiskit_aer":"qiskit-aer","pennylane":"PennyLane","cirq_core":"cirq-core","tensorflow":"tensorflow","tf_keras":"tf-keras","tensorflow_quantum":"tensorflow-quantum","pyparsing":"pyparsing"};out={}
    for k,n in names.items():
        try:out[k]=importlib.metadata.version(n)
        except importlib.metadata.PackageNotFoundError:out[k]=None
    return out
def _git(root):
    def run(*a):
        p=subprocess.run(["git",*a],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL);return p.stdout.strip() if p.returncode==0 else None
    status=run("status","--porcelain");return {"commit":run("rev-parse","HEAD"),"tree":run("rev-parse","HEAD^{tree}"),"branch":run("rev-parse","--abbrev-ref","HEAD"),"dirty":None if status is None else bool(status)}
def _basis_coherent(spec):
    basis=[];pairs=[];coherent=[];cases=[]
    for rule in spec.rules:
      for sid in spec.deterministic_state_ids:
        initial=bits_from_index(sid,spec.n_cells);expected=eca_step(initial,rule);reference=oracle_statevector(rule,spec.n_cells,initial=initial);vectors={}
        for backend in BACKENDS:
          t=time.perf_counter();v=statevector(backend,rule,spec.n_cells,initial=initial);dt=time.perf_counter()-t;vectors[backend]=v
          pe=float(np.max(np.abs(abs(v)**2-abs(reference)**2)));fid=fidelity(v,reference);phase=max_phase_aligned_error(v,reference)
          basis.append({"profile":spec.name,"rule":rule,"state_id":sid,"initial":initial,"expected":expected,"backend":backend,"passed":pe<=(1e-7 if backend=="cirq" else 1e-12) and fid>=1-2e-7,"max_probability_error":pe,"max_phase_error":phase,"fidelity_to_reference":fid,"runtime_seconds":dt})
        for a,b in itertools.combinations(BACKENDS,2):
          fid=fidelity(vectors[a],vectors[b]);pairs.append({"profile":spec.name,"mode":"basis","rule":rule,"state_id":sid,"pair":f"{a}__{b}","fidelity":fid,"max_phase_error":max_phase_aligned_error(vectors[a],vectors[b]),"passed":fid>=1-2e-7})
        cases.append({"rule":rule,"n_cells":spec.n_cells,"mode":"basis","state_id":sid,"initial":list(initial)})
    for rule in spec.rules:
      ref=oracle_statevector(rule,spec.n_cells,plus_input=True);vectors={}
      for backend in BACKENDS:
        t=time.perf_counter();v=statevector(backend,rule,spec.n_cells,plus_input=True);dt=time.perf_counter()-t;vectors[backend]=v;fid=fidelity(v,ref)
        coherent.append({"profile":spec.name,"rule":rule,"backend":backend,"input_state":"|+>^n|0>^n","fidelity_to_reference":fid,"max_phase_error":max_phase_aligned_error(v,ref),"input_output_entropy_bits":von_neumann_entropy_input(v,spec.n_cells),"runtime_seconds":dt,"passed":fid>=1-2e-7})
      for a,b in itertools.combinations(BACKENDS,2):
        fid=fidelity(vectors[a],vectors[b]);pairs.append({"profile":spec.name,"mode":"plus","rule":rule,"state_id":"","pair":f"{a}__{b}","fidelity":fid,"max_phase_error":max_phase_aligned_error(vectors[a],vectors[b]),"passed":fid>=1-2e-7})
      cases.append({"rule":rule,"n_cells":spec.n_cells,"mode":"plus","state_id":None,"initial":None})
    return basis,pairs,coherent,cases
def _tfq(spec,cases,required):
    try:values=tfq_batch_expectations(cases)
    except Exception as e:
      if required:raise
      return [{"profile":spec.name,"available":False,"passed":False,"reason":f"{type(e).__name__}: {e}"}],False,str(e)
    rows=[]
    for case,observed in zip(cases,values,strict=True):
      ref=oracle_statevector(int(case["rule"]),spec.n_cells,plus_input=True) if case["mode"]=="plus" else oracle_statevector(int(case["rule"]),spec.n_cells,initial=case["initial"])
      expected=output_z_expectations(ref,spec.n_cells)
      kwargs={"plus_input":True} if case["mode"]=="plus" else {"initial":case["initial"]}
      cirq_values=output_z_expectations(statevector("cirq",int(case["rule"]),spec.n_cells,**kwargs),spec.n_cells)
      if len(observed)!=spec.n_cells:raise RuntimeError("TFQ: observáveis incompatíveis")
      for cell,(actual,target,cirq_value) in enumerate(zip(observed,expected,cirq_values,strict=True)):
        error=abs(float(actual)-float(cirq_value));analytic_error=abs(float(actual)-float(target));cirq_error=abs(float(cirq_value)-float(target))
        rows.append({"profile":spec.name,"available":True,"rule":case["rule"],"mode":case["mode"],"state_id":"" if case["state_id"] is None else case["state_id"],"output_cell":cell,"cirq_reference_z":float(cirq_value),"analytical_reference_z":float(target),"tfq_z":float(actual),"absolute_error":error,"analytical_absolute_error":analytic_error,"cirq_analytical_absolute_error":cirq_error,"passed":error<=2e-5 and analytic_error<=2e-5 and cirq_error<=2e-5})
    return rows,True,None
def _noise(spec):
    raw=[]
    for rule in spec.rules:
      for sid in spec.noise_state_ids:
       initial=bits_from_index(sid,spec.n_cells);expected=eca_step(initial,rule)
       for p in spec.bitflip_probabilities:
        for base in spec.base_seeds:
         seed=derive_seed("eca-qca-noise-v3",spec.name,rule,sid,p,base);ber,exact=sample_output_bitflip(expected,p,spec.shots,seed)
         for backend in BACKENDS:raw.append({"profile":spec.name,"rule":rule,"state_id":sid,"initial":initial,"expected":expected,"backend":backend,"bitflip_probability":p,"base_seed":base,"simulator_seed":seed,"unit_id":f"{spec.name}:{rule}:{sid}:{p}:{base}","noise_model":"independent_output_bitflip","sampler":"numpy.PCG64","backend_pairing":"same_realization","shots":spec.shots,"bit_error_rate":ber,"exact_state_success":exact,"theoretical_ber":p,"theoretical_exact_success":(1-p)**spec.n_cells})
    groups=defaultdict(list)
    for r in raw:groups[(r["backend"],r["rule"],r["bitflip_probability"])].append(r)
    simultaneous_checks=2*len(groups) # BER e sucesso exato em cada estrato
    summary=[]
    for (backend,rule,p),rows in sorted(groups.items()):
      bers=[x["bit_error_rate"] for x in rows]; exacts=[x["exact_state_success"] for x in rows]
      bci=bootstrap_percentile_ci(bers,resamples=spec.bootstrap_resamples,seed=derive_seed("boot-ber",spec.name,backend,rule,p));eci=bootstrap_percentile_ci(exacts,resamples=spec.bootstrap_resamples,seed=derive_seed("boot-exact",spec.name,backend,rule,p));theory=(1-p)**spec.n_cells
      ber_mean=float(np.mean(bers));exact_mean=float(np.mean(exacts));n_ber=len(rows)*spec.shots*spec.n_cells;n_exact=len(rows)*spec.shots
      # União de Hoeffding: K*2*exp(-2*N*epsilon^2) <= alpha. A banda
      # controla simultaneamente todos os estratos sem aproximação normal.
      ber_width=np.sqrt(np.log(2*simultaneous_checks/FAMILYWISE_ALPHA)/(2*n_ber))
      exact_width=np.sqrt(np.log(2*simultaneous_checks/FAMILYWISE_ALPHA)/(2*n_exact))
      summary.append({"profile":spec.name,"backend":backend,"rule":rule,"bitflip_probability":p,"experimental_units":len(rows),"shots_per_unit":spec.shots,"ber_trials":n_ber,"exact_trials":n_exact,"familywise_alpha":FAMILYWISE_ALPHA,"simultaneous_checks":simultaneous_checks,"ber_mean":ber_mean,"ber_ci95_low":bci[0],"ber_ci95_high":bci[1],"theoretical_ber":p,"ber_theory_inside_ci":bci[0]<=p<=bci[1],"ber_hoeffding_half_width":ber_width,"ber_compatible":abs(ber_mean-p)<=ber_width,"exact_success_mean":exact_mean,"exact_success_ci95_low":eci[0],"exact_success_ci95_high":eci[1],"theoretical_exact_success":theory,"exact_theory_inside_ci":eci[0]<=theory<=eci[1],"exact_hoeffding_half_width":exact_width,"exact_compatible":abs(exact_mean-theory)<=exact_width})
    return raw,summary
def _benchmark(spec):
    for b in BACKENDS:statevector(b,spec.rules[0],spec.n_cells,initial=bits_from_index(spec.noise_state_ids[0],spec.n_cells))
    raw=[]
    for rule in spec.rules:
     for sid in spec.noise_state_ids:
      initial=bits_from_index(sid,spec.n_cells)
      for rep in range(spec.benchmark_repetitions):
       order=list(BACKENDS);np.random.default_rng(derive_seed("bench-order",spec.name,rule,sid,rep)).shuffle(order)
       for oi,b in enumerate(order):
        t=time.perf_counter_ns();v=statevector(b,rule,spec.n_cells,initial=initial);dt=(time.perf_counter_ns()-t)/1e9
        raw.append({"profile":spec.name,"rule":rule,"state_id":sid,"backend":b,"repetition":rep,"randomized_order":oi,"runtime_seconds":dt,"statevector_norm":float(np.vdot(v,v).real)})
    summary=[]
    for b in BACKENDS:
      vals=[r["runtime_seconds"] for r in raw if r["backend"]==b];q1,med,q3=quartiles(vals);summary.append({"profile":spec.name,"backend":b,"observations":len(vals),"q1_seconds":q1,"median_seconds":med,"q3_seconds":q3,"iqr_seconds":q3-q1,"interpretation":"simulador clássico; não mede vantagem quântica"})
    return raw,summary
def _figures(dest, noise, bench):
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib.pyplot as plt
    # Uma realização comum: não fazer média de etiquetas de SDK como se
    # fossem novas amostras. Exibimos o bootstrap do estrato Qiskit.
    rows = [r for r in noise if r["backend"] == "qiskit"]
    n = PROFILE_SPECS[str(rows[0]["profile"])].n_cells
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), layout="constrained")
    for col, (rule, color) in enumerate(zip(SUPPORTED_RULES, ("#147d92", "#9b4bba", "#d65b2c"), strict=True)):
        selected = sorted((r for r in rows if r["rule"] == rule), key=lambda r: r["bitflip_probability"])
        ps = np.asarray([r["bitflip_probability"] for r in selected])
        dense = np.linspace(0, max(ps), 200)
        for row_index, (prefix, label, theory) in enumerate((
            ("ber", "BER", dense),
            ("exact_success", "Sucesso exato", (1-dense)**n),
        )):
            ax = axes[row_index, col]
            mean = np.asarray([r[prefix+"_mean"] for r in selected])
            low = np.asarray([r[prefix+"_ci95_low"] for r in selected])
            high = np.asarray([r[prefix+"_ci95_high"] for r in selected])
            ax.plot(dense, theory, color="#26344e", linestyle="--", label="Previsão analítica")
            ax.errorbar(ps, mean, yerr=[np.maximum(0, mean-low), np.maximum(0, high-mean)],
                        color=color, fmt="o", capsize=4, label="Média e IC95% bootstrap")
            ax.set(xlabel="Probabilidade de bit-flip p", ylabel=label, title=f"Regra {rule}", ylim=(-.03, 1.03) if row_index else (-.02, max(ps)+.06))
            ax.grid(alpha=.18)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2, frameon=False)
    fig.suptitle("Ruído na saída: canal comum aos três SDKs\nUnidades pareadas · ICs descritivos; decisão por Bonferroni–Hoeffding", fontsize=14)
    fig.savefig(dest/"figure_noise.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    for i, (row, color) in enumerate(zip(bench, ("#147d92", "#9b4bba", "#d65b2c"), strict=True)):
        med = 1000*row["median_seconds"]
        ax.errorbar(i, med, yerr=[[med-1000*row["q1_seconds"]], [1000*row["q3_seconds"]-med]],
                    fmt="o", color=color, capsize=8, markersize=9)
        ax.annotate(f"{med:.2f} ms", (i, med), xytext=(12, 7), textcoords="offset points", fontsize=10)
    ax.set_xticks(range(len(bench)), [r["backend"] for r in bench])
    ax.set(xlim=(-.5, 2.6), ylim=(0, 1.25*max(1000*r["q3_seconds"] for r in bench)), ylabel="Construção + simulação (ms)",
           title="Microbenchmark de simuladores clássicos\nMediana e IQR · warm-up excluído · sem inferência de vantagem quântica")
    ax.grid(axis="y", alpha=.2)
    fig.savefig(dest/"figure_benchmark.png", dpi=300)
    plt.close(fig)


def run_experiment(output_dir, *, profile="smoke", require_tfq=True, project_root=None):
    if profile not in PROFILE_SPECS:
        raise ValueError("profile inválido")
    spec = PROFILE_SPECS[profile]
    dest = Path(output_dir).resolve()
    reserved = (*PRIMARY_ARTIFACTS, "manifest.json", "validation_report.json", "SHA256SUMS.txt",
                f"eca_qca_{profile}_bundle.zip", "bundle_receipt.json")
    if any((dest/name).exists() for name in reserved):
        raise FileExistsError("Pasta já contém resultados. Escolha uma nova pasta; os dados existentes não serão sobrescritos.")
    dest.mkdir(parents=True, exist_ok=True)
    root = Path(project_root).resolve() if project_root else Path(__file__).resolve().parents[1]
    started = datetime.now(timezone.utc)
    basis, pairs, coherent, cases = _basis_coherent(spec)
    if not all(r["passed"] for r in basis+pairs+coherent):
        raise RuntimeError("gate determinístico falhou")
    tfq, available, error = _tfq(spec, cases, require_tfq)
    tfq_pass = available and all(r["passed"] for r in tfq)
    if require_tfq and not tfq_pass:
        raise RuntimeError("gate TFQ falhou")
    noise_raw, noise_summary = _noise(spec)
    bench_raw, bench_summary = _benchmark(spec)
    tables = {
        "basis_parity.csv": basis, "statevector_parity.csv": pairs,
        "coherent_states.csv": coherent, "tfq_integration.csv": tfq,
        "noise_raw.csv": noise_raw, "noise_summary.csv": noise_summary,
        "benchmark_raw.csv": bench_raw, "benchmark_summary.csv": bench_summary,
    }
    for name, rows in tables.items():
        _csv(dest/name, rows)
    _figures(dest, noise_summary, bench_summary)
    technical = all(r["passed"] for r in basis+pairs+coherent) and tfq_pass
    confirmatory = profile == "paper" and technical
    result = {
        "schema_version": SCHEMA_VERSION, "profile": profile,
        "technical_gate_passed": technical, "confirmatory_claims_enabled": confirmatory,
        "hypotheses": {
            "H1_basis_equivalence": all(r["passed"] for r in basis),
            "H2_cross_framework_fidelity": all(r["passed"] for r in pairs),
            "H3_ber_matches_p": confirmatory and all(r["ber_compatible"] for r in noise_summary),
            "H4_exact_success_matches_theory": confirmatory and all(r["exact_compatible"] for r in noise_summary),
            "H3_H4_evaluated": confirmatory,
            "decision_rule": "compatibilidade simultânea Bonferroni–Hoeffding com alfa familiar de 0,05; IC95% bootstrap relatado separadamente",
        },
        "counts": {
            "basis_backend_checks": len(basis), "statevector_pair_checks": len(pairs),
            "coherent_backend_checks": len(coherent), "tfq_observable_checks": len(tfq) if available else 0,
            "noise_records": len(noise_raw), "noise_design_units": len({r["unit_id"] for r in noise_raw}),
            "noise_distinct_streams": len({r["simulator_seed"] for r in noise_raw}),
            "native_noise_backend_runs": 0,
            "benchmark_records": len(bench_raw), "primary_artifacts": len(PRIMARY_ARTIFACTS),
        },
        "numerics": {
            "minimum_cross_framework_fidelity": min(r["fidelity"] for r in pairs),
            "maximum_basis_probability_error": max(r["max_probability_error"] for r in basis),
            "maximum_phase_aligned_error": max(r["max_phase_error"] for r in basis+coherent),
            "maximum_tfq_expectation_error": max((r["absolute_error"] for r in tfq if r.get("available")), default=None),
            "maximum_tfq_analytical_error": max((r["analytical_absolute_error"] for r in tfq if r.get("available")), default=None),
        },
        "tfq": {"available": available, "error": error, "interpretation": "integração TensorFlow–Cirq; não é implementação independente"},
        "noise": {
            "model": "independent output bit-flip",
            "sampler": "numpy.random.Generator(PCG64)",
            "pairing": "one realization per design unit, shared across backend labels",
            "limitation": "não executa canais nativos por SDK; não representa ruído por porta ou hardware",
        },
    }
    (dest/"validation_report.json").write_text(stable_json(result), encoding="utf-8")
    hashes = {name: sha256_file(dest/name) for name in PRIMARY_ARTIFACTS}
    manifest = {
        "schema_version": SCHEMA_VERSION, "created_utc": datetime.now(timezone.utc).isoformat(),
        "started_utc": started.isoformat(), "python": sys.version, "platform": platform.platform(),
        "versions": _versions(), "git": _git(root), "specification": spec.to_dict(),
        "result": result, "artifact_sha256": hashes,
    }
    (dest/"manifest.json").write_text(stable_json(manifest), encoding="utf-8")
    checksums = {**hashes, **{name: sha256_file(dest/name) for name in ("manifest.json", "validation_report.json")}}
    (dest/"SHA256SUMS.txt").write_text("".join(f"{value}  {name}\n" for name, value in sorted(checksums.items())), encoding="utf-8")
    bundle = dest/f"eca_qca_{profile}_bundle.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in (*PRIMARY_ARTIFACTS, "manifest.json", "validation_report.json", "SHA256SUMS.txt"):
            archive.write(dest/name, arcname=name)
    # O hash do próprio ZIP é um recibo externo: não modificar o relatório
    # científico depois de arquivá-lo (evita circularidade e divergência).
    receipt = {"bundle": str(bundle), "bundle_sha256": sha256_file(bundle)}
    (dest/"bundle_receipt.json").write_text(stable_json(receipt), encoding="utf-8")
    return {**result, **receipt}
