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
        
        Returns:
        - A dictionary with 'first' and 'follow' keys containing the respective sets.
        """
        if not hasattr(self.parser_generator, 'grammar') or self.parser_generator.grammar is None:
            return {'first': {}, 'follow': {}}
        
        grammar = self.parser_generator.grammar
        
        # Make sure we use the patched first sets for left-recursive grammars
        # This applies the same logic as in the print_first_follow_sets method
        # but without modifying the original sets
        grammar._patch_left_recursive_first_sets()
        
        # Get the complete FIRST sets with proper values for each non-terminal
        first_sets = {}
        for symbol in grammar.nonterminals:
            # Create a copy of the set to avoid modifying the original
            first_sets[symbol] = set(grammar.first_sets.get(symbol, set()))
        
        # For debugging
        print("FIRST sets for GUI:")
        for nt in sorted(grammar.nonterminals):
            first_str = "{" + ", ".join(sorted(first_sets[nt])) + "}"
            print(f"FIRST({nt}) = {first_str}")
        
        return {
            'first': first_sets,
            'follow': grammar.follow_sets
        }
