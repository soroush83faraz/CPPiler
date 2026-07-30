import re

class LexicalAnalyzer:
    token_patterns = [
        (r"\b(?:int|float|void|return|if|while|cin|cout|continue|break|using|namespace|std|main)\b", "RESERVEDWORD"),
        (r"#include\b", "RESERVEDWORD"),
        (r'\".*?\"', "STRING"),
        (r"[a-zA-Z][a-zA-Z0-9]*", "IDENTIFIER"),
        (r"[0-9]+(\.[0-9]+)?", "NUMBER"),
        (r"\+\+|--|\+=|-=|\*=|/=|==|!=|>=|<=|&&|\|\||<<|>>", "SYMBOL"),
        (r"[+\-*/=><!&|;,:\[\]{}()\|]", "SYMBOL"),
    ]

    def __init__(self,code):
        self.compiled_patterns = self.compile_patterns()
        self.variable_types = {}
        self.semicolon_errors = []
        self.wrong_allocations = []
        self.manage_tokens(code)

    def compile_patterns(self):
        return [(re.compile(pattern), token_type) for pattern, token_type in self.token_patterns]

    def analyze(self, line):
        tokens = []
        position = 0

        while position < len(line):
            match = None
            for token_compiler, token_type in self.compiled_patterns:
                match = token_compiler.match(line, position)
                if match:
                    lexeme = match.group(0)

                    if token_type == "NUMBER":
                        tokens.append((token_type.lower(), int(lexeme)))
                    elif token_type == "STRING" or token_type == "IDENTIFIER":
                        tokens.append((token_type.lower(), lexeme)) 
                    else:
                        tokens.append((token_type, lexeme))

                    position = match.end()
                    break

            if not match:
                if line[position].isspace():
                    position += 1
                else:
                    raise ValueError(f"Unexpected character: {line[position]}")

        return tokens

    def missing_semicolon(self, line: str) -> bool:
        line = line.strip()

        if not line:
            return False

        exceptions = [
            "if", "else", "while", "for", "switch", "case", "default",
            "{", "}",
            "#include"
        ]

        for exception in exceptions:
            if line.startswith(exception):
                return False

        if "(" in line and ")" in line:
            return False

        if line.endswith(";"):
            return False

        return True

    def detect_wrong_allocations(self, line: str, line_number: int) -> list:
        errors = []
        line = line.strip()

        if re.match(r"(int|float|void)\s+[a-zA-Z][a-zA-Z0-9]*\s*\(.*\)\s*\{?", line):
            return errors

        declaration_match = re.match(r"(int|float)\s+([a-zA-Z][a-zA-Z0-9]*)\s*;", line)
        if declaration_match:
            var_type = declaration_match.group(1)
            var_name = declaration_match.group(2)
            self.variable_types[var_name] = var_type
            return errors
        
        combined_match = re.match(r"(int|float)\s+([a-zA-Z][a-zA-Z0-9]*)\s*=\s*(.*);", line)
        if combined_match:
            var_type = combined_match.group(1)
            var_name = combined_match.group(2)
            value = combined_match.group(3)

            self.variable_types[var_name] = var_type

            if var_type == "int":
                if re.match(r"\".*\"", value):
                    errors.append(f"Error: Cannot assign string to int variable '{var_name}', line:{line_number}")
                elif re.match(r"[0-9]+\.[0-9]+", value):
                    errors.append(f"Error: Cannot assign float to int variable '{var_name}', line:{line_number}")
            elif var_type == "float":
                if re.match(r"\".*\"", value):
                    errors.append(f"Error: Cannot assign string to float variable '{var_name}', line:{line_number}")

            return errors


        assignment_match = re.match(r"([a-zA-Z][a-zA-Z0-9]*)\s*=\s*(.*);", line)
        if assignment_match:
            var_name = assignment_match.group(1)
            value = assignment_match.group(2)

            if var_name in self.variable_types:
                var_type = self.variable_types[var_name]

                if var_type == "int":
                    if re.match(r"\".*\"", value):
                        errors.append(f"Error: Cannot assign string to int variable '{var_name}', line:{line_number}")
                    elif re.match(r"[0-9]+\.[0-9]+", value):
                        errors.append(f"Error: Cannot assign float to int variable '{var_name}', line:{line_number}")

                elif var_type == "float":
                    if re.match(r"\".*\"", value):
                        errors.append(f"Error: Cannot assign string to float variable '{var_name}', line:{line_number}")

        return errors

    def manage_tokens(self, code):
        tokens = []
        missing_semicolon_lines = []
        wrong_allocations = []

        for line_number, line in enumerate(code.split("\n")):
            line = re.sub(r'#include\s*[<"].*?[>"]', '#include', line)  # preventing include-related errors
            if self.missing_semicolon(line):
                missing_semicolon_lines.append(line_number + 1)

            wrong_allocations.extend(self.detect_wrong_allocations(line, line_number + 1))

            tokens.extend(self.analyze(line))

        self.tokens = tokens
        self.wrong_allocations = wrong_allocations
        self.semicolon_errors = missing_semicolon_lines

