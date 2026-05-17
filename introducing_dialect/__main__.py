import sys
import os

sys.path.append(os.getcwd())

from qiskit_aer import AerSimulator
from qiskit import transpile

import numpy as np

from parser import Parser
from lexer import Lexer
from generator import Generator

if __name__ == "__main__":
    with open("example.sql") as f:
        qsql_query = "\n".join(f.readlines())

    print("=" * 70)
    print("QuantumQL demonstration")
    print("=" * 70)

    print("=" * 70)
    print("\n[1] Tokenizing...")
    print("=" * 70)
    lexer = Lexer(qsql_query)
    tokens = lexer.tokenize()
    print(f"    Generated {len(tokens)} tokens.")

    print("=" * 70)
    print("\n    First 15 tokens:")
    print("=" * 70)
    for t in tokens[:15]:
        print(f"      {t}")

    print("=" * 70)
    print("\n[2] Parsing...")
    print("=" * 70)
    parser = Parser(tokens)
    try:
        program = parser.parse()
        print(f"    Successfully parsed {len(program.statements)} statements.\n")
        print(program)
    except SyntaxError as e:
        print(f"    Parse error: {e}")

    print("=" * 70)
    print("\n[3] Generating circuit...")
    print("=" * 70)

    generator = Generator()
    circuit = generator.generate(program)

    print(f"\nCircuit generated successfully:")
    print(f"  Qubits: {circuit.num_qubits}")
    print(f"  Classical bits: {circuit.num_clbits}")
    print(f"  Depth: {circuit.depth()}")
    print(f"  Gates: {sum(1 for _ in circuit)}")

    print("=" * 70)
    print("\n[4] Transpiling to basic gates...")
    print("=" * 70)

    basis_gates = ['u3', 'u2', 'u1', 'cx', 'cz', 'h', 'x', 'y', 'z', 's', 'sdg', 't', 'tdg', 'swap']

    try:
        circuit_decomposed = circuit.decompose(reps=3)
        print(f"  Decomposition complete.")
        print(f"    Depth after decompose: {circuit_decomposed.depth()}")
        print(f"    Operations after decompose: {len(circuit_decomposed.data)}")

        remaining_high_level = set()
        for instruction in circuit_decomposed.data:
            if instruction.operation.name not in basis_gates and instruction.operation.name != 'measure':
                remaining_high_level.add(instruction.operation.name)

        if remaining_high_level:
            print(f"  Warning: Remaining high-level instructions: {remaining_high_level}")
            print(f"  Transpiling to basis gates...")
            circuit_final = transpile(circuit_decomposed, basis_gates=basis_gates, optimization_level=2)
        else:
            circuit_final = circuit_decomposed

    except Exception as e:
        print(f"  Decomposition failed: {e}")
        print(f"  Trying direct transpile...")
        circuit_final = transpile(circuit, basis_gates=basis_gates, optimization_level=2)

    # TODO: fixme
    shots = 10000
    print("=" * 70)
    print("\n[5] Running simulation...")
    print("=" * 70)
    simulator = AerSimulator()
    job = simulator.run(circuit_final, shots=shots)
    result = job.result()
    counts = result.get_counts()

    print(f"  Simulation complete.")
    print(f"  Unique outcomes: {len(counts)}")
    print(f"  Total shots: {sum(counts.values())}")

    print("\n" + "─" * 70)
    print("[6] POST-PROCESSING")
    print("─" * 70)

    sorted_counts = sorted(counts.items(), key=lambda x: -x[1])

    print(f"\n  Top 15 measurement outcomes:")
    print(f"  {'Binary':<12} {'Count':<10} {'Probability':<12} {'Percentage':<10} {'Bar'}")
    print(f"  {'─'*12} {'─'*10} {'─'*12} {'─'*10} {'─'*30}")

    max_count = max(counts.values())
    for i, (bitstring, count) in enumerate(sorted_counts[:15]):
        probability = count / shots
        percentage = probability * 100
        bar_len = int(30 * count / max_count)
        bar = '█' * bar_len
        print(f"  {bitstring:<12} {count:<10} {probability:<12.4f} {percentage:>6.2f}%    {bar}")

    total_shots = sum(counts.values())
    min_count = min(counts.values())
    mean_count = total_shots / len(counts) if len(counts) > 0 else 0

    print(f"\n  Statistics:")
    print(f"    Max count: {max_count} ({max_count/shots*100:.2f}%)")
    print(f"    Min count: {min_count} ({min_count/shots*100:.2f}%)")
    print(f"    Mean count: {mean_count:.1f}")
    print(f"    Std dev: {np.std(list(counts.values())):.1f}")

    if len(sorted_counts) > 1:
        median_idx = len(sorted_counts) // 2
        median_count = sorted_counts[median_idx][1]
        top_to_median = sorted_counts[0][1] / median_count if median_count > 0 else float('inf')
        print(f"    Top-to-median ratio: {top_to_median:.2f}x")

        probs = np.array([c / shots for c in counts.values()])
        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        max_entropy = np.log2(len(counts))
        print(f"    Entropy: {entropy:.2f} bits (max: {max_entropy:.2f} bits)")
        print(f"    Normalized entropy: {entropy/max_entropy:.4f}")
