import hashlib
from typing import Callable, List, Optional

import numpy as np

from .netlist_parser import load_yosys_json


DILITHIUM2_N = 256
DILITHIUM2_TAU = 39

_KECCAK_ROUND_CONSTANTS = [
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
]


class Shake256Stream:
    def __init__(self, data: bytes, backend: str = "hashlib", keccak_netlist_path: Optional[str] = None):
        self._backend = backend
        self._cursor = 0
        self._cache = b""
        self._keccak_netlist_path = keccak_netlist_path
        if backend == "hashlib":
            self._shake = hashlib.shake_256(data)
        elif backend == "netlist":
            self._seed = data
        else:
            raise ValueError(f"Unsupported SHAKE256 backend: {backend}")

    def read(self, n: int) -> bytes:
        if n <= 0:
            return b""
        if self._backend == "hashlib":
            need = self._cursor + n
            if len(self._cache) < need:
                self._cache = self._shake.digest(need)
            out = self._cache[self._cursor : self._cursor + n]
            self._cursor += n
            return out
        return self._read_netlist(n)

    def _read_netlist(self, n: int) -> bytes:
        need = self._cursor + n
        if len(self._cache) < need:
            self._cache = shake256_netlist(self._seed, need, self._keccak_netlist_path)
        out = self._cache[self._cursor : self._cursor + n]
        self._cursor += n
        return out


def _bytes_to_bits_le(data: bytes) -> List[int]:
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> i) & 1)
    return bits


def _bits_to_bytes_le(bits: List[int]) -> bytes:
    if len(bits) % 8 != 0:
        raise ValueError("Bit length must be a multiple of 8.")
    out = bytearray()
    for i in range(0, len(bits), 8):
        value = 0
        for bit_index in range(8):
            value |= (bits[i + bit_index] & 1) << bit_index
        out.append(value)
    return bytes(out)


def _keccak_permute_netlist(state_bytes: bytes, netlist) -> bytes:
    state_bits = _bytes_to_bits_le(state_bytes)
    for rc in _KECCAK_ROUND_CONSTANTS:
        rc_bits = [(rc >> i) & 1 for i in range(64)]
        outputs = netlist.evaluate(
            {
                "round_in_port": np.array(state_bits),
                "round_constant_signal": np.array(rc_bits),
            },
            secure=False,
        )
        state_bits = [int(round(x)) for x in outputs["round_out_port"].tolist()]
    return _bits_to_bytes_le(state_bits)


def shake256_netlist(data: bytes, out_len: int, keccak_netlist_path: Optional[str]) -> bytes:
    if not keccak_netlist_path:
        raise ValueError("keccak_netlist_path is required for netlist-based SHAKE256.")
    netlist = load_yosys_json(keccak_netlist_path, module_name="keccak_perm_r1")
    rate = 136
    state = bytearray(200)

    padded = bytearray(data)
    padded.append(0x1F)
    while len(padded) % rate != rate - 1:
        padded.append(0x00)
    padded.append(0x80)

    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for i in range(rate):
            state[i] ^= block[i]
        state = bytearray(_keccak_permute_netlist(bytes(state), netlist))

    out = bytearray()
    while len(out) < out_len:
        take = min(rate, out_len - len(out))
        out.extend(state[:take])
        if len(out) < out_len:
            state = bytearray(_keccak_permute_netlist(bytes(state), netlist))

    return bytes(out)


def sample_challenge(
    mu_w1: bytes,
    n: int = DILITHIUM2_N,
    tau: int = DILITHIUM2_TAU,
    shake_backend: str = "hashlib",
    keccak_netlist_path: Optional[str] = None,
) -> List[int]:
    """
    Sample Dilithium challenge polynomial with exactly tau non-zero entries in {-1, +1}.
    """
    stream = Shake256Stream(mu_w1, backend=shake_backend, keccak_netlist_path=keccak_netlist_path)
    signs = stream.read(8)

    c = [0 for _ in range(n)]
    sign_idx = 0

    for i in range(n - tau, n):
        while True:
            b = stream.read(1)[0]
            if b <= i:
                break
        c[i] = c[b]
        sign_bit = (signs[sign_idx // 8] >> (sign_idx % 8)) & 1
        c[b] = 1 if sign_bit == 0 else -1
        sign_idx += 1

    return c
