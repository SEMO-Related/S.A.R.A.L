from dataclasses import dataclass
from typing import Any
from .token_type import TokenType

@dataclass(frozen=True)
class Token:
  type: TokenType
  lexeme: str
  literal: Any

  def __repr__(self) -> str:
    lit = f" literal={self.literal!r}" if self.literal is not None else ""
    return f"Token({self.type.name} {self.lexeme!r}{lit})"
