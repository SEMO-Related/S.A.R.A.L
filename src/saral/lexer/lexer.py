from ..error import LexError
from .token import Token
from .token_type import TokenType, KEYWORDS

_TWO_CHAR_OPERATORS: dict[str, TokenType] = {
  "==": TokenType.EQ,
  "!=": TokenType.NEQ,
  "<=": TokenType.LE,
  ">=": TokenType.GE,
}

_ONE_CHAR_OPERATORS: dict[str, TokenType] = {
  "=": TokenType.ASSIGN,
  "<": TokenType.LT,
  ">": TokenType.GT,
  "+": TokenType.PLUS,
  "-": TokenType.MINUS,
  "*": TokenType.MUL,
  "/": TokenType.DIV,
  "%": TokenType.MOD,
  "(": TokenType.LPAREN,
  ")": TokenType.RPAREN,
  "{": TokenType.LBRACE,
  "}": TokenType.RBRACE,
  "[": TokenType.LBRACKET,
  "]": TokenType.RBRACKET,
  ";": TokenType.SEMICOLON,
  ",": TokenType.COMMA,
}

class Lexer:
  def __init__(self, source: str) -> None:
    self.source = source
    self.tokens: list[Token] = []
    self.errors: list[LexError] = []

    self._start = 0
    self._current = 0
    self._line = 1
    self._col = 1

  def scan_tokens(self) -> list[Token]:
    while not self._at_end():
      self._start = self._current
      self._start_column = self._col
      self._scan_token()
    self.tokens.append(Token(TokenType.EOF, "", None))
    return self.tokens

  def _at_end(self) -> bool:
    """Checks if the pointer is at the end of the source code or not"""
    return self._current >= len(self.source)

  def _advance(self) -> str:
    """Move to next char moving the pointer"""
    ch = self.source[self._current]
    self._current += 1

    # If the character is a line break increase the line counter and reset col counter to 1
    if ch == "\n":
      self._line += 1
      self._col = 1
    else:
      self._col += 1
    return ch

  def _peek(self, offset: int = 0) -> str:
    """Function to peek the next character"""
    idx = self._current + offset
    if idx >= len(self.source):
      return "\0"
    return self.source[idx]


  def _error(self, message: str) -> None:
    """Add error message to the errors list"""
    self.errors.append(LexError(message, self._line, self._start_column))

  def _add_token(self, type_: TokenType, literal=None) -> None:
    """Add the identified token to the tokens list"""
    lexeme = self.source[self._start : self._current]
    self.tokens.append(
      Token(type_, lexeme, literal)
    )

  def _scan_token(self):
    """Scan individual chars"""
    ch = self._advance()

    if ch in "\t\r\n ":
      # skip whitespaces
      return

    if ch == '"':
      self._scan_string()
      return

    if ch.isdigit():
      self._scan_number()
      return

    if ch.isalpha() or ch == "_":
      self._scan_identifier()
      return

    two_char = ch + self._peek()
    if two_char in _TWO_CHAR_OPERATORS:
      self._advance()
      self._add_token(_TWO_CHAR_OPERATORS[two_char])
      return

    if ch in _ONE_CHAR_OPERATORS:
      self._add_token(_ONE_CHAR_OPERATORS[ch])
      return

    self._error(f"Unexpected character {ch!r}")


  def _scan_string(self) -> None:
    value_chars: list[str] = []
    while self._peek() != '"' and not self._at_end() and self._peek() != "\n":
      value_chars.append(self._advance())

    if self._at_end() or self._peek() == "\n":
      self._error("Unterminated string literal")
    else:
      self._advance()
    self._add_token(TokenType.STRING, literal="".join(value_chars))

  def _scan_number(self) -> None:
    while self._peek().isdigit():
      self._advance()

    is_floating = False
    if self._peek() == "." and self._peek(1).isdigit():
      is_floating = True
      self._advance()
      while self._peek().isdigit():
        self._advance()

    lexeme = self.source[self._start: self._current]
    if is_floating:
      literal = float(lexeme)
      self._add_token(TokenType.FLOAT_LITERAL, literal=literal)
    else:
      literal = int(lexeme)
      self._add_token(TokenType.INT_LITERAL, literal=literal)

  def _scan_identifier(self):
    while self._peek().isalnum():
      self._advance()

    text = self.source[self._start : self._current]
    keyword_type = KEYWORDS.get(text)

    if keyword_type in (TokenType.KW_TRUE, TokenType.KW_FALSE):
      self._add_token(keyword_type, literal=(keyword_type == TokenType.KW_TRUE))
    elif keyword_type is not None:
      self._add_token(keyword_type)
    else:
      self._add_token(TokenType.IDENTIFIER)
