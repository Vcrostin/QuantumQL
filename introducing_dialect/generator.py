import numpy as np
from typing import Dict, List, Optional, Set, Tuple, Union
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import StatePreparation


class CircuitGenerationError(Exception):
    """Raised when circuit generation encounters an invalid state."""
    pass


class Generator:
    """
    Generates a Qiskit QuantumCircuit from a QuantumQl parser AST Program.
    """

    def __init__(self):
        self._symbols: Dict[str, QuantumRegister] = {}
        self._classical_regs: Dict[str, ClassicalRegister] = {}
        self._consumed: Set[str] = set()

        self._entangled_to: Dict[str, str] = {}

        self._entanglement_groups: Dict[str, Set[str]] = {}
        self._circuit: Optional[QuantumCircuit] = None

    def generate(self, program) -> QuantumCircuit:
        """
        Generate a Qiskit QuantumCircuit from a parser Program AST.

        Args:
            program: The root Program node (from parser).

        Returns:
            A complete Qiskit QuantumCircuit ready for execution.
        """
        self._symbols.clear()
        self._classical_regs.clear()
        self._consumed.clear()
        self._entangled_to.clear()
        self._entanglement_groups.clear()
        self._circuit = QuantumCircuit()

        for stmt in program.statements:
            self._process_statement(stmt)

        return self._circuit

    def _process_statement(self, stmt) -> None:
        stmt_type = type(stmt).__name__

        # TODO: do better

        if stmt_type == 'PrepareState':
            self._handle_prepare_state(stmt)
        elif stmt_type == 'Apply':
            self._handle_apply(stmt)
        elif stmt_type == 'Entangle':
            self._handle_entangle(stmt)
        elif stmt_type == 'AmplifyWhere':
            self._handle_amplify_where(stmt)
        elif stmt_type == 'Measure':
            self._handle_measure(stmt)
        else:
            raise CircuitGenerationError(
                f"Unknown statement type: {stmt_type}"
            )

    def _resolve_register(self, name: str) -> Tuple[str, QuantumRegister]:
        """
        Resolve a register name to its actual QuantumRegister.
        If the name is an entangled alias, return the joint register.
        If the name is a constituent of an entanglement, return the joint register.
        """
        if name in self._symbols:
            return name, self._symbols[name]

        if name in self._entangled_to:
            joint_name = self._entangled_to[name]
            if joint_name in self._symbols:
                return joint_name, self._symbols[joint_name]

        raise CircuitGenerationError(f"Undefined register: '{name}'")

    def _is_available(self, name: str) -> bool:
        """Check if a register is available for use (not consumed)."""
        if name in self._consumed:
            return False
        if name in self._entangled_to:
            joint_name = self._entangled_to[name]
            if joint_name in self._consumed:
                return False
        return True

    def _handle_prepare_state(self, stmt) -> None:
        """Handle PREPARE STATE statement."""
        if stmt.register in self._symbols:
            raise CircuitGenerationError(
                f"Register '{stmt.register}' is already defined."
            )

        source_type = stmt.source_type
        source_type_name = source_type.name if hasattr(source_type, 'name') else str(source_type)

        if 'TABLE' in source_type_name:
            self._prepare_from_table(stmt)
        elif 'ARRAY' in source_type_name:
            self._prepare_from_array(stmt)
        else:
            raise CircuitGenerationError(
                f"Unsupported source type: {source_type}"
            )

    def _prepare_from_table(self, stmt) -> None:
        """Amplitude encoding from a classical table."""
        encoding_name = stmt.encoding.name if hasattr(stmt.encoding, 'name') else str(stmt.encoding)
        if 'AMPLITUDE' not in encoding_name:
            raise CircuitGenerationError(
                f"TABLE source requires AMPLITUDE encoding, got {stmt.encoding}"
            )

        num_rows = self._get_table_row_count(stmt.source)
        num_qubits = int(np.ceil(np.log2(num_rows)))
        if num_qubits == 0:
            num_qubits = 1

        total_amplitudes = 2 ** num_qubits

        num_features = len(stmt.columns) if stmt.columns else 4
        feature_vectors = self._generate_synthetic_features(num_rows, num_features)

        row_amplitudes = np.mean(feature_vectors, axis=1)

        if len(row_amplitudes) < total_amplitudes:
            padded = np.zeros(total_amplitudes)
            padded[:len(row_amplitudes)] = row_amplitudes
        else:
            padded = row_amplitudes[:total_amplitudes]

        norm = np.linalg.norm(padded)
        if norm > 0:
            padded = padded / norm
        else:
            padded = np.ones(total_amplitudes) / np.sqrt(total_amplitudes)

        qreg = QuantumRegister(num_qubits, name=stmt.register)
        self._circuit.add_register(qreg)
        self._symbols[stmt.register] = qreg

        state_prep = StatePreparation(padded)
        self._circuit.append(state_prep, qreg)

        print(f"  [PrepareState] Table '{stmt.source}': {num_rows} rows -> "
              f"{num_qubits} qubits, {total_amplitudes} amplitudes")

    def _prepare_from_array(self, stmt) -> None:
        """Angle encoding from a classical array."""
        encoding_name = stmt.encoding.name if hasattr(stmt.encoding, 'name') else str(stmt.encoding)
        if 'ANGLE' not in encoding_name:
            raise CircuitGenerationError(
                f"ARRAY source requires ANGLE encoding, got {stmt.encoding}"
            )

        values = self._parse_array_literal(stmt.source)
        num_qubits = len(values)

        if num_qubits == 0:
            raise CircuitGenerationError(
                "ARRAY source must contain at least one value."
            )

        qreg = QuantumRegister(num_qubits, name=stmt.register)
        self._circuit.add_register(qreg)
        self._symbols[stmt.register] = qreg

        for i, value in enumerate(values):
            self._circuit.ry(value * np.pi, qreg[i])

        print(f"  [PrepareState] Array source: {num_qubits} values -> "
              f"{num_qubits} qubits (angle encoding)")

    def _handle_apply(self, stmt) -> None:
        reg_name = stmt.register

        if reg_name not in self._symbols:
            raise CircuitGenerationError(f"Undefined register: '{reg_name}'")
        if not self._is_available(reg_name):
            raise CircuitGenerationError(
                f"Register '{reg_name}' has already been consumed."
            )

        qreg = self._symbols[reg_name]

        circuit_name = stmt.circuit_name
        parameters = stmt.parameters if hasattr(stmt, 'parameters') else []

        print(f"  [Apply] Circuit '{circuit_name}' on register "
              f"'{reg_name}' ({qreg.size} qubits)")

        if 'variational_circuit' in circuit_name or 'feature_map' in circuit_name:
            self._apply_variational_circuit(qreg, parameters)
        elif 'quantum_fourier_transform' in circuit_name or 'qft' in circuit_name.lower():
            self._apply_qft(qreg)
        else:
            self._circuit.h(qreg)

    def _apply_variational_circuit(self, qreg: QuantumRegister, params: List[float]) -> None:
        n = qreg.size

        if not params:
            raise CircuitGenerationError(
                f"Params for variational_circuit must be provided."
            )

        for i in range(n):
            angle = params[i % len(params)]
            self._circuit.ry(angle, qreg[i])

        for i in range(n - 1):
            self._circuit.cx(qreg[i], qreg[i + 1])
        if n > 1:
            self._circuit.cx(qreg[n - 1], qreg[0])

        for i in range(n):
            angle = params[(i + 1) % len(params)]
            self._circuit.ry(angle, qreg[i])

    def _apply_qft(self, qreg: QuantumRegister) -> None:
        n = qreg.size
        for i in range(n):
            self._circuit.h(qreg[i])
            for j in range(i + 1, n):
                angle = np.pi / (2 ** (j - i))
                self._circuit.cp(angle, qreg[j], qreg[i])
        for i in range(n // 2):
            self._circuit.swap(qreg[i], qreg[n - 1 - i])

    def _handle_entangle(self, stmt) -> None:
        reg_a_name = stmt.reg_a
        reg_b_name = stmt.reg_b

        if reg_a_name not in self._symbols:
            raise CircuitGenerationError(f"Undefined register: '{reg_a_name}'")
        if reg_b_name not in self._symbols:
            raise CircuitGenerationError(f"Undefined register: '{reg_b_name}'")
        if not self._is_available(reg_a_name):
            raise CircuitGenerationError(f"Register '{reg_a_name}' already consumed.")
        if not self._is_available(reg_b_name):
            raise CircuitGenerationError(f"Register '{reg_b_name}' already consumed.")

        reg_a = self._symbols[reg_a_name]
        reg_b = self._symbols[reg_b_name]

        gate = stmt.gate.upper() if hasattr(stmt, 'gate') else 'CNOT'

        print(f"  [Entangle] '{reg_a_name}' ({reg_a.size}q) with '{reg_b_name}' "
              f"({reg_b.size}q) using {gate} -> alias '{stmt.alias}'")

        for ctrl, tgt in stmt.qubit_pairs:
            ctrl_idx = ctrl - 1
            tgt_idx = tgt - 1

            if ctrl_idx >= reg_a.size:
                raise CircuitGenerationError(
                    f"Control qubit index {ctrl} out of range "
                    f"(register '{reg_a_name}' has {reg_a.size} qubits)"
                )
            if tgt_idx >= reg_b.size:
                raise CircuitGenerationError(
                    f"Target qubit index {tgt} out of range "
                    f"(register '{reg_b_name}' has {reg_b.size} qubits)"
                )

            if gate == 'CNOT':
                self._circuit.cx(reg_a[ctrl_idx], reg_b[tgt_idx])
            elif gate == 'CZ':
                self._circuit.cz(reg_a[ctrl_idx], reg_b[tgt_idx])
            else:
                raise CircuitGenerationError(f"Unsupported gate: {gate}")

        combined = QuantumRegister(
            reg_a.size + reg_b.size,
            name=stmt.alias
        )
        self._circuit.add_register(combined)
        self._symbols[stmt.alias] = combined

        self._entanglement_groups[stmt.alias] = {reg_a_name, reg_b_name}
        self._entangled_to[reg_a_name] = stmt.alias
        self._entangled_to[reg_b_name] = stmt.alias

    def _handle_amplify_where(self, stmt) -> None:
        source_reg_name = stmt.source_register

        resolved_name, source_reg = self._resolve_register(source_reg_name)

        if not self._is_available(source_reg_name):
            raise CircuitGenerationError(
                f"Register '{source_reg_name}' has already been consumed."
            )

        condition = stmt.condition
        correlation_alias = self._extract_correlation_from_condition(condition)

        if correlation_alias is None:
            raise CircuitGenerationError(
                "Condition must reference CORRELATION OF <alias>."
            )

        if correlation_alias not in self._symbols:
            raise CircuitGenerationError(
                f"Undefined correlation alias in condition: '{correlation_alias}'"
            )

        joint_reg = self._symbols[correlation_alias]

        source_size = source_reg.size if source_reg.name == resolved_name else self._symbols[source_reg_name].size

        ancilla_name = f"ancilla_{correlation_alias}"
        if ancilla_name not in self._symbols:
            ancilla = QuantumRegister(1, name=ancilla_name)
            self._circuit.add_register(ancilla)
            self._symbols[ancilla_name] = ancilla
        else:
            ancilla = self._symbols[ancilla_name]

        mid = source_size

        print(f"  [AmplifyWhere] Source: '{source_reg_name}' ({source_size}q), "
              f"Joint: '{correlation_alias}' ({joint_reg.size}q), "
              f"Ancilla: '{ancilla_name}'")

        target_qubits = [joint_reg[i] for i in range(mid, joint_reg.size)]

        if len(target_qubits) > 0:
            for q in target_qubits:
                self._circuit.x(q)
            self._circuit.mcx(target_qubits, ancilla[0])
            for q in target_qubits:
                self._circuit.x(q)
        else:
            self._circuit.x(ancilla[0])

        n_qubits = source_size
        iterations = int(np.floor(np.pi / 4 * np.sqrt(2 ** n_qubits)))
        iterations = max(1, min(iterations, 10))

        print(f"  [AmplifyWhere] Grover iterations: {iterations}")

        source_qubits = [joint_reg[i] for i in range(source_size)]

        for _ in range(iterations):
            self._circuit.cz(ancilla[0], source_qubits[0])

            for q in source_qubits:
                self._circuit.h(q)
            for q in source_qubits:
                self._circuit.x(q)
            self._circuit.h(source_qubits[-1])
            if len(source_qubits) > 1:
                self._circuit.mcx(
                    source_qubits[:-1],
                    source_qubits[-1]
                )
            self._circuit.h(source_qubits[-1])
            for q in source_qubits:
                self._circuit.x(q)
            for q in source_qubits:
                self._circuit.h(q)

        if len(target_qubits) > 0:
            for q in target_qubits:
                self._circuit.x(q)
            self._circuit.mcx(target_qubits, ancilla[0])
            for q in target_qubits:
                self._circuit.x(q)
        else:
            self._circuit.x(ancilla[0])

        self._consumed.add(ancilla_name)

    def _extract_correlation_from_condition(self, condition) -> Optional[str]:
        left = condition.left
        if hasattr(left, 'alias'):
            return left.alias
        right = condition.right
        if hasattr(right, 'alias'):
            return right.alias
        return None

    def _handle_measure(self, stmt) -> None:
        """Handle MEASURE statement."""
        reg_name = stmt.register

        if reg_name in self._entangled_to:
            joint_name = self._entangled_to[reg_name]
            joint_reg = self._symbols[joint_name]

            source_size = self._symbols[reg_name].size if reg_name in self._symbols else joint_reg.size // 2

            if joint_name in self._consumed:
                raise CircuitGenerationError(
                    f"Joint register '{joint_name}' has already been consumed."
                )

            source_qubits = [joint_reg[i] for i in range(source_size)]

            creg = ClassicalRegister(source_size, name=stmt.output_name)
            self._circuit.add_register(creg)

            for i, q in enumerate(source_qubits):
                self._circuit.measure(q, creg[i])

            self._classical_regs[stmt.output_name] = creg
            self._consumed.add(joint_name)

            print(f"  [Measure] Entangled register '{reg_name}' ({source_size}q) "
                  f"from joint '{joint_name}' -> classical '{stmt.output_name}' "
                  f"({creg.size} bits), shots={stmt.shots}")
        else:
            if reg_name not in self._symbols:
                raise CircuitGenerationError(f"Undefined register: '{reg_name}'")
            if not self._is_available(reg_name):
                raise CircuitGenerationError(
                    f"Register '{reg_name}' has already been consumed."
                )

            qreg = self._symbols[reg_name]
            creg = ClassicalRegister(qreg.size, name=stmt.output_name)
            self._circuit.add_register(creg)
            self._circuit.measure(qreg, creg)
            self._classical_regs[stmt.output_name] = creg
            self._consumed.add(reg_name)

            print(f"  [Measure] Register '{reg_name}' ({qreg.size}q) -> "
                  f"classical '{stmt.output_name}' ({creg.size} bits), "
                  f"shots={stmt.shots}")

    def _get_table_row_count(self, source_name: str) -> int:
        # TODO: add source lookup??
        known_tables = {
            "user_features": 256,
            "product_catalog": 512,
            "transaction_log": 1024,
        }
        return known_tables.get(source_name, 256)

    def _generate_synthetic_features(
        self, num_rows: int, num_features: int
    ) -> np.ndarray:
        rng = np.random.default_rng(seed=42)
        return rng.random((num_rows, num_features))

    def _parse_array_literal(self, source: str) -> List[float]:
        cleaned = source.strip().strip("[]")
        if not cleaned:
            return []
        return [float(x.strip()) for x in cleaned.split(",")]

    @property
    def symbols(self) -> Dict[str, QuantumRegister]:
        return self._symbols

    @property
    def circuit(self) -> Optional[QuantumCircuit]:
        return self._circuit
