import re
from typing import List, Optional, Tuple
from nodes import Program, Stmt, PrepareState, Apply, Entangle, AmplifyWhere, Measure
from tokens import (
    Token, TokenType, SourceType, EncodingType, Condition, Expr, Operator,
    CorrelationRef, RegisterRef, LiteralExpr
)

class Parser:
    """Recursive descent parser."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        statements = []
        while not self._is_eof():
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
            self._skip_semicolons()
        return Program(statements)

    def _parse_statement(self) -> Optional[Stmt]:
        if self._is_eof():
            return None

        token = self._current()
        if token.type != TokenType.KEYWORD:
            raise SyntaxError(f"Expected keyword at line {token.line}, col {token.col}, got '{token.value}'")

        keyword = token.value.upper()

        if keyword == 'PREPARE':
            return self._parse_prepare_state()
        elif keyword == 'APPLY':
            return self._parse_apply()
        elif keyword == 'ENTANGLE':
            return self._parse_entangle()
        elif keyword == 'AMPLIFY':
            return self._parse_amplify_where()
        elif keyword == 'MEASURE':
            return self._parse_measure()
        else:
            raise SyntaxError(f"Unexpected keyword '{keyword}' at line {token.line}, col {token.col}")

    def _parse_prepare_state(self) -> PrepareState:
        self._expect_keyword('PREPARE')
        self._expect_keyword('STATE')

        reg_token = self._expect(TokenType.PIPE_IDENT)
        register = reg_token.value

        self._expect_keyword('FROM')

        source_type, source = self._parse_source()

        self._expect_keyword('USING')

        encoding = self._parse_encoding()

        columns = []
        if self._check_keyword('ON'):
            self._advance()
            self._expect(TokenType.PUNCTUATION, '(')
            columns = self._parse_column_list()
            self._expect(TokenType.PUNCTUATION, ')')

        return PrepareState(register, source, source_type, encoding, columns)

    def _parse_source(self) -> Tuple[SourceType, str]:
        token = self._current()
        if token.type == TokenType.KEYWORD:
            if token.value == 'classical_table':
                self._advance()
                table_name = self._expect(TokenType.IDENTIFIER)
                return SourceType.TABLE, table_name.value
            elif token.value == 'classical_array':
                self._advance()
                self._expect(TokenType.PUNCTUATION, '[')
                array_str = '['
                while not self._check(TokenType.PUNCTUATION, ']'):
                    t = self._current()
                    array_str += t.value
                    self._advance()
                array_str += ']'
                self._expect(TokenType.PUNCTUATION, ']')
                return SourceType.ARRAY, array_str

        raise SyntaxError(f"Expected 'classical_table' or 'classical_array' at line {token.line}")

    def _parse_encoding(self) -> EncodingType:
        token = self._current()
        if token.type == TokenType.KEYWORD:
            if token.value == 'amplitude_encoding':
                self._advance()
                return EncodingType.AMPLITUDE
            elif token.value == 'angle_encoding':
                self._advance()
                return EncodingType.ANGLE
            elif token.value == 'basis_encoding':
                self._advance()
                return EncodingType.BASIS
        raise SyntaxError(f"Expected encoding type at line {token.line}")

    def _parse_column_list(self) -> List[str]:
        columns = []
        columns.append(self._expect(TokenType.IDENTIFIER).value)
        while self._check(TokenType.PUNCTUATION, ','):
            self._advance()
            columns.append(self._expect(TokenType.IDENTIFIER).value)
        return columns

    def _parse_apply(self) -> Apply:
        self._expect_keyword('APPLY')

        circuit_name = self._parse_circuit_name()

        self._expect_keyword('ON')

        reg_token = self._expect(TokenType.PIPE_IDENT)
        register = reg_token.value

        parameters = []
        if self._check_keyword('WITH'):
            self._advance()
            self._expect_keyword('PARAMETERS')
            self._expect(TokenType.PUNCTUATION, '(')
            parameters = self._parse_number_list()
            self._expect(TokenType.PUNCTUATION, ')')

        return Apply(register, circuit_name, parameters)

    def _parse_circuit_name(self) -> str:
        token = self._current()

        if token.type not in (TokenType.IDENTIFIER, TokenType.KEYWORD):
            raise SyntaxError(
                f"Expected circuit name at line {token.line}, col {token.col}, "
                f"got {token.type.name} '{token.value}'"
            )

        name = token.value
        self._advance()

        if self._check(TokenType.PUNCTUATION, '('):
            self._advance()
            param = self._expect(TokenType.STRING)
            name = f"{name}('{param.value}')"
            self._expect(TokenType.PUNCTUATION, ')')

        return name

    def _parse_number_list(self) -> List[float]:
        numbers = []
        numbers.append(float(self._expect(TokenType.NUMBER).value))
        while self._check(TokenType.PUNCTUATION, ','):
            self._advance()
            numbers.append(float(self._expect(TokenType.NUMBER).value))
        return numbers

    def _parse_entangle(self) -> Entangle:
        self._expect_keyword('ENTANGLE')

        reg_a_token = self._expect(TokenType.PIPE_IDENT)
        reg_a = reg_a_token.value

        self._expect_keyword('WITH')

        reg_b = self._parse_register_ref()

        self._expect_keyword('AS')

        alias_token = self._expect(TokenType.IDENTIFIER)
        alias = alias_token.value

        self._expect_keyword('USING')

        gate_token = self._current()
        if gate_token.type not in (TokenType.IDENTIFIER, TokenType.KEYWORD):
            raise SyntaxError(f"Expected gate name at line {gate_token.line}")
        gate = gate_token.value.upper()
        if gate not in ('CNOT', 'CZ'):
            raise SyntaxError(f"Expected CNOT or CZ gate at line {gate_token.line}")
        self._advance()

        self._expect_keyword('ON')

        qubit_pairs = self._parse_qubit_pairs()

        return Entangle(reg_a, reg_b, alias, gate, qubit_pairs)

    def _parse_register_ref(self) -> str:
        if self._current().type == TokenType.PIPE_IDENT:
            name = self._current().value
            self._advance()
            return name
        elif self._current().type == TokenType.IDENTIFIER:
            name = self._current().value
            self._advance()
            return name
        else:
            token = self._current()
            raise SyntaxError(f"Expected register reference at line {token.line}")

    def _parse_qubit_pairs(self) -> List[Tuple[int, int]]:
        pairs = []
        pairs.append(self._parse_qubit_pair())

        # Additional pairs joined by AND
        while self._check_keyword('AND'):
            self._advance()
            pairs.append(self._parse_qubit_pair())

        return pairs

    def _parse_qubit_pair(self) -> Tuple[int, int]:
        self._expect(TokenType.PUNCTUATION, '(')
        q1 = self._parse_qubit_index()
        self._expect(TokenType.PUNCTUATION, ',')
        q2 = self._parse_qubit_index()
        self._expect(TokenType.PUNCTUATION, ')')
        return (q1, q2)

    def _parse_qubit_index(self) -> int:
        token = self._expect(TokenType.IDENTIFIER)
        match = re.match(r'qubit_(\d+)', token.value)
        if not match:
            raise SyntaxError(f"Expected 'qubit_N' at line {token.line}, got '{token.value}'")
        return int(match.group(1))

    def _parse_amplify_where(self) -> AmplifyWhere:
        self._expect_keyword('AMPLIFY')
        self._expect_keyword('SOURCE')

        reg_token = self._expect(TokenType.PIPE_IDENT)
        register = reg_token.value

        self._expect_keyword('WHERE')

        condition = self._parse_condition()

        return AmplifyWhere(register, condition)

    def _parse_condition(self) -> Condition:
        left = self._parse_expression()

        op_token = self._expect(TokenType.OPERATOR)
        op_map = {'>': Operator.GT, '>=': Operator.GE, '<': Operator.LT, '<=': Operator.LE, '=': Operator.EQ}
        if op_token.value not in op_map:
            raise SyntaxError(f"Unknown operator '{op_token.value}' at line {op_token.line}")
        op = op_map[op_token.value]

        right = self._parse_expression()

        return Condition(left, op, right)

    def _parse_expression(self) -> Expr:
        if self._check_keyword('CORRELATION'):
            self._advance()
            self._expect_keyword('OF')
            alias = self._expect(TokenType.IDENTIFIER)
            return CorrelationRef(alias.value)
        elif self._current().type == TokenType.PIPE_IDENT:
            name = self._current().value
            self._advance()
            return RegisterRef(name)
        elif self._current().type == TokenType.IDENTIFIER:
            name = self._current().value
            self._advance()
            return RegisterRef(name)
        elif self._current().type == TokenType.NUMBER:
            value = float(self._current().value)
            self._advance()
            return LiteralExpr(value)
        else:
            token = self._current()
            raise SyntaxError(f"Expected expression at line {token.line}")

    def _parse_measure(self) -> Measure:
        self._expect_keyword('MEASURE')

        reg_token = self._expect(TokenType.PIPE_IDENT)
        register = reg_token.value

        self._expect_keyword('INTO')

        output_token = self._expect(TokenType.IDENTIFIER)
        output_name = output_token.value

        self._expect(TokenType.PUNCTUATION, '(')
        columns = self._parse_column_list()
        self._expect(TokenType.PUNCTUATION, ')')

        confidence = None
        if self._check_keyword('WITH'):
            self._advance()
            self._expect_keyword('CONFIDENCE')
            self._expect(TokenType.OPERATOR, '>=')
            conf_token = self._expect(TokenType.NUMBER)
            confidence = float(conf_token.value)

        shots = 10000  # default
        if self._check_keyword('SHOTS'):
            self._advance()
            self._expect(TokenType.OPERATOR, '=')
            shots_token = self._expect(TokenType.NUMBER)
            shots = int(shots_token.value)

        return Measure(register, output_name, columns, confidence, shots)

    def _current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def _advance(self):
        if self.pos < len(self.tokens):
            self.pos += 1

    def _is_eof(self) -> bool:
        return self._current().type == TokenType.EOF

    def _check(self, token_type: TokenType, value: Optional[str] = None) -> bool:
        token = self._current()
        if token.type != token_type:
            return False
        if value is not None and token.value != value:
            return False
        return True

    def _check_keyword(self, keyword: str) -> bool:
        token = self._current()
        return token.type == TokenType.KEYWORD and token.value.upper() == keyword.upper()

    def _expect(self, token_type: TokenType, value: Optional[str] = None) -> Token:
        token = self._current()
        if token.type != token_type:
            raise SyntaxError(
                f"Expected {token_type.name}" +
                (f" '{value}'" if value else "") +
                f" at line {token.line}, col {token.col}, got {token.type.name} '{token.value}'"
            )
        if value is not None and token.value != value:
            raise SyntaxError(
                f"Expected '{value}' at line {token.line}, col {token.col}, got '{token.value}'"
            )
        self._advance()
        return token

    def _expect_keyword(self, keyword: str) -> Token:
        token = self._current()
        if token.type != TokenType.KEYWORD or token.value.upper() != keyword.upper():
            raise SyntaxError(
                f"Expected keyword '{keyword}' at line {token.line}, col {token.col}, "
                f"got {token.type.name} '{token.value}'"
            )
        self._advance()
        return token

    def _skip_semicolons(self):
        while self._check(TokenType.PUNCTUATION, ';'):
            self._advance()
