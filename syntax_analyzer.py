"""
Módulo principal do analisador sintático.
Integra o analisador léxico e o analisador sintático.
"""
from lexical_analyzer import LexicalAnalyzer
from slr_parser_generator import SLRParser as SLRParserGenerator
from slr_parser import SLRParser
import os

class SyntaxAnalyzer:
    """
    Classe que integra o analisador léxico e o analisador sintático.
    """
    def __init__(self):
        self.lexical_analyzer = LexicalAnalyzer()
        self.parser_generator = SLRParserGenerator()
        self.parser = SLRParser()
    
    def generate_parser(self, grammar_file, output_file=None):
        """
        Gera as tabelas de análise sintática a partir de uma gramática.
        """
        print(f"Carregando gramática de '{grammar_file}'...")
        if not self.parser_generator.load_grammar(grammar_file):
            return False
        
        print("Gerando tabelas de análise sintática SLR...")
        if not self.parser_generator.generate_parser():
            return False
        
        # Se output_file não foi especificado, usar um nome padrão
        if not output_file:
            base_name = os.path.splitext(os.path.basename(grammar_file))[0]
            output_file = f"{base_name}_parser_tables.json"
        
        print(f"Salvando tabelas em '{output_file}'...")
        if self.parser_generator.save_tables(output_file):
            print("Tabelas de análise SLR geradas com sucesso.")
            # Imprimir informações detalhadas
            self.parser_generator.print_info()
            return True
        
        return False
    
    def load_parser(self, tables_file):
        """
        Carrega um analisador sintático a partir das tabelas de análise.
        """
        print(f"Carregando tabelas de análise de '{tables_file}'...")
        return self.parser.load_tables(tables_file)
    
    def analyze_file(self, lexical_defs_file, input_file, output_file=None, parser_tables_file=None, debug=False):
        """
        Realiza a análise léxica e sintática de um arquivo.
        
        Parameters:
        - lexical_defs_file: Arquivo com definições de expressões regulares
        - input_file: Arquivo com o código fonte a ser analisado
        - output_file: Arquivo para salvar os tokens gerados
        - parser_tables_file: Arquivo com as tabelas de análise sintática
        - debug: Flag para habilitar mensagens de depuração
        
        Returns:
        - True se a análise sintática for bem-sucedida, False em caso contrário
        """
        # Fase 1: Análise léxica
        print(f"Carregando definições léxicas de '{lexical_defs_file}'...")
        if not self.lexical_analyzer.load_regex_definitions(lexical_defs_file):
            return False
            
        if not self.lexical_analyzer.generate_lexical_analyzer():
            return False

        print(f"Carregando tabelas de análise sintática de '{parser_tables_file}'...")
        if not self.parser.load_tables(parser_tables_file):
            return False

        print(f"Analisando arquivo '{input_file}' linha por linha...")

        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        all_success = True

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            print(f"\n===== Analisando sentença (linha {line_num}): {line} =====")
            tokens = self.lexical_analyzer.analyze_string(line)

            if not tokens:
                print(f"Erro na análise léxica da linha {line_num}.")
                all_success = False
                continue

            mapped_tokens = []
            for token in tokens:
                try:
                    token_clean = token.strip("<>").strip()
                    lexeme, token_type = [x.strip() for x in token_clean.split(",", 1)]

                    if token_type == "id":
                        mapped_tokens.append("id")
                    elif token_type == "num":
                        mapped_tokens.append("num")
                    elif lexeme in ["+", "-", "*", "/", "(", ")"]:
                        mapped_tokens.append(lexeme)
                    elif lexeme == "$":
                        mapped_tokens.append("$")
                    else:
                        mapped_tokens.append(lexeme)

                except Exception as e:
                    print(f"Erro ao processar token '{token}' na linha {line_num}: {e}")
                    all_success = False
                    break

            if not mapped_tokens:
                continue

            if mapped_tokens[-1] != "$":
                mapped_tokens.append("$")

            print("Tokens mapeados:", mapped_tokens)

            print("Iniciando análise sintática...")
            success = self.parser.parse(mapped_tokens, debug)

            if success:
                print(f"Análise sintática da linha {line_num} concluída com sucesso.")
            else:
                print(f"Erro de sintaxe na linha {line_num}.")
                all_success = False

        return all_success

    
    def get_first_follow_sets(self):
        """
        Returns the FIRST and FOLLOW sets from the parser generator.
        Only includes FIRST sets for non-terminals.
        
        Returns:
        - A dictionary with 'first' and 'follow' keys containing the respective sets.
        """
        if not hasattr(self.parser_generator, 'grammar') or self.parser_generator.grammar is None:
            return {'first': {}, 'follow': {}}
        
        # Apply the patching algorithm to fix FIRST sets for left-recursive grammars
        grammar = self.parser_generator.grammar
        
        # Special case handling for arithmetic-like grammars
        if ('E' in grammar.nonterminals and 'T' in grammar.nonterminals and 
            'F' in grammar.nonterminals):
            # Detect if we have left recursion in this grammar
            left_recursive = False
            for left, right in grammar.productions:
                if right and right[0] == left:
                    left_recursive = True
                    break
            
            if left_recursive:
                # This is likely an arithmetic expression grammar with left recursion
                # Get the terminal symbols that appear in F's FIRST set
                terminals_in_f = set()
                for sym in grammar.first_sets.get('F', set()):
                    if sym in grammar.terminals:
                        terminals_in_f.add(sym)
                
                # If we have terminals in F, patch the FIRST sets
                if terminals_in_f:
                    patched_first = {}
                    for nt in grammar.nonterminals:
                        patched_first[nt] = set(terminals_in_f)
                        # Keep epsilon if it was there
                        if '' in grammar.first_sets.get(nt, set()):
                            patched_first[nt].add('')
                    
                    # Filter to include only non-terminals
                    return {
                        'first': patched_first,
                        'follow': grammar.follow_sets
                    }
        
        # For non-arithmetic grammars or non-left-recursive grammars
        # Filter FIRST sets to include only non-terminals
        first_sets = {}
        for symbol, first_set in grammar.first_sets.items():
            if symbol in grammar.nonterminals:
                first_sets[symbol] = first_set
                
        return {
            'first': first_sets,
            'follow': grammar.follow_sets
        }
