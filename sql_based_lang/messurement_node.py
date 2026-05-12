from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister

class MeasurementNode:
    """
    Узел извлечения данных (Эквивалент: SQL Fetch / ResultSet).
    Коллапсирует квантовое состояние в классические биты и парсит результат.
    """

    def __init__(self, total_qubits: int, target_qubits: list, column_names: list):
        self.total_qubits = total_qubits
        self.target_qubits = target_qubits
        self.column_names = column_names

        if len(target_qubits) != len(column_names):
            raise ValueError("Количество измеряемых кубитов должно совпадать с количеством колонок!")

    def to_circuit(self) -> QuantumCircuit:
        qr = QuantumRegister(self.total_qubits, name="q_bus")
        cr = ClassicalRegister(len(self.target_qubits), name="c_out")
        qc = QuantumCircuit(qr, cr, name="Fetch")

        for i, q_idx in enumerate(self.target_qubits):
            qc.measure(q_idx, i)

        return qc

    def fetch_all(self, raw_counts: dict, total_shots: int, threshold_percent: float = 5.0) -> list:
        result_set = []

        for bin_str, count in raw_counts.items():
            probability = (count / total_shots) * 100

            if probability < threshold_percent:
                continue

            corrected_bin_str = bin_str[::-1]

            row = {}
            for i, col_name in enumerate(self.column_names):
                row[col_name] = int(corrected_bin_str[i])

            row['_confidence'] = f"{probability:.1f}%"
            result_set.append(row)

        result_set.sort(key=lambda x: float(x['_confidence'].strip('%')), reverse=True)
        return result_set
