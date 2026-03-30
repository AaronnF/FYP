import argparse
import csv
import json
import os
import random
from typing import Dict, List, Tuple, Any, Optional

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


def _read_vectors_txt(path: str, ports_order: List[str]) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    vectors: List[Tuple[Dict[str, str], Dict[str, str]]] = []
    rows: List[List[str]] = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(line.split())

    # Standard format: one row contains all ports.
    if all(len(parts) == len(ports_order) for parts in rows):
        for parts in rows:
            mapping = dict(zip(ports_order, parts))
            vectors.append((mapping, {}))
        return vectors

    # Two-line pair format (common for large vectors): input line then output line.
    if len(ports_order) == 2 and all(len(parts) == 1 for parts in rows) and len(rows) % 2 == 0:
        p_in, p_out = ports_order[0], ports_order[1]
        for i in range(0, len(rows), 2):
            mapping = {p_in: rows[i][0], p_out: rows[i + 1][0]}
            vectors.append((mapping, {}))
        return vectors

    bad = " | ".join(" ".join(parts) for parts in rows[:3])
    raise ValueError(f"Unexpected txt vector format. Sample rows: {bad}")


def _read_vectors_csv(path: str) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    vectors: List[Tuple[Dict[str, str], Dict[str, str]]] = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            inputs: Dict[str, str] = {}
            outputs: Dict[str, str] = {}
            for k, v in row.items():
                if v is None:
                    continue
                if k.startswith("in:"):
                    inputs[k[3:]] = v.strip()
                elif k.startswith("out:"):
                    outputs[k[4:]] = v.strip()
            vectors.append((inputs, outputs))
    return vectors


def _read_vectors_json(path: str) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    with open(path, "r") as f:
        data = json.load(f)
    vectors: List[Tuple[Dict[str, str], Dict[str, str]]] = []
    for entry in data:
        inputs = entry.get("inputs", {})
        outputs = entry.get("outputs", {})
        vectors.append((inputs, outputs))
    return vectors


def _load_vectors(path: str, ports_order: List[str]) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    if path.endswith(".json"):
        return _read_vectors_json(path)
    if path.endswith(".csv"):
        return _read_vectors_csv(path)
    return _read_vectors_txt(path, ports_order)


def _auto_vectors_for_full_adder() -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    vectors: List[Tuple[Dict[str, str], Dict[str, str]]] = []
    for a in [0, 1]:
        for b in [0, 1]:
            for cin in [0, 1]:
                sum_bit = (a ^ b ^ cin) & 1
                cout = (a & b) | (a & cin) | (b & cin)
                vectors.append(
                    (
                        {"a": str(a), "b": str(b), "cin": str(cin)},
                        {"sum": str(sum_bit), "cout": str(cout)},
                    )
                )
    return vectors


def _auto_vectors_for_rca_24bit(cases: int, seed: int) -> List[Tuple[Dict[str, str], Dict[str, str]]]:
    rng = random.Random(seed)
    vectors: List[Tuple[Dict[str, str], Dict[str, str]]] = []
    for _ in range(cases):
        a = rng.getrandbits(24)
        b = rng.getrandbits(24)
        cin = rng.getrandbits(1)
        total = a + b + cin
        sum_val = total & ((1 << 24) - 1)
        cout = (total >> 24) & 1

        a_bits = f"{a:024b}"
        b_bits = f"{b:024b}"
        sum_bits = f"{sum_val:024b}"

        vectors.append(
            (
                {"A": a_bits, "B": b_bits, "Cin": str(cin)},
                {"Sum": sum_bits, "Cout": str(cout)},
            )
        )
    return vectors


def _evaluate_case(netlist, inputs: Dict[str, List[int]], secure: bool, c: float) -> Dict[str, List[int]]:
    outputs = netlist.evaluate({k: np.array(v) for k, v in inputs.items()}, secure=secure, c=c)
    return {k: [int(round(x)) for x in arr.tolist()] for k, arr in outputs.items()}


def _score_mapping(
    netlist,
    vectors: List[Tuple[Dict[str, str], Dict[str, str]]],
    port_orders: Dict[str, str],
    input_ports: List[str],
    output_ports: List[str],
    secure: bool,
    c: float,
) -> Tuple[int, List[Tuple[int, str, str, str, str]]]:
    matches = 0
    mismatches: List[Tuple[int, str, str, str, str]] = []

    for idx, (inputs_str, outputs_str) in enumerate(vectors):
        inputs_bits: Dict[str, List[int]] = {}
        for port in input_ports:
            if port not in inputs_str:
                raise KeyError(f"Missing input value for port '{port}' in vector {idx}")
            inputs_bits[port] = _bits_from_str(inputs_str[port], port_orders[port])

        out_bits = _evaluate_case(netlist, inputs_bits, secure, c)

        expected_concat = []
        actual_concat = []
        for port in output_ports:
            if port not in outputs_str:
                raise KeyError(f"Missing expected output for port '{port}' in vector {idx}")
            expected_bits = _bits_from_str(outputs_str[port], port_orders[port])
            actual_bits = out_bits[port]
            expected_concat.append(_bits_to_str(expected_bits, "msb"))
            actual_concat.append(_bits_to_str(actual_bits, "msb"))

        expected_join = "|".join(expected_concat)
        actual_join = "|".join(actual_concat)
        if expected_join == actual_join:
            matches += 1
        else:
            if len(mismatches) < 5:
                mismatches.append(
                    (idx, json.dumps(inputs_str), expected_join, actual_join, json.dumps(port_orders))
                )

    return matches, mismatches


def _all_port_orderings(ports: List[str]) -> List[Dict[str, str]]:
    if not ports:
        return [{}]
    orderings: List[Dict[str, str]] = []
    head, *tail = ports
    for rest in _all_port_orderings(tail):
        for order in ("msb", "lsb"):
            mapping = dict(rest)
            mapping[head] = order
            orderings.append(mapping)
    return orderings


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal Yosys JSON netlist validator")
    parser.add_argument("--netlist", required=True, help="Path to Yosys JSON netlist")
    parser.add_argument("--vectors", help="Path to test vectors (.txt/.csv/.json)")
    parser.add_argument("--module", help="Override module name")
    parser.add_argument("--secure", action="store_true", help="Use secure DNN gates")
    parser.add_argument("--c", type=float, default=0.5, help="Corner function parameter")
    parser.add_argument("--max", type=int, default=0, help="Limit number of test cases (0 = all)")
    parser.add_argument("--auto-vectors", action="store_true", help="Auto-generate vectors for known modules")
    parser.add_argument("--cases", type=int, default=100, help="Number of auto-generated cases")
    parser.add_argument("--seed", type=int, default=1, help="Random seed for auto-generated vectors")
    args = parser.parse_args()

    netlist = load_yosys_json(args.netlist, module_name=args.module)

    input_ports = [name for name, p in netlist.ports.items() if p.get("direction") == "input"]
    output_ports = [name for name, p in netlist.ports.items() if p.get("direction") == "output"]
    ports_order = input_ports + output_ports

    vectors: List[Tuple[Dict[str, str], Dict[str, str]]]
    if args.vectors:
        vectors = _load_vectors(args.vectors, ports_order)
        if args.max:
            vectors = vectors[: args.max]
    elif args.auto_vectors:
        if netlist.module_name == "full_adder":
            vectors = _auto_vectors_for_full_adder()
        elif netlist.module_name == "rca_24bit":
            vectors = _auto_vectors_for_rca_24bit(args.cases, args.seed)
        else:
            raise ValueError("No vectors provided and auto-vectors not supported for this module.")
    else:
        raise ValueError("Provide --vectors or use --auto-vectors for supported modules.")

    # If vectors are in "inputs only" format, split them into inputs/outputs based on port direction
    normalized: List[Tuple[Dict[str, str], Dict[str, str]]] = []
    for inputs, outputs in vectors:
        if outputs:
            normalized.append((inputs, outputs))
        else:
            in_vals = {k: inputs[k] for k in input_ports}
            out_vals = {k: inputs[k] for k in output_ports}
            normalized.append((in_vals, out_vals))
    vectors = normalized

    # Auto-detect bit order per port
    all_ports = input_ports + output_ports
    best_orders: Optional[Dict[str, str]] = None
    best_score = -1
    best_mismatches: List[Tuple[int, str, str, str, str]] = []

    for mapping in _all_port_orderings(all_ports):
        score, mismatches = _score_mapping(
            netlist, vectors, mapping, input_ports, output_ports, args.secure, args.c
        )
        if score > best_score:
            best_score = score
            best_orders = mapping
            best_mismatches = mismatches

    total = len(vectors)
    print(f"Test cases: {total}")
    print(f"Best matches: {best_score}/{total}")
    print("Selected bit order per port:")
    for port in all_ports:
        print(f"  {port}: {best_orders[port]}")

    if best_score != total:
        print("Sample mismatches:")
        for idx, inputs_json, expected, actual, orders in best_mismatches:
            print(f"  case {idx}:")
            print(f"    inputs   = {inputs_json}")
            print(f"    expected = {expected}")
            print(f"    actual   = {actual}")
            print(f"    orders   = {orders}")


if __name__ == "__main__":
    main()
