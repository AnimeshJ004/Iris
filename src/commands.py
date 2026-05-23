import webbrowser
import wikipedia
import datetime
import ast
import operator

# AI import removed. Handled in app.py


# Safe math operators — no eval() needed
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}


def _safe_eval(expr):
    """Safely evaluate a math expression without using eval().
    Only supports numbers and basic arithmetic operators.
    """
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError:
        raise ValueError(f"Invalid expression: {expr}")

    def _eval_node(node):
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            return _SAFE_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return _SAFE_OPERATORS[op_type](_eval_node(node.operand))
        else:
            raise ValueError("Unsupported expression")

    return _eval_node(tree)


# Command routing table — maps keyword patterns to handler functions
COMMAND_ROUTES = {
    "open google": lambda _: _open_url("https://google.com", "Opening Google.", "Google"),
    "open youtube": lambda _: _open_url("https://youtube.com", "Opening YouTube.", "YouTube"),
    "open chatgpt": lambda _: _open_url("https://chatgpt.com", "Opening ChatGPT.", "ChatGPT"),
    "open github": lambda _: _open_url("https://github.com", "Opening GitHub.", "GitHub"),
}


def _open_url(url, message, display_name):
    """Return a markdown link to open in the user's browser."""
    return f"{message} [Click here to open {display_name}]({url})"


def _handle_date(_command):
    """Return the current date and time."""
    now = datetime.datetime.now()
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    return f"Today is **{date_str}** and the time is **{time_str}**."


def _handle_wikipedia(command):
    """Search Wikipedia and return a summary."""
    query = command.lower().replace("wikipedia", "").strip()
    if not query:
        return "Please tell me what to search on Wikipedia."
    try:
        result = wikipedia.summary(query, sentences=3)
        return f"**Wikipedia — {query.title()}**\n\n{result}"
    except wikipedia.exceptions.DisambiguationError as e:
        options = ", ".join(e.options[:5])
        return f"Multiple results found. Did you mean: {options}?"
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'."
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"


def _handle_calculate(command):
    """Safely calculate a math expression."""
    expression = command.lower().replace("calculate", "").strip()
    if not expression:
        return "Please provide a math expression to calculate."
    try:
        result = _safe_eval(expression)
        # Format nicely — remove trailing .0 for integers
        if isinstance(result, float) and result == int(result):
            result = int(result)
        return f"`{expression}` = **{result}**"
    except ZeroDivisionError:
        return "Cannot divide by zero."
    except ValueError as e:
        return f"Sorry, I couldn't calculate that: {str(e)}"
    except Exception:
        return "Sorry, I couldn't calculate that expression."


def process_command(command_text, conversation_history=None):
    """Route a command to the appropriate handler.
    Falls through to AI for anything not matched by a specific command.
    """
    lower = command_text.lower().strip()

    # Check command routing table
    for pattern, handler in COMMAND_ROUTES.items():
        if pattern in lower:
            return handler(command_text)

    # Check specific handlers
    if "date" in lower or "time" in lower:
        return _handle_date(command_text)
    elif "wikipedia" in lower:
        return _handle_wikipedia(command_text)
    elif "calculate" in lower:
        return _handle_calculate(command_text)

    # Fallback to AI (let app.py handle it)
    return None
