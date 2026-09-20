"""Parser tests for S.A.R.A.L (Final Project - Part 3).

Each test lexes a source string, parses it, and asserts on the shape of the
resulting AST. AST nodes are dataclasses, so structural equality is enough.
"""

import pytest

from saral.error import ParseError
from saral.lexer import Lexer
from saral.parser.parser import Parser
from saral.parser.ast import (
    AssignmentStmt,
    Binary,
    BlockStmt,
    BoolNode,
    FunctionCall,
    FunctionStmt,
    IfStmt,
    NumberNode,
    Parameter,
    Program,
    ReturnStmt,
    ShowStmt,
    StringNode,
    Variable,
    WhileStmt,
)


def parse(source: str) -> Program:
    """Run the full lexer -> parser pipeline on a source string."""
    return Parser(Lexer(source).scan_tokens()).parse()


def first_value(source: str):
    """Parse a single declaration and return the expression assigned to it."""
    return parse(source).statements[0].value


# --------------------------- numbers and variables ---------------------------

def test_integer_literal():
    assert first_value("int x = 42;") == NumberNode(value=42)


def test_float_literal():
    assert first_value("float x = 3.5;") == NumberNode(value=3.5)


def test_string_literal():
    assert first_value('string s = "hello";') == StringNode(value="hello")


def test_boolean_literal():
    assert first_value("bool b = true;") == BoolNode(value=True)


def test_variable_reference():
    assert first_value("int x = y;") == Variable(name="y")


# ------------------------- arithmetic and precedence -------------------------

def test_multiplication_binds_tighter_than_addition():
    """The assignment's worked example: 2 + 3 * 4 groups as 2 + (3 * 4)."""
    assert first_value("int x = 2 + 3 * 4;") == Binary(
        left=NumberNode(value=2),
        operator="+",
        right=Binary(
            left=NumberNode(value=3),
            operator="*",
            right=NumberNode(value=4),
        ),
    )


def test_parentheses_override_precedence():
    """(2 + 3) * 4 must group the addition first."""
    assert first_value("int x = (2 + 3) * 4;") == Binary(
        left=Binary(
            left=NumberNode(value=2),
            operator="+",
            right=NumberNode(value=3),
        ),
        operator="*",
        right=NumberNode(value=4),
    )


def test_subtraction_is_left_associative():
    """10 - 4 - 3 must group as (10 - 4) - 3, not 10 - (4 - 3)."""
    assert first_value("int x = 10 - 4 - 3;") == Binary(
        left=Binary(
            left=NumberNode(value=10),
            operator="-",
            right=NumberNode(value=4),
        ),
        operator="-",
        right=NumberNode(value=3),
    )


def test_division_and_modulo_bind_tighter_than_subtraction():
    assert first_value("int x = 20 - 8 / 4 % 3;") == Binary(
        left=NumberNode(value=20),
        operator="-",
        right=Binary(
            left=Binary(
                left=NumberNode(value=8),
                operator="/",
                right=NumberNode(value=4),
            ),
            operator="%",
            right=NumberNode(value=3),
        ),
    )


def test_nested_parentheses():
    assert first_value("int x = ((1 + 2));") == Binary(
        left=NumberNode(value=1),
        operator="+",
        right=NumberNode(value=2),
    )


# -------------------------------- statements ---------------------------------

def test_variable_declaration():
    assert parse("int x = 5;") == Program(
        statements=[AssignmentStmt(var_type="int", name="x", value=NumberNode(value=5))]
    )


def test_variable_reassignment():
    """Reassignment has no type keyword; var_type is None."""
    assert parse("x = 5;") == Program(
        statements=[AssignmentStmt(var_type=None, name="x", value=NumberNode(value=5))]
    )


def test_print_statement_with_string():
    assert parse('show("hi");') == Program(
        statements=[ShowStmt(expression=StringNode(value="hi"))]
    )


def test_print_statement_with_expression():
    assert parse("show(1 + 2);") == Program(
        statements=[
            ShowStmt(
                expression=Binary(
                    left=NumberNode(value=1),
                    operator="+",
                    right=NumberNode(value=2),
                )
            )
        ]
    )


def test_multiple_statements():
    program = parse("int a = 1;\nint b = 2;\nshow(a);")
    assert len(program.statements) == 3
    assert isinstance(program.statements[0], AssignmentStmt)
    assert isinstance(program.statements[1], AssignmentStmt)
    assert isinstance(program.statements[2], ShowStmt)


# ------------------------- control flow and functions ------------------------

def test_comparison_operator_in_condition():
    program = parse("while (n < 5) { show(n); }")
    assert program.statements[0].condition == Binary(
        left=Variable(name="n"),
        operator="<",
        right=NumberNode(value=5),
    )


def test_if_else_statement():
    program = parse('if (x == 1) { show("one"); } else { show("other"); }')
    assert program.statements[0] == IfStmt(
        condition=Binary(
            left=Variable(name="x"),
            operator="==",
            right=NumberNode(value=1),
        ),
        then_branch=BlockStmt(statements=[ShowStmt(expression=StringNode(value="one"))]),
        else_branch=BlockStmt(statements=[ShowStmt(expression=StringNode(value="other"))]),
    )


def test_if_without_else():
    program = parse("if (x > 0) { show(x); }")
    assert program.statements[0].else_branch is None


def test_while_loop_with_reassignment_in_body():
    program = parse("while (n < 5) { show(n); n = n + 1; }")
    assert program.statements[0] == WhileStmt(
        condition=Binary(
            left=Variable(name="n"),
            operator="<",
            right=NumberNode(value=5),
        ),
        body=BlockStmt(
            statements=[
                ShowStmt(expression=Variable(name="n")),
                AssignmentStmt(
                    var_type=None,
                    name="n",
                    value=Binary(
                        left=Variable(name="n"),
                        operator="+",
                        right=NumberNode(value=1),
                    ),
                ),
            ]
        ),
    )


def test_function_declaration():
    program = parse("int add(int a, int b) { return a + b; }")
    assert program.statements[0] == FunctionStmt(
        return_type="int",
        name="add",
        parameters=[
            Parameter(param_type="int", name="a"),
            Parameter(param_type="int", name="b"),
        ],
        body=BlockStmt(
            statements=[
                ReturnStmt(
                    value=Binary(
                        left=Variable(name="a"),
                        operator="+",
                        right=Variable(name="b"),
                    )
                )
            ]
        ),
    )


def test_function_call_as_statement():
    program = parse("addition(3, 4);")
    call = program.statements[0]
    assert isinstance(call, FunctionCall)
    assert call.name == "addition"
    assert [a.value for a in call.arguments] == [NumberNode(value=3), NumberNode(value=4)]


def test_function_call_inside_expression():
    value = first_value("int x = double(21) + 1;")
    assert isinstance(value, Binary)
    assert value.operator == "+"
    assert isinstance(value.left, FunctionCall)
    assert value.left.name == "double"
    assert value.right == NumberNode(value=1)


# ----------------------------- syntax error handling -------------------------

def test_missing_expression_is_syntax_error():
    """The assignment's example: `let x = ;` must be rejected."""
    with pytest.raises(ParseError) as excinfo:
        parse("int x = ;")
    assert "expression" in str(excinfo.value).lower()


def test_missing_semicolon_is_syntax_error():
    with pytest.raises(ParseError) as excinfo:
        parse("int x = 5")
    assert "';'" in str(excinfo.value)


def test_unclosed_parenthesis_is_syntax_error():
    with pytest.raises(ParseError) as excinfo:
        parse("int x = (1 + 2;")
    assert "')'" in str(excinfo.value)


def test_unexpected_token_at_statement_start_is_syntax_error():
    with pytest.raises(ParseError):
        parse("+ 1;")


def test_syntax_error_reports_line_and_column():
    """Errors must carry a source position, not just a message."""
    with pytest.raises(ParseError) as excinfo:
        parse("int a = 1;\nint b = ;")
    assert excinfo.value.line == 2
    assert excinfo.value.column == 9


def test_missing_closing_brace_is_syntax_error():
    with pytest.raises(ParseError):
        parse("while (n < 5) { show(n);")