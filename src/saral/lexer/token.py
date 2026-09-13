from dataclasses import dataclass
from typing import Any
from .token_type import TokenType

@dataclass(frozen=True)
class Token:
  type: TokenType
  lexeme: str
  literal: Any
  line: int
  column: int

  def __repr__(self) -> str:
    lit = f" literal={self.literal!r}" if self.literal is not None else ""
    return f"Token({self.type.name} {self.lexeme!r}{lit} @{self.line}:{self.column})"
