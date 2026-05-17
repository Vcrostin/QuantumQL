from typing import List, Optional, Tuple
from tokens import EncodingType, SourceType, Condition


class Stmt:
    pass


class PrepareState(Stmt):
    def __init__(self, register: str, source: str, source_type: SourceType,
                 encoding: EncodingType, columns: List[str]):
        self.register = register
        self.source = source
        self.source_type = source_type
        self.encoding = encoding
        self.columns = columns

    def __repr__(self):
        return (f"PrepareState(\n"
                f"  register='{self.register}',\n"
                f"  source='{self.source}',\n"
                f"  source_type={self.source_type},\n"
                f"  encoding={self.encoding},\n"
                f"  columns={self.columns}\n"
                f")")


class Apply(Stmt):
    def __init__(self, register: str, circuit_name: str, parameters: List[float]):
        self.register = register
        self.circuit_name = circuit_name
        self.parameters = parameters

    def __repr__(self):
        return (f"Apply(\n"
                f"  register='{self.register}',\n"
                f"  circuit_name='{self.circuit_name}',\n"
                f"  parameters={self.parameters}\n"
                f")")


class Entangle(Stmt):
    def __init__(self, reg_a: str, reg_b: str, alias: str, gate: str,
                 qubit_pairs: List[Tuple[int, int]]):
        self.reg_a = reg_a
        self.reg_b = reg_b
        self.alias = alias
        self.gate = gate
        self.qubit_pairs = qubit_pairs

    def __repr__(self):
        return (f"Entangle(\n"
                f"  reg_a='{self.reg_a}',\n"
                f"  reg_b='{self.reg_b}',\n"
                f"  alias='{self.alias}',\n"
                f"  gate='{self.gate}',\n"
                f"  qubit_pairs={self.qubit_pairs}\n"
                f")")


class AmplifyWhere(Stmt):
    def __init__(self, source_register: str, condition: Condition):
        self.source_register = source_register
        self.condition = condition

    def __repr__(self):
        return (f"AmplifyWhere(\n"
                f"  source_register='{self.source_register}',\n"
                f"  condition={self.condition}\n"
                f")")


class Measure(Stmt):
    def __init__(self, register: str, output_name: str, columns: List[str],
                 confidence: Optional[float], shots: int):
        self.register = register
        self.output_name = output_name
        self.columns = columns
        self.confidence = confidence
        self.shots = shots

    def __repr__(self):
        return (f"Measure(\n"
                f"  register='{self.register}',\n"
                f"  output_name='{self.output_name}',\n"
                f"  columns={self.columns},\n"
                f"  confidence={self.confidence},\n"
                f"  shots={self.shots}\n"
                f")")


class Program:
    def __init__(self, statements: List[Stmt]):
        self.statements = statements

    def __repr__(self):
        result = "Program:\n"
        for i, stmt in enumerate(self.statements, 1):
            result += f"\n  Statement {i}:\n  {stmt}\n"
        return result
