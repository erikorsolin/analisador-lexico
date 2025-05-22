# Lista de arquivos ou diretórios a serem removidos
CLEAN_FILES = \
	__pycache__ \
	afd_*.txt \
	afnd_*.txt \
	tokens.txt \
	test_cases/*/tokens_*.txt

# Diretório dos casos de teste
TEST_DIR = test_cases

.PHONY: clean run

# Limpa os arquivos temporários
clean:
	@echo "Limpando arquivos..."
	@rm -rf $(CLEAN_FILES)
	@echo "Limpeza concluída."

# Execução de casos de teste
run:
	@if [ -z "$(case)" ]; then \
		echo "Erro: Especifique um caso de teste com 'case=X'"; \
		echo "Exemplo: make run case=1"; \
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
	python3 main.py "$$DEFS" "$$TEST" "$$OUTPUT"; \
	echo "Análise completa. Resultado salvo em $$OUTPUT"