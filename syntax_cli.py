"""
Interface de linha de comando para o analisador sintático.
"""
import sys
import os
import argparse
from syntax_analyzer import SyntaxAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Analisador Sintático SLR')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando para gerar tabelas do parser
    generate_parser = subparsers.add_parser('gerar', help='Gerar tabelas de análise sintática')
    generate_parser.add_argument('grammar_file', help='Arquivo com a gramática')
    generate_parser.add_argument('-o', '--output', help='Arquivo de saída para as tabelas', default=None)
    
    # Comando para análise léxica
    analyze_lexical = subparsers.add_parser('lexico', help='Executar apenas a análise léxica')
    analyze_lexical.add_argument('regex_file', help='Arquivo com definições de expressões regulares')
    analyze_lexical.add_argument('input_file', help='Arquivo com o código fonte a analisar')
    analyze_lexical.add_argument('-o', '--output', help='Arquivo de saída para os tokens', default=None)
    
    # Comando para análise sintática
    analyze_syntax = subparsers.add_parser('sintatico', help='Executar análise léxica e sintática')
    analyze_syntax.add_argument('regex_file', help='Arquivo com definições de expressões regulares')
    analyze_syntax.add_argument('input_file', help='Arquivo com o código fonte a analisar')
    analyze_syntax.add_argument('parser_file', help='Arquivo com as tabelas do parser')
    analyze_syntax.add_argument('-o', '--output', help='Arquivo de saída para os tokens', default=None)
    analyze_syntax.add_argument('-d', '--debug', action='store_true', help='Mostrar informações detalhadas da análise')
    
    args = parser.parse_args()
    
    # Se não for especificado um comando, mostrar a ajuda
    if not args.command:
        parser.print_help()
        return
    
    analyzer = SyntaxAnalyzer()
    
    if args.command == 'gerar':
        # Gerar tabelas de análise sintática
        print("Modo de Geração de Tabelas SLR")
        print("=" * 50)
        result = analyzer.generate_parser(args.grammar_file, args.output)
        sys.exit(0 if result else 1)
        
    elif args.command == 'lexico':
        # Executar apenas a análise léxica
        print("Modo de Análise Léxica")
        print("=" * 50)
        print("Executando apenas a análise léxica (sem análise sintática)")
        result = analyzer.analyze_file(args.regex_file, args.input_file, args.output)
        sys.exit(0 if result else 1)
        
    elif args.command == 'sintatico':
        # Executar análise léxica e sintática
        print("Modo de Análise Sintática")
        print("=" * 50)
        result = analyzer.analyze_file(
            args.regex_file, args.input_file, args.output, args.parser_file, args.debug
        )
        sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()
