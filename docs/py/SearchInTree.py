class SearchInTree:
    def __init__(self, root, non_terminals):
        self.root = root
        self.non_terminals = non_terminals

    def find_declaration(self, identifier_to_find):
        stack = [self.root]

        while stack:
            current_node = stack.pop()

            if current_node.value == "Id":
                variable_type = current_node.children[0].value  

                l_node = current_node.children[1]  
                
                result = self.process_l_node(variable_type, l_node, identifier_to_find)
                if result:  # If declaration is found, return it
                    return result

            stack.extend(reversed(current_node.children))

        return None

    def process_l_node(self, variable_type, l_node, identifier_to_find):
        declaration = f"{variable_type} "
        stack = [l_node]
        identifier_parent = None

        while stack:
            current_node = stack.pop()

            # Set identifier_parent when finding the first identifier node
            if not identifier_parent or any(child.value == "identifier" for child in current_node.children):
                identifier_parent = current_node

            # Skip nodes that are not in the non-terminal list
            if current_node.value not in self.non_terminals:
                continue

            if current_node.value == "identifier":
                identifier_node = self.find_terminal(current_node)
                identifier = identifier_node.value

                if identifier == identifier_to_find:
                    declaration += identifier

                    assign_node = next((sibling for sibling in identifier_parent.children if sibling.value == "Assign"), None)
                    if assign_node:
                        assign_child = assign_node.children[0] if assign_node.children else None
                        if assign_child and assign_child.value == "ε":  # Epsilon
                            declaration += ";"
                            return declaration
                        elif assign_child:
                            declaration += " = "
                            number_node = self.find_number_node(assign_node)
                            if number_node:
                                terminal = self.find_terminal(number_node)
                                declaration += terminal.value

                    declaration += ";"
                    return declaration

            stack.extend(reversed(current_node.children))

        return None

    def find_terminal(self, node):
        current_node = node

        while current_node.value in self.non_terminals:
            current_node = current_node.children[0]

        return current_node

    def find_number_node(self, node):
        stack = [node]

        while stack:
            current_node = stack.pop()

            if current_node.value == "number":
                return current_node

            stack.extend(reversed(current_node.children))

        return None
