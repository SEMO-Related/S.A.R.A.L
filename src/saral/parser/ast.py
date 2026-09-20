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


_GAP = 3

def _layout(node, field_name: str = "") -> tuple[list[str], int]:
    """Lay out the subtree rooted at `node` as a block of equal-width lines.

    Returns (lines, anchor), where `anchor` is the column of the node's
    label centre, so the parent knows where to attach its connector.
    """
    label = f"{field_name}: {_label(node)}" if field_name else _label(node)
    kids = [_layout(child, name) for name, child in _children(node)]

    if not kids:
        return [label], len(label) // 2

    # 1. Place the child blocks side by side and remember each anchor column.
    anchors: list[int] = []
    x = 0
    for block, anchor in kids:
        anchors.append(x + anchor)
        x += len(block[0]) + _GAP
    span = x - _GAP

    height = max(len(block) for block, _ in kids)
    body: list[str] = []
    for row in range(height):
        cells = [
            block[row] if row < len(block) else " " * len(block[0])
            for block, _ in kids
        ]
        body.append((" " * _GAP).join(cells))

    # 2. Draw the connector row between this node and its children.
    centre = (anchors[0] + anchors[-1]) // 2
    bar = [" "] * span
    if len(anchors) == 1:
        bar[centre] = "│"
    else:
        for i in range(anchors[0], anchors[-1] + 1):
            bar[i] = "─"
        for a in anchors:
            bar[a] = "┬"
        bar[anchors[0]] = "┌"
        bar[anchors[-1]] = "┐"
        bar[centre] = "┼" if centre in anchors else "┴"

    # 3. Centre this node's label above the connector. If the label sticks
    #    out past the left edge, shift everything right to make room.
    start = centre - len(label) // 2
    shift = max(0, -start)
    start += shift
    width = max(span + shift, start + len(label))

    rows = [
        " " * start + label,
        " " * shift + "".join(bar),
        *(" " * shift + line for line in body),
    ]
    return [row.ljust(width) for row in rows], centre + shift


def render_tree(node) -> str:
    """Render an AST as a top-down tree.
                    Program
                       │
            AssignmentStmt (int x)
                       │
               value: Binary (+)
             ┌─────────┴──────────┐
    left: NumberNode 2   right: NumberNode 3
    """
    lines, _ = _layout(node)
    return "\n".join(line.rstrip() for line in lines)


def print_ast(node) -> None:
    """Print an AST as a tree."""
    print(render_tree(node))
