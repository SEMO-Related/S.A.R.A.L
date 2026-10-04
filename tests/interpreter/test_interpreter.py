import pytest

from saral.error import InterpreterError
from saral.interpreter.env import Environment
from saral.interpreter.interpreter import Interpreter
from saral.parser.ast import (
    Argument,
    ArrayStmt,
    AssignmentStmt,
    Binary,
    BlockStmt,
    BoolNode,
    FunctionCall,
    FunctionStmt,
    IfStmt,
    Index,
    NumberNode,
    Parameter,
    Program,
    ReturnStmt,
    ShowStmt,
    StringNode,
    Variable,
    WhileStmt,
)


def run(statements, interp: Interpreter | None = None) -> Interpreter:
    interp = interp or Interpreter()
    interp.interpret(Program(statements=statements))
    return interp


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


def test_arithmetic_precedence(capsys):
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


@pytest.mark.parametrize("op,expected", [
    ("==", False), ("!=", True), ("<", True),
    (">", False), ("<=", True), (">=", False),
])
def test_all_comparison_operators(op, expected, capsys):
    expr = Binary(left=NumberNode(3), operator=op, right=NumberNode(5))
    run([ShowStmt(expression=expr)])
    assert capsys.readouterr().out == ("true\n" if expected else "false\n")


def test_if_true_branch(capsys):
    stmt = IfStmt(
        condition=BoolNode(True),
        then_branch=BlockStmt([ShowStmt(NumberNode(1))]),
        else_branch=BlockStmt([ShowStmt(NumberNode(0))]),
    )
    run([stmt])
    assert capsys.readouterr().out == "1\n"


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


def test_function_call_and_return(capsys):
    add_fn = FunctionStmt(
        return_type="int", name="add",
        parameters=[Parameter("int", "a"), Parameter("int", "b")],
        body=BlockStmt([
            ReturnStmt(value=Binary(left=Variable("a"), operator="+", right=Variable("b")))
        ]),
    )
    call = FunctionCall(name="add", arguments=[Argument(NumberNode(2)), Argument(NumberNode(3))])
    run([add_fn, ShowStmt(expression=call)])
    assert capsys.readouterr().out == "5\n"


def test_array_literal_matching_declared_element_type_is_allowed(capsys):
    # `int arr = [1, 2, 3];` -- the grammar has no separate "array of T"
    # type keyword, so "int" here means "array of int", not "arr must be
    # a scalar int". This used to incorrectly raise a Type mismatch.
    stmts = [
        AssignmentStmt(
            var_type="int", name="arr",
            value=ArrayStmt([NumberNode(1), NumberNode(2), NumberNode(3)]),
        ),
        ShowStmt(expression=Variable("arr")),
    ]
    run(stmts)
    assert capsys.readouterr().out == "[1, 2, 3]\n"


def test_array_literal_with_mismatched_element_type_still_raises():
    stmts = [
        AssignmentStmt(
            var_type="int", name="arr",
            value=ArrayStmt([NumberNode(1), StringNode("two"), NumberNode(3)]),
        ),
    ]
    with pytest.raises(InterpreterError, match="element 1 of array 'arr'"):
        run(stmts)


def test_array_index_read(capsys):
    stmts = [
        AssignmentStmt(
            var_type="int", name="arr",
            value=ArrayStmt([NumberNode(1), NumberNode(2), NumberNode(3)]),
        ),
        ShowStmt(expression=Index(array=Variable("arr"), index=NumberNode(1))),
    ]
    run(stmts)
    assert capsys.readouterr().out == "2\n"


def test_array_index_out_of_bounds_raises():
    stmts = [
        AssignmentStmt(var_type="int", name="arr", value=ArrayStmt([NumberNode(1)])),
        ShowStmt(expression=Index(array=Variable("arr"), index=NumberNode(5))),
    ]
    with pytest.raises(InterpreterError, match="Index out of bounds"):
        run(stmts)


def test_indexing_a_non_array_raises():
    stmts = [
        AssignmentStmt(var_type="int", name="x", value=NumberNode(5)),
        ShowStmt(expression=Index(array=Variable("x"), index=NumberNode(0))),
    ]
    with pytest.raises(InterpreterError, match="cannot index into int"):
        run(stmts)


def test_nested_array_index(capsys):
    stmts = [
        AssignmentStmt(
            var_type="int", name="grid",
            value=ArrayStmt([
                ArrayStmt([NumberNode(1), NumberNode(2)]),
                ArrayStmt([NumberNode(3), NumberNode(4)]),
            ]),
        ),
        ShowStmt(expression=Index(
            array=Index(array=Variable("grid"), index=NumberNode(1)),
            index=NumberNode(0),
        )),
    ]
    run(stmts)
    assert capsys.readouterr().out == "3\n"


def test_undefined_variable_raises():
    with pytest.raises(InterpreterError, match="Undefined variable 'y'"):
        run([ShowStmt(expression=Variable("y"))])