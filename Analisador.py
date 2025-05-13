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

