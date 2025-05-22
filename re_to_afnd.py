"""
Implementação da conversão de Expressão Regular para Autômato Finito Não-Determinístico.
"""
from automaton import Automaton

class RegexToAFND:
    def __init__(self):
        self.next_state = 0
    
    def _get_next_state(self):
        """Retorna o próximo estado disponível."""
        state = self.next_state
        self.next_state += 1
        return state
    
    def convert(self, regex):
        """Converte uma expressão regular para um AFND."""
        # Remover espaços em branco
        regex = regex.replace(" ", "")
        
        # Converter a expressão para um AFND
        automaton = self._parse_expression(regex)
        
        return automaton
    
    def _parse_expression(self, regex):
        """Analisa uma expressão regular e constrói o AFND correspondente."""
        if not regex:
            # Expressão vazia
            automaton = Automaton()
            start = self._get_next_state()
            end = self._get_next_state()
            
            automaton.set_initial_state(start)
            automaton.add_final_state(end)
            automaton.add_transition(start, '&', end)
            
            return automaton
        
        # Verificar se a expressão contém alternativas (|)
        parts = []
        i = 0
        start_part = 0
        paren_count = 0
        
        while i < len(regex):
            if regex[i] == '(':
                paren_count += 1
            elif regex[i] == ')':
                paren_count -= 1
            elif regex[i] == '|' and paren_count == 0:
                parts.append(regex[start_part:i])
                start_part = i + 1
            
            i += 1
        
        parts.append(regex[start_part:])
        
        if len(parts) > 1:
            # Expressão tem alternativas (|)
            return self._parse_union(parts)
        
        # Expressão não tem alternativas, processar como concatenação
        return self._parse_concatenation(regex)
    
    def _parse_union(self, parts):
        """Constrói um AFND para a união de expressões."""
        automaton = Automaton()
        start = self._get_next_state()
        end = self._get_next_state()
        
        automaton.set_initial_state(start)
        automaton.add_final_state(end)
        
        for part in parts:
            part_automaton = self._parse_expression(part)
            
            # Adicionar transição do início para o início da parte
            automaton.add_transition(start, '&', part_automaton.initial_state)
            
            # Adicionar transição do fim da parte para o fim
            for final_state in part_automaton.final_states:
                automaton.add_transition(final_state, '&', end)
            
            # Incorporar estados e transições
            for state in part_automaton.states:
                automaton.add_state(state)
            
            for from_state, transitions in part_automaton.transitions.items():
                for symbol, to_states in transitions.items():
                    for to_state in to_states:
                        automaton.add_transition(from_state, symbol, to_state)
        
        return automaton
    
    def _parse_concatenation(self, regex):
        """Constrói um AFND para a concatenação de símbolos."""
        i = 0
        parts = []
        
        while i < len(regex):
            if regex[i] == '[':
                # Encontrou um grupo de caracteres
                end = regex.find(']', i)
                if end == -1:
                    raise ValueError(f"Grupo não fechado na expressão: {regex}")
                
                group = regex[i:end+1]
                parts.append(self._parse_group(group))
                i = end + 1
            elif regex[i] == '(':
                # Encontrou uma subexpressão
                paren_count = 1
                j = i + 1
                
                while j < len(regex) and paren_count > 0:
                    if regex[j] == '(':
                        paren_count += 1
                    elif regex[j] == ')':
                        paren_count -= 1
                    j += 1
                
                if paren_count != 0:
                    raise ValueError(f"Parênteses não balanceados na expressão: {regex}")
                
                subexpr = regex[i+1:j-1]
                parts.append(self._parse_expression(subexpr))
                
                # Verificar se há um operador após o fechamento do parêntese
                if j < len(regex) and regex[j] in '*+?':
                    if regex[j] == '*':
                        parts[-1] = self._apply_kleene_star(parts[-1])
                    elif regex[j] == '+':
                        parts[-1] = self._apply_kleene_plus(parts[-1])
                    elif regex[j] == '?':
                        parts[-1] = self._apply_optional(parts[-1])
                    j += 1
                
                i = j
            else:
                # Caractere simples ou operador
                if i + 1 < len(regex) and regex[i+1] in '*+?':
                    # Caractere seguido por operador
                    if regex[i] in '.|()[]':
                        raise ValueError(f"Operador inválido aplicado a: {regex[i]}")
                    
                    char_automaton = self._parse_char(regex[i])
                    
                    if regex[i+1] == '*':
                        parts.append(self._apply_kleene_star(char_automaton))
                    elif regex[i+1] == '+':
                        parts.append(self._apply_kleene_plus(char_automaton))
                    elif regex[i+1] == '?':
                        parts.append(self._apply_optional(char_automaton))
                    
                    i += 2
                else:
                    # Caractere simples
                    if regex[i] not in '.|()[]':
                        parts.append(self._parse_char(regex[i]))
                    i += 1
        
        if not parts:
            # Não há partes, criar um autômato que aceita a string vazia
            automaton = Automaton()
            start = self._get_next_state()
            end = self._get_next_state()
            
            automaton.set_initial_state(start)
            automaton.add_final_state(end)
            automaton.add_transition(start, '&', end)
            
            return automaton
        
        if len(parts) == 1:
            # Apenas uma parte
            return parts[0]
        
        # Concatenar todas as partes
        automaton = Automaton()
        
        # Usar o estado inicial da primeira parte
        automaton.set_initial_state(parts[0].initial_state)
        
        # Usar o estado final da última parte
        for final_state in parts[-1].final_states:
            automaton.add_final_state(final_state)
        
        # Conectar as partes com transições vazias
        for i in range(len(parts) - 1):
            for final_state in parts[i].final_states:
                automaton.add_transition(final_state, '&', parts[i+1].initial_state)
        
        # Incorporar todos os estados e transições
        for part in parts:
            for state in part.states:
                automaton.add_state(state)
            
            for from_state, transitions in part.transitions.items():
                for symbol, to_states in transitions.items():
                    for to_state in to_states:
                        automaton.add_transition(from_state, symbol, to_state)
        
        return automaton
    
    def _parse_char(self, char):
        """Constrói um AFND para um caractere simples."""
        automaton = Automaton()
        start = self._get_next_state()
        end = self._get_next_state()
        
        automaton.set_initial_state(start)
        automaton.add_final_state(end)
        automaton.add_transition(start, char, end)
        
        return automaton
    
    def _parse_group(self, group):
        """
        Constrói um AFND para um grupo de caracteres [a-z].
        Retorna um autômato que aceita qualquer caractere no grupo.
        """
        # Remover os colchetes
        group_content = group[1:-1]
        
        automaton = Automaton()
        start = self._get_next_state()
        end = self._get_next_state()
        
        automaton.set_initial_state(start)
        automaton.add_final_state(end)
        
        i = 0
        while i < len(group_content):
            if i + 2 < len(group_content) and group_content[i+1] == '-':
                # Range de caracteres (e.g., a-z)
                start_char = group_content[i]
                end_char = group_content[i+2]
                
                for c in range(ord(start_char), ord(end_char) + 1):
                    automaton.add_transition(start, chr(c), end)
                
                i += 3
            else:
                # Caractere único
                automaton.add_transition(start, group_content[i], end)
                i += 1
        
        return automaton
    
    def _apply_kleene_star(self, base_automaton):
        """Aplica o operador de Kleene star (*) a um autômato."""
        automaton = Automaton()
        start = self._get_next_state()
        end = self._get_next_state()
        
        automaton.set_initial_state(start)
        automaton.add_final_state(end)
        
        # Transição direta do início para o fim (0 ocorrências)
        automaton.add_transition(start, '&', end)
        
        # Transição do início para o início do autômato base
        automaton.add_transition(start, '&', base_automaton.initial_state)
        
        # Transições dos estados finais do base para o fim
        for final_state in base_automaton.final_states:
            automaton.add_transition(final_state, '&', end)
            # Loop de volta para o início do base
            automaton.add_transition(final_state, '&', base_automaton.initial_state)
        
        # Incorporar todos os estados e transições
        for state in base_automaton.states:
            automaton.add_state(state)
        
        for from_state, transitions in base_automaton.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    automaton.add_transition(from_state, symbol, to_state)
        
        return automaton
    
    def _apply_kleene_plus(self, base_automaton):
        """Aplica o operador de Kleene plus (+) a um autômato."""
        automaton = Automaton()
        start = self._get_next_state()
        end = self._get_next_state()
        
        automaton.set_initial_state(start)
        automaton.add_final_state(end)
        
        # Transição do início para o início do autômato base
        automaton.add_transition(start, '&', base_automaton.initial_state)
        
        # Transições dos estados finais do base para o fim
        for final_state in base_automaton.final_states:
            automaton.add_transition(final_state, '&', end)
            # Loop de volta para o início do base
            automaton.add_transition(final_state, '&', base_automaton.initial_state)
        
        # Incorporar todos os estados e transições
        for state in base_automaton.states:
            automaton.add_state(state)
        
        for from_state, transitions in base_automaton.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    automaton.add_transition(from_state, symbol, to_state)
        
        return automaton
    
    def _apply_optional(self, base_automaton):
        """Aplica o operador opcional (?) a um autômato."""
        automaton = Automaton()
        start = self._get_next_state()
        end = self._get_next_state()
        
        automaton.set_initial_state(start)
        automaton.add_final_state(end)
        
        # Transição direta do início para o fim (0 ocorrências)
        automaton.add_transition(start, '&', end)
        
        # Transição do início para o início do autômato base
        automaton.add_transition(start, '&', base_automaton.initial_state)
        
        # Transições dos estados finais do base para o fim
        for final_state in base_automaton.final_states:
            automaton.add_transition(final_state, '&', end)
        
        # Incorporar todos os estados e transições
        for state in base_automaton.states:
            automaton.add_state(state)
        
        for from_state, transitions in base_automaton.transitions.items():
            for symbol, to_states in transitions.items():
                for to_state in to_states:
                    automaton.add_transition(from_state, symbol, to_state)
        
        return automaton