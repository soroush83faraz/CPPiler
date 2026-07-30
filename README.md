# CPPiler

A compiler front-end for a small subset of C++, written in Python. It tokenizes a C++ program, checks it against an LL(1) grammar using a non-recursive predictive parser, builds a parse tree, and renders the tree as an image with Graphviz.

## Pipeline

1. **Lexical analysis** (`LexicalAnalyzer.py`) — regex-based tokenizer that classifies input into reserved words, identifiers, numbers, strings, and symbols. It also performs two lightweight checks before parsing: missing-semicolon detection (with line numbers) and simple type-mismatch detection on assignments (e.g. assigning a float or string literal to an `int` variable).
2. **Token table** (`TokenTable.py`) — hashes the collected tokens into a small hash table and prints it.
3. **Grammar and parse table** (`ParseTable.py`) — defines the LL(1) context-free grammar for the C++ subset, computes FIRST and FOLLOW sets, constructs the predictive parse table, and saves it as a formatted table (`generated_parse_table.txt`).
4. **Parsing** (`NonRecursivePredictiveParser.py`) — stack-based (non-recursive) predictive parser driven by the parse table. Records every production used to `productions_used.txt`.
5. **Parse tree** (`ParseTree.py`) — rebuilds the derivation as a tree from the recorded productions and renders it to `parse_tree.png` via Graphviz.
6. **Tree search** (`SearchInTree.py`) — walks the parse tree to find the declaration of a given identifier and reconstructs it (e.g. `int x;`).

## Supported language subset

The grammar covers a minimal but complete program shape:

- `#include` directives and `using namespace std;`
- `int main() { ... return <number>; }`
- `int` / `float` variable declarations, with optional initialization and comma-separated declarator lists (`int s = 0, t = 10;`)
- Assignments and arithmetic expressions with `+`, `-`, `*`
- `while` loops with comparison conditions (`==`, `>=`, `<=`, `!=`)
- Input with `cin >>` (chainable) and output with `cout <<` (chainable, including string literals)

## Requirements

- Python 3
- Python packages: `graphviz`, `tabulate`

  ```bash
  pip install graphviz tabulate
  ```

- [Graphviz](https://graphviz.org/download/) installed on your system (the `dot` executable must be on your `PATH`) — only needed for the parse-tree PNG; everything else runs without it.

## Usage

The input program is the `input_code` string at the top of `main.py`. Edit it (or keep the built-in sample), then run:

```bash
python main.py
```

## Example

With the sample program in `main.py`:

```cpp
#include <iostream>
using namespace std;
int main(){
    int x;
    int s=0, t=10;
    while (t >= 0){
        cin>>x;
        t = t - 1;
        s = s + x;
    }
    cout<<"sum="<<s;
    return 0;
}
```

the run produces:

```text
No errors found!
[20, 23, 24, 25, 40, 41, 43, 44, 45, 59, 61, 14, 21, 31, 37, 50, 72, 75]
Parse table saved to generated_parse_table.txt.
Parsing completed. Productions saved to 'productions_used.txt'.
Parse tree saved to parse_tree.png
int x;
```

- The list of numbers is the token hash table.
- `int x;` is the result of searching the parse tree for the declaration of identifier `x`.
- `productions_used.txt` records the leftmost derivation, e.g.:

  ```text
  Start -> S N M
  S -> #include S
  S -> ε
  N -> using namespace std ;
  M -> int main ( ) { T V }
  T -> Id T
  Id -> int L
  ...
  ```

- `parse_tree.png` is the rendered parse tree (a sample is committed in this repo).

If the input has a missing semicolon or a bad assignment (e.g. `int x = 2.5;`), the errors are reported with line numbers and the pipeline stops before parsing.

## Project structure

| File | Purpose |
| --- | --- |
| `main.py` | Entry point; wires the whole pipeline together |
| `LexicalAnalyzer.py` | Tokenizer plus semicolon and assignment-type checks |
| `TokenTable.py` | Hash table of tokens |
| `ParseTable.py` | Grammar definition, FIRST/FOLLOW sets, LL(1) parse table |
| `NonRecursivePredictiveParser.py` | Stack-based predictive parser |
| `ParseTree.py` | Parse-tree construction and Graphviz rendering |
| `SearchInTree.py` | Finds an identifier's declaration in the parse tree |
| `parse_tree.png` | Sample rendered parse tree |
| `time complexity.pdf` | Notes on the time complexity of the implementation |
