"""
Implementação do analisador de tokens que usa o AFD para reconhecer tokens no texto.
"""
class TokenAnalyzer:
    def __init__(self, automaton, symbol_table):
        """
        Inicializa o analisador de tokens com um autômato e uma tabela de símbolos.
        """
        self.automaton = automaton
        self.symbol_table = symbol_table
    
    def analyze(self, text):
        """
        Analisa o texto e retorna a lista de tokens no formato <lexema, padrão>.
        """
        tokens = []
        position = 0
        
        while position < len(text):
            # Pular espaços em branco
            while position < len(text) and text[position].isspace():
                position += 1
            
            if position >= len(text):
                break
            
            # Tentar reconhecer o próximo token
            token = self._get_next_token(text, position)
            
            if token:
                lexeme, pattern, length = token
                
                # Atualizar a tabela de símbolos
                self.symbol_table.add_symbol(lexeme, pattern)
                
                # Verificar se o lexema é uma palavra reservada
                final_pattern = self.symbol_table.get_pattern(lexeme)
                
                tokens.append(f"<{lexeme}, {final_pattern}>")
                position += length
            else:
                # Caractere não reconhecido
                error_lexeme = text[position]
                tokens.append(f"<{error_lexeme}, erro!>")
                position += 1
        
        return tokens
    
    def _get_next_token(self, text, start_pos):
        """
        Reconhece o próximo token no texto a partir da posição especificada.
        Retorna uma tupla (lexeme, pattern, length) ou None se nenhum token for reconhecido.
        """
        current_state = self.automaton.initial_state
        max_final_pos = -1
        max_final_pattern = None
        
        pos = start_pos
        
        while pos < len(text) and not text[pos].isspace():
            char = text[pos]
            
            # Verificar se há transição para este caractere
            next_state = None
            
            for symbol, to_states in self.automaton.transitions.get(current_state, {}).items():
                if symbol == char:
                    next_state = next(iter(to_states))  # AFD tem apenas um próximo estado
                    break
            
            if next_state is not None:
                current_state = next_state
                pos += 1
                
                # Verificar se este é um estado final
                for state, pattern in self.automaton.final_states:
                    if state == current_state:
                        max_final_pos = pos - 1
                        max_final_pattern = pattern
                        break
            else:
                # Não há transição para este caractere
                break
        
        if max_final_pos >= start_pos:
            lexeme = text[start_pos:max_final_pos + 1]
            return (lexeme, max_final_pattern, len(lexeme))
        
        return None