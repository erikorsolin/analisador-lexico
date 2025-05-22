"""
Implementação da conversão direta de Expressão Regular para Autômato Finito Determinístico
usando o algoritmo Follow-Pos (método de construção de Berry-Sethi/Glushkov).
"""
from automaton import Automaton
from collections import defaultdict

class RegexNode:
    """Classe que representa um nó na árvore sintática da expressão regular."""
    def __init__(self, type, value=None):
        self.type = type            # Tipo do nó: 'concat', 'alt', 'star', 'plus', 'opt', 'symbol'
        self.value = value          # Valor do nó (apenas para símbolos)
        self.left = None            # Filho esquerdo
        self.right = None           # Filho direito
        self.position = None        # Posição única do nó (apenas para símbolos)
        self.nullable = False       # True se o nó pode gerar a string vazia
        self.firstpos = set()       # Conjunto de posições que podem iniciar a string
        self.lastpos = set()        # Conjunto de posições que podem terminar a string
        self.followpos = None       # Não usado no nó, mas definido para clareza

class RegexToAFD:
    def __init__(self):
        self.position_counter = 0    # Contador para gerar posições únicas
        self.followpos = defaultdict(set)  # Mapeamento de posições para seus followpos
        self.position_symbol = {}    # Mapeamento de posições para símbolos
        self.regex_string = ""       # String da expressão regular
        self.current_pos = 0         # Posição atual na string
        self.root = None             # Raiz da árvore de expressão
    
    def convert(self, regex):
        """Converte uma expressão regular para um AFD usando o algoritmo follow-pos."""
        # Remover espaços em branco
        self.regex_string = regex.replace(" ", "")
        self.current_pos = 0
        self.position_counter = 1
        self.followpos = defaultdict(set)
        self.position_symbol = {}
        
        # Adicionar o marcador de fim para facilitar o algoritmo
        augmented_regex = f"({self.regex_string})#"
        self.regex_string = augmented_regex
        
        # Construir a árvore sintática
        print(f"Construindo árvore sintática para: {self.regex_string}")
        self.root = self._parse_expression()
        
        # Calcular firstpos, lastpos e nullable
        self._calculate_sets(self.root)
        
        # Calcular followpos
        self._calculate_followpos(self.root)
        
        # Construir o AFD a partir das informações calculadas
        return self._build_afd()
    
    def _parse_expression(self):
        """Analisa uma expressão regular e constrói a árvore sintática."""
        # Analisar alternativas (separadas por |)
        result = self._parse_term()
        
        while self.current_pos < len(self.regex_string) and self.regex_string[self.current_pos] == '|':
            self.current_pos += 1  # Consumir o '|'
            
            # Criar nó de alternância
            alt_node = RegexNode('alt')
            alt_node.left = result
            alt_node.right = self._parse_term()
            
            result = alt_node
        
        return result
    
    def _parse_term(self):
        """Analisa um termo (sequência de fatores) na expressão regular."""
        # Analisar o primeiro fator
        result = self._parse_factor()
        
        # Enquanto houver outro fator, fazer a concatenação
        while (self.current_pos < len(self.regex_string) and
               self.regex_string[self.current_pos] != '|' and
               self.regex_string[self.current_pos] != ')'):
            
            # Criar nó de concatenação
            concat_node = RegexNode('concat')
            concat_node.left = result
            concat_node.right = self._parse_factor()
            
            result = concat_node
        
        return result
    
    def _parse_factor(self):
        """Analisa um fator (átomo possivelmente seguido por *, + ou ?) na expressão regular."""
        # Analisar o átomo
        result = self._parse_atom()
        
        # Verificar se há um operador de repetição
        if self.current_pos < len(self.regex_string):
            if self.regex_string[self.current_pos] == '*':
                self.current_pos += 1
                # Criar nó de fechamento de Kleene
                star_node = RegexNode('star')
                star_node.left = result
                result = star_node
            elif self.regex_string[self.current_pos] == '+':
                self.current_pos += 1
                # Criar nó de fechamento positivo
                plus_node = RegexNode('plus')
                plus_node.left = result
                result = plus_node
            elif self.regex_string[self.current_pos] == '?':
                self.current_pos += 1
                # Criar nó opcional
                opt_node = RegexNode('opt')
                opt_node.left = result
                result = opt_node
        
        return result
    
    def _parse_atom(self):
        """Analisa um átomo (caractere, grupo ou subexpressão) na expressão regular."""
        if self.current_pos >= len(self.regex_string):
            raise ValueError("Fim inesperado da expressão regular")
        
        char = self.regex_string[self.current_pos]
        
        if char == '(':
            # Subexpressão entre parênteses
            self.current_pos += 1  # Consumir o '('
            result = self._parse_expression()
            
            if self.current_pos >= len(self.regex_string) or self.regex_string[self.current_pos] != ')':
                raise ValueError(f"Parêntese não fechado na expressão regular: {self.regex_string}")
            
            self.current_pos += 1  # Consumir o ')'
            return result
        
        elif char == '[':
            # Grupo de caracteres
            return self._parse_character_class()
        
        elif char == '\\':
            # Caractere escapado
            if self.current_pos + 1 >= len(self.regex_string):
                raise ValueError("Escape no final da expressão regular")
            
            self.current_pos += 1  # Pular o '\'
            char = self.regex_string[self.current_pos]
            self.current_pos += 1  # Consumir o caractere escapado
            
            # Criar nó de símbolo
            symbol_node = RegexNode('symbol', char)
            symbol_node.position = self.position_counter
            self.position_symbol[self.position_counter] = char
            self.position_counter += 1
            
            return symbol_node
        
        else:
            # Caractere simples
            self.current_pos += 1
            
            # Criar nó de símbolo
            symbol_node = RegexNode('symbol', char)
            symbol_node.position = self.position_counter
            self.position_symbol[self.position_counter] = char
            self.position_counter += 1
            
            return symbol_node
    
    def _parse_character_class(self):
        """Analisa uma classe de caracteres [a-z] na expressão regular."""
        if self.current_pos >= len(self.regex_string) or self.regex_string[self.current_pos] != '[':
            raise ValueError("Esperava '[' para iniciar classe de caracteres")
        
        self.current_pos += 1  # Consumir o '['
        start_pos = self.current_pos
        
        # Procurar o fechamento do grupo
        while self.current_pos < len(self.regex_string) and self.regex_string[self.current_pos] != ']':
            self.current_pos += 1
        
        if self.current_pos >= len(self.regex_string):
            raise ValueError(f"Classe de caracteres não fechada na expressão regular: {self.regex_string}")
        
        # Extrair o conteúdo do grupo
        group_content = self.regex_string[start_pos:self.current_pos]
        self.current_pos += 1  # Consumir o ']'
        
        # Processar o grupo para extrair caracteres
        chars = []
        i = 0
        while i < len(group_content):
            if i + 2 < len(group_content) and group_content[i+1] == '-':
                # Range de caracteres (e.g., a-z)
                start_char = group_content[i]
                end_char = group_content[i+2]
                
                for c in range(ord(start_char), ord(end_char) + 1):
                    chars.append(chr(c))
                
                i += 3
            else:
                # Caractere único
                chars.append(group_content[i])
                i += 1
        
        # Construir um nó de alternância para cada caractere no grupo
        if not chars:
            raise ValueError("Classe de caracteres vazia")
        
        # Criar nó de símbolo para o primeiro caractere
        result = RegexNode('symbol', chars[0])
        result.position = self.position_counter
        self.position_symbol[self.position_counter] = chars[0]
        self.position_counter += 1
        
        # Adicionar alternância para os outros caracteres
        for char in chars[1:]:
            alt_node = RegexNode('alt')
            alt_node.left = result
            
            symbol_node = RegexNode('symbol', char)
            symbol_node.position = self.position_counter
            self.position_symbol[self.position_counter] = char
            self.position_counter += 1
            
            alt_node.right = symbol_node
            result = alt_node
        
        return result
    
    def _calculate_sets(self, node):
        """Calcula os conjuntos nullable, firstpos e lastpos para cada nó."""
        if node is None:
            return
        
        if node.type == 'symbol':
            # Nó de símbolo
            node.nullable = False
            node.firstpos = {node.position}
            node.lastpos = {node.position}
        
        elif node.type == 'concat':
            # Nó de concatenação
            self._calculate_sets(node.left)
            self._calculate_sets(node.right)
            
            node.nullable = node.left.nullable and node.right.nullable
            
            if node.left.nullable:
                node.firstpos = node.left.firstpos | node.right.firstpos
            else:
                node.firstpos = node.left.firstpos
            
            if node.right.nullable:
                node.lastpos = node.left.lastpos | node.right.lastpos
            else:
                node.lastpos = node.right.lastpos
        
        elif node.type == 'alt':
            # Nó de alternância
            self._calculate_sets(node.left)
            self._calculate_sets(node.right)
            
            node.nullable = node.left.nullable or node.right.nullable
            node.firstpos = node.left.firstpos | node.right.firstpos
            node.lastpos = node.left.lastpos | node.right.lastpos
        
        elif node.type == 'star':
            # Nó de fechamento de Kleene
            self._calculate_sets(node.left)
            
            node.nullable = True
            node.firstpos = node.left.firstpos
            node.lastpos = node.left.lastpos
        
        elif node.type == 'plus':
            # Nó de fechamento positivo
            self._calculate_sets(node.left)
            
            node.nullable = node.left.nullable
            node.firstpos = node.left.firstpos
            node.lastpos = node.left.lastpos
        
        elif node.type == 'opt':
            # Nó opcional
            self._calculate_sets(node.left)
            
            node.nullable = True
            node.firstpos = node.left.firstpos
            node.lastpos = node.left.lastpos
    
    def _calculate_followpos(self, node):
        """Calcula o conjunto followpos para cada posição."""
        if node is None:
            return
        
        if node.type == 'concat':
            # Para cada posição em lastpos(esquerda), adicione firstpos(direita) ao seu followpos
            for pos in node.left.lastpos:
                self.followpos[pos].update(node.right.firstpos)
            
            # Recursivamente calcular followpos para os filhos
            self._calculate_followpos(node.left)
            self._calculate_followpos(node.right)
        
        elif node.type in ('star', 'plus'):
            # Para cada posição em lastpos(n), adicione firstpos(n) ao seu followpos
            for pos in node.lastpos:
                self.followpos[pos].update(node.firstpos)
            
            # Recursivamente calcular followpos para o filho
            self._calculate_followpos(node.left)
        
        elif node.type in ('alt', 'opt'):
            # Recursivamente calcular followpos para os filhos
            self._calculate_followpos(node.left)
            if node.right:
                self._calculate_followpos(node.right)
    
    def _build_afd(self):
        """Constrói o AFD a partir das informações de followpos."""
        # Posição do marcador de fim #
        end_marker_pos = self.position_counter - 1
        
        afd = Automaton()
        
        # O estado inicial do AFD é o firstpos da raiz
        initial_state_positions = frozenset(self.root.firstpos)
        
        # Mapear conjuntos de posições para estados do AFD
        states_dict = {initial_state_positions: 0}
        unmarked_states = [initial_state_positions]
        
        # Adicionar o estado inicial ao AFD
        afd.set_initial_state(0)
        
        # Se o marcador de fim está no estado inicial, então a ε é aceita
        if end_marker_pos in initial_state_positions:
            afd.add_final_state(0)
        
        # Processar estados não marcados
        while unmarked_states:
            current_positions = unmarked_states.pop(0)
            current_state = states_dict[current_positions]
            
            # Para cada símbolo do alfabeto (exceto o marcador de fim)
            symbols = set()
            for pos in current_positions:
                if pos != end_marker_pos:
                    symbol = self.position_symbol[pos]
                    symbols.add(symbol)
            
            for symbol in symbols:
                # Determinar as posições alcançáveis a partir do estado atual pelo símbolo
                next_positions = set()
                for pos in current_positions:
                    if self.position_symbol[pos] == symbol:
                        next_positions.update(self.followpos[pos])
                
                if not next_positions:
                    continue
                
                next_positions = frozenset(next_positions)
                
                # Verificar se este conjunto de posições já corresponde a um estado
                if next_positions not in states_dict:
                    next_state = len(states_dict)
                    states_dict[next_positions] = next_state
                    unmarked_states.append(next_positions)
                    
                    # Verificar se o novo estado contém o marcador de fim
                    if end_marker_pos in next_positions:
                        afd.add_final_state(next_state)
                else:
                    next_state = states_dict[next_positions]
                
                # Adicionar a transição ao AFD
                afd.add_transition(current_state, symbol, next_state)
        
        # Adicionar estados ao AFD
        for i in range(len(states_dict)):
            afd.add_state(i)
        
        return afd