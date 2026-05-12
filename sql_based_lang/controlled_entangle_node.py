from qiskit import QuantumCircuit, QuantumRegister

class ControlledEntangleNode:
    """
    Узел квантового JOIN-а.
    Сравнивает два регистра (ключи таблиц). Если они равны, переводит flag_qubit в состояние |1>.
    """

    def __init__(self, key_size: int):
        self.key_size = key_size

    def to_circuit(self) -> QuantumCircuit:
        reg_a = QuantumRegister(self.key_size, name="key_A")
        reg_b = QuantumRegister(self.key_size, name="key_B")
        reg_ancilla = QuantumRegister(self.key_size, name="ancilla")
        reg_flag = QuantumRegister(1, name="JOIN_flag")

        qc = QuantumCircuit(reg_a, reg_b, reg_ancilla, reg_flag, name="JOIN")

        for i in range(self.key_size):
            qc.cx(reg_a[i], reg_ancilla[i])
            qc.cx(reg_b[i], reg_ancilla[i])

        for i in range(self.key_size):
            qc.x(reg_ancilla[i])

        if self.key_size == 1:
            qc.cx(reg_ancilla[0], reg_flag[0])
        else:
            qc.mcx(reg_ancilla, reg_flag[0])

        for i in range(self.key_size):
            qc.x(reg_ancilla[i])
            qc.cx(reg_b[i], reg_ancilla[i])
            qc.cx(reg_a[i], reg_ancilla[i])

        return qc
