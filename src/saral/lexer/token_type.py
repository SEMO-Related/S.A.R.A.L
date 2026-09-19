from enum import Enum, auto

class TokenType(Enum):
  IDENTIFIER = auto()

  # type keywords
  KW_INT = auto()
  INT_LITERAL = auto()
  KW_FLOAT = auto()
  FLOAT_LITERAL = auto()
  KW_STRING = auto()
  STRING_LITERAL = auto()
  BOOL = auto()

  # boolean literal keywords
  KW_TRUE = auto()
  KW_FALSE = auto()

  # control-flow / statement keywords
  SHOW = auto()
  IF = auto()
  ELSE = auto()
  WHILE = auto()
  RETURN = auto()

  # comparison operators
  EQ = auto()          # ==
  NEQ = auto()         # !=
  LT = auto()          # <
  GT = auto()          # >
  LE = auto()          # <=
  GE = auto()          # >=

  # arithmetic operators
  PLUS = auto()        # +
  MINUS = auto()       # -
  MUL = auto()        # *
  DIV = auto()       # /
  MOD = auto()     # %

  # assignment
  ASSIGN = auto()      # =

  # punctuation / delimiters
  LPAREN = auto()      # (
  RPAREN = auto()      # )
  LBRACE = auto()      # {
  RBRACE = auto()      # }
  LBRACKET = auto()    # [
  RBRACKET = auto()    # ]
  SEMICOLON = auto()   # ;
  COMMA = auto()       # ,

  # end of stream
  EOF = auto()

KEYWORDS: dict[str, TokenType] = {
    "int": TokenType.KW_INT,
    "float": TokenType.KW_FLOAT,
    "string": TokenType.KW_STRING,
    "bool": TokenType.BOOL,
    "true": TokenType.KW_TRUE,
    "false": TokenType.KW_FALSE,
    "show": TokenType.SHOW,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "return": TokenType.RETURN,
}
