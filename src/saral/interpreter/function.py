from __future__ import annotations

from ..parser.ast import FunctionStmt
from .env import Environment

class ReturnSignal(Exception):
    """A signal to indicate that a return statement has been executed in a function."""

    def __init__(self, value: Any):
        self.value = value

class SaralFunction:
    """A Callable, user-defined function.

    Wraps the FunctionStmt AST node plus the environment that was active at this point
    the function was defined.
    """

    def __init__(self, declaration: FunctionStmt, closure: Environment):
        self.declaration = declaration
        self.closure = closure
    
    @property
    def name(self) -> str:
        return self.declaration.name

    @property
    def arity(self) -> int:
        return len(self.declaration.parameters)

    def call(self, interpreter: Interpreter, arguments: list[Any]) -> Any:
        env = Environment(enclosing=self.closure)
        for param, arg_value in zip(self.declaration.parameters, arguments):
            env.define(param.name, arg_value)

        try:
            interpreter.execute_block(self.declaration.body.statements, env)
        except ReturnSignal as return_signal:
            return return_signal.value
        return None
    
    def __repr__(self) -> str:
        return f"<function {self.name}>"