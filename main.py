from lexical_analyzer import LexicalAnalyzer
import sys
import time

def main():
    print("Analisador Léxico - Trabalho de Linguagens Formais")
    print("=" * 50)
    
    if len(sys.argv) < 3:
        print("Uso: python main.py <arquivo_definicoes> <arquivo_teste> [arquivo_saida]")
        print("\nExemplo:")
        print("python main.py definicoes.txt teste.txt tokens.txt")
        return
    
    regex_file = sys.argv[1]
    test_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "tokens.txt"
    
    # Iniciar temporizador
    start_time = time.time()
    
    analyzer = LexicalAnalyzer()
    
    # Carregar definições de expressões regulares
    print(f"\nCarregando definições de expressões regulares de '{regex_file}'...")
    if not analyzer.load_regex_definitions(regex_file):
        print("Falha ao carregar definições. Abortando.")
        return
    
    # Gerar analisador léxico
    print("\nGerando analisador léxico seguindo o fluxo:")
    print("1. ER → AFD (usando Follow Pos)")
    print("2. União de AFDs via ε-transição → AFND")
    print("3. Determinização do AFND → AFD")
    print("4. Construção da tabela de símbolos")
    
    if not analyzer.generate_lexical_analyzer():
        print("Falha ao gerar analisador léxico. Abortando.")
        return
    
    # Exibir e salvar os autômatos
    print("\nSalvando autômatos gerados...")
    for i, automaton in enumerate(analyzer.automata):
        pattern = analyzer.patterns[i]
        analyzer.print_automaton(automaton, f"AFD para '{pattern}' (via Follow Pos)")
        analyzer.save_automaton_to_file(automaton, f"afd_{pattern}.txt")
    
    analyzer.print_automaton(analyzer.combined_automaton, "Autômato Combinado (AFND via ε-transição)")
    analyzer.save_automaton_to_file(analyzer.combined_automaton, "afnd_combined.txt")
    
    analyzer.print_automaton(analyzer.determinized_automaton, "Autômato Determinizado (AFD)")
    analyzer.save_automaton_to_file(analyzer.determinized_automaton, "afd_determinized.txt")
    
    # Analisar arquivo de teste
    print(f"\nAnalisando arquivo de teste '{test_file}'...")
    tokens = analyzer.analyze_file(test_file, output_file)
    
    # Calcular tempo de execução
    elapsed_time = time.time() - start_time
    
    print(f"\nTokens gerados e salvos em '{output_file}':")
    for token in tokens:
        print(token)
    
    print(f"\nProcessamento concluído com sucesso em {elapsed_time:.4f} segundos!")

if __name__ == "__main__":
    main()