import argparse
from typing import List, Tuple

import numpy as np

from core.netlist_parser import load_yosys_json


def _bits_from_str(bitstr: str, order: str) -> List[int]:
    bits = [int(ch) for ch in bitstr.strip()]
    if order == "lsb":
        bits = list(reversed(bits))
    return bits


def _bits_to_str(bits: List[int], order: str) -> str:
    out = bits[:]
    if order == "lsb":
        out = list(reversed(out))
    return "".join(str(int(b)) for b in out)


def _load_vectors(path: str, max_cases: int) -> List[Tuple[str, str, str]]:
    vectors = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(f"Unexpected line format: {line}")
            vectors.append((parts[0], parts[1], parts[2]))
            if max_cases and len(vectors) >= max_cases:
                break
    return vectors


def _evaluate_case(netlist, b_bits, c_bits, secure: bool, c: float) -> List[int]:
    outputs = netlist.evaluate(
        {"b": np.array(b_bits), "c": np.array(c_bits)},
        secure=secure,
        c=c,
    )
    raw = outputs["a"].tolist()
    return [int(round(v)) for v in raw]


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate mul24_gate.json against mul24_test.txt")
    parser.add_argument("--netlist", default="Dilithium Building Blocks/mul24_gate.json")
    parser.add_argument("--vectors", default="Dilithium Building Blocks/mul24_test.txt")
    parser.add_argument("--max", type=int, default=0, help="Limit number of test cases (0 = all)")
    parser.add_argument("--secure", action="store_true", help="Use secure DNN gates")
    parser.add_argument("--c", type=float, default=0.5, help="Corner function parameter")
    args = parser.parse_args()

    netlist = load_yosys_json(args.netlist, module_name="mul24")
    vectors = _load_vectors(args.vectors, args.max)

    input_order = "lsb"
    output_order = "lsb"
    matches = 0
    mismatches: List[Tuple[int, str, str, str, str]] = []

    for idx, (b_str, c_str, a_str) in enumerate(vectors):
        b_bits = _bits_from_str(b_str, input_order)
        c_bits = _bits_from_str(c_str, input_order)

        out_bits = _evaluate_case(netlist, b_bits, c_bits, args.secure, args.c)
        out_str = _bits_to_str(out_bits, output_order)

        if out_str == a_str:
            matches += 1
        else:
            if len(mismatches) < 5:
                mismatches.append((idx, b_str, c_str, a_str, out_str))

    total = len(vectors)
    print(f"Test cases: {total}")
    print(f"Mapping in={input_order}, out={output_order}: {matches}/{total} matches")

    if matches != total:
        print("Sample mismatches:")
        for idx, b_str, c_str, a_str, out_str in mismatches:
            print(f"  case {idx}:")
            print(f"    b   = {b_str}")
            print(f"    c   = {c_str}")
            print(f"    exp = {a_str}")
            print(f"    got = {out_str}")


if __name__ == "__main__":
    main()
