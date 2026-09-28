class SaralError(Exception):
  def __init__(self, message: str, line: int | None = None, column: int | None = None):
    self.message = message
    self.line = line
    self.column = column
    if line is not None:
      location = f"[line {line}, col {column}]" if column is not None else f"[line {line}]"
      super().__init__(f"{location} {message}")
    else:
      super().__init__(message)

class LexError(SaralError):
    """Raised for a single invalid token during lexing."""

class ParseError(SaralError):
    """Raised when the token stream does not match the S.A.R.A.L grammar."""

class InterpreterError(SaralError):
   """Raised when a runtime error occurs"""
