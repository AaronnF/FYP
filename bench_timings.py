import time
import statistics as stats
import numpy as np

def time_dist_ms(fn, warmup=30, iters=200):
    # warmup
    for _ in range(warmup):
        fn()
    # measure distribution
    samples = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        samples.append((t1 - t0) * 1000.0)
    return {
        "mean_ms": stats.mean(samples),
        "median_ms": stats.median(samples),
        "stdev_ms": stats.pstdev(samples),
        "min_ms": min(samples),
        "max_ms": max(samples),
        "n": len(samples),
    }

def main():
    print("=== CPU Timing Benchmarks ===")

    # -----------------------
    # (A) AES timing (your AESDNN)
    # -----------------------
    from src.core.aes_dnn import AESDNN

    aes = AESDNN(128)

    # fixed test vectors (16 bytes each)
    plaintext = np.frombuffer(b"Hello, World!123", dtype=np.uint8)  # 16 bytes
    key       = np.frombuffer(b"SecretKey1234567", dtype=np.uint8)  # 16 bytes

    def aes_nonsecure():
        aes.encrypt_block(plaintext, key, secure=False)

    def aes_secure():
        aes.encrypt_block(plaintext, key, secure=True)

    aes_ns = time_dist_ms(aes_nonsecure, warmup=20, iters=100)
    aes_sc = time_dist_ms(aes_secure, warmup=20, iters=100)
    print(f"[AES encrypt_block non-secure] {aes_ns}")
    print(f"[AES encrypt_block secure]     {aes_sc}")

    # -----------------------
    # (B) Dilithium2 verify timing (oqs-python)
    # -----------------------
    try:
        import oqs
    except ImportError:
        print("[Dilithium2 verify] oqs not installed. Run: pip install oqs")
        oqs = None

    if oqs is not None:
        msg = b"benchmark message" * 8
        sigalg = "Dilithium2"

        with oqs.Signature(sigalg) as s:
            pk = s.generate_keypair()
            sig = s.sign(msg)

        def dilithium_verify():
            # create verifier object per-call is slower but “pure”;
            # you can also reuse a verifier if you want “best-case”
            with oqs.Signature(sigalg) as v:
                v.verify(msg, sig, pk)

        dil = time_dist_ms(dilithium_verify, warmup=10, iters=50)
        print(f"[Dilithium2 verify (oqs-python)] {dil}")

    # -----------------------
    # (C) NN forward timing (placeholder)
    # Replace with your real NN forward call.
    # -----------------------
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        print("[NN] PyTorch not installed; skipping.")
        return

    model = nn.Sequential(nn.Flatten(), nn.Linear(32*32*3, 10))
    model.eval()
    x = torch.randn(1, 3, 32, 32)

    @torch.no_grad()
    def nn_forward():
        _ = model(x)

    nn_t = time_dist_ms(nn_forward, warmup=50, iters=300)
    print(f"[NN forward (placeholder)] {nn_t}")

if __name__ == "__main__":
    main()
