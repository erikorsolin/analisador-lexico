class Lexer:
    def __init__(self, dfa, reserved_words=None):
        self.dfa = dfa
        self.reserved_words = reserved_words or {}

    def tokenize(self, text):
        tokens = []
        pos = 0
        while pos < len(text):
            longest_match = None
            current_state = self.dfa
            start_pos = pos
            while pos < len(text):
                char = text[pos]
                if char in current_state.transitions:
                    current_state = current_state.transitions[char]
                    pos += 1
                    if current_state.is_accepting:
                        longest_match = (current_state.token_type, text[start_pos:pos])
                else:
                    break
            if longest_match:
                token_type, lexeme = longest_match
                # Check reserved words first
                if lexeme in self.reserved_words:
                    token_type = self.reserved_words[lexeme]
                tokens.append((lexeme, token_type))
            else:
                # Handle error
                raise SyntaxError(f"Invalid token at position {start_pos}")
        return tokens