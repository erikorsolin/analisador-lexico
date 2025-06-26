"""
Implementação do analisador sintático SLR.
"""
import json

class SLRParser:
    """
    Analisador sintático SLR que utiliza as tabelas de análise geradas.
    """
    def __init__(self):
        self.action_table = {}  # Tabela ACTION
        self.goto_table = {}  # Tabela GOTO
        self.productions = []  # Produções da gramática
        self.terminals = []  # Símbolos terminais
        self.nonterminals = []  # Símbolos não terminais
        self.start_symbol = None  # Símbolo inicial
        self.augmented_start = None  # Símbolo inicial aumentado
    
    def load_tables(self, tables_file):
        """
        Carrega as tabelas de análise a partir de um arquivo JSON.
        """
        try:
            with open(tables_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Carregar tabela ACTION
            self.action_table = {}
            for state, actions in data['action'].items():
                state_idx = int(state)
                self.action_table[state_idx] = {}
                for symbol, action in actions.items():
                    self.action_table[state_idx][symbol] = tuple(action)
            
            # Carregar tabela GOTO
            self.goto_table = {}
            for state, gotos in data['goto'].items():
                state_idx = int(state)
                self.goto_table[state_idx] = {}
                for symbol, goto_state in gotos.items():
                    self.goto_table[state_idx][symbol] = goto_state
            
            # Carregar informações da gramática
            self.terminals = data['terminals']
            self.nonterminals = data['nonterminals']
            self.start_symbol = data['start_symbol']
            self.augmented_start = data['augmented_start']
            
            # Carregar produções
            self.productions = []
            for prod in data['productions']:
                self.productions.append((prod['left'], prod['right']))
            
            print(f"Tabelas de análise carregadas com sucesso.")
            return True
        except FileNotFoundError:
            print(f"Erro: Arquivo {tables_file} não encontrado.")
            return False
        except Exception as e:
            print(f"Erro ao carregar tabelas: {str(e)}")
            return False
    
    def parse(self, tokens, debug=False):
        """
        Analisa uma sequência de tokens usando o algoritmo LR.
        Retorna True se a análise for bem-sucedida, False caso contrário.
        """
        # Adicionar marcador de fim ($)
        tokens = tokens + ["$"]

        stack = [0]
        token_index = 0

        if debug:
            print("\ntokens:", tokens)
            print("Início da análise sintática:")
            print(f"{'Pilha':30} {'Entrada':30} {'Ação'}")

        while True:
            current_state = stack[-1]
            current_token = tokens[token_index]  # Agora o token já é o símbolo que o parser espera (ex: 'id', '+', '(', ')', etc)

            if debug:
                stack_str = " ".join(str(s) for s in stack)
                input_str = " ".join(tokens[token_index:])
                print(f"{stack_str:30}  {input_str:30}  ", end="")

            # Verificar ação
            if current_state in self.action_table and current_token in self.action_table[current_state]:
                action = self.action_table[current_state][current_token]
                action_type, action_value = action

                if action_type == 'shift':
                    stack.append(current_token)
                    stack.append(action_value)
                    token_index += 1
                    if debug:
                        print(f"Shift {action_value}")

                elif action_type == 'reduce':
                    production = self.productions[action_value]
                    left, right = production

                    num_to_pop = 2 * len(right)
                    if num_to_pop > 0:
                        stack = stack[:-num_to_pop]

                    stack.append(left)

                    top_state = stack[-2]
                    if top_state in self.goto_table and left in self.goto_table[top_state]:
                        goto_state = self.goto_table[top_state][left]
                        stack.append(goto_state)
                    else:
                        if debug:
                            print(f"Erro: Não há transição GOTO[{top_state}, {left}]")
                        return False

                    if debug:
                        prod_str = f"{left} → {' '.join(right) if right else 'ε'}"
                        print(f"Reduce {action_value}: {prod_str}")

                elif action_type == 'accept':
                    if debug:
                        print("Accept - Análise concluída com sucesso")
                    return True
            else:
                if debug:
                    print(f"Erro de sintaxe: não há ação definida para o estado {current_state} e símbolo '{current_token}'")
                    print(f"Token atual: '{current_token}'")
                    print(f"Ações disponíveis para o estado {current_state}: {self.action_table.get(current_state, {})}")
                    print(f"Tokens esperados: {list(self.action_table.get(current_state, {}).keys())}")
                return False
    
    def _extract_token_symbol(self, token):
        """
        Extrai o símbolo do token para uso na análise sintática.
        """
        # Para o símbolo de fim
        if token == "$":
            return token
        
        # Formatos esperados:
        # 1. <id, índice>
        # 2. <lexema, PR>
        # 3. <lexema, padrão>
        
        try:
            # Remover < e > e dividir em partes
            token = token.strip("<>")
            parts = token.split(",", 1)
            
            if len(parts) != 2:
                raise ValueError(f"Formato de token inválido: {token}")
            
            token_type = parts[0].strip()
            token_value = parts[1].strip()
            
            # Para identificadores, retornar 'id'
            if token_type == 'id':
                return 'id'
                
            # Para números, retornar 'num'
            if token_value == 'num':
                return 'num'
            
            # Para palavras reservadas, o lexema é o símbolo
            if token_value == 'PR':
                return token_type
            
            # Para operadores, o lexema é o símbolo (+, -, *, /)
            if token_value == 'op':
                return token_type
                
            # Para operadores específicos, verificar pelo valor
            if token_value.strip() in ['+', '-', '*', '/', '(', ')']:
                return token_value.strip()
            
            # Para outros tokens, tentar usar o lexema como o símbolo na gramática
            return token_type
                
        except Exception as e:
            print(f"Erro ao extrair símbolo do token '{token}': {str(e)}")
            return token  # Retornar o token original em caso de erro
    
    def print_tables(self):
        """
        Imprime as tabelas de análise no formato LR(0).
        """
        print("\nLR table")
        print("State\tACTION\tGOTO")
        
        # Cabeçalho ACTION (terminais + $)
        action_headers = sorted(self.terminals) + ['$']
        
        # Cabeçalho GOTO (não-terminais)
        goto_headers = sorted(self.nonterminals)
        
        # Linha de cabeçalho completa
        header = "\t"
        for h in action_headers:
            header += f"{h}\t"
        for h in goto_headers:
            header += f"{h}\t"
        print(header)
        
        # Percorrer todos os estados
        all_states = sorted(set(self.action_table.keys()) | set(self.goto_table.keys()))
        for state in all_states:
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
