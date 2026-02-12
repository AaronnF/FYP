import time
import numpy as np

# adjust import to match your project layout
from src.core.aes_dnn import AESDNN
from src.core.crypto_dnn import CryptographicPrimitives

def stats_ms(times_s):
    arr = np.array(times_s, dtype=np.float64) * 1000.0
    return {
        "mean_ms": float(arr.mean()),
        "median_ms": float(np.median(arr)),
        "stdev_ms": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        "min_ms": float(arr.min()),
        "max_ms": float(arr.max()),
        "n": int(len(arr)),
    }

def bench(fn, iters=5000, warmup=200):
    # warmup
    for _ in range(warmup):
        fn()

    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return stats_ms(times)

def main():
    aes = AESDNN(128)

    # ---------- SBOX NN inference (one byte) ----------
    byte_bits = np.random.randint(0, 2, 8, dtype=np.uint8)

    def sbox_nonsecure():
        aes.sbox_dnn(byte_bits)

    def sbox_secure():
        # matches your sub_bytes secure path
        def secure_sbox(bits):
            return aes.sbox_dnn(bits)
        from src.core.crypto_dnn import CryptoDNN
        CryptoDNN.secure_dnn_forward(byte_bits, secure_sbox)

    # ---------- XOR NN inference (128 bits) ----------
    state_bits = np.random.randint(0, 2, 128, dtype=np.uint8)
    key_bits   = np.random.randint(0, 2, 128, dtype=np.uint8)
    combined_input = np.stack([state_bits, key_bits], axis=-1)  # shape (128,2)

    def xor_nonsecure():
        CryptographicPrimitives.nnxor(combined_input)

    def xor_secure():
        CryptographicPrimitives.secure_nnxor(combined_input)

    print("=== NN Inference Microbenchmarks (CPU) ===")
    print("[SBOX 1-byte non-secure]", bench(sbox_nonsecure, iters=5000))
    print("[SBOX 1-byte secure]    ", bench(sbox_secure, iters=5000))
    print("[XOR 128-bit non-secure]", bench(xor_nonsecure, iters=5000))
    print("[XOR 128-bit secure]    ", bench(xor_secure, iters=5000))

    # Optional: estimate per-block NN time for AES-128 encrypt
    # AES-128 has 16 SBOX calls per round * 10 rounds = 160 SBOX calls
    # AddRoundKey = 11 XOR calls (initial + 10 rounds)
    # (This is a rough estimate because caching/overheads can differ.)
    # You can compute:
    #   block_ms ≈ 160*sbox_ms + 11*xor_ms

if __name__ == "__main__":
    main()
