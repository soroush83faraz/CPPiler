import re

class NonRecursivePredictiveParser:
    def __init__(self, parse_table, start_symbol):
        self.parse_table = parse_table
        self.start_symbol = start_symbol

    def parse(self, input_tokens, output_file="productions_used.txt"):
        processed_tokens = []
        for token in input_tokens:
            if isinstance(token, tuple) and token[0] in ["identifier", "number", "string"]:
                processed_tokens.append(token) # Keeping the tuple as is
            elif isinstance(token, tuple):
                processed_tokens.append(token[1])  # Use the first element of the tuple


        processed_tokens.append("$")  # End marker to processed tokens

        stack = ["$"]
        stack.append(self.start_symbol)
        cursor = 0

        productions_used = []

        with open(output_file, "w",encoding="utf-8") as f:
            while stack:
                top = stack.pop()
                current_token = processed_tokens[cursor]
                
                if top == "$":
                    if current_token == "$":
                        print(f"Parsing completed. Productions saved to '{output_file}'.")
                        return productions_used
                    else:
                        raise ValueError(f"Unexpected token '{current_token}' at the end of input.")

                elif top == current_token:  
                    cursor += 1

                elif top in ["identifier", "number", "string"]:  
                    if isinstance(current_token, tuple) and current_token[0] == top:
                        productions_used.append(f"{top} -> {current_token[1]}")
                        cursor += 1
                    else:
                        raise ValueError(f"Expected {top} but got '{current_token}'.")
                    
                elif top in self.parse_table or (isinstance(current_token, tuple) and current_token[0] in self.parse_table):  # Non-terminal Symbols and Transitions in the Parse Table
                    token_key = current_token[0] if isinstance(current_token, tuple) else current_token
                    if token_key in self.parse_table[top]:
                        production = self.parse_table[top][token_key]


                        if (len(production) == 1 and production[0] in ["identifier", "number", "string"] and isinstance(current_token, tuple)):
                            
                            f.write(f"{top} -> {current_token[1]}\n")
                            productions_used.append(f"{top} -> {current_token[1]}")
                            
                            stack.append(production[0])
                        else:
                            f.write(f"{top} -> {' '.join(production)}\n")
                            productions_used.append(f"{top} -> {' '.join(production)}")

                            if production != ["ε"]:
                                stack.extend(reversed(production))
                    else:
                        raise ValueError(f"No rule for '{top}' with input '{token_key}' in parse table.")
                    


                else:
                    raise ValueError(f"Unexpected symbol '{top}' on stack.")

            if cursor != len(processed_tokens) - 1:
                raise ValueError("Input not fully parsed.")

        return productions_used
