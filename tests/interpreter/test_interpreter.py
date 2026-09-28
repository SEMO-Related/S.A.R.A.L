import pytest

from saral.error import InterpreterError
from saral.interpreter.env import Environment
from saral.interpreter.interpreter import Interpreter
from saral.parser.ast import (
    AssignmentStmt,
    Binary,
    BlockStmt,
    BoolNode,
    IfStmt,
    NumberNode,
    Program,
    ShowStmt,
    StringNode,
    Variable,
    WhileStmt,
)


def run(statements, interp: Interpreter | None = None) -> Interpreter:
    interp = interp or Interpreter()
    interp.interpret(Program(statements=statements))
    return interp


# ---------------------------------------------------------------------------
# Environment / symbol table
# ---------------------------------------------------------------------------

def test_environment_define_and_get():
    env = Environment()
    env.define("x", 10)
    assert env.get("x") == 10


def test_environment_get_undefined_raises():
    env = Environment()
    with pytest.raises(InterpreterError, match="Undefined variable 'x'"):
        env.get("x")


def test_environment_assign_requires_prior_declaration():
    env = Environment()
    with pytest.raises(InterpreterError, match="Undefined variable"):
        env.assign("x", 5)


def test_environment_child_scope_sees_parent():
    parent = Environment()
    parent.define("x", 1)
    child = Environment(enclosing=parent)
    assert child.get("x") == 1


def test_environment_assign_climbs_to_parent():
    parent = Environment()
    parent.define("x", 1)
    child = Environment(enclosing=parent)
    child.assign("x", 99)
    assert parent.get("x") == 99  # not shadowed locally -- mutated in place


# ---------------------------------------------------------------------------
# Variable assignment
# ---------------------------------------------------------------------------

def test_variable_declaration_and_read(capsys):
    stmts = [
        AssignmentStmt(var_type="int", name="x", value=NumberNode(10)),
        ShowStmt(expression=Variable("x")),
    ]
    run(stmts)
    assert capsys.readouterr().out == "10\n"


def test_reassignment_updates_value(capsys):
    stmts = [
        AssignmentStmt(var_type="int", name="x", value=NumberNode(1)),
        AssignmentStmt(var_type=None, name="x", value=NumberNode(2)),
        ShowStmt(expression=Variable("x")),
    ]
    run(stmts)
    assert capsys.readouterr().out == "2\n"


def test_declared_type_mismatch_raises():
    stmts = [AssignmentStmt(var_type="int", name="x", value=StringNode("oops"))]
    with pytest.raises(InterpreterError, match="Type mismatch"):
        run(stmts)


# ---------------------------------------------------------------------------
# Arithmetic + precedence
# ---------------------------------------------------------------------------

def test_arithmetic_precedence(capsys):
    # 2 + 3 * 4 should be 14, not 20 -- precedence is baked into how the
    # PARSER nests the Binary nodes (Mul binds tighter than Add), so this
    # also doubles as a check that the AST shape itself is correct.
    expr = Binary(left=NumberNode(2), operator="+", right=Binary(
        left=NumberNode(3), operator="*", right=NumberNode(4)
    ))
    run([ShowStmt(expression=expr)])
    assert capsys.readouterr().out == "14\n"


def test_division_by_zero_raises():
    expr = Binary(left=NumberNode(1), operator="/", right=NumberNode(0))
    with pytest.raises(InterpreterError, match="Division by zero"):
        run([ShowStmt(expression=expr)])


def test_invalid_operation_raises():
    expr = Binary(left=StringNode("hi"), operator="-", right=NumberNode(1))
    with pytest.raises(InterpreterError, match="Invalid operation"):
        run([ShowStmt(expression=expr)])


def test_string_concatenation_with_plus(capsys):
    expr = Binary(left=StringNode("foo"), operator="+", right=StringNode("bar"))
    run([ShowStmt(expression=expr)])
    assert capsys.readouterr().out == "foobar\n"


# ---------------------------------------------------------------------------
# Comparisons
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("op,expected", [
    ("==", False), ("!=", True), ("<", True),
    (">", False), ("<=", True), (">=", False),
])
def test_all_comparison_operators(op, expected, capsys):
    expr = Binary(left=NumberNode(3), operator=op, right=NumberNode(5))
    run([ShowStmt(expression=expr)])
    assert capsys.readouterr().out == ("true\n" if expected else "false\n")


# ---------------------------------------------------------------------------
# If / else
# ---------------------------------------------------------------------------

def test_if_true_branch(capsys):
    stmt = IfStmt(
        condition=BoolNode(True),
        then_branch=BlockStmt([ShowStmt(NumberNode(1))]),
        else_branch=BlockStmt([ShowStmt(NumberNode(0))]),
    )
    run([stmt])
    assert capsys.readouterr().out == "1\n"


def test_if_false_branch_runs_else(capsys):
    stmt = IfStmt(
        condition=BoolNode(False),
        then_branch=BlockStmt([ShowStmt(NumberNode(1))]),
        else_branch=BlockStmt([ShowStmt(NumberNode(0))]),
    )
    run([stmt])
    assert capsys.readouterr().out == "0\n"


# ---------------------------------------------------------------------------
# While loops
# ---------------------------------------------------------------------------

def test_while_loop_mutates_enclosing_scope(capsys):
    stmts = [
        AssignmentStmt(var_type="int", name="x", value=NumberNode(1)),
        WhileStmt(
            condition=Binary(left=Variable("x"), operator="<=", right=NumberNode(3)),
            body=BlockStmt([
                ShowStmt(Variable("x")),
                AssignmentStmt(
                    var_type=None, name="x",
                    value=Binary(left=Variable("x"), operator="+", right=NumberNode(1)),
                ),
            ]),
        ),
    ]
    run(stmts)
    assert capsys.readouterr().out == "1\n2\n3\n"


# ---------------------------------------------------------------------------
# Runtime errors
# ---------------------------------------------------------------------------

def test_undefined_variable_raises():
    with pytest.raises(InterpreterError, match="Undefined variable 'y'"):
        run([ShowStmt(expression=Variable("y"))])