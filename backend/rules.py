"""Three-state AND/OR requirement evaluation for machine-readable use templates."""


def evaluate(expression, checks):
    if "check" in expression:
        return checks[expression["check"]]["status"]
    op = expression.get("op")
    children = expression.get("children", [])
    if op not in ("AND", "OR") or not children:
        raise ValueError("Expected nonempty AND/OR expression")
    states = [evaluate(c, checks) for c in children]
    if op == "AND":
        return (
            "FAIL" if "FAIL" in states else "UNKNOWN" if "UNKNOWN" in states else "PASS"
        )
    return "PASS" if "PASS" in states else "UNKNOWN" if "UNKNOWN" in states else "FAIL"


def all_checks(checks):
    expression = {"op": "AND", "children": [{"check": i} for i in range(len(checks))]}
    return evaluate(expression, checks), expression
