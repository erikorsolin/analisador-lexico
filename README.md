# Analisador Léxico - Framework

## Descrição
Este projeto implementa um framework para a geração de analisadores léxicos baseados em expressões regulares. O sistema segue um fluxo específico para processar expressões regulares e gerar tokens:

1. **Conversão de Expressões Regulares para AFD**
2. **União dos AFDs via ε-transição**
3. **Determinização do AFND**
4. **Construção da Tabela de Símbolos**

## Estrutura do Projeto

### Arquivos Principais

#### `main.py`
Arquivo principal que serve como ponto de entrada para o programa. Este módulo:
- Processa argumentos de linha de comando
- Coordena a execução das etapas de análise léxica
- Carrega definições de expressões regulares
- Exibe resultados e métricas de desempenho

#### `lexical_analyzer.py`
Implementa a classe `LexicalAnalyzer` que orquestra o processo de análise léxica:
- Carrega definições de expressões regulares de arquivos
- Converte cada expressão em um AFD usando Follow Pos
- Combina os AFDs via ε-transições em um AFND
- Determiniza o AFND combinado
- Gerencia a tabela de símbolos e o reconhecimento de tokens

#### `re_to_afd.py`
Implementa a classe `RegexToAFD` que converte expressões regulares diretamente em AFDs:
- Constrói a árvore sintática para a expressão regular
- Calcula os conjuntos firstpos, lastpos e nullable
- Computa o followpos para cada posição
- Constrói o AFD a partir dessas informações
- Lida com operadores de expressões regulares (*, +, ?, |)

#### `afnd_to_afd.py`
Contém o algoritmo de determinização para converter AFNDs em AFDs:
- Implementa o algoritmo de subconjuntos
- Calcula ε-fechamentos e movimentos
- Preserva as informações de padrão associadas aos estados finais

#### `automaton.py`
Define a classe `Automaton` que representa a estrutura de dados para um autômato finito:
- Mantém estados, alfabeto, transições e estados finais
- Fornece métodos para manipulação de autômatos
- Implementa operações importantes como ε-fechamento e movimento

#### `symbol_table.py`
Implementa a classe `SymbolTable` para gerenciar a tabela de símbolos:
- Armazena informações sobre lexemas e seus padrões
- Fornece suporte para palavras reservadas com prioridade
- Permite consultas eficientes sobre lexemas

#### `token_analyzer.py`
Define a classe `TokenAnalyzer` que utiliza o AFD para análise léxica:
- Processa o texto de entrada caractere por caractere
- Identifica tokens usando o princípio do "maior token possível"
- Gera a sequência de tokens no formato `<lexema, padrão>`
- Lida com caracteres não reconhecidos, marcando-os como erros

## Algoritmos Implementados

### 1. Conversão de ER para AFD usando Follow Pos
O algoritmo Follow Pos (Berry-Sethi/Glushkov) converte uma expressão regular diretamente em um AFD através dos seguintes passos:

1. **Pré-processamento**: Adicionar um marcador de fim (#) à expressão regular
2. **Construção da árvore sintática**: Criar uma árvore para representar a expressão
3. **Cálculo dos conjuntos**:
   - **nullable(n)**: Indica se o nó n pode gerar a string vazia
   - **firstpos(n)**: Posições que podem iniciar strings geradas pelo nó n
   - **lastpos(n)**: Posições que podem terminar strings geradas pelo nó n
   - **followpos(p)**: Para cada posição p, posições que podem seguir p em uma string válida
4. **Construção do AFD**:
   - Estados são conjuntos de posições da árvore sintática
   - O estado inicial corresponde a firstpos da raiz
   - As transições são determinadas pelo followpos de cada posição
   - Estados contendo o marcador de fim são finais

### 2. União de AFDs via ε-transição
Este algoritmo combina múltiplos AFDs em um único AFND:

1. Criar um novo estado inicial
2. Adicionar ε-transições do novo estado inicial para cada estado inicial dos AFDs originais
3. Preservar todas as transições e estados finais originais
4. O autômato resultante é não-determinístico devido às múltiplas transições possíveis a partir do estado inicial

### 3. Determinização de Autômatos
Converte o AFND resultante da união em um AFD equivalente:

1. Calcular o ε-fechamento do estado inicial do AFND
2. Construir novos estados do AFD, onde cada estado representa um conjunto de estados do AFND
3. Para cada conjunto de estados e símbolo, calcular o conjunto de estados alcançáveis
4. Um estado do AFD é final se contém pelo menos um estado final do AFND

### 4. Construção da Tabela de Símbolos
O sistema gerencia uma tabela de símbolos que:

1. Armazena lexemas reconhecidos pelo analisador
2. Associa cada lexema a seu padrão correspondente
3. Trata palavras reservadas com precedência especial
4. Atribui o tipo "PR" para palavras reservadas

## Instruções de Uso

### Pré-requisitos
- Python 3.6 ou superior

### Execução
O programa pode ser executado através da linha de comando com a seguinte sintaxe:

```bash
python main.py definicoes.txt teste.txt tokens.txt
```

Ou pelo comando do make

```bash
make run
```

Para limpar os arquivos gerados, execute

```bash
make clean
```

