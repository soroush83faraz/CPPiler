"""Headless/browser entry point for the CPPiler pipeline.

This module reuses the repository's existing modules unchanged and exposes a
single helper, run_pipeline(code) -> dict, that runs the whole pipeline on a
source string and captures each stage's output as text.  It is what the
in-browser playground (docs/index.html, via Pyodide) calls, and it also works
from a normal Python interpreter:

    python web_pipeline.py path/to/code.cpp
    python -c "import web_pipeline, json; print(json.dumps(web_pipeline.run_pipeline(open('f.cpp').read()), indent=2))"

Two import-time shims make the existing modules loadable anywhere:

* ``tabulate``  – if the real package is not installed (e.g. inside Pyodide
  without micropip), a minimal plain-text "grid" implementation is registered
  so ParseTable.save_to_file works without any network dependency.
* ``graphviz``  – PNG rendering cannot work in the browser, so a stub is
  registered when graphviz is missing.  ParseTree.visualize() is simply never
  called here; the tree is rendered as text instead.
"""

import io
import json
import sys
import types
from contextlib import redirect_stdout

# --------------------------------------------------------------------------
# Shim 1: tabulate fallback (plain-text "grid" tables, no network needed)
# --------------------------------------------------------------------------
try:
    import tabulate as _tabulate_mod  # noqa: F401  (real package, if present)
except ImportError:
    def _grid_tabulate(rows, headers=(), tablefmt="grid"):
        table = []
        if headers:
            table.append([str(h) for h in headers])
        table.extend([str(c) for c in row] for row in rows)
        if not table:
            return ""
        ncols = max(len(r) for r in table)
        for r in table:
            r.extend("" for _ in range(ncols - len(r)))
        widths = [max(len(r[i]) for r in table) for i in range(ncols)]

        def sep(ch):
            return "+" + "+".join(ch * (w + 2) for w in widths) + "+"

        def fmt(row):
            return "| " + " | ".join(c.ljust(w) for c, w in zip(row, widths)) + " |"

        lines = [sep("-")]
        body = table
        if headers:
            lines.append(fmt(table[0]))
            lines.append(sep("="))
            body = table[1:]
        for row in body:
            lines.append(fmt(row))
            lines.append(sep("-"))
        return "\n".join(lines)

    _mod = types.ModuleType("tabulate")
    _mod.tabulate = _grid_tabulate
    sys.modules["tabulate"] = _mod

# --------------------------------------------------------------------------
# Shim 2: graphviz stub (PNG rendering is skipped outside the desktop)
# --------------------------------------------------------------------------
try:
    import graphviz as _graphviz_mod  # noqa: F401
except ImportError:
    class _StubDigraph:
        def __init__(self, *args, **kwargs):
            pass

        def node(self, *args, **kwargs):
            pass

        def edge(self, *args, **kwargs):
            pass

        def render(self, *args, **kwargs):
            raise RuntimeError("graphviz rendering is not available in this environment")

    _gv = types.ModuleType("graphviz")
    _gv.Digraph = _StubDigraph
    sys.modules["graphviz"] = _gv

# --------------------------------------------------------------------------
# The repository's actual modules (unchanged)
# --------------------------------------------------------------------------
from LexicalAnalyzer import LexicalAnalyzer
from TokenTable import TokenTable
from ParseTable import CFG, ParseTable
from NonRecursivePredictiveParser import NonRecursivePredictiveParser
from ParseTree import ParseTree
from SearchInTree import SearchInTree
from tabulate import tabulate

# Same constants as main.py
SPECIFIED_ORDER = ['Start', 'S', 'N', 'M', 'T', 'V', 'Id', 'L', 'Z', 'Operation',
                   'P', 'O', 'W', 'Assign', 'Expression', 'K', 'Loop', 'Input',
                   'F', 'Output', 'H', 'C']
TERMINALS = ['#include', 'using', 'namespace', 'std', ';', 'int', 'main', '(', ')',
             '{', '}', 'return', 'number', 'float', 'identifier', ',', '+', '-',
             '*', '=', '==', '>=', '<=', '!=', 'while', 'cin', '>>', 'cout', '<<',
             'string', '$']
TREE_SYMBOLS = SPECIFIED_ORDER + ["identifier", "string", "number"]

PARSE_TABLE_FILE = "generated_parse_table.txt"
PRODUCTIONS_FILE = "productions_used.txt"


def _render_tree_text(root):
    """Plain-text rendering of the ParseTree (replaces the graphviz PNG)."""
    lines = [str(root.value)]

    def walk(node, prefix):
        for i, child in enumerate(node.children):
            last = i == len(node.children) - 1
            lines.append(prefix + ("└── " if last else "├── ") + str(child.value))
            walk(child, prefix + ("    " if last else "│   "))

    walk(root, "")
    return "\n".join(lines)


def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def run_pipeline(code):
    """Run the full CPPiler pipeline on ``code`` and capture every stage.

    Returns a dict of plain strings/lists (JSON-serialisable):
        ok            bool  – True when the whole pipeline succeeded
        errors        list  – lexical / syntax error messages (empty when ok)
        log           str   – the status lines main.py prints
        tokens        str   – token stream from LexicalAnalyzer
        token_table   str   – exactly what TokenTable.display() prints
        first_follow  str   – FIRST/FOLLOW sets of the CFG (grid table)
        parse_table   str   – contents of generated_parse_table.txt
        derivation    str   – leftmost derivation (productions used, in order)
        tree          str   – text rendering of the parse tree
        declarations  str   – SearchInTree.find_declaration for each identifier
    """
    result = {
        "ok": False,
        "errors": [],
        "log": "",
        "tokens": "",
        "token_table": "",
        "first_follow": "",
        "parse_table": "",
        "derivation": "",
        "tree": "",
        "declarations": "",
    }
    log_lines = []

    # ---- Lexical analysis -------------------------------------------------
    try:
        analyzer = LexicalAnalyzer(code)
    except ValueError as exc:
        result["errors"].append(f"Lexical error: {exc}")
        result["log"] = "Pipeline stopped during lexical analysis."
        return result

    if analyzer.semicolon_errors:
        result["errors"].append(
            "missing semicolon, line: " + ", ".join(map(str, analyzer.semicolon_errors)))
    result["errors"].extend(analyzer.wrong_allocations)

    tokens = analyzer.tokens
    result["tokens"] = "\n".join(repr(t) for t in tokens)

    if result["errors"]:
        # main.py exit()s here; we stop the pipeline the same way.
        result["log"] = "Pipeline stopped: lexical errors found (main.py exits here)."
        return result
    log_lines.append("No errors found!")

    # ---- Token table ------------------------------------------------------
    token_table = TokenTable(tokens)
    buf = io.StringIO()
    with redirect_stdout(buf):
        token_table.display()
    result["token_table"] = buf.getvalue().strip()

    # ---- CFG, FIRST/FOLLOW and parse table --------------------------------
    cfg = CFG()
    parse_table_generator = ParseTable(cfg)
    parse_table = parse_table_generator.construct_parse_table()

    ff_rows = [[nt,
                ", ".join(sorted(cfg.first.get(nt, set()))),
                ", ".join(sorted(cfg.follow.get(nt, set())))]
               for nt in SPECIFIED_ORDER]
    result["first_follow"] = tabulate(ff_rows,
                                      headers=["Non-terminal", "FIRST", "FOLLOW"],
                                      tablefmt="grid")

    buf = io.StringIO()
    with redirect_stdout(buf):
        parse_table_generator.save_to_file(PARSE_TABLE_FILE, SPECIFIED_ORDER, TERMINALS)
    log_lines.append(buf.getvalue().strip())
    result["parse_table"] = _read_file(PARSE_TABLE_FILE)

    # ---- Non-recursive predictive parsing ---------------------------------
    parser = NonRecursivePredictiveParser(parse_table, "Start")
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            productions_used = parser.parse(tokens, output_file=PRODUCTIONS_FILE)
        log_lines.append(buf.getvalue().strip())
    except ValueError as exc:
        result["errors"].append(f"Syntax error: {exc}")
        partial = _read_file(PRODUCTIONS_FILE).strip()
        if partial:
            result["derivation"] = ("(partial derivation before the error)\n\n" + partial)
        result["log"] = "\n".join(log_lines + ["Pipeline stopped during parsing."])
        return result

    result["derivation"] = "\n".join(
        f"{i:>4}. {p}" for i, p in enumerate(productions_used, 1))

    # ---- Parse tree (text rendering; graphviz PNG stage is skipped) -------
    parse_tree = ParseTree("Start")
    parse_tree.build_from_productions(productions_used, TREE_SYMBOLS)
    result["tree"] = _render_tree_text(parse_tree.root)

    # ---- Declaration search (main.py hardcodes "x"; we try every identifier)
    search_in_tree = SearchInTree(parse_tree.root, TREE_SYMBOLS)
    seen = []
    for token_type, value in tokens:
        if token_type == "identifier" and value not in seen:
            seen.append(value)
    decl_lines = []
    for identifier in seen:
        declaration = search_in_tree.find_declaration(identifier)
        if declaration:
            decl_lines.append(declaration)
        else:
            decl_lines.append(f"Identifier '{identifier}' not found in the parse tree.")
    result["declarations"] = "\n".join(decl_lines) if decl_lines else "No identifiers in the input."

    result["log"] = "\n".join(line for line in log_lines if line)
    result["ok"] = True
    return result


def run_pipeline_json(code):
    """JSON string wrapper around run_pipeline (used by the web playground)."""
    return json.dumps(run_pipeline(code))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            source = f.read()
    else:
        source = sys.stdin.read()
    print(json.dumps(run_pipeline(source), indent=2, ensure_ascii=False))
