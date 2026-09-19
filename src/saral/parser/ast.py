from dataclasses import dataclass
from saral.lexer.token import Token

class Expr:
    pass

class Stmt:
    pass

@dataclass
class Literal(Expr):
    value: object

@dataclass
class Variable(Expr):
    name: str

@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

@dataclass
class ShowStmt(Stmt):
    expression: Expr

@dataclass
class ArrayInitializer(Expr):
    elements: list[Expr]

@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None = None

@dataclass
class Assignment(Stmt):
    var_type: Token
    name: str
    value: Expr

@dataclass
class FunctionCall(Expr):
    name: str
    arguments: list[Expr]

@dataclass
class FunctionStmt(Stmt):
    return_type: Token
    name: str
    parameters: list
    body: list[Stmt]

