from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import ZGate
import qiskit.quantum_info as qi

class PhaseOracleNode:
    """
    Узел квантового оракула (Эквивалент: WHERE condition).
    Инвертирует фазу (амплитуду умножает на -1) для заданных индексов в суперпозиции.
    """

    def __init__(self, target_indices: list, num_qubits: int, condition_str: str = "custom_where"):
        self.target_indices = target_indices
        self.num_qubits = num_qubits
        self.condition_str = condition_str

    def to_circuit(self) -> QuantumCircuit:
        qr = QuantumRegister(self.num_qubits, name="q_reg")
        qc = QuantumCircuit(qr, name=f"WHERE({self.condition_str})")

        if not self.target_indices:
            return qc

        if self.num_qubits == 1:
            mcz = ZGate()
        else:
            mcz = ZGate().control(self.num_qubits - 1)

        for target in self.target_indices:
            bin_str = format(target, f'0{self.num_qubits}b')

            zero_qubits = []

            for i, bit in enumerate(reversed(bin_str)):
                if bit == '0':
                    qc.x(i)
                    zero_qubits.append(i)

            if self.num_qubits == 1:
                qc.append(mcz, [0])
            else:
                controls = list(range(self.num_qubits - 1))
                target_qubit = self.num_qubits - 1
                qc.append(mcz, controls + [target_qubit])

            for i in zero_qubits:
                qc.x(i)

            qc.barrier()

        return qc

if __name__ == "__main__":
    mock_db = [
        (0, "Alice", "user"),
        (1, "Bob",   "admin"),
        (2, "Charlie","user"),
        (3, "Dave",  "admin")
    ]

    print("SQL: SELECT * FROM users WHERE role = 'admin'")
    num_qubits = 2
    target_ids = [row[0] for row in mock_db if row[2] == "admin"]
    print(f"[SQL Engine] Найдено совпадение по индексам: {target_ids}\n")

    oracle_node = PhaseOracleNode(target_indices=target_ids,
                                   num_qubits=num_qubits,
                                   condition_str="role='admin'")
    oracle_circuit = oracle_node.to_circuit()

    print("Квантовая цепь Оракула (DAG Node):")
    print(oracle_circuit.draw())

    operator = qi.Operator(oracle_circuit)
    diagonal = operator.data.diagonal()

    print("\nТензор манипуляции (Диагональ матрицы оракула):")
    for idx, val in enumerate(diagonal):
        clean_val = int(val.real)
        state_bin = format(idx, f'0{num_qubits}b')
        marker = "<-- ПОМЕЧЕНО (WHERE = True)" if clean_val == -1 else ""
        print(f"Состояние |{state_bin}> (индекс {idx}): Фазовый множитель = {clean_val:2d} {marker}")
