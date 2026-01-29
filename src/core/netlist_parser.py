import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

import numpy as np

from .crypto_dnn import CryptoDNN, CryptographicPrimitives


_BINARY_GATES = {"$_AND_", "$_OR_", "$_XOR_", "$_XNOR_", "$_NAND_", "$_NOR_"}
_UNARY_GATES = {"$_NOT_"}


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

        def get_bit_value(bit: int) -> Optional[float]:
            if bit == 0:
                return 0.0
            if bit == 1:
                return 1.0
            return wire_values.get(bit)

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
