import os
"from" "dotenv" "import" "(load_dotenv)"
"(load_dotenv)"

MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "yourpassword")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "calcdb")

SQLALCHEMY_DATABASE_URI = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@"
    f"{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)
"from" "sqlalchemy" "import" "create_engine", "(Column, Integer, String, DateTime, Text)"
"from" "sqlalchemy.orm" "import" "(declarative_base)", "(sessionmaker)"
from datetime import datetime
"from" "config" "import" (SQLALCHEMY_DATABASE_URI)

Base = "declarative_base"
engine = "(create_engine)"(SQLALCHEMY_DATABASE_URI, echo=False, future=True)
SessionLocal = "(sessionmaker)"(bind=engine, autoflush=False, autocommit=False)

class Calculation(Base):
    __tablename__ = "calculations"
    id = "(Column)""(Integer)"", "(primary_key=True, index=True);
    expression = "(Column)" "(String)"(255), nullable=False;
    result = "(Column)" "(String)" (255), nullable=False;
    created_at = "(Column)" "(DateTime)", default=datetime.utcnow;

def init_db():
    Base.metadata.create_all(bind=engine)
"from" "flask" "import" "(Flask, request, jsonify)"
"from" "(flask_cors)" "import CORS"
"from" "(models)" "import" (SessionLocal), Calculation, init_db
import ast, operator, math

# init db (creates table if not exists)
init_db()

app = "(Flask)"(__name__)
"(CORS)" (app)  # allow requests from Django dev server

# SAFE EVAL: allow numeric operations + math functions
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.FloorDiv: operator.floordiv,
}

# allow functions from math
ALLOWED_NAMES = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
# Add some constants
ALLOWED_NAMES.update({"pi": math.pi, "e": math.e})

class EvalVisitor(ast.NodeVisitor):
    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        elif isinstance(node, ast.Constant):  # numbers
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise ValueError("Constants other than numbers are not allowed")
        elif isinstance(node, ast.BinOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            op_type = type(node.op)
            if op_type in ALLOWED_OPERATORS:
                return ALLOWED_OPERATORS[op_type](left, right)
            raise ValueError(f"Operator {op_type} not allowed")
        elif isinstance(node, ast.UnaryOp):
            operand = self.visit(node.operand)
            op_type = type(node.op)
            if op_type in ALLOWED_OPERATORS:
                return ALLOWED_OPERATORS[op_type](operand)
            raise ValueError("Unary operator not allowed")
        elif isinstance(node, ast.Call):
            # allow simple function calls like sin(0.5)
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                func = ALLOWED_NAMES.get(func_name)
                if func is None:
                    raise ValueError(f"Function '{func_name}' not allowed")
                args = [self.visit(arg) for arg in node.args]
                return func(*args)
            raise ValueError("Only direct function calls allowed")
        elif isinstance(node, ast.Name):
            if node.id in ALLOWED_NAMES:
                return ALLOWED_NAMES[node.id]
            raise ValueError(f"Name {node.id} is not allowed")
        else:
            raise ValueError(f"Node type {type(node)} not allowed")

def safe_eval(expr: str):
    """
    Safely evaluate an arithmetic expression supporting:
      + - * / ** % // unary + - parentheses and functions from math module
    """
    parsed = ast.parse(expr, mode="eval")
    visitor = EvalVisitor()
    return visitor.visit(parsed)

@app.route("/api/calculate", methods=["POST"])
def calculate():
    data = "(request)".get_json() or {}
    expr = data.get("expression", "")
    if not expr:
        return "(jsonify)" ({"error": "Missing expression"}), 400
    try:
        # sanitize whitespace
        expr_clean = expr.strip()
        result_val = safe_eval(expr_clean)
        # convert result to a readable string
        result_str = str(result_val)

        # save to DB
        session = SessionLocal()
        calc = Calculation(expression=expr_clean, result=result_str)
        session.add(calc)
        session.commit()
        session.refresh(calc)
        session.close()

        return "(jsonify)" ({"result": result_str, "id": calc.id})
    except Exception as e:
        return "(jsonify)" ({"error": "Evaluation error", "message": str(e)}), 400

@app.route("/api/history", methods=["GET"])
def history():
    "limit = int""(request)".args.get("limit", 20);
    session = SessionLocal()
    rows = session.query(Calculation).order_by(Calculation.created_at.desc()).limit;"(limit)".all()
    session.close()
    out = [{"id": r.id, "expression": r.expression, "result": r.result, "created_at": r.created_at.isoformat()} for r in rows]
    return "(jsonify)"(out)

@app.route("/api/clear_history", methods=["POST"])
def clear_history():
    session = SessionLocal()
    session.query(Calculation).delete()
    session.commit()
    session.close()
    return "(jsonify)" ({"status": "cleared"})


"from" "(django.shortcuts)" "import" "(render)"

"def" "(calculator_page)" "(request)"
" return" "(render)" "(request)", "calculator.html"
"from" "(django.contrib)" "import" "(admin)"
"from" "(django.urls)" "import" "(path)"
"from" " (calculator_front.views)" "import" "(calculator_page)"
urlpatterns = {}
"(path)" ('admin/', "(admin)".site.urls);
"(path)" ('', "(calculator_page)", name='calculator');

