"""
Implementação da determinização de Autômatos Finitos Não-Determinísticos.
"""
from automaton import Automaton
from collections import deque

def determinize(afnd):
    """
    Converte um AFND para um AFD usando o algoritmo de subconjuntos.
    """
    print("Iniciando determinização...")
    
    # Criar um novo autômato determinístico
    afd = Automaton()
    
    # Calcular o ε-fechamento do estado inicial
    initial_closure = frozenset(afnd.get_epsilon_closure(afnd.initial_state))
    
    # Mapear conjuntos de estados do AFND para estados únicos no AFD
    state_mapping = {}
    state_mapping[initial_closure] = 0
    
    # Fila para processamento dos estados
    queue = deque([initial_closure])
    
    # Adicionar o estado inicial ao AFD
    afd.add_state(0)
    afd.set_initial_state(0)
    
    # Processar estados finais no conjunto inicial
    for state in initial_closure:
        for final_state, pattern in afnd.final_states:
            if state == final_state:
                afd.final_states.add((0, pattern))
                break
    
    # Conjunto de estados processados para evitar duplicações
    processed = set([initial_closure])
    
    # Processamento principal
    while queue:
        current_states = queue.popleft()
        current_afd_state = state_mapping[current_states]
        
        # Para cada símbolo no alfabeto (exceto ε)
        for symbol in sorted(afnd.alphabet - {'&'}):
            # Calcular o movimento seguido pelo ε-fechamento
            next_states = set()
            for state in current_states:
                next_states.update(afnd.get_move({state}, symbol))
            
            if not next_states:
                continue  # Não há transições para este símbolo
            
            epsilon_closure = set()
            for state in next_states:
                epsilon_closure.update(afnd.get_epsilon_closure(state))
            
            if not epsilon_closure:
                continue  # Não há estados alcançáveis
            
            epsilon_closure = frozenset(epsilon_closure)
            
            # Verificar se este conjunto já foi mapeado
            if epsilon_closure not in state_mapping:
                new_state = len(state_mapping)
                state_mapping[epsilon_closure] = new_state
                afd.add_state(new_state)
                
                # Verificar se contém estados finais
                for state in epsilon_closure:
                    for final_state, pattern in afnd.final_states:
                        if state == final_state:
                            afd.final_states.add((new_state, pattern))
                            break
                
                # Adicionar à fila se ainda não foi processado
                if epsilon_closure not in processed:
                    queue.append(epsilon_closure)
                    processed.add(epsilon_closure)
            
            # Adicionar a transição no AFD
            next_afd_state = state_mapping[epsilon_closure]
            afd.add_transition(current_afd_state, symbol, next_afd_state)
    
    print(f"Determinização concluída. AFD resultante tem {len(afd.states)} estados.")
    return afd