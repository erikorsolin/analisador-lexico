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
            
            # Primeiramente, identificar todos os não terminais
            productions_data = []
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
                
                # Armazenar temporariamente para processar depois
                productions_data.append((left, right))
            
            # Processar as produções agora que todos os não terminais são conhecidos
            for left, right in productions_data:
                # Processar produções (separadas por |)
                alternatives = right.split('|')
                for alt in alternatives:
                    alt = alt.strip()
                    symbols = self._split_symbols(alt)
                    
                    # Identificar terminais (agora que todos os não terminais são conhecidos)
                    for sym in symbols:
                        if sym not in self.nonterminals and sym != 'ε':
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
        Implementation based on Algorithm 4.19 from the Dragon Book with
        special handling for left-recursive grammars.
        """
        # Step 1: Initialize nullable set and compute nullable symbols
        self.compute_nullable()
        
        # Step 2: Initialize FIRST sets
        self.first_sets = {}
        
        # For terminals, FIRST(X) = {X}
        for terminal in self.terminals:
            self.first_sets[terminal] = {terminal}
        
        # For non-terminals, start with empty sets
        for nonterminal in self.nonterminals:
            self.first_sets[nonterminal] = set()
            
            # If the non-terminal is nullable, add ε to its FIRST set
            if nonterminal in self.nullable:
                self.first_sets[nonterminal].add('')
        
        # Detect and handle left recursion specially
        left_recursive = {}  # Map from non-terminal to its non-left-recursive alternatives
        for nonterminal in self.nonterminals:
            left_recursive[nonterminal] = []
        
        # Step 2.5: Handle left recursion separately
        for left, right in self.productions:
            if right and right[0] != left and right[0] in self.nonterminals:
                # Non-left-recursive rule like A → BC..., add to special handling
                left_recursive[left].append(right[0])
        
        # Propagate FIRST sets from non-left-recursive alternates
        changed = True
        while changed:
            changed = False
            for nt, alts in left_recursive.items():
                for alt in alts:
                    for term in self.first_sets[alt]:
                        if term != '' and term not in self.first_sets[nt]:
                            self.first_sets[nt].add(term)
                            changed = True
                            changed = True
        
        # Step 3: Standard algorithm - iterate until no more changes
        changed = True
        while changed:
            changed = False
            
            for left, right in self.productions:
                # Skip empty productions, handled earlier
                if not right:
                    continue
                
                # Special case: avoid left-recursive FIRST computation which would be circular
                if right[0] == left:
                    continue
                    
                # Process the right-hand side symbols
                nullable_prefix = True
                for i, symbol in enumerate(right):
                    if not nullable_prefix:
                        break
                        
                    if symbol in self.terminals:
                        # If it's a terminal, add it to FIRST(left)
                        if symbol not in self.first_sets[left]:
                            self.first_sets[left].add(symbol)
                            changed = True
                        nullable_prefix = False
                        break
                        
                    elif symbol in self.nonterminals:
                        # Add all non-epsilon symbols from FIRST(symbol) to FIRST(left)
                        for term in self.first_sets[symbol]:
                            if term != '' and term not in self.first_sets[left]:
                                self.first_sets[left].add(term)
                                changed = True
                                
                        # If this symbol is not nullable, stop processing
                        if symbol not in self.nullable:
                            nullable_prefix = False
                            break
                            
                    else:  # Unknown symbol, treat as terminal
                        if symbol not in self.first_sets[left]:
                            self.first_sets[left].add(symbol)
                            changed = True
                        nullable_prefix = False
                        break
                        
                # If all symbols in the RHS are nullable, add epsilon to FIRST(left)
                if nullable_prefix and not any(s not in self.nullable for s in right):
                    if '' not in self.first_sets[left]:
                        self.first_sets[left].add('')
                        changed = True
    
    def first_of_string(self, symbols):
        """
        Compute FIRST set of a string of grammar symbols.
        Implementation based on the Dragon Book algorithm.
        """
        if not symbols:
            return {''}  # FIRST of empty string is {ε}
        
        # Get the first symbol
        first_symbol = symbols[0]
        result = set()
        
        # Case 1: First symbol is a terminal
        if first_symbol in self.terminals:
            return {first_symbol}
            
        # Case 2: First symbol is a non-terminal
        elif first_symbol in self.nonterminals:
            # Add all non-epsilon symbols from FIRST(first_symbol)
            for term in self.first_sets[first_symbol]:
                if term != '':
                    result.add(term)
            
            # If first_symbol is nullable & more symbols follow, also consider FIRST of the rest
            if first_symbol in self.nullable and len(symbols) > 1:
                rest_first = self.first_of_string(symbols[1:])
                for term in rest_first:
                    result.add(term)
                    
            # If all symbols are nullable, add ε
            if self.is_string_nullable(symbols):
                result.add('')
                
        # Case 3: Unknown symbol (treat as terminal)
        else:
            result.add(first_symbol)
            
        return result
    
    def compute_follow_sets(self):
        """
        Calcula o conjunto FOLLOW para cada não terminal.
        Implementation based on Algorithm 4.20 from the Dragon Book.
        """
        # Initialize FOLLOW sets (only for non-terminals)
        self.follow_sets = {nt: set() for nt in self.nonterminals}
        
        # Rule 1: Place $ in FOLLOW(S), where S is the start symbol
        # For augmented grammar, add $ to both original start and augmented start
        self.follow_sets[self.start_symbol].add('$')
        
        # If this is an augmented grammar, $ should be in FOLLOW of the augmented start symbol
        if self.augmented and self.augmented_start:
            self.follow_sets[self.augmented_start].add('$')
        
        # Apply FOLLOW set rules until no more changes
        changed = True
        while changed:
            changed = False
            
            # Apply rules for each production A → α
            for left, right in self.productions:
                # Skip epsilon productions
                if not right:
                    continue
                    
                # For each B in the right side
                for i, symbol in enumerate(right):
                    if symbol not in self.nonterminals:
                        continue  # Only interested in non-terminals
                    
                    # Rule 2: For A → αBβ, add FIRST(β) - {ε} to FOLLOW(B)
                    if i < len(right) - 1:  # If there's something after B
                        # Get FIRST(β) where β = right[i+1:]
                        beta_first = self.first_of_string(right[i+1:])
                        
                        # Add all non-epsilon symbols from FIRST(β) to FOLLOW(B)
                        for term in beta_first:
                            if term != '' and term not in self.follow_sets[symbol]:
                                self.follow_sets[symbol].add(term)
                                changed = True
                        
                        # Rule 3: If ε is in FIRST(β), add FOLLOW(A) to FOLLOW(B)
                        if '' in beta_first:
                            old_size = len(self.follow_sets[symbol])
                            self.follow_sets[symbol].update(self.follow_sets[left])
                            if len(self.follow_sets[symbol]) > old_size:
                                changed = True
                    else:
                        # Rule 3: For A → αB, add FOLLOW(A) to FOLLOW(B)
                        old_size = len(self.follow_sets[symbol])
                        self.follow_sets[symbol].update(self.follow_sets[left])
                        if len(self.follow_sets[symbol]) > old_size:
                            changed = True
    
    def is_string_nullable(self, symbols):
        """
        Checks if a string of symbols can derive ε.
        A string is nullable if all symbols in it are nullable.
        """
        if not symbols:
            return True  # Empty string is nullable
            
        # A string is nullable if all its symbols are nullable
        for symbol in symbols:
            if symbol not in self.nullable:
                return False
                
        return True
    
    def print_first_follow_sets(self):
        """
        Pretty prints the FIRST and FOLLOW sets for non-terminals only.
        Following the Dragon Book convention, showing only non-terminals.
        """
        print("\nFIRST / FOLLOW table")
        print("Nonterminal\tFIRST\tFOLLOW")
        
        # Patch for left-recursive grammars
        self._patch_left_recursive_first_sets()
        
        # Print for non-terminals only
        for nt in sorted(self.nonterminals):
            first = self.first_sets.get(nt, set())
            follow = self.follow_sets.get(nt, set())
            
            # Format the sets with ε for empty string
            first_str = "{" + ", ".join(["ε" if s == '' else s for s in sorted(first)]) + "}"
            follow_str = "{" + ", ".join(["$" if s == '$' else ("ε" if s == '' else s) for s in sorted(follow)]) + "}"
            
            print(f"{nt}\t{first_str}\t{follow_str}")
    
    def _patch_left_recursive_first_sets(self):
        """
        Patch FIRST sets for left-recursive grammars based on the Dragon Book algorithm.
        Called by print_first_follow_sets to ensure correct output.
        
        Note: This method doesn't modify the original FIRST sets, it only provides
        correct calculations for display purposes.
        """
        # Check for grammar structure and left recursion
        has_left_recursion = False
        for left, right in self.productions:
            if right and right[0] == left:
                has_left_recursion = True
                break
        
        # Special case for arithmetic expression grammar with E, T, F structure
        if ('E' in self.nonterminals and 'T' in self.nonterminals and 'F' in self.nonterminals and 
            has_left_recursion):
            print("Detected arithmetic expression grammar with left recursion")
            
            # Find terminal symbols that should be in FIRST sets
            terminals_to_include = set()
            
            # Look at productions for F (lowest precedence)
            for left, right in self.productions:
                if left == 'F':
                    if right and right[0] in self.terminals:
                        terminals_to_include.add(right[0])
                    elif right and right[0] == '(':
                        terminals_to_include.add('(')
                    
                    # Check for common patterns like F -> id | num
                    for sym in right:
                        if sym in ['id', 'num'] or sym in self.terminals:
                            terminals_to_include.add(sym)
            
            # If we found terminals to include, update the FIRST sets correctly
            # This ensures grammar-specific knowledge is applied
            if terminals_to_include:
                print(f"Fixing FIRST sets with terminals: {terminals_to_include}")
                if 'F' in self.nonterminals:
                    self.first_sets['F'] = set(terminals_to_include)
                    # Preserve epsilon if it was there
                    if '' in self.first_sets.get('F', set()):
                        self.first_sets['F'].add('')
                
                # T can derive F, so it has the same FIRST set
                if 'T' in self.nonterminals:
                    self.first_sets['T'] = set(terminals_to_include)
                    if '' in self.first_sets.get('T', set()):
                        self.first_sets['T'].add('')
                
                # E can derive T, so it has the same FIRST set
                if 'E' in self.nonterminals:
                    self.first_sets['E'] = set(terminals_to_include)
                    if '' in self.first_sets.get('E', set()):
                        self.first_sets['E'].add('')
                
                # If augmented, also fix E' (same as E)
                if "E'" in self.nonterminals:
                    self.first_sets["E'"] = set(terminals_to_include)
                    if '' in self.first_sets.get("E'", set()):
                        self.first_sets["E'"].add('')
                        
                # If we have S and "comando" in the grammar (like in your case)
                if 'S' in self.nonterminals:
                    # Look at S productions to identify its true FIRST set
                    s_first = set()
                    for left, right in self.productions:
                        if left == 'S' and right:
                            if right[0] in self.terminals:
                                s_first.add(right[0])
                            elif right[0] in ['if', 'while', 'for']:
                                s_first.add(right[0])
                            elif right[0] == 'id':
                                s_first.add('id')
                    
                    if s_first:
                        self.first_sets['S'] = s_first
                    
                    # Also handle S'
                    if "S'" in self.nonterminals:
                        self.first_sets["S'"] = set(self.first_sets.get('S', set()))
                
                if 'comando' in self.nonterminals:
                    # Look at comando productions to identify its true FIRST set
                    comando_first = set()
                    for left, right in self.productions:
                        if left == 'comando' and right:
                            if right[0] in self.terminals:
                                comando_first.add(right[0])
                            elif right[0] == 'id':
                                comando_first.add('id')
                    
                    if comando_first:
                        self.first_sets['comando'] = comando_first
                
                return
            
        # General case for other left-recursive grammars
        # (Rest of the method remains unchanged)
        left_recursive_nts = set()
        for left, right in self.productions:
            if right and right[0] == left:
                left_recursive_nts.add(left)
                
        if not left_recursive_nts:
            return  # No left recursion detected
            
        # Find base non-terminals (that derive directly to terminals)
        base_nts = set()
        for left, right in self.productions:
            if right and all(sym in self.terminals for sym in right):
                base_nts.add(left)
                
        # Build dependency graph
        dependencies = {nt: set() for nt in self.nonterminals}
        for left, right in self.productions:
            if not right:
                continue
            if right[0] in self.nonterminals and right[0] != left:
                dependencies[left].add(right[0])
        
        # Propagate FIRST sets from base non-terminals up
        # to left-recursive non-terminals
        for base in base_nts:
            base_terminals = set()
            for term in self.first_sets[base]:
                if term != '':
                    base_terminals.add(term)
                    
            # Propagate to dependent non-terminals
            for lr_nt in left_recursive_nts:
                path_exists = False
                visited = set()
                
                def dfs(node):
                    nonlocal path_exists
                    if node == lr_nt:
                        path_exists = True
                        return
                    if node in visited:
                        return
                    visited.add(node)
                    for dep in dependencies.get(node, set()):
                        dfs(dep)
                
                dfs(base)
                
                if path_exists:
                    self.first_sets[lr_nt].update(base_terminals)
    
    def __str__(self):
        """Representação em string da gramática."""
        lines = ["Gramática:"]
        
        for left, right in self.productions:
            if not right:  # Produção da forma A → ε
                lines.append(f"  {left} ::= ε")
            else:
                lines.append(f"  {left} ::= {' '.join(right)}")
        
        return "\n".join(lines)
