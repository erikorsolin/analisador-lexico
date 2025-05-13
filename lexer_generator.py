import sys
from collections import deque

class NFAState:
    def __init__(self, is_accepting=False):
        self.transitions = {}  # {char: set of states}
        self.epsilon_transitions = set()
        self.is_accepting = is_accepting
        self.token_type = None

class DFAState:
    def __init__(self, states, is_accepting=False, token_type=None):
        self.states = states  # frozenset of NFA states
        self.transitions = {}  # {char: DFAState}
        self.is_accepting = is_accepting
        self.token_type = token_type

    def __hash__(self):
        return hash(self.states)

    def __eq__(self, other):
        return self.states == other.states

class LexerGenerator:
    def __init__(self):
        self.dfas = []
        self.reserved_words = {}

    def parse_er_file(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                name, er = line.split(':', 1)
                name = name.strip()
                er = er.strip()
                nfa = self.er_to_nfa(er, name)
                dfa = self.nfa_to_dfa(nfa)
                self.dfas.append(dfa)

    def er_to_nfa(self, er, token_type):
        # TODO: Implement ER to NFA conversion (Thompson's algorithm)
        # Placeholder: create a simple NFA for testing
        start = NFAState()
        end = NFAState(is_accepting=True)
        end.token_type = token_type
        start.transitions['a'] = {end}  # Example transition
        return (start, end)

    def nfa_to_dfa(self, nfa):
        # TODO: Implement subset construction to convert NFA to DFA
        # Placeholder: return a simple DFA
        start = DFAState(frozenset([nfa[0]]), False)
        end = DFAState(frozenset([nfa[1]]), True, nfa[1].token_type)
        start.transitions['a'] = end
        return start

    def combine_dfas(self):
        # Combine all DFAs into a single NFA with epsilon transitions
        # Create new start state with epsilon transitions to each DFA's start
        combined_start = NFAState()
        for dfa in self.dfas:
            # TODO: Convert DFA back to NFA? Or handle differently
            pass
        # TODO: Implement combining logic
        return combined_start

    def determinize_nfa(self, nfa_start):
        # TODO: Implement subset construction to determinize combined NFA
        pass

    def generate_lexer(self):
        # Combine all DFAs into NFA, then determinize to get final DFA
        combined_nfa = self.combine_dfas()
        final_dfa = self.determinize_nfa(combined_nfa)
        return final_dfa