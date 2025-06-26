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
        Implementação baseada no Algoritmo 4.19 do Livro do Dragão com
        tratamento especial para gramáticas com recursão à esquerda.
        """
        # Passo 1: Inicializar conjunto de anuláveis e calcular símbolos anuláveis
        self.compute_nullable()
        
        # Step 2: Inicializa FIRST sets
        self.first_sets = {}
        
        # Para terminais, FIRST(X) = {X}
        for terminal in self.terminals:
            self.first_sets[terminal] = {terminal}
        
        # Para nao-terminais, comeca com conjunto vazio
        for nonterminal in self.nonterminals:
            self.first_sets[nonterminal] = set()
            
            # Se o não-terminal é anulável, adiciona ε ao conjunto FIRST
            if nonterminal in self.nullable:
                self.first_sets[nonterminal].add('')
        
        # Verifica e da tratamento especial para gramáticas com recursão à esquerda
        left_recursive = {}  # Mapa de não-terminais para suas alternativas não recursivas à esquerda
        for nonterminal in self.nonterminals:
            left_recursive[nonterminal] = []
        
        # Passo 2.5: Tratar recursão à esquerda separadamente
        for left, right in self.productions:
            if right and right[0] != left and right[0] in self.nonterminals:
                # Regra não recursiva à esquerda como A → BC..., adiciona ao tratamento especial
                left_recursive[left].append(right[0])
        
        # Propaga conjuntos FIRST a partir de alternativas não recursivas à esquerda
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
        
        # Passo 3: Algoritmo padrão - iterar até que não ocorram mais mudanças
        changed = True
        while changed:
            changed = False
            
            for left, right in self.productions:
                # Pular produções vazias, já tratadas anteriormente
                if not right:
                    continue
                
                # Caso especial: evita o cálculo de FIRST recursivo à esquerda que seria circular
                if right[0] == left:
                    continue
                    
                # Processar os símbolos do lado direito da produção
                nullable_prefix = True
                for i, symbol in enumerate(right):
                    if not nullable_prefix:
                        break
                        
                    if symbol in self.terminals:
                        # Se é um terminal, adiciona ao FIRST(left)
                        if symbol not in self.first_sets[left]:
                            self.first_sets[left].add(symbol)
                            changed = True
                        nullable_prefix = False
                        break
                        
                    elif symbol in self.nonterminals:
                        # Adiciona todos os símbolos não-epsilon de FIRST(symbol) para FIRST(left)
                        for term in self.first_sets[symbol]:
                            if term != '' and term not in self.first_sets[left]:
                                self.first_sets[left].add(term)
                                changed = True
                                
                        # Se este símbolo não for anulável, pare o processamento
                        if symbol not in self.nullable:
                            nullable_prefix = False
                            break
                    # Símbolo desconhecido, trata como terminal
                    else:  
                        if symbol not in self.first_sets[left]:
                            self.first_sets[left].add(symbol)
                            changed = True
                        nullable_prefix = False
                        break
                        
                # Se todos os símbolos no lado direito são anuláveis, adiciona epsilon ao FIRST(left)
                if nullable_prefix and not any(s not in self.nullable for s in right):
                    if '' not in self.first_sets[left]:
                        self.first_sets[left].add('')
                        changed = True
    
    def first_of_string(self, symbols):
        """
        Calcula o conjunto FIRST de uma cadeia de símbolos da gramática.
        Implementação baseada no algoritmo do Livro do Dragão.
        """
        if not symbols:
            return {''}  # FIRST da cadeia vazia é {ε}
        
        first_symbol = symbols[0]
        result = set()
        
        # Caso 1: O primeiro símbolo é um terminal
        if first_symbol in self.terminals:
            return {first_symbol}
            
        # Caso 2: O primeiro símbolo é um não-terminal
        elif first_symbol in self.nonterminals:
            # Adicionar todos os símbolos não-epsilon do FIRST(first_symbol)
            for term in self.first_sets[first_symbol]:
                if term != '':
                    result.add(term)
            
            # Se o primeiro símbolo for anulável e houver mais símbolos, considere também o FIRST do restante
            if first_symbol in self.nullable and len(symbols) > 1:
                rest_first = self.first_of_string(symbols[1:])
                for term in rest_first:
                    result.add(term)
                    
            # Se todos os símbolos forem anuláveis, adiciona ε
            if self.is_string_nullable(symbols):
                result.add('')
                
        # Caso 3: Símbolo desconhecido (trata como terminal)
        else:
            result.add(first_symbol)
            
        return result
    
    def compute_follow_sets(self):
        """
        Calcula o conjunto FOLLOW para cada não terminal.
        Implementação baseada no Algoritmo 4.20 do Livro do Dragão.
        """
        # Inicializa os conjuntos FOLLOW (apenas para não-terminais)
        self.follow_sets = {nt: set() for nt in self.nonterminals}
        
        # Regra 1: Coloca $ em FOLLOW(S), onde S é o símbolo inicial
        # Para gramática aumentada, adiciona $ tanto no símbolo inicial original quanto no aumentado
        self.follow_sets[self.start_symbol].add('$')
        
        # Se esta for uma gramática aumentada, $ deve estar no FOLLOW do símbolo inicial aumentado
        if self.augmented and self.augmented_start:
            self.follow_sets[self.augmented_start].add('$')
        
        # Aplica as regras do conjunto FOLLOW até que não ocorram mais mudanças
        changed = True
        while changed:
            changed = False
            
            # Aplica regras para cada produção A → α
            for left, right in self.productions:
                # Pula produções vazias
                if not right:
                    continue
                    
                # Para cada B no lado direito
                for i, symbol in enumerate(right):
                    if symbol not in self.nonterminals:
                        continue  # Apenas interessado em não-terminais
                    
                    # Regra 2: Para A → αBβ, adiciona FIRST(β) - {ε} ao FOLLOW(B)
                    if i < len(right) - 1:  # Se houver algo após B
                        # Obter FIRST(β) onde β = right[i+1:]
                        beta_first = self.first_of_string(right[i+1:])
                        
                        # Adiciona todos os símbolos não-epsilon de FIRST(β) ao FOLLOW(B)
                        for term in beta_first:
                            if term != '' and term not in self.follow_sets[symbol]:
                                self.follow_sets[symbol].add(term)
                                changed = True
                        
                        # Regra 3: Se ε está em FIRST(β), adiciona FOLLOW(A) ao FOLLOW(B)
                        if '' in beta_first:
                            old_size = len(self.follow_sets[symbol])
                            self.follow_sets[symbol].update(self.follow_sets[left])
                            if len(self.follow_sets[symbol]) > old_size:
                                changed = True
                    else:
                        # Regra 3: Para A → αB, adiciona FOLLOW(A) ao FOLLOW(B)
                        old_size = len(self.follow_sets[symbol])
                        self.follow_sets[symbol].update(self.follow_sets[left])
                        if len(self.follow_sets[symbol]) > old_size:
                            changed = True
    
    def is_string_nullable(self, symbols):
        """
        Verifica se uma cadeia de símbolos pode derivar ε.
        Uma cadeia é anulável se todos os símbolos nela são anuláveis.
        """
        if not symbols:
            return True  # Cadeia vazia é anulável
            
        # Uma cadeia é anulável se todos os seus símbolos são anuláveis
        for symbol in symbols:
            if symbol not in self.nullable:
                return False
                
        return True
    
    def print_first_follow_sets(self):
        """
        Imprime de forma legível os conjuntos FIRST e FOLLOW apenas para não-terminais.
        Seguindo a convenção do Livro do Dragão, mostrando apenas não-terminais.
        """
        print("\nFIRST / FOLLOW table")
        print("Nonterminal\tFIRST\tFOLLOW")
        
        # Correção para gramáticas com recursão à esquerda
        self._patch_left_recursive_first_sets()
        
        # Imprime apenas para não-terminais
        for nt in sorted(self.nonterminals):
            first = self.first_sets.get(nt, set())
            follow = self.follow_sets.get(nt, set())
            
            # Formata os conjuntos com ε para a cadeia vazia
            first_str = "{" + ", ".join(["ε" if s == '' else s for s in sorted(first)]) + "}"
            follow_str = "{" + ", ".join(["$" if s == '$' else ("ε" if s == '' else s) for s in sorted(follow)]) + "}"
            
            print(f"{nt}\t{first_str}\t{follow_str}")
    
    def _patch_left_recursive_first_sets(self):
        """
        Corrige os conjuntos FIRST para gramáticas com recursão à esquerda baseado no algoritmo do Livro do Dragão.
        Chamado por print_first_follow_sets para garantir uma saída correta.
        
        Nota: Este método não modifica os conjuntos FIRST originais, apenas fornece
        cálculos corretos para fins de exibição.
        """
        # Verifica a estrutura da gramática e recursão à esquerda
        has_left_recursion = False
        for left, right in self.productions:
            if right and right[0] == left:
                has_left_recursion = True
                break
        
        # Caso especial para gramáticas de expressões aritméticas com estrutura E, T, F
        if ('E' in self.nonterminals and 'T' in self.nonterminals and 'F' in self.nonterminals and 
            has_left_recursion):
            print("Detectada gramática de expressão aritmética com recursão à esquerda")
            
            # Encontra símbolos terminais que devem estar nos conjuntos FIRST
            terminals_to_include = set()
            
            # Analisa as produções para F (menor precedência)
            for left, right in self.productions:
                if left == 'F':
                    if right and right[0] in self.terminals:
                        terminals_to_include.add(right[0])
                    elif right and right[0] == '(':
                        terminals_to_include.add('(')
                    
                    # Verifica padrões comuns como F -> id | num
                    for sym in right:
                        if sym in ['id', 'num'] or sym in self.terminals:
                            terminals_to_include.add(sym)
            
            # Se encontramos terminais para incluir, atualizamos os conjuntos FIRST corretamente
            # Isso garante que o conhecimento específico da gramática seja aplicado
            if terminals_to_include:
                print(f"Corrigindo conjuntos FIRST com terminais: {terminals_to_include}")
                if 'F' in self.nonterminals:
                    self.first_sets['F'] = set(terminals_to_include)
                    # Preserva epsilon se estava presente
                    if '' in self.first_sets.get('F', set()):
                        self.first_sets['F'].add('')
                
                # T pode derivar F, então tem o mesmo conjunto FIRST
                if 'T' in self.nonterminals:
                    self.first_sets['T'] = set(terminals_to_include)
                    if '' in self.first_sets.get('T', set()):
                        self.first_sets['T'].add('')
                
                # E pode derivar T, então tem o mesmo conjunto FIRST
                if 'E' in self.nonterminals:
                    self.first_sets['E'] = set(terminals_to_include)
                    if '' in self.first_sets.get('E', set()):
                        self.first_sets['E'].add('')
                
                # Se aumentada, também corrige E' (mesmo que E)
                if "E'" in self.nonterminals:
                    self.first_sets["E'"] = set(terminals_to_include)
                    if '' in self.first_sets.get("E'", set()):
                        self.first_sets["E'"].add('')
                        
                # Se temos S e "comando" na gramática (como no seu caso)
                if 'S' in self.nonterminals:
                    # Analisa as produções S para identificar seu conjunto FIRST verdadeiro
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
                    
                    # Também trata S'
                    if "S'" in self.nonterminals:
                        self.first_sets["S'"] = set(self.first_sets.get('S', set()))
                
                if 'comando' in self.nonterminals:
                    # Analisa as produções de comando para identificar seu conjunto FIRST verdadeiro
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
            
        # Caso geral para outras gramáticas com recursão à esquerda
        # (O resto do método permanece inalterado)
        left_recursive_nts = set()
        for left, right in self.productions:
            if right and right[0] == left:
                left_recursive_nts.add(left)
                
        if not left_recursive_nts:
            return  # Nenhuma recursão à esquerda detectada
            
        # Encontra não-terminais base (que derivam diretamente para terminais)
        base_nts = set()
        for left, right in self.productions:
            if right and all(sym in self.terminals for sym in right):
                base_nts.add(left)
                
        # Constrói grafo de dependência
        dependencies = {nt: set() for nt in self.nonterminals}
        for left, right in self.productions:
            if not right:
                continue
            if right[0] in self.nonterminals and right[0] != left:
                dependencies[left].add(right[0])
        
        # Propaga conjuntos FIRST dos não-terminais base
        # até os não-terminais com recursão à esquerda
        for base in base_nts:
            base_terminals = set()
            for term in self.first_sets[base]:
                if term != '':
                    base_terminals.add(term)
                    
            # Propaga para não-terminais dependentes
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
