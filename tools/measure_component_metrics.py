#!/usr/bin/env python3
import json
import multiprocessing as mp
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.netlist_parser import load_yosys_json  # noqa: E402
import test_netlist_parser as harness  # noqa: E402


@dataclass(frozen=True)
class Component:
    name: str
    json_path: Path
    vectors_path: Optional[Path] = None
    module_name: Optional[str] = None
    auto_vectors: bool = False
    auto_cases: int = 100
    auto_seed: int = 1


COMPONENTS: List[Component] = [
    Component(
        name="comparator",
        json_path=ROOT / "Dilithium Building Blocks" / "comparator.json",
        vectors_path=ROOT / "dilithium_tests" / "comparator.txt",
        module_name="comparator",
    ),
    Component(
        name="unpack_z_one_coeff",
        json_path=ROOT / "Dilithium Building Blocks" / "unpack_z_one_coeff.json",
        vectors_path=ROOT / "dilithium_tests" / "unpack_z_one_coeff.txt",
        module_name="unpack_z_one_coeff",
    ),
    Component(
        name="poly_caddq",
        json_path=ROOT / "Dilithium Building Blocks" / "poly_caddq.json",
        vectors_path=ROOT / "dilithium_tests" / "poly_caddq.txt",
        module_name="poly_caddq",
    ),
    Component(
        name="poly_sub_vector",
        json_path=ROOT / "Dilithium Building Blocks" / "poly_sub_vector.json",
        vectors_path=ROOT / "dilithium_tests" / "poly_sub_vector.txt",
        module_name="poly_sub_vector",
    ),
    Component(
        name="montgomery_vector_reduce",
        json_path=ROOT / "Dilithium Building Blocks" / "montgomery_vector_reduce.json",
        vectors_path=ROOT / "dilithium_tests" / "montgomery_vector_reduce.txt",
        module_name="montgomery_vector_reduce",
    ),
    Component(
        name="poly_use_hint",
        json_path=ROOT / "Dilithium Building Blocks" / "poly_use_hint.json",
        vectors_path=ROOT / "dilithium_tests" / "poly_use_hint.txt",
        module_name="poly_use_hint",
    ),
    Component(
        name="invntt_256_comb",
        json_path=ROOT / "Dilithium Building Blocks" / "invntt_256_comb.json",
        vectors_path=ROOT / "dilithium_tests" / "invntt_256_comb.txt",
        module_name="invntt_256_comb",
    ),
    Component(
        name="full_adder",
        json_path=ROOT / "Dilithium Building Blocks" / "full_adder_gate.json",
        vectors_path=ROOT / "Dilithium Building Blocks" / "full_adder_test.txt",
        module_name="full_adder",
    ),
    Component(
        name="if_else_test",
        json_path=ROOT / "Dilithium Building Blocks" / "if_else_test_gate.json",
        vectors_path=ROOT / "Dilithium Building Blocks" / "if_else_test_vectors.txt",
        module_name="if_else_test",
    ),
    Component(
        name="mul24",
        json_path=ROOT / "Dilithium Building Blocks" / "mul24_gate.json",
        vectors_path=ROOT / "Dilithium Building Blocks" / "mul24_test.txt",
        module_name="mul24",
    ),
    Component(
        name="keccak_perm_r1",
        json_path=ROOT / "Dilithium Building Blocks" / "keccak_perm_r1.json",
        vectors_path=ROOT / "Dilithium Building Blocks" / "keccak_perm_r1.txt",
        module_name="keccak_perm_r1",
    ),
    Component(
        name="dilithium_ntt_unrolled",
        json_path=ROOT / "Dilithium Building Blocks" / "dilithium_ntt_unrolled.json",
        vectors_path=ROOT / "Dilithium Building Blocks" / "dilithium_ntt_unrolled_test.txt",
        module_name="dilithium_ntt_unrolled",
    ),
    Component(
        name="rca_24bit",
        json_path=ROOT / "Dilithium Building Blocks" / "rca_24bit.json",
        module_name="rca_24bit",
        auto_vectors=True,
    ),
]


RELU_PER_CELL = {
    "$_NOT_": 5,
    "$_AND_": 8,
    "$_NAND_": 8,
    "$_XOR_": 9,
    "$_XNOR_": 9,
    "$_OR_": 10,
    "$_NOR_": 10,
}


def _param_int(cell: Dict[str, object], key: str, default: int = 0) -> int:
    raw = cell.get("parameters", {}).get(key, default)
    if isinstance(raw, str):
        return int(raw, 2)
    return int(raw)


def _relu_cost_for_cell(cell: Dict[str, object], cell_type: str) -> int:
    if cell_type in RELU_PER_CELL:
        return RELU_PER_CELL[cell_type]

    conns = cell.get("connections", {})
    if cell_type == "$mux":
        width = len(conns.get("Y", []))
        return 5 + 26 * width

    if cell_type == "$eq":
        width = max(len(conns.get("A", [])), len(conns.get("B", [])))
        return 0 if width == 0 else (9 * width + 8 * (width - 1))

    if cell_type == "$gt":
        width = max(len(conns.get("A", [])), len(conns.get("B", [])))
        signed = bool(_param_int(cell, "A_SIGNED", 0)) or bool(_param_int(cell, "B_SIGNED", 0))
        return 48 * width + (40 if signed and width > 0 else 0)

    if cell_type == "$ge":
        width = max(len(conns.get("A", [])), len(conns.get("B", [])))
        signed = bool(_param_int(cell, "A_SIGNED", 0)) or bool(_param_int(cell, "B_SIGNED", 0))
        eq_cost = 0 if width == 0 else (9 * width + 8 * (width - 1))
        gt_cost = 48 * width + (40 if signed and width > 0 else 0)
        return eq_cost + gt_cost + 10

    if cell_type in {"$add", "$sub", "$mul", "$div", "$mod"}:
        width = _param_int(cell, "Y_WIDTH", len(conns.get("Y", [])))
        return 5 * width

    return 0


def count_relus(json_path: Path, module_name: Optional[str]) -> Tuple[int, Dict[str, int], List[str]]:
    netlist = load_yosys_json(str(json_path), module_name=module_name)
    counts: Dict[str, int] = {}
    unknown: List[str] = []
    total = 0
    for cell in netlist.cells:
        cell_type = cell["type"]
        if isinstance(cell_type, str) and cell_type.startswith("\\"):
            cell_type = cell_type[1:]
        counts[cell_type] = counts.get(cell_type, 0) + 1
        total += _relu_cost_for_cell(cell, cell_type)
        if _relu_cost_for_cell(cell, cell_type) == 0 and cell_type.startswith("$_"):
            if cell_type not in unknown:
                unknown.append(cell_type)
    return total, counts, sorted(unknown)


def load_vectors_for_component(comp: Component, module_name: str):
    netlist = load_yosys_json(str(comp.json_path), module_name=module_name)
    input_ports = [name for name, p in netlist.ports.items() if p.get("direction") == "input"]
    output_ports = [name for name, p in netlist.ports.items() if p.get("direction") == "output"]
    ports_order = input_ports + output_ports

    if comp.auto_vectors:
        if module_name == "full_adder":
            vectors = harness._auto_vectors_for_full_adder()
        elif module_name == "rca_24bit":
            vectors = harness._auto_vectors_for_rca_24bit(comp.auto_cases, comp.auto_seed)
        else:
            raise ValueError(f"No auto-vectors available for {module_name}")
    else:
        if comp.vectors_path is None:
            raise ValueError(f"Missing vectors for {comp.name}")
        vectors = harness._load_vectors(str(comp.vectors_path), ports_order)

    normalized = []
    for inputs, outputs in vectors:
        if outputs:
            normalized.append((inputs, outputs))
        else:
            in_vals = {k: inputs[k] for k in input_ports}
            out_vals = {k: inputs[k] for k in output_ports}
            normalized.append((in_vals, out_vals))
    return netlist, input_ports, output_ports, normalized


def find_best_orders(netlist, input_ports, output_ports, vectors):
    all_ports = input_ports + output_ports
    best_orders = None
    best_score = -1
    for mapping in harness._all_port_orderings(all_ports):
        score, _ = harness._score_mapping(
            netlist, vectors, mapping, input_ports, output_ports, secure=False, c=0.5
        )
        if score > best_score:
            best_score = score
            best_orders = mapping
    if best_orders is None:
        raise RuntimeError("Could not determine bit ordering")
    return best_orders


def _time_worker(queue, comp: Component, secure: bool):
    try:
        module_name = comp.module_name or load_yosys_json(str(comp.json_path)).module_name
        netlist, input_ports, output_ports, vectors = load_vectors_for_component(comp, module_name)
        best_orders = find_best_orders(netlist, input_ports, output_ports, vectors)

        start = time.perf_counter()
        matches = 0
        for inputs_str, outputs_str in vectors:
            inputs_bits = {
                port: harness._bits_from_str(inputs_str[port], best_orders[port]) for port in input_ports
            }
            out_bits = harness._evaluate_case(netlist, inputs_bits, secure=secure, c=0.5)
            expected_concat = []
            actual_concat = []
            for port in output_ports:
                expected_bits = harness._bits_from_str(outputs_str[port], best_orders[port])
                actual_bits = out_bits[port]
                expected_concat.append(harness._bits_to_str(expected_bits, "msb"))
                actual_concat.append(harness._bits_to_str(actual_bits, "msb"))
            if "|".join(expected_concat) == "|".join(actual_concat):
                matches += 1
        elapsed = time.perf_counter() - start
        queue.put(
            {
                "ok": True,
                "elapsed_s": elapsed,
                "vectors": len(vectors),
                "matches": matches,
                "orders": best_orders,
            }
        )
    except Exception as exc:
        queue.put({"ok": False, "error": str(exc)})


def measure_runtime(comp: Component, secure: bool, timeout_s: int = 600):
    queue = mp.Queue()
    proc = mp.Process(target=_time_worker, args=(queue, comp, secure))
    proc.start()
    proc.join(timeout_s)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        return {"ok": False, "timeout": True}
    if queue.empty():
        return {"ok": False, "error": "no result returned"}
    return queue.get()


def main():
    print(
        f"{'component':24} {'relus':>12} {'classic_ms':>12} {'secure_ms':>12} {'vectors':>8} result"
    )
    print("-" * 86)
    for comp in COMPONENTS:
        module_name = comp.module_name or load_yosys_json(str(comp.json_path)).module_name
        relus, counts, unknown = count_relus(comp.json_path, module_name)
        classic = measure_runtime(comp, secure=False)
        secure = measure_runtime(comp, secure=True)

        vectors = "-"
        result = "FAIL"
        classic_ms = "ERR"
        secure_ms = "ERR"
        if classic.get("ok"):
            vectors = str(classic["vectors"])
            classic_ms = f"{classic['elapsed_s'] * 1000:.3f}"
            result = f"{classic['matches']}/{classic['vectors']}"
        elif classic.get("timeout"):
            classic_ms = "TIMEOUT"

        if secure.get("ok"):
            secure_ms = f"{secure['elapsed_s'] * 1000:.3f}"
        elif secure.get("timeout"):
            secure_ms = "TIMEOUT"

        print(f"{comp.name:24} {relus:12} {classic_ms:>12} {secure_ms:>12} {vectors:>8} {result}")

        if unknown:
            print(f"  unknown_secure_gate_types={unknown}")
        if classic.get("ok"):
            cell_counts_subset = {k: counts[k] for k in sorted(counts) if counts[k]}
            print(f"  bit_orders={classic['orders']}")
            print(f"  cell_counts_subset={cell_counts_subset}")
        elif classic.get("error"):
            print(f"  classic_error={classic['error']}")
        if secure.get("error"):
            print(f"  secure_error={secure['error']}")


if __name__ == "__main__":
    mp.set_start_method("spawn")
    main()
