# Lista de arquivos ou diretórios a serem removidos
CLEAN_FILES = \
	__pycache__ \
	afd_*.txt \
	afnd_*.txt \
	tokens.txt

.PHONY: clean

clean:
	@echo "Limpando arquivos..."
	@rm -rf $(CLEAN_FILES)
	@echo "Limpeza concluída."

run:
	@python3 main.py definicoes.txt teste.txt tokens.txt