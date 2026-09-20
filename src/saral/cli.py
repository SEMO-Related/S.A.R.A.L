import argparse
import sys

from .lexer import Lexer
from .parser.parser import Parser
from .parser.ast import print_ast

def cmd_tokenize(path: str) -> int:
  source = get_source(path)

  lexer = Lexer(source)
  tokens = lexer.scan_tokens()

  for tok in tokens:
    print(tok)

  if lexer.errors:
    print(f"\n{len(lexer.errors)} lexical error(s):", file=sys.stderr)
    for err in lexer.errors:
      print(f"  {err}", file=sys.stderr)
    return 1

  return 0

def cmd_parse(path: str) -> int:
  source = get_source(path)
  lexer = Lexer(source)
  tokens = lexer.scan_tokens()

  if lexer.errors:
    print(f"\n{len(lexer.errors)} lexical error(s):", file=sys.stderr)
    for err in lexer.errors:
      print(f"  {err}", file=sys.stderr)
    return 1

  parser = Parser(tokens)
  ast = parser.parse()

  print_ast(ast)
  return 0

def get_source(path: str | None) -> str:
  if path:
    with open(path, "r", encoding="utf-8") as f:
      return f.read()

  return input("saral> ")

def main() -> int:
  parser = argparse.ArgumentParser(prog="saral")
  subparsers = parser.add_subparsers(dest="command", required=True)

  tokenize_parser = subparsers.add_parser(
    "tokenize", help="Run the lexer on a file and print its tokens"
  )

  tokenize_parser.add_argument(
  "file",
  nargs="?",
  help="Path to a .saral source file"
)

  parse_parser = subparsers.add_parser(
    "parse", help="Parse a file and print its AST"
  )

  parse_parser.add_argument(
    "file",
    nargs="?",
    help="Path to a .saral source file"
  )

  args = parser.parse_args()

  if args.command == "tokenize":
    return cmd_tokenize(args.file)

  elif args.command == "parse":
    return cmd_parse(args.file)

  return 0

if __name__ == "__main__":
  raise SystemExit(main())
