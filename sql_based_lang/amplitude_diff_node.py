from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import ZGate

class AmplitudeDiffusionNode:
    """
    Узел амплитудного усиления (Диффузор Гровера).
    Отражает амплитуды относительно среднего значения, усиливая вероятность "помеченных" оракулом элементов.
    Тензорная операция: D = 2|ψ><ψ| - I
    """

    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits

    def to_circuit(self) -> QuantumCircuit:
        qr = QuantumRegister(self.num_qubits, name="q_reg")
        qc = QuantumCircuit(qr, name="Diffuser")

        if self.num_qubits == 0:
            return qc

        qc.h(qr)

        qc.x(qr)

        if self.num_qubits == 1:
            qc.z(0)
        else:
            mcz = ZGate().control(self.num_qubits - 1)
            controls = list(range(self.num_qubits - 1))
            target = self.num_qubits - 1
            qc.append(mcz, controls + [target])

        qc.x(qr)

        qc.h(qr)

        return qc
