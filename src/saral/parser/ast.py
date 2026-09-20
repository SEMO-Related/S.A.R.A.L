from dataclasses import dataclass, fields, is_dataclass

class Expr:
    pass

class Stmt:
    pass

@dataclass
class Program:
    statements: list[Stmt]

# ------------------------------- expressions --------------------------------
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
class ArrayStmt(Expr):
    elements: list[Expr]

# -------------------------------- statements --------------------------------
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
class FunctionCall(Stmt, Expr):
    name: str
    arguments: list[Argument]

# ------------------------------- tree printing -------------------------------
def _label(node) -> str:
    """Short one-line description of a node, folding in its scalar fields."""
    name = type(node).__name__

    if isinstance(node, NumberNode):
        return f"{name} {node.value}"
    if isinstance(node, StringNode):
        return f'{name} "{node.value}"'
    if isinstance(node, BoolNode):
        return f"{name} {str(node.value).lower()}"
    if isinstance(node, Variable):
        return f"{name} {node.name}"
    if isinstance(node, Binary):
        return f"{name} ({node.operator})"
    if isinstance(node, AssignmentStmt):
        declared = f"{node.var_type} " if node.var_type else ""
        return f"{name} ({declared}{node.name})"
    if isinstance(node, FunctionStmt):
        return f"{name} ({node.return_type} {node.name})"
    if isinstance(node, FunctionCall):
        return f"{name} ({node.name})"
    if isinstance(node, Parameter):
        return f"{name} ({node.param_type} {node.name})"
    return name


def _children(node) -> list[tuple[str, object]]:
    """Child nodes of `node`, each paired with the field name it came from."""
    result: list[tuple[str, object]] = []
    for field in fields(node):
        value = getattr(node, field.name)
        if is_dataclass(value):
            result.append((field.name, value))
        elif isinstance(value, list):
            # List items are identified by position, so the field name would
            # just repeat on every line.
            for item in value:
                if is_dataclass(item):
                    result.append(("", item))
    return result


def render_tree(
    node,
    prefix: str = "",
    field_name: str = "",
    is_last: bool = True,
    is_root: bool = True,
) -> str:
    """Render an AST as an indented tree.

        Program
        └── AssignmentStmt (int x)
            └── Binary (+)
                ├── NumberNode 2
                └── Binary (*)
                    ├── NumberNode 3
                    └── NumberNode 4
    """
    if is_root:
        line = _label(node)
        child_prefix = ""
    else:
        connector = "└── " if is_last else "├── "
        tag = f"{field_name}: " if field_name else ""
        line = f"{prefix}{connector}{tag}{_label(node)}"
        child_prefix = prefix + ("    " if is_last else "│   ")

    lines = [line]
    children = _children(node)
    for index, (name, child) in enumerate(children):
        lines.append(
            render_tree(
                child,
                child_prefix,
                name,
                index == len(children) - 1,
                is_root=False,
            )
        )
    return "\n".join(lines)

def print_ast(node) -> None:
    """Print an AST as a tree."""
    print(render_tree(node))
