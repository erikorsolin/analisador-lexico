"""
Implementação do gerador de analisadores sintáticos SLR.
"""
from grammar import Grammar
from collections import deque, defaultdict
import json
import os

class LR0Item:
    """
    Representa um item LR(0), que é uma produção com um marcador de posição (•).
    """
    def __init__(self, left, right, dot_position):
        self.left = left  # Lado esquerdo da produção
        self.right = right  # Lado direito da produção (lista de símbolos)
        self.dot_position = dot_position  # Posição do marcador •
        
    def __str__(self):
        """Representação em string do item LR(0)."""
        result = f"{self.left} → "
        for i, symbol in enumerate(self.right):
            if i == self.dot_position:
                result += "• "
            result += f"{symbol} "
        
        if self.dot_position == len(self.right):
            result += "•"
        
        return result.rstrip()
    
    def __eq__(self, other):
        if not isinstance(other, LR0Item):
            return False
        return (self.left == other.left and
                self.right == other.right and
                self.dot_position == other.dot_position)
    
    def __hash__(self):
        return hash((self.left, tuple(self.right), self.dot_position))
        
    def next_symbol(self):
        """Retorna o símbolo após o marcador •, ou None se • estiver no final."""
        if self.dot_position < len(self.right):
            return self.right[self.dot_position]
        return None
    
    def is_complete(self):
        """Verifica se o item é completo (• está no final)."""
        return self.dot_position == len(self.right)
    
    def advance_dot(self):
        """Retorna um novo item com o marcador • avançado uma posição."""
        if self.dot_position < len(self.right):
            return LR0Item(self.left, self.right, self.dot_position + 1)
        return None


class SLRParser:
    """
    Implementação do algoritmo de geração de tabelas de análise sintática SLR.
    """
    def __init__(self):
        self.grammar = None
        self.states = []  # Estados do autômato LR(0)
        self.state_map = {}  # Mapeamento de conjuntos de itens para números de estados
        self.action_table = {}  # Tabela ACTION
        self.goto_table = {}  # Tabela GOTO
        
    def load_grammar(self, grammar_file):
        """Carrega a gramática a partir de um arquivo."""
        self.grammar = Grammar()
        return self.grammar.load_from_file(grammar_file)
    
    def generate_parser(self):
        """Gera as tabelas de análise sintática SLR."""
        if not self.grammar:
            print("Erro: Gramática não carregada")
            return False
        
        print("Calculando conjuntos NULLABLE, FIRST e FOLLOW...")
        # Preparar a gramática
        self.grammar.augment()
        self.grammar.compute_nullable()
        self.grammar.compute_first_sets()
        self.grammar.compute_follow_sets()
        
        print("Construindo coleção canônica de itens LR(0)...")
        # Construir a coleção canônica de itens LR(0)
        self._build_canonical_collection()
        
        print("Gerando tabelas ACTION e GOTO...")
        # Construir as tabelas ACTION e GOTO
        self._build_parsing_table()
        
        # Verificar conflitos
        conflicts = self._check_conflicts()
        if conflicts > 0:
            print(f"Aviso: {conflicts} conflitos encontrados na tabela de análise.")
            print("A gramática pode não ser SLR(1).")
            return False
        
        return True
    
    def closure(self, items):
        """
        Calcula o fecho de um conjunto de itens LR(0).
        """
        closure_set = set(items)
        changed = True
        
        while changed:
            changed = False
            new_items = set()
            
            for item in closure_set:
                # Se o símbolo após o • é um não terminal
                next_sym = item.next_symbol()
                if next_sym in self.grammar.nonterminals:
                    # Para cada produção B → γ, adicionar B → •γ
                    for left, right in self.grammar.productions:
                        if left == next_sym:
                            new_item = LR0Item(left, right, 0)
                            if new_item not in closure_set:
                                new_items.add(new_item)
                                changed = True
            
            closure_set.update(new_items)
        
        return frozenset(closure_set)
    
    def goto(self, items, symbol):
        """
        Calcula o conjunto de itens alcançáveis a partir de 'items'
        usando transições com o símbolo dado.
        """
        goto_set = set()
        
        for item in items:
            if item.next_symbol() == symbol:
                advanced = item.advance_dot()
                if advanced:
                    goto_set.add(advanced)
        
        if goto_set:
            return self.closure(goto_set)
        return frozenset()
    
    def _build_canonical_collection(self):
        """
        Constrói a coleção canônica de conjuntos de itens LR(0).
        """
        # Criar o primeiro conjunto de itens (estado 0)
        initial_item = LR0Item(self.grammar.augmented_start, [self.grammar.start_symbol], 0)
        initial_set = self.closure({initial_item})
        
        # Inicializar estruturas de dados
        self.states = [initial_set]
        self.state_map = {initial_set: 0}
        self.goto_transitions = defaultdict(dict)
        
        # Usar BFS para construir a coleção canônica
        queue = deque([initial_set])
        processed = {initial_set}
        
        while queue:
            current_set = queue.popleft()
            current_state = self.state_map[current_set]
            
            # Para cada símbolo da gramática
            all_symbols = self.grammar.terminals | self.grammar.nonterminals
            for symbol in all_symbols:
                next_set = self.goto(current_set, symbol)
                
                if next_set and next_set not in processed:
                    # Novo estado encontrado
                    next_state = len(self.states)
                    self.states.append(next_set)
                    self.state_map[next_set] = next_state
                    queue.append(next_set)
                    processed.add(next_set)
                    
                    # Adicionar transição
                    self.goto_transitions[current_state][symbol] = next_state
                elif next_set and next_set in self.state_map:
                    # Estado existente
                    next_state = self.state_map[next_set]
                    self.goto_transitions[current_state][symbol] = next_state
        
        print(f"Coleção canônica construída com {len(self.states)} estados.")
    
    def _build_parsing_table(self):
        """
        Constrói as tabelas ACTION e GOTO para o analisador SLR.
        """
        self.action_table = {}
        self.goto_table = {}
        self.terminals_with_end = self.grammar.terminals | {'$'}
        
        # Mapear os simbolos terminais para seus nomes corretos na tabela
        terminal_mapping = {}
        for terminal in self.grammar.terminals:
            # Mapeamos 'id' como o próprio 'id', importante para o analisador léxico
            terminal_mapping[terminal] = terminal
        
        for state_idx, state in enumerate(self.states):
            self.action_table[state_idx] = {}
            self.goto_table[state_idx] = {}
            
            # Para cada item no estado
            for item in state:
                # Caso 1: [A → α • a β] (shift)
                if not item.is_complete():
                    next_sym = item.next_symbol()
                    if next_sym in self.grammar.terminals:
                        if state_idx in self.goto_transitions and next_sym in self.goto_transitions[state_idx]:
                            next_state = self.goto_transitions[state_idx][next_sym]
                            terminal_key = terminal_mapping.get(next_sym, next_sym)
                            self.action_table[state_idx][terminal_key] = ('shift', next_state)
                
                # Caso 2: [A → α •] (reduce)
                elif item.is_complete():
                    # Exceção para o item [S' → S •]
                    if item.left == self.grammar.augmented_start and len(item.right) == 1 and item.right[0] == self.grammar.start_symbol:
                        self.action_table[state_idx]['$'] = ('accept', None)
                    else:
                        # Para cada terminal a em FOLLOW(A), ACTION[i,a] = "reduce A → α"
                        for terminal in self.grammar.follow_sets[item.left]:
                            # Encontrar o índice da produção
                            production_idx = None
                            for idx, (left, right) in enumerate(self.grammar.productions):
                                if left == item.left and right == item.right:
                                    production_idx = idx
                                    break
                            
                            if production_idx is not None:
                                terminal_key = terminal_mapping.get(terminal, terminal)
                                self.action_table[state_idx][terminal_key] = ('reduce', production_idx)
            
            # Transições GOTO para não terminais
            if state_idx in self.goto_transitions:
                for symbol, next_state in self.goto_transitions[state_idx].items():
                    if symbol in self.grammar.nonterminals:
                        self.goto_table[state_idx][symbol] = next_state
    
    def _check_conflicts(self):
        """
        Verifica conflitos na tabela de análise.
        Retorna o número de conflitos encontrados.
        """
        conflicts = 0
        for state, actions in self.action_table.items():
            for terminal, action in actions.items():
                # Verificar transições duplicadas para o mesmo símbolo
                for other_terminal, other_action in actions.items():
                    if terminal == other_terminal and action != other_action:
                        conflicts += 1
                        print(f"Conflito no estado {state} para o símbolo '{terminal}':")
                        print(f"  {action} vs {other_action}")
        return conflicts
    
    def save_tables(self, output_file):
        """
        Salva as tabelas ACTION e GOTO em um arquivo JSON.
        """
        # Converter as tabelas para um formato serializável
        action_dict = {}
        for state, actions in self.action_table.items():
            action_dict[state] = {sym: list(act) for sym, act in actions.items()}
            
        goto_dict = {}
        for state, gotos in self.goto_table.items():
            goto_dict[state] = gotos
            
        # Incluir informações sobre a gramática
        productions_data = []
        for left, right in self.grammar.productions:
            productions_data.append({
                "left": left,
                "right": right
            })
        # Include FIRST and FOLLOW sets but only for non-terminals
        first_sets_serializable = {}
        for nt in self.grammar.nonterminals:
            if nt in self.grammar.first_sets:
                first_sets_serializable[nt] = list(self.grammar.first_sets[nt])
            
        follow_sets_serializable = {}
        for nt in self.grammar.nonterminals:
            if nt in self.grammar.follow_sets:
                follow_sets_serializable[nt] = list(self.grammar.follow_sets[nt])
            
        data = {
            "action": action_dict,
            "goto": goto_dict,
            "terminals": list(self.grammar.terminals),
            "nonterminals": list(self.grammar.nonterminals),
            "start_symbol": self.grammar.start_symbol,
            "augmented_start": self.grammar.augmented_start,
            "productions": productions_data,
            "first_sets": first_sets_serializable,
            "follow_sets": follow_sets_serializable
        }
        
        try:
            # Garantir que o diretório exista
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2)
            print(f"Tabelas salvas em '{output_file}'")
            return True
        except Exception as e:
            print(f"Erro ao salvar tabelas: {str(e)}")
            return False
    
    def print_info(self):
        """
        Imprime informações sobre os estados e as tabelas de análise.
        """
        print("\nEstados do Autômato LR(0):")
        for i, state in enumerate(self.states):
            print(f"\nEstado {i}:")
            for item in sorted(state, key=str):
                print(f"  {item}")
        
        # Print FIRST and FOLLOW sets using the grammar's pretty print method
        self.grammar.print_first_follow_sets()
        
        # Imprimir tabela no formato LR
        print("\nLR table")
        print("State\tACTION\tGOTO")
        
        # Cabeçalho ACTION (terminais + $)
        action_headers = sorted(self.grammar.terminals) + ['$']
        
        # Cabeçalho GOTO (não-terminais)
        goto_headers = sorted(self.grammar.nonterminals)
        
        # Linha de cabeçalho completa
        header = "\t"
        for h in action_headers:
            header += f"{h}\t"
        for h in goto_headers:
            header += f"{h}\t"
        print(header)
        
        # Percorrer todos os estados
        for state in range(len(self.states)):
            row = f"{state}\t"
            
            # ACTION - para cada terminal
            for terminal in action_headers:
                if state in self.action_table and terminal in self.action_table[state]:
                    action = self.action_table[state][terminal]
                    if action[0] == 'shift':
                        row += f"s{action[1]}\t"
                    elif action[0] == 'reduce':
                        row += f"r{action[1]}\t"
                    elif action[0] == 'accept':
                        row += f"acc\t"
                else:
                    row += f" \t"
            
            # GOTO - para cada não-terminal
            for nonterm in goto_headers:
                if state in self.goto_table and nonterm in self.goto_table[state]:
                    row += f"{self.goto_table[state][nonterm]}\t"
                else:
                    row += f" \t"
                    
            print(row)
