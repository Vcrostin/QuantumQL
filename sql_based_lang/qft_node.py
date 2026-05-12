import math
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT

class QFTNode:
    """
    Узел квантового преобразования Фурье.
    Тензорная операция, переводящая фазу (frequency domain) в базисные состояния (computational basis).
    В квантовом SQL используется в обратном режиме (Inverse) для финализации агрегации.
    """
    def __init__(self, num_qubits: int, inverse: bool = True):
        self.num_qubits = num_qubits
        self.inverse = inverse

    def to_circuit(self) -> QuantumCircuit:
        return QFT(num_qubits=self.num_qubits, inverse=self.inverse, insert_barriers=True)
