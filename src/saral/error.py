class SaralError(Exception):
  def __init__(self, message: str, line: int, column: int):
    self.message = message
    self.line = line
    self.column = column
    super().__init__(f"[line {line}, col {column}] {message}")


class LexError(SaralError):
    """Raised for a single invalid token during lexing."""
