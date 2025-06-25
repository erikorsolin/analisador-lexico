"""
Implementação da Tabela de Símbolos para armazenar informações sobre os tokens.
"""
class SymbolTable:
    def __init__(self):
        self.symbols = {}        # Dicionário para busca rápida por lexema
        self.symbol_list = []    # Lista para busca por índice
        self.reserved_words = set()
    
    def add_symbol(self, lexeme, pattern):
        """
        Adiciona um símbolo à tabela.
        Retorna (True, index) se o símbolo foi adicionado, onde index é a posição na lista.
        Retorna (False, index) se o símbolo já existia, onde index é a posição na lista.
        """
        if lexeme in self.reserved_words:
            # Palavras reservadas têm prioridade e sempre recebem o padrão "PR"
            self.symbols[lexeme] = "PR"
            return True, "PR"
        
        if lexeme not in self.symbols:
            # Para identificadores, armazenamos o índice na lista
            if pattern == "id":
                self.symbol_list.append(lexeme)
                index = len(self.symbol_list) - 1
                self.symbols[lexeme] = (pattern, index)
                return True, index
            else:
                # Para outros tokens, armazenamos apenas o padrão
                self.symbols[lexeme] = pattern
                return True, pattern
        else:
            # Se o símbolo já existe, retornamos seu índice (para identificadores)
            if isinstance(self.symbols[lexeme], tuple) and self.symbols[lexeme][0] == "id":
                return False, self.symbols[lexeme][1]
            return False, self.symbols[lexeme]
    
    def add_reserved_word(self, word):
        """Adiciona uma palavra reservada à tabela."""
        self.reserved_words.add(word)
        self.symbols[word] = "PR"
    
    def get_pattern(self, lexeme):
        """
        Retorna o padrão associado ao lexema.
        Se o lexema não estiver na tabela, retorna None.
        Para identificadores, retorna uma tupla (pattern, index).
        """
        return self.symbols.get(lexeme)
    
    def get_symbol_by_index(self, index):
        """
        Retorna o lexema associado ao índice na lista de símbolos.
        """
        if 0 <= index < len(self.symbol_list):
            return self.symbol_list[index]
        return None
        
    def __str__(self):
        """Representação em string da tabela de símbolos."""
        result = ["Tabela de Símbolos:"]
        for lexeme, pattern in sorted(self.symbols.items()):
            if isinstance(pattern, tuple):
                result.append(f"  {lexeme}: {pattern[0]}, index={pattern[1]}")
            else:
                result.append(f"  {lexeme}: {pattern}")
        return "\n".join(result)

    def get_token_representation(self, lexeme):
        """
        Retorna a representação do token no formato especificado para análise sintática.
        Para identificadores: <id, index>
        Para palavras reservadas: <lexema, PR>
        Para outros: <lexeme, pattern>
        """
        if lexeme not in self.symbols:
            return None
        
        pattern = self.symbols[lexeme]
        
        if lexeme in self.reserved_words:
            return f"<{lexeme}, PR>"
        elif isinstance(pattern, tuple) and pattern[0] == "id":
            return f"<id, {pattern[1]}>"
        elif isinstance(pattern, tuple):
            return f"<{lexeme}, {pattern[0]}>"
        else:
            return f"<{lexeme}, {pattern}>"