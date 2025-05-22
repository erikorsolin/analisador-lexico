"""
Implementação da Tabela de Símbolos para armazenar informações sobre os tokens.
"""
class SymbolTable:
    def __init__(self):
        """Inicializa a tabela de símbolos vazia."""
        self.symbols = {}
        self.reserved_words = set()
    
    def add_symbol(self, lexeme, pattern):
        """
        Adiciona um símbolo à tabela.
        Retorna True se o símbolo foi adicionado, False se já existia.
        """
        if lexeme in self.reserved_words:
            # Palavras reservadas têm prioridade e sempre recebem o padrão "PR"
            self.symbols[lexeme] = "PR"
            return True
        
        if lexeme not in self.symbols:
            self.symbols[lexeme] = pattern
            return True
        return False
    
    def add_reserved_word(self, word):
        """Adiciona uma palavra reservada à tabela."""
        self.reserved_words.add(word)
        self.symbols[word] = "PR"
    
    def get_pattern(self, lexeme):
        """
        Retorna o padrão associado ao lexema.
        Se o lexema não estiver na tabela, retorna None.
        """
        return self.symbols.get(lexeme)
    
    def __str__(self):
        """Representação em string da tabela de símbolos."""
        result = ["Tabela de Símbolos:"]
        for lexeme, pattern in sorted(self.symbols.items()):
            result.append(f"  {lexeme}: {pattern}")
        return "\n".join(result)