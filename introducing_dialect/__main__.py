import sys
import os

sys.path.append(os.getcwd())

from parser import Parser
from lexer import Lexer

if __name__ == "__main__":
    with open("example.sql") as f:
        qsql_query = "\n".join(f.readlines())

    print("=" * 70)
    print("QSQL PARSER DEMONSTRATION")
    print("=" * 70)

    print("\n[1] Tokenizing...")
    lexer = Lexer(qsql_query)
    tokens = lexer.tokenize()
    print(f"    Generated {len(tokens)} tokens.")

    print("\n    First 15 tokens:")
    for t in tokens[:15]:
        print(f"      {t}")

    print("\n[2] Parsing...")
    parser = Parser(tokens)
    try:
        program = parser.parse()
        print(f"    Successfully parsed {len(program.statements)} statements.\n")
        print(program)
    except SyntaxError as e:
        print(f"    Parse error: {e}")
