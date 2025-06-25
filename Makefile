# Lista de arquivos ou diretórios a serem removidos
CLEAN_FILES = \
	__pycache__ \
	test_cases/*/tokens_*.txt \
	AFs/*.txt \
	tabelas/*.json

# Diretórios do projeto
TEST_DIR = test_cases
GRAMMAR_DIR = gramaticas
TABLES_DIR = tabelas

.PHONY: clean run run-lexical run-lexical-gui run-syntax-gui gen-parser run-parser dirs

# Criar diretórios necessários
dirs:
	@mkdir -p $(TEST_DIR) $(GRAMMAR_DIR) $(TABLES_DIR) AFs

# Limpa os arquivos temporários
clean:
	@echo "Limpando arquivos..."
	@rm -rf $(CLEAN_FILES)
	@echo "Limpeza concluída."

# Execução de casos de teste do analisador léxico
run-lexical:
	@if [ -z "$(case)" ]; then \
		echo "Erro: Especifique um caso de teste com 'case=X'"; \
		echo "Exemplo: make run-lexical case=1"; \
		exit 1; \
	fi; \
	if [ ! -d "$(TEST_DIR)/case$(case)" ]; then \
		echo "Erro: Diretório $(TEST_DIR)/case$(case) não existe!"; \
		exit 1; \
	fi; \
	DEFS=$$(find "$(TEST_DIR)/case$(case)" -name "definicoes*.txt" | head -1); \
	TEST=$$(find "$(TEST_DIR)/case$(case)" -name "teste*.txt" | head -1); \
	OUTPUT="$(TEST_DIR)/case$(case)/tokens_case$(case).txt"; \
	if [ -z "$$DEFS" ] || [ -z "$$TEST" ]; then \
		echo "Erro: Arquivos de definições ou teste não encontrados em $(TEST_DIR)/case$(case)"; \
		exit 1; \
	fi; \
	echo "Executando caso de teste $(case)..."; \
	echo "  Definições: $$DEFS"; \
	echo "  Teste: $$TEST"; \
	echo "  Saída: $$OUTPUT"; \
	python3 syntax_cli.py lexico "$$DEFS" "$$TEST" -o "$$OUTPUT"; \
	echo "Análise léxica completa. Resultado salvo em $$OUTPUT"

# Gerar tabelas do analisador sintático
gen-parser:
	@if [ -z "$(grammar)" ]; then \
		echo "Erro: Especifique um arquivo de gramática com 'grammar=arquivo.txt'"; \
		echo "Exemplo: make gen-parser grammar=expressoes.txt"; \
		exit 1; \
	fi; \
	if [ ! -f "$(GRAMMAR_DIR)/$(grammar)" ]; then \
		echo "Erro: Arquivo $(GRAMMAR_DIR)/$(grammar) não existe!"; \
		exit 1; \
	fi; \
	OUTPUT="$(TABLES_DIR)/$$(basename $(grammar) .txt)_parser.json"; \
	echo "Gerando tabelas de análise sintática..."; \
	echo "  Gramática: $(GRAMMAR_DIR)/$(grammar)"; \
	echo "  Saída: $$OUTPUT"; \
	python3 syntax_cli.py gerar "$(GRAMMAR_DIR)/$(grammar)" -o "$$OUTPUT"; \
	echo "Geração de tabelas concluída."

# Executar análise sintática
run-parser:
	@if [ -z "$(case)" ] || [ -z "$(grammar)" ]; then \
		echo "Erro: Especifique um caso de teste e uma gramática."; \
		echo "Exemplo: make run-parser case=1 grammar=expressoes.txt"; \
		exit 1; \
	fi; \
	if [ ! -d "$(TEST_DIR)/case$(case)" ]; then \
		echo "Erro: Diretório $(TEST_DIR)/case$(case) não existe!"; \
		exit 1; \
	fi; \
	PARSER_FILE="$(TABLES_DIR)/$$(basename $(grammar) .txt)_parser.json"; \
	if [ ! -f "$$PARSER_FILE" ]; then \
		echo "Erro: Arquivo de tabelas $$PARSER_FILE não existe!"; \
		echo "Execute primeiro: make gen-parser grammar=$(grammar)"; \
		exit 1; \
	fi; \
	DEFS=$$(find "$(TEST_DIR)/case$(case)" -name "definicoes*.txt" | head -1); \
	TEST=$$(find "$(TEST_DIR)/case$(case)" -name "teste*.txt" | head -1); \
	OUTPUT="$(TEST_DIR)/case$(case)/tokens_case$(case).txt"; \
	if [ -z "$$DEFS" ] || [ -z "$$TEST" ]; then \
		echo "Erro: Arquivos de definições ou teste não encontrados em $(TEST_DIR)/case$(case)"; \
		exit 1; \
	fi; \
	DEBUG_FLAG=""; \
	if [ "$(debug)" = "true" ]; then \
		DEBUG_FLAG="-d"; \
	fi; \
	echo "Executando análise sintática..."; \
	echo "  Definições: $$DEFS"; \
	echo "  Teste: $$TEST"; \
	echo "  Parser: $$PARSER_FILE"; \
	echo "  Debug: $${DEBUG_FLAG:-desabilitado}"; \
	python3 syntax_cli.py sintatico "$$DEFS" "$$TEST" "$$PARSER_FILE" -o "$$OUTPUT" $$DEBUG_FLAG; \
	echo "Análise completa. Tokens salvos em $$OUTPUT"

# Listar gramáticas disponíveis
list-grammars:
	@echo "Gramáticas disponíveis:"
	@find $(GRAMMAR_DIR) -name "*.txt" -exec basename {} \; | sort

# Listar casos de teste disponíveis
list-tests:
	@echo "Casos de teste disponíveis:"
	@find $(TEST_DIR) -type d -name "case*" | sed 's|.*case|case|' | sort

# Exibir ajuda com os comandos disponíveis
help:
	@echo "Framework de Análise Léxica e Sintática SLR"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make dirs                   - Criar diretórios necessários"
	@echo "  make clean                  - Limpar arquivos temporários"
	@echo "  make list-grammars          - Listar gramáticas disponíveis"
	@echo "  make list-tests             - Listar casos de teste disponíveis"
	@echo "  make run-lexical case=X     - Executar análise léxica no caso X"
	@echo "  make run-lexical-gui        - Iniciar interface gráfica do analisador léxico"
	@echo "  make run-syntax-gui         - Iniciar interface gráfica do analisador sintático"
	@echo "  make gen-parser grammar=X   - Gerar tabelas SLR para gramática X"
	@echo "  make run-parser case=X grammar=Y [debug=true] - Análise sintática"
	@echo ""
	@echo "Exemplos:"
	@echo "  make run-lexical case=1"
	@echo "  make gen-parser grammar=expressoes.txt"
	@echo "  make run-parser case=1 grammar=expressoes.txt debug=true"
	@echo "  make run-syntax-gui"

# Launch lexical analyzer GUI
run-lexical-gui:
	@echo "Iniciando interface gráfica do analisador léxico..."
	@python3 lexical_gui.py

# Launch syntax analyzer GUI
run-syntax-gui:
	@echo "Iniciando interface gráfica do analisador sintático..."
	@python3 syntax_gui.py

# Manter compatibilidade com scripts antigos
run: run-lexical

# Definir o comando help como default
.DEFAULT_GOAL := help