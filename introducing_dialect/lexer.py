from typing import List
from tokens import Token, TokenType

class Lexer:
    """Tokenizes QSQL source code."""

    KEYWORDS = {
        'PREPARE', 'STATE', 'FROM', 'USING', 'ON',
        'APPLY', 'WITH', 'PARAMETERS',
        'ENTANGLE', 'AS', 'AND',
        'AMPLIFY', 'SOURCE', 'WHERE', 'CORRELATION', 'OF',
        'MEASURE', 'INTO', 'CONFIDENCE', 'SHOTS',
        'classical_table', 'classical_array',
        'amplitude_encoding', 'angle_encoding', 'basis_encoding',
        'CNOT', 'CZ',
        'AUTO',
    }

    CIRCUIT_NAMES = {
        'variational_circuit',
        'quantum_fourier_transform',
        'feature_map',
        'ansatz',
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source and return a list of tokens."""
        self.tokens = []
        while self.pos < len(self.source):
            char = self.source[self.pos]

            # Whitespace
            if char in ' \t\r':
                self._advance()
                continue

            # Newline
            if char == '\n':
                self.line += 1
                self.col = 1
                self.pos += 1
                continue

            # Comments: -- until end of line
            if char == '-' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '-':
                self._skip_comment()
                continue

            # Pipe-wrapped identifiers: |name>
            if char == '|':
                self._tokenize_pipe_ident()
                continue

            # Numbers (integers and floats)
            if char.isdigit() or (char == '.' and self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit()):
                self._tokenize_number()
                continue

            # Strings (single-quoted)
            if char == "'":
                self._tokenize_string()
                continue

            # Operators (>=, <=, >, <, =)
            if char in '><=':
                self._tokenize_operator()
                continue

            # Punctuation
            if char in '(),;[]':
                self._add_token(TokenType.PUNCTUATION, char)
                self._advance()
                continue

            # Identifiers and keywords
            if char.isalpha() or char == '_':
                self._tokenize_identifier_or_keyword()
                continue

            raise SyntaxError(f"Unexpected character '{char}' at line {self.line}, col {self.col}")

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens

    def _advance(self):
        self.pos += 1
        self.col += 1

    def _add_token(self, token_type: TokenType, value: str):
        self.tokens.append(Token(token_type, value, self.line, self.col))

    def _skip_comment(self):
        while self.pos < len(self.source) and self.source[self.pos] != '\n':
            self.pos += 1
            self.col += 1

    def _tokenize_pipe_ident(self):
        start_line, start_col = self.line, self.col
        self._advance()
        ident = ''
        while self.pos < len(self.source) and self.source[self.pos] != '>':
            ident += self.source[self.pos]
            self._advance()
        if self.pos >= len(self.source):
            raise SyntaxError(f"Unterminated pipe identifier at line {start_line}, col {start_col}")
        self._advance()
        self.tokens.append(Token(TokenType.PIPE_IDENT, ident.strip(), start_line, start_col))

    def _tokenize_number(self):
        start_line, start_col = self.line, self.col
        num_str = ''
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            num_str += self.source[self.pos]
            self._advance()
        self.tokens.append(Token(TokenType.NUMBER, num_str, start_line, start_col))

    def _tokenize_string(self):
        start_line, start_col = self.line, self.col
        self._advance()
        s = ''
        while self.pos < len(self.source) and self.source[self.pos] != "'":
            s += self.source[self.pos]
            self._advance()
        if self.pos >= len(self.source):
            raise SyntaxError(f"Unterminated string at line {start_line}, col {start_col}")
        self._advance()
        self.tokens.append(Token(TokenType.STRING, s, start_line, start_col))

    def _tokenize_operator(self):
        start_line, start_col = self.line, self.col
        op = self.source[self.pos]
        self._advance()
        if op in '><' and self.pos < len(self.source) and self.source[self.pos] == '=':
            op += '='
            self._advance()
        self.tokens.append(Token(TokenType.OPERATOR, op, start_line, start_col))

    def _tokenize_identifier_or_keyword(self):
        start_line, start_col = self.line, self.col
        ident = ''
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] in '_'):
            ident += self.source[self.pos]
            self._advance()

        if ident in self.KEYWORDS:
            self.tokens.append(Token(TokenType.KEYWORD, ident, start_line, start_col))
        else:
            self.tokens.append(Token(TokenType.IDENTIFIER, ident, start_line, start_col))
