import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

import numpy as np

from .crypto_dnn import CryptoDNN, CryptographicPrimitives


_BINARY_GATES = {"$_AND_", "$_OR_", "$_XOR_", "$_XNOR_", "$_NAND_", "$_NOR_"}
_UNARY_GATES = {"$_NOT_"}
_ARITH_CELLS = {"$add", "$sub", "$mul", "$div", "$ge", "$gt", "$eq", "$mux", "$mod", "$scopeinfo"}


def _to_scalar(value: Any) -> float:
    arr = np.asarray(value)
    if arr.shape == ():
        return float(arr)
    return float(arr.reshape(-1)[0])


def _secure_not(x: float) -> float:
    return _to_scalar(CryptoDNN.secure_dnn_forward(np.array([x]), lambda p: 1 - p))


def _secure_nand(a: float, b: float, c: float) -> float:
    return _to_scalar(CryptoDNN.secure_dnn_forward(np.array([a, b]), lambda p: 1 - CryptographicPrimitives.nnand(p, c)))


def _secure_nor(a: float, b: float, c: float) -> float:
    return _to_scalar(CryptoDNN.secure_dnn_forward(np.array([a, b]), lambda p: 1 - CryptographicPrimitives.nnor(p, c)))


def _secure_xnor(a: float, b: float, c: float) -> float:
    return _to_scalar(CryptoDNN.secure_dnn_forward(np.array([a, b]), lambda p: 1 - CryptographicPrimitives.nnxor(p, c)))


def _secure_identity(x: float) -> float:
    return _to_scalar(CryptoDNN.secure_dnn_forward(np.array([x]), lambda p: p))


@dataclass
class YosysNetlist:
    module_name: str
    ports: Dict[str, Dict[str, Any]]
    cells: List[Dict[str, Any]]

    def evaluate(self, inputs: Dict[str, Any], secure: bool = True, c: float = 0.5) -> Dict[str, np.ndarray]:
        """
        Evaluate the netlist given input values.

        Args:
            inputs: Mapping of input port name -> scalar or array of bits.
            secure: Use secure gate implementations when True.
            c: Corner function parameter for DNN gates.

        Returns:
            Mapping of output port name -> numpy array of output bits.
        """
        wire_values: Dict[int, float] = {}

        def get_bit_value(bit: Any) -> Optional[float]:
            if bit == 0 or bit == "0":
                return 0.0
            if bit == 1 or bit == "1":
                return 1.0
            return wire_values.get(bit)

        def get_bit_int(bit: int) -> Optional[int]:
            val = get_bit_value(bit)
            if val is None:
                return None
            return int(round(float(val)))

        def get_vec_int(bits: List[int]) -> Optional[List[int]]:
            out: List[int] = []
            for bit in bits:
                v = get_bit_int(bit)
                if v is None:
                    return None
                out.append(v)
            return out

        def get_vec_values(bits: List[int]) -> Optional[List[float]]:
            out: List[float] = []
            for bit in bits:
                v = get_bit_value(bit)
                if v is None:
                    return None
                out.append(float(v))
            return out

        def bits_to_int(bits: List[int], signed: bool = False) -> int:
            value = 0
            for i, b in enumerate(bits):
                value |= (int(b) & 1) << i
            if signed and bits and bits[-1]:
                value -= 1 << len(bits)
            return value

        def int_to_bits(value: int, width: int) -> List[int]:
            if width <= 0:
                return []
            mask = (1 << width) - 1
            value &= mask
            return [(value >> i) & 1 for i in range(width)]

        def set_vec(bits: List[int], values: List[int]) -> None:
            for bit_id, bit_val in zip(bits, values):
                if bit_id > 1:
                    wire_values[bit_id] = float(int(bit_val))

        def set_vec_secure(bits: List[int], values: List[int]) -> None:
            for bit_id, bit_val in zip(bits, values):
                if bit_id > 1:
                    wire_values[bit_id] = float(_secure_identity(float(int(bit_val))))

        def param_int(cell: Dict[str, Any], key: str, default: int = 0) -> int:
            raw = cell.get("parameters", {}).get(key, default)
            if isinstance(raw, str):
                return int(raw, 2)
            return int(raw)

        def secure_and(a: float, b: float) -> float:
            return _to_scalar(CryptographicPrimitives.secure_nnand(np.array([a, b]), c))

        def secure_or(a: float, b: float) -> float:
            return _to_scalar(CryptographicPrimitives.secure_nnor(np.array([a, b]), c))

        def secure_xor(a: float, b: float) -> float:
            return _to_scalar(CryptographicPrimitives.secure_nnxor(np.array([a, b]), c))

        def extend_vec(values: List[float], width: int, signed: bool) -> List[float]:
            if len(values) >= width:
                return values[:width]
            fill = values[-1] if (signed and values) else 0.0
            return values + [fill] * (width - len(values))

        def secure_eq_vec(a_vals: List[float], b_vals: List[float], signed: bool = False) -> float:
            width = max(len(a_vals), len(b_vals))
            av = extend_vec(a_vals, width, signed)
            bv = extend_vec(b_vals, width, signed)
            if width == 0:
                return 1.0
            eq_val = _secure_xnor(av[0], bv[0], c)
            for i in range(1, width):
                bit_eq = _secure_xnor(av[i], bv[i], c)
                eq_val = secure_and(eq_val, bit_eq)
            return eq_val

        def secure_gt_vec(a_vals: List[float], b_vals: List[float], a_signed: bool = False, b_signed: bool = False) -> float:
            width = max(len(a_vals), len(b_vals))
            signed = a_signed or b_signed
            av = extend_vec(a_vals, width, a_signed)
            bv = extend_vec(b_vals, width, b_signed)
            gt_val = 0.0
            prefix_eq = 1.0
            for i in range(width - 1, -1, -1):
                not_b = _secure_not(bv[i])
                a_gt_b = secure_and(av[i], not_b)
                gt_here = secure_and(prefix_eq, a_gt_b)
                gt_val = secure_or(gt_val, gt_here)
                bit_eq = _secure_xnor(av[i], bv[i], c)
                prefix_eq = secure_and(prefix_eq, bit_eq)

            if not signed or width == 0:
                return gt_val

            sign_a = av[width - 1]
            sign_b = bv[width - 1]
            signs_same = _secure_xnor(sign_a, sign_b, c)
            a_nonneg = _secure_not(sign_a)
            pos_vs_neg = secure_and(a_nonneg, sign_b)
            same_sign_gt = secure_and(signs_same, gt_val)
            return secure_or(pos_vs_neg, same_sign_gt)

        def secure_mux_vec(a_vals: List[float], b_vals: List[float], s_val: float) -> List[int]:
            width = max(len(a_vals), len(b_vals))
            av = extend_vec(a_vals, width, False)
            bv = extend_vec(b_vals, width, False)
            not_s = _secure_not(s_val)
            out: List[int] = []
            for i in range(width):
                from_a = secure_and(not_s, av[i])
                from_b = secure_and(s_val, bv[i])
                out_val = secure_or(from_a, from_b)
                out.append(int(round(out_val)))
            return out

        # Assign input port values to wires
        for port_name, port in self.ports.items():
            if port.get("direction") != "input":
                continue
            if port_name not in inputs:
                raise KeyError(f"Missing input for port '{port_name}'")
            bits = port.get("bits", [])
            value = np.asarray(inputs[port_name]).reshape(-1)
            if len(bits) == 1:
                wire_values[bits[0]] = float(value[0]) if value.size else float(inputs[port_name])
            else:
                if value.size != len(bits):
                    raise ValueError(f"Input '{port_name}' expected {len(bits)} bits, got {value.size}")
                for bit_id, bit_val in zip(bits, value):
                    wire_values[bit_id] = float(bit_val)

        # Gate evaluation loop
        pending = list(self.cells)
        progressed = True
        while pending and progressed:
            progressed = False
            next_pending = []

            for cell in pending:
                cell_type = cell["type"]
                # Yosys may emit escaped type names like "\$_AND_".
                if isinstance(cell_type, str) and cell_type.startswith("\\"):
                    cell_type = cell_type[1:]
                conns = cell["connections"]

                if cell_type in _BINARY_GATES:
                    a_bits = conns.get("A", [])
                    b_bits = conns.get("B", [])
                    y_bits = conns.get("Y", [])
                    if len(a_bits) != 1 or len(b_bits) != 1 or len(y_bits) != 1:
                        raise ValueError(f"Unsupported multi-bit gate in cell type {cell_type}")

                    a_val = get_bit_value(a_bits[0])
                    b_val = get_bit_value(b_bits[0])
                    if a_val is None or b_val is None:
                        next_pending.append(cell)
                        continue

                    if secure:
                        if cell_type == "$_AND_":
                            out = CryptographicPrimitives.secure_nnand(np.array([a_val, b_val]), c)
                            out_val = _to_scalar(out)
                        elif cell_type == "$_OR_":
                            out = CryptographicPrimitives.secure_nnor(np.array([a_val, b_val]), c)
                            out_val = _to_scalar(out)
                        elif cell_type == "$_XOR_":
                            out = CryptographicPrimitives.secure_nnxor(np.array([a_val, b_val]), c)
                            out_val = _to_scalar(out)
                        elif cell_type == "$_XNOR_":
                            out_val = _secure_xnor(a_val, b_val, c)
                        elif cell_type == "$_NAND_":
                            out_val = _secure_nand(a_val, b_val, c)
                        elif cell_type == "$_NOR_":
                            out_val = _secure_nor(a_val, b_val, c)
                        else:
                            raise ValueError(f"Unsupported gate type {cell_type}")
                    else:
                        if cell_type == "$_AND_":
                            out_val = 1.0 if (a_val and b_val) else 0.0
                        elif cell_type == "$_OR_":
                            out_val = 1.0 if (a_val or b_val) else 0.0
                        elif cell_type == "$_XOR_":
                            out_val = float((int(round(a_val)) + int(round(b_val))) % 2)
                        elif cell_type == "$_XNOR_":
                            out_val = 1.0 - float((int(round(a_val)) + int(round(b_val))) % 2)
                        elif cell_type == "$_NAND_":
                            out_val = 0.0 if (a_val and b_val) else 1.0
                        elif cell_type == "$_NOR_":
                            out_val = 0.0 if (a_val or b_val) else 1.0
                        else:
                            raise ValueError(f"Unsupported gate type {cell_type}")

                    wire_values[y_bits[0]] = float(out_val)
                    progressed = True
                    continue

                if cell_type in _UNARY_GATES:
                    a_bits = conns.get("A", [])
                    y_bits = conns.get("Y", [])
                    if len(a_bits) != 1 or len(y_bits) != 1:
                        raise ValueError(f"Unsupported multi-bit gate in cell type {cell_type}")
                    a_val = get_bit_value(a_bits[0])
                    if a_val is None:
                        next_pending.append(cell)
                        continue

                    if secure:
                        out_val = _secure_not(a_val)
                    else:
                        out_val = 1.0 - float(int(round(a_val)))

                    wire_values[y_bits[0]] = float(out_val)
                    progressed = True
                    continue

                if cell_type in _ARITH_CELLS:
                    if cell_type == "$scopeinfo":
                        # Debug-only metadata cell; no functional outputs to resolve.
                        progressed = True
                        continue

                    if cell_type == "$mux":
                        a_bits = conns.get("A", [])
                        b_bits = conns.get("B", [])
                        s_bits = conns.get("S", [])
                        y_bits = conns.get("Y", [])
                        if secure:
                            a_vals = get_vec_values(a_bits)
                            b_vals = get_vec_values(b_bits)
                            s_vals = get_vec_values(s_bits)
                            if a_vals is None or b_vals is None or s_vals is None:
                                next_pending.append(cell)
                                continue
                            out_vals = secure_mux_vec(a_vals, b_vals, s_vals[0])
                        else:
                            a_vals = get_vec_int(a_bits)
                            b_vals = get_vec_int(b_bits)
                            s_vals = get_vec_int(s_bits)
                            if a_vals is None or b_vals is None or s_vals is None:
                                next_pending.append(cell)
                                continue
                            out_vals = b_vals if s_vals[0] else a_vals
                        set_vec(y_bits, out_vals)
                        progressed = True
                        continue

                    a_bits = conns.get("A", [])
                    b_bits = conns.get("B", [])
                    y_bits = conns.get("Y", [])

                    a_signed = bool(param_int(cell, "A_SIGNED", 0))
                    b_signed = bool(param_int(cell, "B_SIGNED", 0))
                    y_width = param_int(cell, "Y_WIDTH", len(y_bits))

                    if secure and cell_type in {"$eq", "$gt", "$ge"}:
                        a_vals_f = get_vec_values(a_bits)
                        b_vals_f = get_vec_values(b_bits)
                        if a_vals_f is None or b_vals_f is None:
                            next_pending.append(cell)
                            continue
                        if cell_type == "$eq":
                            yv = secure_eq_vec(a_vals_f, b_vals_f, signed=(a_signed or b_signed))
                        elif cell_type == "$gt":
                            yv = secure_gt_vec(a_vals_f, b_vals_f, a_signed=a_signed, b_signed=b_signed)
                        elif cell_type == "$ge":
                            gt_val = secure_gt_vec(a_vals_f, b_vals_f, a_signed=a_signed, b_signed=b_signed)
                            eq_val = secure_eq_vec(a_vals_f, b_vals_f, signed=(a_signed or b_signed))
                            yv = secure_or(gt_val, eq_val)
                        else:
                            raise ValueError(f"Unsupported secure arithmetic cell type {cell_type}")
                        set_vec(y_bits, int_to_bits(int(round(yv)), y_width))
                        progressed = True
                        continue

                    a_vals = get_vec_int(a_bits)
                    b_vals = get_vec_int(b_bits)
                    if a_vals is None or b_vals is None:
                        next_pending.append(cell)
                        continue
                    av = bits_to_int(a_vals, signed=a_signed)
                    bv = bits_to_int(b_vals, signed=b_signed)

                    if cell_type == "$add":
                        yv = av + bv
                    elif cell_type == "$sub":
                        yv = av - bv
                    elif cell_type == "$mul":
                        yv = av * bv
                    elif cell_type == "$div":
                        if bv == 0:
                            yv = 0
                        else:
                            yv = int(av / bv)
                    elif cell_type == "$ge":
                        yv = 1 if av >= bv else 0
                    elif cell_type == "$gt":
                        yv = 1 if av > bv else 0
                    elif cell_type == "$eq":
                        yv = 1 if av == bv else 0
                    elif cell_type == "$mod":
                        if bv == 0:
                            yv = 0
                        else:
                            yv = av - int(av / bv) * bv
                    else:
                        raise ValueError(f"Unsupported arithmetic cell type {cell_type}")

                    out_bits = int_to_bits(yv, y_width)
                    if secure and cell_type in {"$add", "$sub", "$mul", "$div", "$mod"}:
                        set_vec_secure(y_bits, out_bits)
                    else:
                        set_vec(y_bits, out_bits)
                    progressed = True
                    continue

                raise ValueError(f"Unsupported cell type {cell_type}")

            pending = next_pending

        if pending:
            raise RuntimeError("Failed to resolve all gates; check for cycles or missing inputs.")

        # Collect output port values
        outputs: Dict[str, np.ndarray] = {}
        for port_name, port in self.ports.items():
            if port.get("direction") != "output":
                continue
            bits = port.get("bits", [])
            values = []
            for bit_id in bits:
                val = get_bit_value(bit_id)
                if val is None:
                    raise RuntimeError(f"Output bit {bit_id} for '{port_name}' was not resolved.")
                values.append(val)
            outputs[port_name] = np.array(values, dtype=float)

        return outputs


def load_yosys_json(path: str, module_name: Optional[str] = None) -> YosysNetlist:
    """Load a Yosys JSON netlist and return a YosysNetlist object."""
    with open(path, "r") as f:
        data = json.load(f)

    modules = data.get("modules", {})
    if not modules:
        raise ValueError("No modules found in JSON netlist.")

    if module_name is None:
        for name, mod in modules.items():
            if mod.get("attributes", {}).get("top") == "00000000000000000000000000000001":
                module_name = name
                break
        if module_name is None:
            module_name = next(iter(modules.keys()))

    if module_name not in modules:
        raise KeyError(f"Module '{module_name}' not found in netlist.")

    mod = modules[module_name]
    ports = mod.get("ports", {})
    cells = list(mod.get("cells", {}).values())

    return YosysNetlist(module_name=module_name, ports=ports, cells=cells)
