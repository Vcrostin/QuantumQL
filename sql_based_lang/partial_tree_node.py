from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import qiskit.quantum_info as qi

class PartialTraceNode:
    """
    Узел проекции столбцов (Эквивалент: SELECT col1, col2).
    Отбрасывает ненужные кубиты (колонки) и извлекает результат нужных.
    """

    def __init__(self, total_qubits: int, target_qubits: list, column_names: list = None):
        self.total_qubits = total_qubits
        self.target_qubits = target_qubits
        self.column_names = column_names if column_names else [f"col_{i}" for i in range(len(target_qubits))]

    def to_circuit(self) -> QuantumCircuit:
        qr = QuantumRegister(self.total_qubits, name="db_reg")

        cr = ClassicalRegister(len(self.target_qubits), name="SELECT_out")

        qc = QuantumCircuit(qr, cr, name="SELECT")

        for classical_idx, quantum_idx in enumerate(self.target_qubits):
            qc.measure(quantum_idx, classical_idx)

        return qc

    @staticmethod
    def show_tensor_math(circuit: QuantumCircuit, keep_qubits: list):
        state = qi.Statevector.from_instruction(circuit.remove_final_measurements(inplace=False))
        density_matrix = qi.DensityMatrix(state)

        total_qubits = circuit.num_qubits
        discard_qubits = [q for q in range(total_qubits) if q not in keep_qubits]

        reduced_density_matrix = qi.partial_trace(density_matrix, discard_qubits)
        return reduced_density_matrix

if __name__ == "__main__":
    from qiskit import transpile
    from qiskit_aer import AerSimulator

    print("SQL: SELECT id FROM items WHERE color = 'Blue'")

    total_qubits = 3
    dag = QuantumCircuit(total_qubits)

    dag.h(1)
    dag.x(0)
    dag.x(2)

    dag.barrier()

    select_node = PartialTraceNode(
        total_qubits=total_qubits,
        target_qubits=[0, 1], # Забираем только q0 и q1
        column_names=["id"]
    )

    full_dag = dag.compose(select_node.to_circuit())

    print("\nКвантовый DAG (Execution Plan):")
    print(full_dag.draw())

    simulator = AerSimulator()
    compiled_circuit = transpile(full_dag, simulator)
    job = simulator.run(compiled_circuit, shots=1000)
    counts = job.result().get_counts()

    print("\nРезультаты выборки (Только колонка 'id'):")
    parsed_results = {int(k, 2): v for k, v in counts.items()}

    for item_id, count in parsed_results.items():
        print(f"ID = {item_id} | Найдено в {(count/1000)*100}% случаев")
