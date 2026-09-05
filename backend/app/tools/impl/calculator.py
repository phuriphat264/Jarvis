import ast
import operator
from typing import Dict, Any
from app.interfaces.tool import BaseTool, ToolExecutionContext, ToolExecutionResult

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform safe mathematical calculations using +, -, *, /, **, ()"
    category = "utility"
    permission_level = "read"
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate, e.g. '25 * 8' or '(10 + 5) / 3'"
                }
            },
            "required": ["expression"]
        }
        
    async def execute(self, context: ToolExecutionContext, arguments: Dict[str, Any]) -> ToolExecutionResult:
        expression = arguments.get("expression")
        if not expression:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "INVALID_ARGUMENT", "message": "Missing expression"})
            
        try:
            result = self._safe_eval(expression)
            return ToolExecutionResult(success=True, tool_name=self.name, data={"result": result})
        except Exception as e:
            return ToolExecutionResult(success=False, tool_name=self.name, error={"code": "EVAL_ERROR", "message": str(e)})

    def _safe_eval(self, expr: str) -> float:
        # Define allowed operators
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos
        }
        
        def _eval(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    return node.value
                raise TypeError("Unsupported constant")
            elif isinstance(node, ast.BinOp):
                op = type(node.op)
                if op not in operators:
                    raise TypeError(f"Unsupported operator: {op}")
                # Prevent massive power operations
                if op == ast.Pow:
                    left = _eval(node.left)
                    right = _eval(node.right)
                    if right > 100 or right < -100:
                        raise ValueError("Power too large")
                    return operators[op](left, right)
                return operators[op](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.UnaryOp):
                op = type(node.op)
                if op not in operators:
                    raise TypeError(f"Unsupported operator: {op}")
                return operators[op](_eval(node.operand))
            elif isinstance(node, ast.Expression):
                return _eval(node.body)
            else:
                raise TypeError(f"Unsupported AST node: {type(node)}")
                
        tree = ast.parse(expr, mode='eval')
        return _eval(tree.body)
