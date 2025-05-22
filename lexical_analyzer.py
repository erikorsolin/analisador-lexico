"""
Arquivo principal do analisador léxico.
Contém a interface para carregar expressões regulares, gerar AFDs, e analisar textos.
"""
import sys
from collections import defaultdict
from re_to_afd import RegexToAFD
from afnd_to_afd import determinize
from automaton import Automaton
from symbol_table import SymbolTable
from token_analyzer import TokenAnalyzer

class LexicalAnalyzer:
    def __init__(self):
        self.automata = []
        self.patterns = []
        self.combined_automaton = None
        self.determinized_automaton = None
        self.symbol_table = SymbolTable()
        self.token_analyzer = None
        
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
                        
                        # Se for o padrão "pr", adicionar palavras reservadas à tabela de símbolos
                        if pattern_name.lower() == "pr":
                            reserved_words = [w.strip() for w in regex.split('|')]
                            for word in reserved_words:
                                self.symbol_table.add_reserved_word(word)
                        
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
        converter = RegexToAFD()
        automaton = converter.convert(regex)
        automaton.pattern = pattern_name
        
        # Adicionar informação do padrão aos estados finais do autômato
        original_finals = automaton.final_states.copy()
        automaton.final_states = set()
        for final in original_finals:
            automaton.final_states.add((final, pattern_name))
        
        self.patterns.append(pattern_name)
        self.automata.append(automaton)
        return automaton
    
    def combine_automata(self):
        """
        Combina todos os autômatos via ε-transições.
        Isso converte os AFDs individuais em um AFND combinado.
        """
        if not self.automata:
            print("Nenhum autômato para combinar.")
            return None
        
        print("Combinando automatos via ε-transições...")
        combined = Automaton()
        combined.states = {0}  # Estado inicial do autômato combinado
        combined.initial_state = 0
        combined.final_states = set()
        
        # Mapeamento de estados originais para estados no novo autômato
        state_mapping = {}
        next_state = 1
        
        # Mapear estados de cada autômato para novos estados no automato combinado
        for idx, automaton in enumerate(self.automata):
            pattern = self.patterns[idx]
            
            # Mapear os estados
            for state in automaton.states:
                state_mapping[(idx, state)] = next_state
                combined.add_state(next_state)
                
                # Se o estado é final no autômato original, também é no combinado
                if isinstance(automaton.final_states, set) and any(isinstance(fs, tuple) and fs[0] == state for fs in automaton.final_states):
                    for final_state, pattern in automaton.final_states:
                        if final_state == state:
                            combined.final_states.add((next_state, pattern))
                            break
                
                next_state += 1
            
            # Adicionar ε-transição do estado inicial combinado para o estado inicial do autômato
            mapped_initial = state_mapping[(idx, automaton.initial_state)]
            combined.add_transition(0, '&', mapped_initial)
            
            # Adicionar símbolos do alfabeto
            for symbol in automaton.alphabet:
                combined.add_symbol(symbol)
        
        # Adicionar todas as transições de cada autômato
        for idx, automaton in enumerate(self.automata):
            for from_state, transitions in automaton.transitions.items():
                mapped_from = state_mapping[(idx, from_state)]
                
                for symbol, to_states in transitions.items():
                    for to_state in to_states:
                        mapped_to = state_mapping[(idx, to_state)]
                        combined.add_transition(mapped_from, symbol, mapped_to)
        
        self.combined_automaton = combined
        return combined
    
    def generate_lexical_analyzer(self):
        """Gera o analisador léxico a partir dos autômatos combinados e determinizados."""
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
        headers = ["Estado"] + sorted(automaton.alphabet - {'&'})
        header_format = "{:<8}" * len(headers)
        print(header_format.format(*headers))
        
        # Imprimir linhas da tabela
        for state in sorted(automaton.states):
            row = [str(state)]
            for symbol in sorted(automaton.alphabet - {'&'}):
                if symbol in automaton.transitions.get(state, {}):
                    targets = automaton.transitions[state][symbol]
                    cell = ", ".join(map(str, targets))
                else:
                    cell = "-"
                row.append(cell)
            print(header_format.format(*row))
    
    def save_automaton_to_file(self, automaton, filename):
        """Salva um autômato em um arquivo no formato especificado."""
        try:
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
                    for symbol in sorted(automaton.alphabet - {'&'}):
                        if symbol in automaton.transitions.get(state, {}):
                            targets = automaton.transitions[state][symbol]
                            for target in sorted(targets):
                                file.write(f"{state},{symbol},{target}\n")
            
            print(f"Autômato salvo em {filename}")
        except Exception as e:
            print(f"Erro ao salvar autômato: {str(e)}")