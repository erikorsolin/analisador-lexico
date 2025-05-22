"""
Implementação da classe Automaton para representar um Autômato Finito.
"""
from collections import defaultdict

class Automaton:
    def __init__(self):
        self.states = set()          # Conjunto de estados
        self.alphabet = set()        # Alfabeto
        self.transitions = defaultdict(lambda: defaultdict(set))  # Função de transição
        self.initial_state = None    # Estado inicial
        self.final_states = set()    # Conjunto de estados finais
        self.pattern = None          # Padrão associado ao autômato
    
    def add_state(self, state):
        """Adiciona um estado ao autômato."""
        self.states.add(state)
    
    def add_symbol(self, symbol):
        """Adiciona um símbolo ao alfabeto."""
        self.alphabet.add(symbol)
    
    def add_transition(self, from_state, symbol, to_state):
        """Adiciona uma transição ao autômato."""
        self.add_state(from_state)
        self.add_state(to_state)
        self.add_symbol(symbol)
        self.transitions[from_state][symbol].add(to_state)
    
    def set_initial_state(self, state):
        """Define o estado inicial."""
        self.add_state(state)
        self.initial_state = state
    
    def add_final_state(self, state):
        """Adiciona um estado final."""
        self.add_state(state)
        self.final_states.add(state)
    
    def __str__(self):
        """Representação em string do autômato."""
        result = []
        result.append(f"Estados: {self.states}")
        result.append(f"Alfabeto: {self.alphabet}")
        result.append(f"Estado inicial: {self.initial_state}")
        result.append(f"Estados finais: {self.final_states}")
        result.append("Transições:")
        
        for from_state, transitions in sorted(self.transitions.items()):
            for symbol, to_states in sorted(transitions.items()):
                for to_state in sorted(to_states):
                    result.append(f"  {from_state} --{symbol}--> {to_state}")
        
        return "\n".join(result)