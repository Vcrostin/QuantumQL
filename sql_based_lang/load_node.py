import math
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
import qiskit

class LoadNode:
    def __init__(self, table_name: str, data: list, mode: str = 'superposition'):
        self.table_name = table_name
        self.mode = mode

        self.data = data
        self.num_qubits = self._calculate_qubits()

    def _calculate_qubits(self) -> int:
        if len(self.data) == 0:
            raise ValueError(f"Таблица {self.table_name} пуста!")
        return math.ceil(math.log2(len(self.data)))

    def to_circuit(self) -> QuantumCircuit:
        qr = QuantumRegister(self.num_qubits, name=f"reg_{self.table_name}")
        qc = QuantumCircuit(qr, name=f"Init_{self.table_name}")

        if self.mode == 'superposition':
            qc.h(qr)

        elif self.mode == 'amplitude_encoding':
            vector = np.array(self.data, dtype=float)

            norm = np.linalg.norm(vector)
            if norm == 0:
                raise ValueError("Вектор данных не может состоять только из нулей.")
            normalized_vector = vector / norm

            target_dim = 2 ** self.num_qubits
            if len(normalized_vector) < target_dim:
                padded_vector = np.pad(normalized_vector, (0, target_dim - len(normalized_vector)))
            else:
                padded_vector = normalized_vector

            qc.initialize(padded_vector, qr)

        else:
            raise ValueError(f"Неизвестный режим инициализации: {self.mode}")

        return qc


if __name__ == "__main__":
    node_users = LoadNode(table_name="users", data=[1]*8, mode='superposition')
    circuit_users = node_users.to_circuit()

    print("DAG Node: Инициализация FROM users (Superposition)")
    print(circuit_users.draw())

    salaries = [50000, 75000, 60000]
    node_employees = LoadNode(table_name="emp_salary", data=salaries, mode='amplitude_encoding')
    circuit_employees = node_employees.to_circuit()

    print("\nDAG Node: Инициализация FROM emp_salary (Amplitude Encoding - QRAM simulation)")
    print(circuit_employees.draw())

    print(qiskit.quantum_info.Statevector.from_instruction(circuit_employees))
