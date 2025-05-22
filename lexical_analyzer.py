"""
Arquivo principal do analisador léxico.
Contém a interface para carregar expressões regulares, gerar AFDs, e analisar textos.
"""
import sys
from collections import defaultdict
from re_to_afnd import RegexToAFND
from afnd_to_afd import determinize
from automaton import Automaton
from symbol_table import SymbolTable
from token_analyzer import TokenAnalyzer

class LexicalAnalyzer:
    def __init__(self):
        self.automata = []
        self.patterns = []
        self.combined_automaton = None
        self.symbol_table = SymbolTable()
        self.token_analyzer = None
        
    # Ajuste no método load_regex_definitions
    def load_regex_definitions(self, filename):
        """Carrega as definições de expressões regulares do arquivo."""
        try:
            with open(filename, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':', 1)
                    if len(parts) != 2:
                        print(f"Aviso: linha inválida no arquivo de definições: {line}")
                        continue
                    
                    pattern_name = parts[0].strip()
                    regex = parts[1].strip()
                    
                    if pattern_name and regex:
                        print(f"Adicionando padrão: {pattern_name} com regex: {regex}")
                        try:
                            self.add_pattern(pattern_name, regex)
                        except Exception as e:
                            print(f"Erro ao adicionar padrão {pattern_name}: {str(e)}")
                            return False
                
                if not self.patterns:
                    print("Nenhum padrão válido encontrado no arquivo.")
                    return False
                
                print(f"Definições de expressões regulares carregadas de {filename}")
                return True
        except FileNotFoundError:
            print(f"Erro: Arquivo {filename} não encontrado.")
            return False
        except Exception as e:
            print(f"Erro ao carregar definições: {str(e)}")
            return False
    
    def add_pattern(self, pattern_name, regex):
        """Adiciona um padrão e sua expressão regular."""
        print(f"Adicionando padrão: {pattern_name} com regex: {regex}")
        converter = RegexToAFND()
        automaton = converter.convert(regex)
        automaton.pattern = pattern_name
        
        self.patterns.append(pattern_name)
        self.automata.append(automaton)
        return automaton
    
    def combine_automata(self):
        """Combina todos os autômatos via ε-transições."""
        if not self.automata:
            print("Nenhum autômato para combinar.")
            return None
        
        print("Combinando automatos...")
        combined = Automaton()
        combined.states = {0}  # Estado inicial do autômato combinado
        combined.initial_state = 0
        combined.final_states = set()
        combined.alphabet = set()
        combined.transitions = defaultdict(lambda: defaultdict(set))
        
        # Mapeamento de estados originais para estados no novo autômato
        state_mapping = {}
        next_state = 1
        
        # Adicionar ε-transição do estado inicial para cada autômato
        for idx, automaton in enumerate(self.automata):
            pattern = self.patterns[idx]
            
            # Mapear o estado inicial do autômato
            state_mapping[(id(automaton), automaton.initial_state)] = next_state
            
            # Adicionar ε-transição
            combined.add_transition(0, '&', next_state)
            
            # Atualizar próximo estado disponível
            next_state += 1
        
        # Adicionar todos os estados e transições de cada autômato
        for idx, automaton in enumerate(self.automata):
            pattern = self.patterns[idx]
            
            # Adicionar estados
            for state in automaton.states:
                if (id(automaton), state) not in state_mapping:
                    state_mapping[(id(automaton), state)] = next_state
                    next_state += 1
            
            # Adicionar transições
            for from_state, transitions in automaton.transitions.items():
                mapped_from = state_mapping[(id(automaton), from_state)]
                
                for symbol, to_states in transitions.items():
                    for to_state in to_states:
                        mapped_to = state_mapping[(id(automaton), to_state)]
                        combined.add_transition(mapped_from, symbol, mapped_to)
            
            # Adicionar estados finais com informação do padrão
            for final_state in automaton.final_states:
                mapped_final = state_mapping[(id(automaton), final_state)]
                combined.final_states.add((mapped_final, pattern))
        
        combined.states = set(range(next_state))
        self.combined_automaton = combined
        return combined
    
    def generate_lexical_analyzer(self):
        """Gera o analisador léxico a partir dos autômatos combinados."""
        if not self.combined_automaton:
            self.combine_automata()
        
        if not self.combined_automaton:
            print("Falha ao gerar o analisador léxico.")
            return False
        
        print("Determinizando o autômato combinado...")
        self.determinized_automaton = determinize(self.combined_automaton)
        
        print("Criando analisador de tokens...")
        self.token_analyzer = TokenAnalyzer(self.determinized_automaton, self.symbol_table)
        
        return True
    
    def analyze_file(self, input_filename, output_filename=None):
        """Analisa um arquivo de entrada e gera os tokens."""
        if not self.token_analyzer:
            print("Analisador léxico não foi gerado. Execute generate_lexical_analyzer primeiro.")
            return False
        
        try:
            with open(input_filename, 'r') as file:
                text = file.read()
                
            tokens = self.token_analyzer.analyze(text)
            
            if output_filename:
                with open(output_filename, 'w') as out_file:
                    for token in tokens:
                        out_file.write(f"{token}\n")
            
            return tokens
        except FileNotFoundError:
            print(f"Erro: Arquivo {input_filename} não encontrado.")
            return []
        except Exception as e:
            print(f"Erro ao analisar arquivo: {str(e)}")
            return []
    
    def print_automaton(self, automaton, title="Autômato"):
        """Imprime um autômato na forma de tabela."""
        print(f"\n{title}:")
        print(f"Número de estados: {len(automaton.states)}")
        print(f"Estado inicial: {automaton.initial_state}")
        
        # Imprimir estados finais com seus padrões associados
        if isinstance(automaton.final_states, set) and all(isinstance(fs, tuple) for fs in automaton.final_states):
            final_states_str = ", ".join([f"{state}({pattern})" for state, pattern in automaton.final_states])
            print(f"Estados finais: {final_states_str}")
        else:
            print(f"Estados finais: {', '.join(map(str, automaton.final_states))}")
        
        print(f"Alfabeto: {', '.join(sorted(automaton.alphabet - {'&'}))}")
        
        print("\nTabela de Transições:")
        # Criar cabeçalho da tabela
        headers = ["Estado"] + sorted(automaton.alphabet)
        header_format = "{:<8}" * len(headers)
        print(header_format.format(*headers))
        
        # Imprimir linhas da tabela
        for state in sorted(automaton.states):
            row = [str(state)]
            for symbol in sorted(automaton.alphabet):
                if symbol in automaton.transitions.get(state, {}):
                    targets = automaton.transitions[state][symbol]
                    cell = ", ".join(map(str, targets))
                else:
                    cell = "-"
                row.append(cell)
            print(header_format.format(*row))
    
    def save_automaton_to_file(self, automaton, filename):
        """Salva um autômato em um arquivo no formato especificado."""
        with open(filename, 'w') as file:
            # Número de estados
            file.write(f"{len(automaton.states)}\n")
            
            # Estado inicial
            file.write(f"{automaton.initial_state}\n")
            
            # Estados finais
            if isinstance(automaton.final_states, set) and all(isinstance(fs, tuple) for fs in automaton.final_states):
                final_states = sorted([state for state, _ in automaton.final_states])
            else:
                final_states = sorted(automaton.final_states)
            file.write(f"{','.join(map(str, final_states))}\n")
            
            # Alfabeto (excluindo epsilon)
            alphabet = sorted(automaton.alphabet - {'&'})
            file.write(f"{','.join(alphabet)}\n")
            
            # Transições
            for state in sorted(automaton.states):
                for symbol in sorted(automaton.alphabet):
                    if symbol == '&':  # Pular transições epsilon
                        continue
                    if symbol in automaton.transitions.get(state, {}):
                        targets = automaton.transitions[state][symbol]
                        for target in sorted(targets):
                            file.write(f"{state},{symbol},{target}\n")

def main():
    if len(sys.argv) < 3:
        print("Uso: python lexical_analyzer.py <arquivo_definicoes> <arquivo_teste> [arquivo_saida]")
        sys.exit(1)
    
    regex_file = sys.argv[1]
    test_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "tokens.txt"
    
    analyzer = LexicalAnalyzer()
    
    # Carregar definições de expressões regulares
    if not analyzer.load_regex_definitions(regex_file):
        sys.exit(1)
    
    # Gerar analisador léxico
    if not analyzer.generate_lexical_analyzer():
        sys.exit(1)
    
    # Exibir e salvar os autômatos
    for i, automaton in enumerate(analyzer.automata):
        analyzer.print_automaton(automaton, f"Autômato para {analyzer.patterns[i]}")
        analyzer.save_automaton_to_file(automaton, f"automaton_{analyzer.patterns[i]}.txt")
    
    analyzer.print_automaton(analyzer.combined_automaton, "Autômato Combinado")
    analyzer.save_automaton_to_file(analyzer.combined_automaton, "automaton_combined.txt")
    
    analyzer.print_automaton(analyzer.determinized_automaton, "Autômato Determinizado")
    analyzer.save_automaton_to_file(analyzer.determinized_automaton, "automaton_determinized.txt")
    
    # Analisar arquivo de teste
    tokens = analyzer.analyze_file(test_file, output_file)
    
    print(f"\nTokens gerados e salvos em {output_file}:")
    for token in tokens:
        print(token)

if __name__ == "__main__":
    main()