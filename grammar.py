"""
Implementação da classe Grammar para representar gramáticas livres de contexto.
"""
from collections import defaultdict

class Grammar:
    def __init__(self):
        self.productions = []  # Lista de produções
        self.nonterminals = set()  # Conjunto de não terminais
        self.terminals = set()  # Conjunto de terminais
        self.start_symbol = None  # Símbolo inicial
        self.augmented_start = None  # Símbolo inicial aumentado
        self.first_sets = {}  # Conjunto FIRST
        self.follow_sets = {}  # Conjunto FOLLOW
        self.nullable = set()  # Conjunto de símbolos anuláveis
        self.augmented = False  # Indica se a gramática foi aumentada
        
    def load_from_file(self, filename):
        """
        Carrega uma gramática a partir de um arquivo.
        
        Formato esperado:
        <não-terminal> ::= <corpo da produção>
        Uma produção por linha.
        
        Exemplo:
        S ::= E
        E ::= E + T | T
        T ::= T * F | F
        F ::= ( E ) | id
        """
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Processar cada linha
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Separar lado esquerdo e direito
                parts = line.split('::=')
                if len(parts) != 2:
                    raise ValueError(f"Formato inválido na linha {i+1}: {line}")
                
                left = parts[0].strip()
                right = parts[1].strip()
                
                # Adicionar não terminal
                self.nonterminals.add(left)
                
                # Definir símbolo inicial (primeiro não terminal encontrado)
                if self.start_symbol is None:
                    self.start_symbol = left
                
                # Processar produções (separadas por |)
                alternatives = right.split('|')
                for alt in alternatives:
                    alt = alt.strip()
                    symbols = self._split_symbols(alt)
                    
                    # Identificar terminais
                    for sym in symbols:
                        if not sym in self.nonterminals and sym != 'ε':
                            self.terminals.add(sym)
                    
                    # Adicionar produção
                    if alt == 'ε':
                        self.productions.append((left, []))
                    else:
                        self.productions.append((left, symbols))
            
            print(f"Gramática carregada com {len(self.nonterminals)} não terminais, " +
                  f"{len(self.terminals)} terminais e {len(self.productions)} produções.")
            return True
            
        except FileNotFoundError:
            print(f"Erro: Arquivo {filename} não encontrado.")
            return False
        except Exception as e:
            print(f"Erro ao carregar gramática: {str(e)}")
            return False
    
    def _split_symbols(self, symbols_str):
        """
        Divide uma string em símbolos individuais, 
        respeitando símbolos com múltiplos caracteres.
        """
        tokens = []
        current_token = ""
        in_quotes = False
        
        for char in symbols_str:
            if char == "'" and not in_quotes:
                in_quotes = True
                current_token = "'"
            elif char == "'" and in_quotes:
                in_quotes = False
                current_token += "'"
                tokens.append(current_token)
                current_token = ""
            elif in_quotes:
                current_token += char
            elif char.isspace() and not current_token:
                continue  # Ignorar espaços extras
            elif char.isspace():
                tokens.append(current_token)
                current_token = ""
            else:
                current_token += char
        
        if current_token:
            tokens.append(current_token)
            
        return tokens
    
    def augment(self):
        """
        Aumenta a gramática adicionando uma nova produção S' → S,
        onde S é o símbolo inicial original.
        """
        if self.augmented:
            return
            
        if not self.start_symbol:
            raise ValueError("Não é possível aumentar a gramática: símbolo inicial não definido")
            
        self.augmented_start = f"{self.start_symbol}'"
        self.nonterminals.add(self.augmented_start)
        self.productions.insert(0, (self.augmented_start, [self.start_symbol]))
        self.augmented = True
        print(f"Gramática aumentada: {self.augmented_start} → {self.start_symbol}")
    
    def compute_nullable(self):
        """
        Calcula o conjunto de símbolos anuláveis (que podem derivar ε).
        """
        self.nullable = set()
        
        # Fase 1: Identificar não terminais que produzem ε diretamente
        for left, right in self.productions:
            if not right:  # Produção da forma A → ε
                self.nullable.add(left)
        
        # Fase 2: Adicionar não terminais que produzem strings de não terminais anuláveis
        changed = True
        while changed:
            changed = False
            for left, right in self.productions:
                if left not in self.nullable and all(sym in self.nullable for sym in right):
                    self.nullable.add(left)
                    changed = True
    
    def compute_first_sets(self):
        """
        Calcula o conjunto FIRST para cada símbolo da gramática.
        """
        # Inicializar FIRST(X) = {X} para cada terminal X
        self.first_sets = {}
        for terminal in self.terminals:
            self.first_sets[terminal] = {terminal}
            
        # Inicializar FIRST(X) = {} para cada não terminal X
        for nonterminal in self.nonterminals:
            self.first_sets[nonterminal] = set()
        
        # Calcular conjuntos FIRST
        changed = True
        while changed:
            changed = False
            for left, right in self.productions:
                old_first = self.first_sets[left].copy()
                
                # Produção da forma A → ε
                if not right:
                    continue  # Não afeta FIRST, apenas NULLABLE
                
                # Adicionar FIRST dos símbolos da produção
                all_nullable = True
                for i, symbol in enumerate(right):
                    # Adicionar FIRST(symbol) a FIRST(left)
                    if symbol in self.first_sets:
                        new_elements = self.first_sets[symbol] - self.first_sets[left]
                        if new_elements:
                            self.first_sets[left].update(new_elements)
                            changed = True
                    
                    # Se o símbolo não é anulável, paramos aqui
                    if symbol not in self.nullable:
                        all_nullable = False
                        break
                    
                if all_nullable and left not in self.nullable:
                    self.nullable.add(left)
                    changed = True
    
    def first_of_string(self, symbols):
        """
        Calcula o FIRST de uma string de símbolos.
        """
        if not symbols:
            return set()
            
        first_set = set()
        all_nullable = True
        
        for symbol in symbols:
            if symbol in self.first_sets:
                first_set.update(self.first_sets[symbol])
                
            if symbol not in self.nullable:
                all_nullable = False
                break
        
        return first_set
    
    def compute_follow_sets(self):
        """
        Calcula o conjunto FOLLOW para cada não terminal.
        """
        # Inicializar FOLLOW(X) = {} para cada não terminal X
        self.follow_sets = {nt: set() for nt in self.nonterminals}
        
        # Adicionar $ a FOLLOW(S), onde S é o símbolo inicial aumentado
        self.follow_sets[self.augmented_start].add('$')
        
        # Calcular conjuntos FOLLOW
        changed = True
        while changed:
            changed = False
            
            for left, right in self.productions:
                # Para cada não-terminal B em right
                for i, symbol in enumerate(right):
                    if symbol in self.nonterminals:  # Se o símbolo é não terminal
                        # Calcular FIRST da string que segue B
                        following = right[i+1:] if i+1 < len(right) else []
                        
                        if not following:  # Nada depois de B
                            # Adicionar FOLLOW(A) a FOLLOW(B)
                            old_follow = self.follow_sets[symbol].copy()
                            self.follow_sets[symbol].update(self.follow_sets[left])
                            if len(self.follow_sets[symbol]) > len(old_follow):
                                changed = True
                        else:
                            # Adicionar FIRST(following) a FOLLOW(B)
                            first_of_following = self.first_of_string(following)
                            old_follow = self.follow_sets[symbol].copy()
                            self.follow_sets[symbol].update(first_of_following)
                            if len(self.follow_sets[symbol]) > len(old_follow):
                                changed = True
                            
                            # Se following é anulável, adicionar FOLLOW(A) a FOLLOW(B)
                            all_nullable = True
                            for sym in following:
                                if sym not in self.nullable:
                                    all_nullable = False
                                    break
                            
                            if all_nullable:
                                old_follow = self.follow_sets[symbol].copy()
                                self.follow_sets[symbol].update(self.follow_sets[left])
                                if len(self.follow_sets[symbol]) > len(old_follow):
                                    changed = True
    
    def __str__(self):
        """Representação em string da gramática."""
        lines = ["Gramática:"]
        
        for left, right in self.productions:
            if not right:  # Produção da forma A → ε
                lines.append(f"  {left} ::= ε")
            else:
                lines.append(f"  {left} ::= {' '.join(right)}")
        
        return "\n".join(lines)
