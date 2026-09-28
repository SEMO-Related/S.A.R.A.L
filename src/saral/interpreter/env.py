from __future__ import annotations

from typing import Any

from ..error import InterpreterError

class Environment:
    """A symbol table mapping variable names to runtime values."""

    def __init__(self, enclosing: "Environment | None" = None):
        self.enclosing = enclosing
        self.values: dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.enclosing is not None:
            return self.enclosing.get(name)
        raise InterpreterError(f"Undefined variable '{name}'")

    def assign(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
        raise InterpreterError(
            f"Undefined variable '{name}' (cannot assign to a variable that "
            f"was never declared)"
        )