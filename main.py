def main():
    if len(sys.argv) < 3:
        print("Usage: python lexer_generator.py <er_file> <test_file>")
        sys.exit(1)

    er_file = sys.argv[1]
    test_file = sys.argv[2]

    # Generate lexer
    generator = LexerGenerator()
    generator.parse_er_file(er_file)
    final_dfa = generator.generate_lexer()

    # Read test file
    with open(test_file, 'r') as f:
        text = f.read().split()

    # Tokenize
    lexer = Lexer(final_dfa)
    tokens = lexer.tokenize(text)

    # Print tokens
    for token in tokens:
        print(f"<{token[0]}, {token[1]}>")

if __name__ == "__main__":
    main()