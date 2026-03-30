# Dilithium Neural Mapping Pipeline

This repository contains a minimal, reproducible pipeline for evaluating Dilithium-related hardware components from Verilog RTL through Yosys JSON netlists, software netlist execution, secure/neural-style evaluation, and component-level metrics.

The supported workflow is:

`Verilog RTL -> testbench-generated vectors -> Yosys JSON netlist -> parser evaluation -> optional secure/neural evaluation -> component metrics`

## Repository Layout

```text
.
├── README.md
├── .gitignore
├── component_metrics.py
├── src/
│   ├── test_netlist_parser.py
│   └── core/
│       ├── netlist_parser.py
│       └── crypto_dnn.py
├── tools/
│   └── measure_component_metrics.py
├── Dilithium Building Blocks/
│   ├── *.v
│   ├── *.json
│   ├── *.ys
│   └── tb_*.v
└── dilithium_tests/
    └── *.txt
```

## Purpose

The repository validates Dilithium hardware building blocks by:

1. Generating deterministic test vectors from Verilog testbenches
2. Synthesizing Verilog into Yosys JSON netlists
3. Evaluating the JSON netlists in software
4. Comparing computed outputs to expected outputs
5. Measuring runtime and ReLU usage in classical and secure/neural modes

`secure=False` performs direct logic/arithmetic simulation.

`secure=True` uses the analytic neural-style secure evaluation path implemented in `src/core/crypto_dnn.py` and `src/core/netlist_parser.py`.

## Requirements

Install the following tools manually:

- Python 3.11+
- `numpy`
- Yosys
- Icarus Verilog (`iverilog`, `vvp`)

Example Python setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy
```

## 1. Generate Test Vectors

Generate vectors by compiling and running the matching Verilog testbench.

Example: inverse NTT

```bash
iverilog -o main "Dilithium Building Blocks/tb_invntt_256_comb.v" "Dilithium Building Blocks/invntt_256_comb.v"
vvp main
rm -f main
```

This writes vectors to:

```text
dilithium_tests/invntt_256_comb.txt
```

Example: forward NTT

```bash
iverilog -o main "Dilithium Building Blocks/tb_dilithium_ntt_unrolled.v" "Dilithium Building Blocks/dilithium_ntt_unrolled_kamal.v"
vvp main
rm -f main
```

This writes vectors to:

```text
Dilithium Building Blocks/dilithium_ntt_unrolled_test.txt
```

## 2. Generate JSON Netlists

Use Yosys to synthesize Verilog into JSON.

Example using a `.ys` script:

```bash
yosys -s "Dilithium Building Blocks/dilithium_ntt_unrolled.ys"
```

Example using an inline command:

```bash
yosys -p 'read_verilog -sv "Dilithium Building Blocks/poly_use_hint.v"; hierarchy -check -top poly_use_hint; proc; opt; flatten; opt_clean; write_json "Dilithium Building Blocks/poly_use_hint.json"'
```

Use `flatten` for modules that instantiate helper submodules and therefore require a flat JSON netlist for the parser.

## 3. Run the Parser

Classical evaluation example:

```bash
python src/test_netlist_parser.py \
  --netlist "Dilithium Building Blocks/invntt_256_comb.json" \
  --module invntt_256_comb \
  --vectors "dilithium_tests/invntt_256_comb.txt"
```

Secure/neural evaluation example:

```bash
python src/test_netlist_parser.py \
  --netlist "Dilithium Building Blocks/invntt_256_comb.json" \
  --module invntt_256_comb \
  --vectors "dilithium_tests/invntt_256_comb.txt" \
  --secure
```

The parser:

1. Loads the Yosys JSON netlist
2. Reads the vector file
3. Detects port bit ordering
4. Evaluates the circuit
5. Reports `matches / total`

## 4. Run Metrics

The metrics script reports:

- estimated ReLU count
- classical runtime
- secure runtime
- vector count
- pass/fail result

Run:

```bash
python component_metrics.py
```

or:

```bash
python tools/measure_component_metrics.py
```

## Reproducible Example

For a complete example using `invntt_256_comb`:

```bash
iverilog -o main "Dilithium Building Blocks/tb_invntt_256_comb.v" "Dilithium Building Blocks/invntt_256_comb.v"
vvp main
rm -f main

yosys -s "Dilithium Building Blocks/invntt_256_comb.ys"

python src/test_netlist_parser.py \
  --netlist "Dilithium Building Blocks/invntt_256_comb.json" \
  --module invntt_256_comb \
  --vectors "dilithium_tests/invntt_256_comb.txt"
```

## Notes

- Most generated vector files are deterministic because the testbenches use a fixed seed.
- Some components use fewer vectors than others because large secure-mode evaluations are expensive.
- The parser automatically detects port bit ordering from the best-matching vector interpretation.
- `component_metrics.py` is a convenience wrapper around `tools/measure_component_metrics.py`.
- The repository is organized for reproducibility rather than arbitrary Verilog support.

## Acknowledgements

The Verilog hardware modules (`.v` files) used in this repository were provided by Kamal Raj (GitHub: kamlarajnegi).
