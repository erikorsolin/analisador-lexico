# SLR Parser Generator Framework

## Descrição
Este projeto implementa um framework completo para geração e execução de analisadores sintáticos do tipo SLR (Simple LR). O sistema é dividido em duas interfaces:

1. **Interface de Projeto**: Gera tabelas de análise a partir de uma gramática.
2. **Interface de Execução**: Utiliza as tabelas geradas para analisar uma sentença.

## Estrutura do Projeto

### Arquivos Principais

- `grammar.py`: Define a estrutura para gramáticas livres de contexto (GLC).
- `slr_parser_generator.py`: Gera tabelas de análise SLR a partir de uma GLC.
- `slr_parser.py`: Implementa o analisador SLR que utiliza as tabelas geradas.
- `syntax_analyzer.py`: Integra o analisador léxico com o sintático.
- `syntax_cli.py`: Interface de linha de comando.
- `symbol_table.py`: Implementa a tabela de símbolos.
- `token_analyzer.py`: Analisa tokens a partir do AFD e da tabela de símbolos.

### Pastas

- `gramaticas/`: Contém as gramáticas de entrada.
- `tabelas/`: Armazena as tabelas de análise geradas.
- `test_cases/`: Casos de teste para verificação do sistema.

## Algoritmos Implementados

1. **Cálculo dos conjuntos FIRST e FOLLOW**:
   - Para cada símbolo da gramática, calcula os conjuntos FIRST e FOLLOW.
   - Essencial para a construção da tabela SLR.

2. **Construção da Coleção Canônica de Itens LR(0)**:
   - Implementa as funções CLOSURE e GOTO conforme algoritmo de Aho.
   - Constrói o conjunto completo de todos os conjuntos de itens LR(0).

3. **Geração da Tabela SLR**:
   - Cria as tabelas ACTION e GOTO.
   - Implementa as ações de shift, reduce e accept.
   - Detecta e reporta conflitos na tabela.

4. **Algoritmo do Parser LR**:
   - Utiliza a tabela ACTION para determinar a próxima ação.
   - Empilha estados e símbolos gramaticais.
   - Realiza reduções quando necessário.

## Formatos de Entrada e Saída

### Formato do Arquivo de Gramática
```
<não-terminal> ::= <corpo da produção> | <alternativa>
```

### Formato dos Tokens
- Identificadores: `<id, índice>`
- Palavras Reservadas: `<lexema, PR>`
- Outros tokens: `<lexema, padrão>`

### Formato da Tabela de Análise
A tabela é armazenada em formato JSON com:
- `action`: Ações para terminais (shift, reduce, accept)
- `goto`: Transições para não-terminais
- Informações sobre a gramática (terminais, não-terminais, produções)

## Como Usar

### Usando o Make (Recomendado)

#### Lista de Comandos Disponíveis
```bash
make help
```

#### Listar Gramáticas e Casos de Teste Disponíveis
```bash
make list-grammars
make list-tests
```

#### Gerar Tabelas de Análise SLR
```bash
make gen-parser grammar=expressoes.txt
```

#### Executar Apenas Análise Léxica
```bash
make run-lexical case=1
```

#### Executar Análise Léxica e Sintática
```bash
make run-parser case=1 grammar=expressoes.txt
```

Para ativar o modo de debug, adicione `debug=true`:
```bash
make run-parser case=1 grammar=expressoes.txt debug=true
```

### Usando o CLI Diretamente

#### Gerar Tabelas de Análise
```bash
python syntax_cli.py gerar <arquivo_gramática> [-o <arquivo_saída>]
```

#### Executar Apenas Análise Léxica
```bash
python syntax_cli.py lexico <arquivo_definicoes> <arquivo_entrada> [-o <arquivo_saída>]
```

#### Executar Análise Léxica e Sintática
```bash
python syntax_cli.py sintatico <arquivo_definicoes> <arquivo_entrada> <arquivo_parser> [-o <arquivo_saída>] [-d]
```

O parâmetro `-d` ativa o modo de debug, mostrando os passos da análise sintática.

## Utilizando o Makefile

Para facilitar o uso do framework, o projeto fornece um Makefile com diversos comandos úteis:

### Comandos Disponíveis

```bash
# Listar todos os comandos disponíveis
make help

# Criar diretórios necessários para o projeto
make dirs

# Limpar arquivos temporários
make clean

# Listar gramáticas disponíveis 
make list-grammars

# Listar casos de teste disponíveis
make list-tests

# Executar análise léxica em um caso específico
make run-lexical case=1

# Gerar tabelas de análise para uma gramática
make gen-parser grammar=expressoes.txt

# Executar análise sintática completa com um caso e gramática específicos
make run-parser case=1 grammar=expressoes.txt

# Ativar modo debug na análise sintática
make run-parser case=1 grammar=expressoes.txt debug=true
```

### Exemplos de Uso

1. Gerar tabelas de análise para uma gramática:
```bash
make gen-parser grammar=expressoes.txt
```

2. Executar análise léxica em um caso de teste:
```bash
make run-lexical case=1
```

3. Executar análise sintática completa:
```bash
make run-parser case=1 grammar=expressoes.txt
```

4. Executar análise sintática com modo debug ativado:
```bash
make run-parser case=1 grammar=expressoes.txt debug=true
```
