from dataclasses import dataclass, fields, is_dataclass
from saral.lexer.token import Token
from saral.lexer.token_type import TokenType

def print_ast(node, indent=0):
    prefix =(" " * indent) + ("|- " if indent > 1 else "")

    if isinstance(node, list):
        for item in node:
            print_ast(item, indent)
        return

    if is_dataclass(node):
        print(f"{prefix}{type(node).__name__}")

        for field in fields(node):
            value = getattr(node, field.name)

            if is_dataclass(value) or isinstance(value, list):
                print(f"{prefix}{field.name}:")
                print_ast(value, indent + 3)
            else:
                print(f"{prefix}{field.name}:  {value}")

        return

    print(f"{prefix}{node}")

class Expr:
    pass

class Stmt:
    pass

@dataclass
class Program:
    statements: list[Stmt]

@dataclass
class NumberNode(Expr):
    value: int | float

@dataclass
class StringNode(Expr):
    value: str

@dataclass
class BoolNode(Expr):
    value: bool

@dataclass
class Variable(Expr):
    name: str

@dataclass
class Binary(Expr):
    left: Expr
    operator: str
    right: Expr

@dataclass
class Parameter:
    param_type: str
    name: str

@dataclass
class Argument:
    value: Expr

@dataclass
class BlockStmt(Stmt):
    statements: list[Stmt]

@dataclass
class AssignmentStmt(Stmt):
    var_type: str | None
    name: str
    value: Expr

@dataclass
class ShowStmt(Stmt):
    expression: Expr

@dataclass
class ReturnStmt(Stmt):
    value: Expr | None = None

@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: BlockStmt 
    else_branch: BlockStmt | None = None

@dataclass
class WhileStmt(Stmt):
    condition: Expr
    body: BlockStmt


@dataclass
class FunctionStmt(Stmt):
    return_type: str
    name: str
    parameters: list[Parameter]
    body: BlockStmt

@dataclass
class FunctionCall(Stmt):
    name: str
    arguments: list[Argument]

@dataclass
class ArrayStmt(Expr):
    elements: list[Expr]

