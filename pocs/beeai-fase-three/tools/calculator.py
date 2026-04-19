import ast
import operator

CALCULATOR_TOOL_SCHEMA = {
    "name": "calculate",
    "description": "Evaluate a mathematical expression safely. Supports +, -, *, /, **, and parentheses.",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A mathematical expression, e.g. '(2 + 3) * 4'",
            }
        },
        "required": ["expression"],
    },
}

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")
    if isinstance(node, ast.BinOp):
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Operator {type(node.op).__name__} is not allowed")
        return op(_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Operator {type(node.op).__name__} is not allowed")
        return op(_safe_eval(node.operand))
    raise ValueError(f"Unsupported node type: {type(node).__name__}")


def calculate(expression: str) -> dict:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree.body)
        return {"ok": True, "data": {"expression": expression, "result": result}, "error": None}
    except ZeroDivisionError:
        return {"ok": False, "data": None, "error": "Division by zero"}
    except (ValueError, TypeError) as e:
        return {"ok": False, "data": None, "error": str(e)}
    except SyntaxError:
        return {"ok": False, "data": None, "error": "Invalid expression syntax"}
