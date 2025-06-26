"""
Implementação do analisador de tokens que usa o AFD para reconhecer tokens no texto.
"""
class TokenAnalyzer:
    def __init__(self, automaton, symbol_table):
        self.automaton = automaton
        self.symbol_table = symbol_table
        self.last_tokens = []

    def analyze(self, text):
        tokens = []
        self.last_tokens = []
        position = 0
        text_length = len(text)

        while position < text_length:
            # Pular espaços
            while position < text_length and text[position].isspace():
                position += 1

            if position >= text_length:
                break

            token = self._get_next_token(text, position)

            if token:
                lexeme, pattern, length = token
                is_new, token_value = self.symbol_table.add_symbol(lexeme, pattern)

                if pattern == "id":
                    tokens.append(f"<{lexeme}, id>")
                elif pattern == "num":
                    tokens.append(f"<{lexeme}, num>")
                elif lexeme in self.symbol_table.reserved_words:
                    tokens.append(f"<{lexeme}, PR>")
                else:
                    tokens.append(f"<{lexeme}, {pattern}>")

                position += length
            else:
                print(f"Erro léxico: lexema '{text[position]}' não reconhecido.")
                return None

        return tokens

    def _get_next_token(self, text, start_pos):
        current_state = self.automaton.initial_state
        last_final_state = None
        last_final_pos = -1
        pos = start_pos

        while pos < len(text):
            char = text[pos]
            transitions = self.automaton.transitions.get(current_state, {})
            next_state = transitions.get(char)

            if next_state:
                next_state = next(iter(next_state))
                current_state = next_state
                pos += 1

                for state, pattern in self.automaton.final_states:
                    if state == current_state:
                        last_final_state = pattern
                        last_final_pos = pos
            else:
                break

        if last_final_pos != -1 and last_final_pos > start_pos:
            lexeme = text[start_pos:last_final_pos]
            return (lexeme, last_final_state, len(lexeme))

        return None
