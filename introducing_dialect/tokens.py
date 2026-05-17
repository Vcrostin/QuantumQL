from enum import Enum, auto


class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    PIPE_IDENT = auto()          # |register_name>
    NUMBER = auto()
    STRING = auto()
    OPERATOR = auto()
    PUNCTUATION = auto()
    EOF = auto()


class SourceType(Enum):
    TABLE = auto()
    ARRAY = auto()


class EncodingType(Enum):
    AMPLITUDE = auto()
    ANGLE = auto()
    BASIS = auto()


class Operator(Enum):
    GT = ">"
    GE = ">="
    LT = "<"
    LE = "<="
    EQ = "="


class Token:
    def __init__(self, token_type: TokenType, value: str, line: int, col: int):
        self.type = token_type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', line={self.line}, col={self.col})"


class Expr:
    pass


class RegisterRef(Expr):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"RegisterRef({self.name})"


class CorrelationRef(Expr):
    def __init__(self, alias: str):
        self.alias = alias

    def __repr__(self):
        return f"CorrelationRef({self.alias})"


class LiteralExpr(Expr):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"LiteralExpr({self.value})"


class Condition:
    def __init__(self, left: Expr, op: Operator, right: Expr):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"Condition({self.left} {self.op.value} {self.right})"
