from dataclasses import dataclass

class Expr:
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
    operator: object
    right: Expr
