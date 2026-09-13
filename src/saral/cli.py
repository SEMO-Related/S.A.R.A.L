import argparse
import sys

from .lexer import Lexer

def cmd_tokenize(path: str) -> int:
  with open(path, "r", encoding="utf-8") as f:
    source = f.read()

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

def main() -> int:
  parser = argparse.ArgumentParser(prog="saral")
  subparsers = parser.add_subparsers(dest="command", required=True)

  tokenize_parser = subparsers.add_parser(
    "tokenize", help="Run the lexer on a file and print its tokens"
  )
  tokenize_parser.add_argument("file", help="Path to a .saral source file")

  args = parser.parse_args()

  if args.command == "tokenize":
    return cmd_tokenize(args.file)

  return 0

if __name__ == "__main__":
  raise SystemExit(main())
