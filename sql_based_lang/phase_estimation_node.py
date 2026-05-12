from qiskit import QuantumCircuit, QuantumRegister
from .qft_node import Node_QFT


class PhaseEstimationNode:
    """
    Узел агрегации (Эквивалент: SELECT COUNT(*) WHERE ...).
    Оценивает угол поворота унитарного оператора (в нашем случае - оператора Гровера).
    """
    def __init__(self, eval_qubits: int, state_qubits: int, unitary_operator: QuantumCircuit):
        self.eval_qubits = eval_qubits
        self.state_qubits = state_qubits
        # Превращаем цепь Гровера в единый тензорный вентиль (Gate)
        self.U_gate = unitary_operator.to_gate(label="Grover_Step")

    def to_circuit(self) -> QuantumCircuit:
        qr_eval = QuantumRegister(self.eval_qubits, name="eval_q")
        qr_state = QuantumRegister(self.state_qubits, name="db_q")
        qc = QuantumCircuit(qr_eval, qr_state, name="Phase_Estimation")

        qc.h(qr_eval)

        for j in range(self.eval_qubits):
            power = 2 ** j
            controlled_U = self.U_gate.power(power).control(1)

            qc.append(controlled_U, [qr_eval[j]] + qr_state[:])

        iqft_node = Node_QFT(self.eval_qubits, inverse=True)
        qc.append(iqft_node.to_circuit(), qr_eval)

        return qc
