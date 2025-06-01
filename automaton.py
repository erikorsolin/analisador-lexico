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
        self.states.add(state)
    
    def add_symbol(self, symbol):
        self.alphabet.add(symbol)
    
    def add_transition(self, from_state, symbol, to_state):
        self.add_state(from_state)
        self.add_state(to_state)
        self.add_symbol(symbol)
        self.transitions[from_state][symbol].add(to_state)
    
    def set_initial_state(self, state):
        self.add_state(state)
        self.initial_state = state
    
    def add_final_state(self, state):
        self.add_state(state)
        self.final_states.add(state)
    
    def get_epsilon_closure(self, state_or_states):
        """
        Retorna o ε-fecho de um estado ou conjunto de estados.
        """
        if isinstance(state_or_states, (int, str)):
            states = {state_or_states}
        else:
            states = set(state_or_states)
        
        closure = set(states)
        stack = list(states)
        
        while stack:
            state = stack.pop()
            for next_state in self.transitions[state].get('&', set()):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        
        return closure
    
    def get_move(self, states, symbol):
        """
        Retorna o conjunto de estados alcançáveis a partir de states
        usando transições com o símbolo dado.
        """
        result = set()
        for state in states:
            result.update(self.transitions[state].get(symbol, set()))
        return result
    
    def __str__(self):
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