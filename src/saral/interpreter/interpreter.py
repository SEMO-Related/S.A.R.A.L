from __future__ import annotations

from typing import Any
from ..error import InterpreterError
from ..parser.ast import (
    ArrayStmt,
    AssignmentStmt,
    Binary,
    BlockStmt,
    BoolNode,
    Expr,
    FunctionCall,
    FunctionStmt,
    IfStmt,
    Index,
    NumberNode,
    Program,
    ReturnStmt,
    ShowStmt,
    Stmt,
    StringNode,
    Variable,
    WhileStmt,
)
from .env import Environment
from .function import ReturnSignal, SaralFunction

_NUMERIC = (int, float)

_TYPE_CHECKS = {
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: isinstance(v, float) or (isinstance(v, int) and not isinstance(v, bool)),
    "string": lambda v: isinstance(v, str),
    "bool": lambda v: isinstance(v, bool),
}


class Interpreter:
    """Tree-walking interpreter: executes a Program by recursively
    dispatching on each AST node's Python type.
    """

    def __init__(self):
        self.globals = Environment()
        self.environment = self.globals

    def interpret(self, program: Program) -> None:
        for stmt in program.statements:
            self.execute(stmt)

    def execute(self, stmt: Stmt) -> None:
        handler = getattr(self, f"exec_{type(stmt).__name__}", None)
        if handler is None:
            raise InterpreterError(f"No execution rule for statement '{type(stmt).__name__}'")
        handler(stmt)

    def execute_block(self, statements: list[Stmt], env: Environment) -> None:
        previous = self.environment
        self.environment = env
        try:
            for stmt in statements:
                self.execute(stmt)
        finally:
            self.environment = previous

    def exec_AssignmentStmt(self, stmt: AssignmentStmt) -> None:
        value = self.evaluate(stmt.value)
        if stmt.var_type is not None:
            self._check_declared_type(stmt.var_type, value, stmt.name)
            self.environment.define(stmt.name, value)
        else:
            self.environment.assign(stmt.name, value)

    def exec_IndexAssignment(self, stmt: IndexAssignment) -> None:
        value = self.evaluate(stmt.value)
        array = self.evaluate(stmt.target.array)
        index = self.evaluate(stmt.target.index)

        if not isinstance(array, list):
            raise InterpreterError(
                f"Invalid operation: cannot index into {self._type_name(array)}"
            )
        if not (isinstance(index, int) and not isinstance(index, bool)):
            raise InterpreterError(
                f"Invalid operation: array index must be an int, got "
                f"{self._type_name(index)}"
            )
        if index < 0 or index >= len(array):
            raise InterpreterError(
                f"Index out of bounds: index {index} for array of length {len(array)}"
            )
        array[index] = value

    def _check_declared_type(self, var_type: str, value: Any, name: str) -> None:
        check = _TYPE_CHECKS.get(var_type)
        if check is None:
            return

        if isinstance(value, list):
            for i, element in enumerate(value):
                if isinstance(element, list):
                    self._check_declared_type(var_type, element, f"{name}[{i}]")
                elif not check(element):
                    raise InterpreterError(
                        f"Type mismatch: element {i} of array '{name}' is "
                        f"{self._type_name(element)}, expected '{var_type}'"
                    )
            return

        if not check(value):
            raise InterpreterError(
                f"Type mismatch: cannot assign {self._type_name(value)} value "
                f"to '{var_type}' variable '{name}'"
            )

    def exec_ShowStmt(self, stmt: ShowStmt) -> None:
        print(self._stringify(self.evaluate(stmt.expression)))

    def exec_IfStmt(self, stmt: IfStmt) -> None:
        if self._is_truthy(self.evaluate(stmt.condition)):
            self.execute_block(stmt.then_branch.statements, self.environment)
        elif stmt.else_branch is not None:
            self.execute_block(stmt.else_branch.statements, self.environment)

    def exec_WhileStmt(self, stmt: WhileStmt) -> None:
        while self._is_truthy(self.evaluate(stmt.condition)):
            self.execute_block(stmt.body.statements, self.environment)

    def exec_BlockStmt(self, stmt: BlockStmt) -> None:
        self.execute_block(stmt.statements, self.environment)

    def exec_FunctionStmt(self, stmt: FunctionStmt) -> None:
        self.environment.define(stmt.name, SaralFunction(stmt, self.environment))

    def exec_ReturnStmt(self, stmt: ReturnStmt) -> None:
        value = self.evaluate(stmt.value) if stmt.value is not None else None
        raise ReturnSignal(value)

    def exec_FunctionCall(self, stmt: FunctionCall) -> None:
        self.evaluate(stmt)

    def evaluate(self, expr: Expr) -> Any:
        handler = getattr(self, f"eval_{type(expr).__name__}", None)
        if handler is None:
            raise InterpreterError(f"No evaluation rule for expression '{type(expr).__name__}'")
        return handler(expr)

    def eval_NumberNode(self, expr: NumberNode) -> Any:
        return expr.value

    def eval_StringNode(self, expr: StringNode) -> Any:
        return expr.value

    def eval_BoolNode(self, expr: BoolNode) -> Any:
        return expr.value

    def eval_Variable(self, expr: Variable) -> Any:
        return self.environment.get(expr.name)

    def eval_ArrayStmt(self, expr: ArrayStmt) -> Any:
        return [self.evaluate(el) for el in expr.elements]

    def eval_Index(self, expr: Index) -> Any:
        array = self.evaluate(expr.array)
        index = self.evaluate(expr.index)

        if not isinstance(array, list):
            raise InterpreterError(
                f"Invalid operation: cannot index into {self._type_name(array)}"
            )
        if not (isinstance(index, int) and not isinstance(index, bool)):
            raise InterpreterError(
                f"Invalid operation: array index must be an int, got "
                f"{self._type_name(index)}"
            )
        if index < 0 or index >= len(array):
            raise InterpreterError(
                f"Index out of bounds: index {index} for array of length {len(array)}"
            )
        return array[index]

    def eval_Binary(self, expr: Binary) -> Any:
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        return self._apply_operator(expr.operator, left, right)

    def eval_FunctionCall(self, expr: FunctionCall) -> Any:
        callee = self.environment.get(expr.name)
        if not isinstance(callee, SaralFunction):
            raise InterpreterError(f"'{expr.name}' is not a function")

        args = [self.evaluate(arg.value) for arg in expr.arguments]
        if len(args) != callee.arity:
            raise InterpreterError(
                f"Function '{expr.name}' expects {callee.arity} argument(s) "
                f"but got {len(args)}"
            )
        return callee.call(self, args)

    def _apply_operator(self, op: str, left: Any, right: Any) -> Any:
        if op == "+":
            if isinstance(left, _NUMERIC) and isinstance(right, _NUMERIC) \
                    and not isinstance(left, bool) and not isinstance(right, bool):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            raise InterpreterError(
                f"Invalid operation: cannot apply '+' to "
                f"{self._type_name(left)} and {self._type_name(right)}"
            )

        if op in ("-", "*", "/", "%"):
            if not self._both_numeric(left, right):
                raise InterpreterError(
                    f"Invalid operation: cannot apply '{op}' to "
                    f"{self._type_name(left)} and {self._type_name(right)}"
                )
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise InterpreterError("Division by zero")
                return left / right
            if op == "%":
                if right == 0:
                    raise InterpreterError("Division by zero (modulo)")
                return left % right

        if op == "==":
            return left == right
        if op == "!=":
            return left != right

        if op in ("<", ">", "<=", ">="):
            if not self._both_numeric(left, right):
                raise InterpreterError(
                    f"Invalid operation: cannot compare "
                    f"{self._type_name(left)} and {self._type_name(right)} with '{op}'"
                )
            if op == "<":
                return left < right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == ">=":
                return left >= right

        raise InterpreterError(f"Unknown operator '{op}'")

    @staticmethod
    def _both_numeric(left: Any, right: Any) -> bool:
        return (
            isinstance(left, _NUMERIC) and not isinstance(left, bool)
            and isinstance(right, _NUMERIC) and not isinstance(right, bool)
        )

    @staticmethod
    def _is_truthy(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, _NUMERIC):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        return True

    @staticmethod
    def _type_name(value: Any) -> str:
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "array"
        if isinstance(value, SaralFunction):
            return "function"
        if value is None:
            return "null"
        return type(value).__name__

    @classmethod
    def _stringify(cls, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        if isinstance(value, list):
            return "[" + ", ".join(cls._stringify(v) for v in value) + "]"
        return str(value)