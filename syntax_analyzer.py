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
        
        print(f"Analisando arquivo '{input_file}'...")
        tokens = self.lexical_analyzer.analyze_file(input_file, output_file)
        
        if not tokens:
            print("Erro na análise léxica.")
            return False
            
        # Mostrar a tabela de símbolos
        print("\n" + str(self.lexical_analyzer.symbol_table))
        
        # Se não for especificado um arquivo de tabelas, apenas retornar após a análise léxica
        if not parser_tables_file:
            print("Análise léxica concluída com sucesso.")
            return True
        
        # Fase 2: Análise sintática
        print(f"Carregando tabelas de análise sintática de '{parser_tables_file}'...")
        if not self.parser.load_tables(parser_tables_file):
            return False
        
        print("Iniciando análise sintática...")
        success = self.parser.parse(tokens, debug)
        
        if success:
            print("Análise sintática concluída com sucesso.")
        else:
            print("Erro na análise sintática.")
        
        return success
    
    def get_first_follow_sets(self):
        """
        Returns the FIRST and FOLLOW sets from the parser generator.
        
        Returns:
        - A dictionary with 'first' and 'follow' keys containing the respective sets.
        """
        if not hasattr(self.parser_generator, 'grammar') or self.parser_generator.grammar is None:
            return {'first': {}, 'follow': {}}
            
        return {
            'first': self.parser_generator.grammar.first_sets,
            'follow': self.parser_generator.grammar.follow_sets
        }
