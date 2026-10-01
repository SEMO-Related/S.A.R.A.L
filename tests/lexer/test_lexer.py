from saral.lexer.lexer import Lexer, TokenType
from saral.error import SaralError


def types_of(source: str) -> list[TokenType]:
    return [t.type for t in Lexer(source).scan_tokens()]

def test_line_comment_produces_no_tokens():
    lexer = Lexer("int x = 5; // this sets x\nshow(x);")
    tokens = lexer.scan_tokens()
    assert lexer.errors == []
    assert [t.type for t in tokens] == [
        TokenType.KW_INT, TokenType.IDENTIFIER, TokenType.ASSIGN,
        TokenType.INT_LITERAL, TokenType.SEMICOLON,
        TokenType.SHOW, TokenType.LPAREN, TokenType.IDENTIFIER,
        TokenType.RPAREN, TokenType.SEMICOLON, TokenType.EOF,
    ]

def test_line_comment_at_eof_with_no_trailing_newline():
    types = types_of("int x = 5; // trailing comment, no newline")
    assert types == [
        TokenType.KW_INT, TokenType.IDENTIFIER, TokenType.ASSIGN,
        TokenType.INT_LITERAL, TokenType.SEMICOLON, TokenType.EOF,
    ]

def test_block_comment_inline():
    tokens = Lexer("int x /* inline note */ = 5;").scan_tokens()
    assert [t.type for t in tokens] == [
        TokenType.KW_INT, TokenType.IDENTIFIER, TokenType.ASSIGN,
        TokenType.INT_LITERAL, TokenType.SEMICOLON, TokenType.EOF,
    ]

def test_block_comment_spanning_multiple_lines_tracks_line_numbers():
    src = "int x = 1;\n/* this is\n   multi-line */\nshow(x);"
    tokens = Lexer(src).scan_tokens()
    show_tok = next(t for t in tokens if t.type == TokenType.SHOW)
    assert show_tok.line == 4

def test_unterminated_block_comment_reports_error_not_crash():
    lexer = Lexer("int x = 1; /* oops")
    tokens = lexer.scan_tokens()
    assert len(lexer.errors) == 1
    assert "Unterminated block comment" in lexer.errors[0].message
    # lexing still completed rather than crashing -- but note the bad
    # comment produced NO token at all (same as whitespace), so the only
    # way to detect this is checking `lexer.errors`, not the token list
    assert tokens[-1].type == TokenType.EOF

def test_block_comments_do_not_nest():
    # per the grammar, the FIRST closing "*/" ends the comment
    tokens = Lexer("int x /* outer /* inner */ y */ = 5;").scan_tokens()
    types = [t.type for t in tokens]
    # "y" survives as a real identifier, and the leftover "*/" re-lexes
    # as MUL then DIV rather than closing anything (no nesting)
    assert TokenType.IDENTIFIER in types
    idents = [t for t in tokens if t.type == TokenType.IDENTIFIER]
    assert idents[-1].lexeme == "y"

def test_comment_does_not_appear_inside_expression():
    tokens = Lexer("int x = 1 + /* two */ 2;").scan_tokens()
    types = [t.type for t in tokens]
    assert types == [
        TokenType.KW_INT, TokenType.IDENTIFIER, TokenType.ASSIGN,
        TokenType.INT_LITERAL, TokenType.PLUS, TokenType.INT_LITERAL,
        TokenType.SEMICOLON, TokenType.EOF,
    ]

def test_lone_slash_is_still_division():
    lexer = Lexer("int x = 10 / 2;")
    types = [t.type for t in lexer.scan_tokens()]
    assert TokenType.DIV in types
    assert lexer.errors == []

def test_punctuation_and_operators():
    assert types_of("(+-*/%){}[];,") == [
        TokenType.LPAREN,
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.MUL,
        TokenType.DIV,
        TokenType.MOD,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.LBRACKET,
        TokenType.RBRACKET,
        TokenType.SEMICOLON,
        TokenType.COMMA,
        TokenType.EOF,
    ]


def test_comparison_operators_are_greedy():
    # must NOT split "==" into "=" "="
    assert types_of("== != <= >= < > =") == [
        TokenType.EQ,
        TokenType.NEQ,
        TokenType.LE,
        TokenType.GE,
        TokenType.LT,
        TokenType.GT,
        TokenType.ASSIGN,
        TokenType.EOF,
    ]


def test_integer_and_float_numbers():
    tokens = Lexer("42 3.14 0").scan_tokens()
    assert [t.literal for t in tokens[:-1]] == [42, 3.14, 0]
    assert [t.type for t in tokens[:-1]] == [
        TokenType.INT_LITERAL,
        TokenType.FLOAT_LITERAL,
        TokenType.INT_LITERAL,
    ]


def test_identifier_vs_keyword():
    tokens = Lexer("int x show").scan_tokens()
    assert [t.type for t in tokens[:-1]] == [
        TokenType.KW_INT,
        TokenType.IDENTIFIER,
        TokenType.SHOW,
    ]
    assert tokens[1].lexeme == "x"


def test_all_type_and_control_keywords():
    source = "int float string bool if else while return true false"
    assert types_of(source) == [
        TokenType.KW_INT,
        TokenType.KW_FLOAT,
        TokenType.KW_STRING,
        TokenType.BOOL,
        TokenType.IF,
        TokenType.ELSE,
        TokenType.WHILE,
        TokenType.RETURN,
        TokenType.KW_TRUE,
        TokenType.KW_FALSE,
        TokenType.EOF,
    ]


def test_bool_literal_values():
    tokens = Lexer("true false").scan_tokens()
    assert tokens[0].literal is True
    assert tokens[1].literal is False


def test_string_literal():
    tokens = Lexer('"hello world!"').scan_tokens()
    assert tokens[0].type == TokenType.STRING_LITERAL
    assert tokens[0].literal == "hello world!"


def test_unterminated_string_reports_error():
    lexer = Lexer('"oops')
    lexer.scan_tokens()
    assert len(lexer.errors) == 1
    assert "Unterminated" in lexer.errors[0].message


def test_unknown_character_reports_error_but_continues():
    lexer = Lexer("x = 1 ~ 2;")
    tokens = lexer.scan_tokens()
    assert len(lexer.errors) == 1
    assert tokens[-1].type == TokenType.EOF
    assert TokenType.INT_LITERAL in [t.type for t in tokens]


def test_line_and_column_tracking():
    tokens = Lexer("int x;\nshow(x);").scan_tokens()
    show_tok = next(t for t in tokens if t.type == TokenType.SHOW)
    assert show_tok.line == 2
    assert show_tok.column == 1


def test_full_show_statement():
    types = types_of('show("hi");')
    assert types == [
        TokenType.SHOW,
        TokenType.LPAREN,
        TokenType.STRING_LITERAL,
        TokenType.RPAREN,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]


def test_func_stmt_with_params():
    source = "int add(int a, int b) { return a + b; }"
    types = types_of(source)
    assert types == [
        TokenType.KW_INT,
        TokenType.IDENTIFIER,
        TokenType.LPAREN,
        TokenType.KW_INT,
        TokenType.IDENTIFIER,
        TokenType.COMMA,
        TokenType.KW_INT,
        TokenType.IDENTIFIER,
        TokenType.RPAREN,
        TokenType.LBRACE,
        TokenType.RETURN,
        TokenType.IDENTIFIER,
        TokenType.PLUS,
        TokenType.IDENTIFIER,
        TokenType.SEMICOLON,
        TokenType.RBRACE,
        TokenType.EOF,
    ]


def test_array_access_and_dimensions():
    types = types_of("int arr[3]; arr[0] = 1;")
    assert types == [
        TokenType.KW_INT,
        TokenType.IDENTIFIER,
        TokenType.LBRACKET,
        TokenType.INT_LITERAL,
        TokenType.RBRACKET,
        TokenType.SEMICOLON,
        TokenType.IDENTIFIER,
        TokenType.LBRACKET,
        TokenType.INT_LITERAL,
        TokenType.RBRACKET,
        TokenType.ASSIGN,
        TokenType.INT_LITERAL,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
