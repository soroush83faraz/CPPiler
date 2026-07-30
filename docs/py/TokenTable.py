class TokenTable:
    def hash_function(self, key):
        if isinstance(key, str):
            return sum(ord(char) for char in key) % self.size
        elif isinstance(key, int):
            return key % self.size
        else:
            raise TypeError("Key must be a string or integer")

    def create_table(self):
        res = []
        elements = ["STRING", "NUMBER", "SYMBOL", "IDENTIFIER", "RESERVEDWORD"]
        for element in elements:
            if element in self.tokens:
                for hashed_token in self.tokens[element]:
                    if hashed_token not in res:
                        res.append(hashed_token)
        self.token_table = res

    def manage_tokens(self, token_list):
        for token_name, token in token_list:
            if token_name not in self.tokens:
                self.tokens[token_name] = set()
            if token not in self.tokens[token_name]:
                self.tokens[token_name].add(token)
        for key, value in self.tokens.items():
            new_ls = sorted(list(value), key=lambda s: self.hash_function(s))
            new_ls = list(map(self.hash_function, new_ls))
            self.tokens[key] = new_ls

    def __init__(self, token_list, size=100):
        self.tokens = {}
        self.size = size
        self.manage_tokens(token_list)
        if self.tokens:
            self.create_table()
    
    def display(self):
        print(self.token_table)