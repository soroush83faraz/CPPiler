from collections import defaultdict
from tabulate import tabulate

class CFG:
    def __init__(self):
        self.rules = {}
        self.start = "Start"
        self.first = {}
        self.follow = {}
        self.fill()

    def add_production(self, variable, production):
        if variable not in self.rules:
            self.rules[variable] = []

        if isinstance(production, str):
            self.rules[variable].append(production.split())
        elif isinstance(production, list):
            self.rules[variable].extend([p.split() for p in production])

    def fill(self):
        self.add_production("Start", ["S N M"])
        self.add_production("S", ["#include S", "ε"])
        self.add_production("N", ["using namespace std ;", "ε"])
        self.add_production("M", ["int main ( ) { T V }"])
        self.add_production("T", ["Id T", "L T", "Loop T", "Input T", "Output T", "ε"])
        self.add_production("V", ["return number ;", "ε"]) # Added 'number' instead of zero after the return statement
        self.add_production("Id", ["int L", "float L"])
        self.add_production("L", ["identifier Assign Z"])
        self.add_production("Z", [", identifier Assign Z", ";"])
        self.add_production("Operation", ["number P", "identifier P"])
        self.add_production("P", ["O W P", "ε"])
        self.add_production("O", ["+", "-", "*"])
        self.add_production("W", ["number", "identifier"])
        self.add_production("Assign", ["= Operation", "ε"])
        self.add_production("Expression", ["Operation K Operation"])
        self.add_production("K", ["==", ">=", "<=", "!="])
        self.add_production("Loop", ["while ( Expression ) { T }"])
        self.add_production("Input", ["cin >> identifier F ;"])
        self.add_production("F", [">> identifier F", "ε"])
        self.add_production("Output", ["cout << C H ;"])
        self.add_production("H", ["<< C H", "ε"])
        self.add_production("C", ["number", "string", "identifier"])

    def calculate_first(self):
        self.first = {non_terminal: set() for non_terminal in self.rules}

        changed = True
        while changed:
            changed = False
            for variable, productions in self.rules.items():
                for production in productions:
                    for symbol in production:
                        if symbol not in self.rules:  # Terminal
                            if symbol not in self.first[variable]:
                                self.first[variable].add(symbol)
                                changed = True
                            break
                        else:  # Non-terminal
                            before = len(self.first[variable])
                            self.first[variable].update(self.first[symbol] - {"ε"})
                            if "ε" in self.first[symbol]:
                                continue
                            after = len(self.first[variable])
                            if before != after:
                                changed = True
                            break
                    else:  # Add epsilon if all symbols allow epsilon
                        if "ε" not in self.first[variable]:
                            self.first[variable].add("ε")
                            changed = True

    def calculate_follow(self):
        self.follow = {non_terminal: set() for non_terminal in self.rules}
        self.follow[self.start].add("$")

        changed = True
        while changed:
            changed = False
            for variable, productions in self.rules.items():
                for production in productions:
                    follow_temp = self.follow[variable].copy()
                    for symbol in reversed(production):
                        if symbol in self.rules:  # Non-terminal
                            before = len(self.follow[symbol])
                            self.follow[symbol].update(follow_temp)
                            after = len(self.follow[symbol])
                            if before != after:
                                changed = True
                            if "ε" in self.first[symbol]:
                                follow_temp.update(self.first[symbol] - {"ε"})
                            else:
                                follow_temp = self.first[symbol].copy()
                        else:  # Terminal
                            follow_temp = {symbol}

    def first_of_sequence(self, sequence):
        result = set()
        for symbol in sequence:
            if symbol not in self.rules:  # Terminal
                result.add(symbol)
                break
            result.update(self.first[symbol] - {"ε"})
            if "ε" not in self.first[symbol]:
                break
        else:
            result.add("ε")
        return result

class ParseTable:
    def __init__(self, cfg):
        self.cfg = cfg
        self.parse_table = None

    def construct_parse_table(self):
        self.cfg.calculate_first()
        self.cfg.calculate_follow()

        parse_table = defaultdict(lambda: defaultdict(lambda: []))

        for variable, productions in self.cfg.rules.items():
            for production in productions:
                first_set = self.cfg.first_of_sequence(production)
                for terminal in first_set:
                    if terminal != "ε":
                        parse_table[variable][terminal] = production
                if "ε" in first_set:
                    for terminal in self.cfg.follow[variable]:
                        parse_table[variable][terminal] = production

        self.parse_table = parse_table
        return self.parse_table

    def save_to_file(self, output_file, specified_order, terminals):
        headers = ["Non-Terminal"] + terminals
        rows = []
        for nt in specified_order:
            row = [nt] + [f"[{', '.join(self.parse_table[nt][t])}]" if self.parse_table[nt][t] else "[]" for t in terminals]
            rows.append(row)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(tabulate(rows, headers=headers, tablefmt="grid"))

        print(f"Parse table saved to {output_file}.")
