"""Worker isolado TensorFlow Quantum–Cirq."""
import json,os,sys
os.environ.setdefault("TF_USE_LEGACY_KERAS","1");os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL","3");os.environ.setdefault("CUDA_VISIBLE_DEVICES","-1")
def main():
    try:
        import cirq, tensorflow_quantum as tfq
        from .adapters import build_cirq_circuit
        cases=json.loads(sys.stdin.read()); ns={int(x["n_cells"]) for x in cases}
        if len(ns)!=1:raise ValueError("lote deve ter um n_cells")
        n=ns.pop(); circuits=[]
        for x in cases:
            plus=x["mode"]=="plus";circuits.append(build_cirq_circuit(int(x["rule"]),n,initial=None if plus else x["initial"],plus_input=plus))
        q=list(cirq.LineQubit.range(2*n)); ops=[cirq.Z(q[n+i]) for i in range(n)]
        values=tfq.layers.Expectation()(tfq.convert_to_tensor(circuits),operators=ops).numpy().tolist()
        print("TFQ_RESULT_JSON="+json.dumps(values,separators=(",",":")));return 0
    except Exception as e:print(f"TFQ_WORKER_ERROR={type(e).__name__}: {e}",file=sys.stderr);return 1
if __name__=="__main__":raise SystemExit(main())
