import sys
import os
import json
import tempfile
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QLabel, QSplitter,
                             QFileDialog, QMessageBox, QComboBox, QHeaderView,
                             QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from syntax_analyzer import SyntaxAnalyzer
import re

class SyntaxAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.init_ui()
        self.apply_styles()
        
        self.analyzer = SyntaxAnalyzer()
        self.parser_tables = None
        self.parse_result = False
        self.parse_steps = []
        self.current_grammar_path = ""
        self.current_grammar_name = ""
        
        # These attributes are needed for the update_parser_tables method
        self.action_table = None
        self.goto_table = None
        
        # Find grammar files
        self.update_grammar_list()

    def init_ui(self):
        self.setWindowTitle("Syntax Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Create a horizontal splitter for input/output
        splitter = QSplitter(Qt.Horizontal)
        
        # Input section - left side
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # Grammar selection
        grammar_layout = QHBoxLayout()
        grammar_layout.addWidget(QLabel("Grammar:"))
        self.grammar_combo = QComboBox()
        self.grammar_combo.currentIndexChanged.connect(self.grammar_selected)
        grammar_layout.addWidget(self.grammar_combo)
        
        # Load grammar button
        self.load_grammar_btn = QPushButton("Load Grammar")
        self.load_grammar_btn.clicked.connect(self.load_grammar_file)
        grammar_layout.addWidget(self.load_grammar_btn)
        
        # Generate parser button
        self.generate_parser_btn = QPushButton("Generate Parser")
        self.generate_parser_btn.clicked.connect(self.generate_parser)
        grammar_layout.addWidget(self.generate_parser_btn)
        
        input_layout.addLayout(grammar_layout)

        # Grammar text editor
        input_layout.addWidget(QLabel("Grammar Definition:"))
        self.grammar_input = QTextEdit()
        self.grammar_input.setPlaceholderText(
            "Enter grammar in BNF format:\n"
            "Example:\n"
            "P ::= S\n"
            "S ::= S ; S | if E then S else S | id = E\n"
            "E ::= E + T | E - T | T\n"
            "T ::= T * F | T / F | F\n"
            "F ::= ( E ) | id | num"
        )
        input_layout.addWidget(self.grammar_input)
        
        # Lexical definitions section
        lex_layout = QHBoxLayout()
        lex_layout.addWidget(QLabel("Lexical Definitions:"))
        
        # Load button
        self.load_regex_btn = QPushButton("Load Definitions")
        self.load_regex_btn.clicked.connect(self.load_regex_file)
        lex_layout.addStretch()
        lex_layout.addWidget(self.load_regex_btn)
        
        input_layout.addLayout(lex_layout)
        
        # Lexical definitions editor
        self.regex_input = QTextEdit()
        self.regex_input.setPlaceholderText(
            "Enter regular definitions (one per line):\n"
            "Example:\n"
            "pr: if | else | while | for\n"
            "id: [a-zA-Z]([a-zA-Z]|[0-9])*\n"
            "num: [0-9]+"
        )
        input_layout.addWidget(self.regex_input)
        
        # Source text section
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source Text:"))
        
        # Load source button
        self.load_source_btn = QPushButton("Load Source")
        self.load_source_btn.clicked.connect(self.load_source_file)
        source_layout.addStretch()
        source_layout.addWidget(self.load_source_btn)
        
        input_layout.addLayout(source_layout)
        
        # Source text editor
        self.source_input = QTextEdit()
        self.source_input.setPlaceholderText("Enter source text to analyze")
        input_layout.addWidget(self.source_input)
        
        # Analyze button
        analyze_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.analyze_text)
        analyze_layout.addWidget(self.analyze_btn)
        
        # Debug checkbox
        self.debug_checkbox = QLabel("Debug Mode:")
        analyze_layout.addWidget(self.debug_checkbox)
        
        # Debug checkbox
        self.debug_combo = QComboBox()
        self.debug_combo.addItems(["Off", "On"])
        analyze_layout.addWidget(self.debug_combo)
        
        input_layout.addLayout(analyze_layout)
        
        # Add the input widget to the splitter
        splitter.addWidget(input_widget)
        
        # Output section - right side using tab widget
        self.tabs = QTabWidget()
        
        # Tab for tokens
        self.tokens_tab = QWidget()
        tokens_layout = QVBoxLayout(self.tokens_tab)
        self.tokens_output = QTextEdit()
        self.tokens_output.setReadOnly(True)
        tokens_layout.addWidget(self.tokens_output)
        self.tabs.addTab(self.tokens_tab, "Tokens")
        
        # Tab for parse result
        self.parse_tab = QWidget()
        parse_layout = QVBoxLayout(self.parse_tab)
        self.parse_output = QTextEdit()
        self.parse_output.setReadOnly(True)
        parse_layout.addWidget(self.parse_output)
        self.tabs.addTab(self.parse_tab, "Parse Result")
        
        # Tab for symbol table
        self.symbol_table_tab = QWidget()
        symbol_table_layout = QVBoxLayout(self.symbol_table_tab)
        self.symbol_table_widget = QTableWidget()
        self.symbol_table_widget.setColumnCount(2)
        self.symbol_table_widget.setHorizontalHeaderLabels(["Lexeme", "Pattern/Index"])
        
        # Make columns stretch to fill available space evenly
        header = self.symbol_table_widget.horizontalHeader()
        header.setSectionResizeMode(0, header.Stretch)
        header.setSectionResizeMode(1, header.Stretch)
        
        # Remove grid lines for cleaner look (optional)
        self.symbol_table_widget.setShowGrid(True)
        
        symbol_table_layout.addWidget(self.symbol_table_widget)
        self.tabs.addTab(self.symbol_table_tab, "Symbol Table")
        
        # Tab for parse steps
        self.steps_tab = QWidget()
        steps_layout = QVBoxLayout(self.steps_tab)
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(3)
        self.steps_table.setHorizontalHeaderLabels(["Stack", "Input", "Action"])
        
        # Set column stretch
        header = self.steps_table.horizontalHeader()
        header.setSectionResizeMode(0, header.Stretch)
        header.setSectionResizeMode(1, header.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        steps_layout.addWidget(self.steps_table)
        self.tabs.addTab(self.steps_tab, "Parse Steps")
        
        # Tab for parser tables
        self.tables_tab = QWidget()
        tables_layout = QVBoxLayout(self.tables_tab)
        
        # Add a title label
        tables_layout.addWidget(QLabel("LR Table (Combined ACTION and GOTO):"))
        
        # Create a single combined table for both ACTION and GOTO
        self.lr_table = QTableWidget()
        self.lr_table.setShowGrid(True)
        tables_layout.addWidget(self.lr_table)
        
        self.tabs.addTab(self.tables_tab, "LR Table")
        
        # Tab for FIRST and FOLLOW sets
        self.first_follow_tab = QWidget()
        first_follow_layout = QVBoxLayout(self.first_follow_tab)
        
        # Create a splitter for FIRST and FOLLOW tables
        sets_splitter = QSplitter(Qt.Vertical)
        
        # FIRST sets section
        first_group = QWidget()
        first_layout = QVBoxLayout(first_group)
        first_layout.addWidget(QLabel("FIRST Sets:"))
        self.first_table = QTableWidget()
        self.first_table.setColumnCount(2)
        self.first_table.setHorizontalHeaderLabels(["Symbol", "FIRST Set"])
        
        # Configure table appearance
        header = self.first_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.first_table.setShowGrid(True)
        self.first_table.setAlternatingRowColors(True)
        
        first_layout.addWidget(self.first_table)
        sets_splitter.addWidget(first_group)
        
        # FOLLOW sets section
        follow_group = QWidget()
        follow_layout = QVBoxLayout(follow_group)
        follow_layout.addWidget(QLabel("FOLLOW Sets:"))
        self.follow_table = QTableWidget()
        self.follow_table.setColumnCount(2)
        self.follow_table.setHorizontalHeaderLabels(["Non-terminal", "FOLLOW Set"])
        
        # Configure table appearance
        header = self.follow_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.follow_table.setShowGrid(True)
        self.follow_table.setAlternatingRowColors(True)
        
        follow_layout.addWidget(self.follow_table)
        sets_splitter.addWidget(follow_group)
        
        # Add the splitter to the layout
        first_follow_layout.addWidget(sets_splitter)
        self.tabs.addTab(self.first_follow_tab, "FIRST/FOLLOW Sets")
        
        # Add the tabs to the splitter
        splitter.addWidget(self.tabs)
        
        # Set initial sizes
        splitter.setSizes([400, 800])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        self.setCentralWidget(main_widget)

    def apply_styles(self):
        """Apply simple but pleasant styling to the widgets"""
        # Simple styling with light colors
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f8f9fa;
                color: #212529;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 3px;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 6px 12px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: #4b6cb7;
                color: white;
            }
            
            QPushButton {
                background-color: #4b6cb7;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
            }
            
            QPushButton:hover {
                background-color: #3b5998;
            }
            
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 3px;
                background-color: white;
            }
            
            QTableWidget {
                border: 1px solid #ced4da;
                background-color: white;
                alternate-background-color: #f1f3f5;
            }
            
            QHeaderView::section {
                background-color: #4b6cb7;
                color: white;
                padding: 4px;
                border: none;
            }
        """)

    def update_grammar_list(self):
        """Find and load available grammar files"""
        self.grammar_combo.clear()
        grammars_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gramaticas')
        
        if os.path.isdir(grammars_dir):
            grammar_files = [f for f in os.listdir(grammars_dir) if f.endswith('.txt')]
            for grammar in sorted(grammar_files):
                self.grammar_combo.addItem(grammar, os.path.join(grammars_dir, grammar))
                
    def grammar_selected(self, index):
        """Handle grammar selection from dropdown"""
        if index < 0:
            return
            
        # Get file path from combo box
        file_path = self.grammar_combo.itemData(index)
        self.current_grammar_path = file_path
        self.current_grammar_name = self.grammar_combo.itemText(index)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.grammar_input.setText(f.read())
                
            # Check if parser tables exist
            parser_file = os.path.join(
                'tabelas', 
                f"{os.path.splitext(os.path.basename(file_path))[0]}_parser.json"
            )
            
            if os.path.exists(parser_file):
                self.load_parser(parser_file)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading grammar file: {str(e)}")

    def load_grammar_file(self):
        """Load a grammar file from disk"""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Grammar File", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.grammar_input.setText(f.read())
                self.current_grammar_path = filename
                self.current_grammar_name = os.path.basename(filename)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")

    def load_regex_file(self):
        """Load a regular definitions file from disk"""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Regular Definitions File", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.regex_input.setText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def load_source_file(self):
        """Load a source file from disk"""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Source Text File", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.source_input.setText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
                
    def generate_parser(self):
        """Generate parser tables from the current grammar"""
        if not self.grammar_input.toPlainText().strip():
            QMessageBox.critical(self, "Error", "Grammar is empty. Please enter a grammar before generating tables.")
            return
            
        # Create temporary file for grammar
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as grammar_file:
            grammar_file.write(self.grammar_input.toPlainText())
            grammar_file_name = grammar_file.name
            
        # Create output file name
        if self.current_grammar_name:
            base_name = os.path.splitext(self.current_grammar_name)[0]
        else:
            base_name = "grammar"
            
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tabelas')
        
        # Create tabelas directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        output_file = os.path.join(output_dir, f"{base_name}_parser.json")
        
        # Generate parser
        success = self.analyzer.generate_parser(grammar_file_name, output_file)
        
        # Clean up temporary file
        os.unlink(grammar_file_name)
        
        if success:
            QMessageBox.information(self, "Success", f"Parser tables generated and saved to '{output_file}'")
            self.load_parser(output_file)
            
            # Update FIRST and FOLLOW tables
            self.update_first_follow_tables()
            
            # Switch to the FIRST/FOLLOW tab to show the results
            self.tabs.setCurrentIndex(self.tabs.indexOf(self.first_follow_tab))
        else:
            QMessageBox.critical(self, "Error", "Failed to generate parser tables. Check the console for details.")

    def load_parser(self, parser_file):
        """Load parser tables from a file"""
        try:
            with open(parser_file, 'r', encoding='utf-8') as f:
                self.parser_tables = json.load(f)
                
            self.analyzer.parser.load_tables(parser_file)
            
            # Update the UI with parser tables
            self.update_parser_tables()
            
            # We need to reload the grammar to compute FIRST and FOLLOW sets
            # This is required because the parser doesn't have FIRST/FOLLOW sets directly
            # Extract grammar file path from the parser file path if possible
            grammar_path = None
            base_name = os.path.splitext(os.path.basename(parser_file))[0]
            if base_name.endswith("_parser"):
                gram_name = base_name[:-7]  # Remove "_parser" suffix
                possible_grammar = os.path.join("gramaticas", f"{gram_name}.txt")
                if os.path.exists(possible_grammar):
                    grammar_path = possible_grammar
            
            print(f"Looking for grammar file for FIRST/FOLLOW computation: {grammar_path}")
            if grammar_path:
                # Load the grammar to compute FIRST and FOLLOW sets
                print(f"Loading grammar from {grammar_path} for FIRST/FOLLOW sets...")
                self.analyzer.parser_generator.load_grammar(grammar_path)
                if hasattr(self.analyzer.parser_generator, 'grammar'):
                    # Compute FIRST and FOLLOW sets
                    print("Computing FIRST and FOLLOW sets...")
                    self.analyzer.parser_generator.grammar.augment()
                    self.analyzer.parser_generator.grammar.compute_nullable()
                    self.analyzer.parser_generator.grammar.compute_first_sets()
                    self.analyzer.parser_generator.grammar.compute_follow_sets()
                    
                    # Print some debug info
                    print("FIRST sets:")
                    for symbol, first_set in self.analyzer.parser_generator.grammar.first_sets.items():
                        print(f"  FIRST({symbol}) = {first_set}")
                    print("FOLLOW sets:")
                    for symbol, follow_set in self.analyzer.parser_generator.grammar.follow_sets.items():
                        print(f"  FOLLOW({symbol}) = {follow_set}")
                    
                    # Update FIRST and FOLLOW tables
                    self.update_first_follow_tables()
            else:
                print("No grammar file found for computing FIRST/FOLLOW sets")
            
            return True
        except Exception as e:
            print(f"Error in load_parser: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error loading parser tables: {str(e)}")
            return False
            
    def update_parser_tables(self):
        """Update the UI with the current parser tables"""
        try:
            if not self.parser_tables:
                print("No parser tables loaded")
                return
                
            print("Updating parser tables in UI")
            # Debug: Print what we have in the parser tables
            print(f"ACTION table keys: {self.parser_tables.get('action', {}).keys()}")
            print(f"GOTO table keys: {self.parser_tables.get('goto', {}).keys()}")
            print(f"Terminals: {self.parser_tables.get('terminals', [])}")
            print(f"Nonterminals: {self.parser_tables.get('nonterminals', [])}")
                
            # Get tables data
            action_table = self.parser_tables.get('action', {})
            goto_table = self.parser_tables.get('goto', {})
            
            # Get grammar symbols (with filtering to avoid duplicates)
            raw_terminals = self.parser_tables.get('terminals', [])
            raw_nonterminals = self.parser_tables.get('nonterminals', [])
            
            # Filter out any symbols that appear in both lists - they should only be nonterminals
            # Some JSON files might have inconsistencies in how terminals and nonterminals are categorized
            # This is a workaround until the parser generator is fixed
            terminals = []
            corrected_action_table = {}
            
            # Create a deep copy of the action table that we can modify
            for state, actions in action_table.items():
                corrected_action_table[state] = {}
                for symbol, action in actions.items():
                    if symbol not in raw_nonterminals:
                        corrected_action_table[state][symbol] = action
                    else:
                        print(f"WARNING: Symbol '{symbol}' found in both terminals and nonterminals lists, treating as nonterminal")
                        # This entry will be moved to the GOTO table
            
            # Update our action table reference
            action_table = corrected_action_table
            
            # Only include true terminals in our terminals list
            for t in raw_terminals:
                if t not in raw_nonterminals:
                    terminals.append(t)
            
            # Sort and add end marker
            terminals = sorted(terminals) + ['$']
            nonterminals = sorted(raw_nonterminals)
            
            # Check if we have valid states
            if not action_table:
                print("ERROR: No ACTION table data found")
                return
                
            # Get the states from the action table keys
            try:
                states = sorted(map(int, action_table.keys()))
            except Exception as e:
                print(f"ERROR: Cannot convert state keys to integers: {e}")
                # Fall back to string keys if needed
                states = sorted(action_table.keys(), key=lambda x: int(x) if x.isdigit() else 0)
            
            # Create a combined LR table with both ACTION and GOTO
            all_symbols = terminals + nonterminals
            
            print(f"Setting up LR table with {len(states)} states and {len(all_symbols)} symbols")
            print(f"Terminals: {terminals}")
            print(f"Nonterminals: {nonterminals}")
            
            # Clear the table
            self.lr_table.clear()
            self.lr_table.setRowCount(len(states) + 1)  # +1 for the header row
            self.lr_table.setColumnCount(len(all_symbols))
            self.lr_table.setHorizontalHeaderLabels(all_symbols)
            
            # Create a header row to distinguish ACTION and GOTO sections
            header_row = 0
            for col, symbol in enumerate(all_symbols):
                if col < len(terminals):
                    item = QTableWidgetItem("ACTION")
                else:
                    item = QTableWidgetItem("GOTO")
                item.setBackground(QColor("#343a40"))
                item.setForeground(QColor("white"))
                font = QFont()
                font.setBold(True)
                item.setFont(font)
                self.lr_table.setItem(header_row, col, item)
                
            # Set vertical headers (state numbers)
            state_headers = [""] + [str(state) for state in states]  # Empty first row for the header
            self.lr_table.setVerticalHeaderLabels(state_headers)
        except Exception as e:
            print(f"ERROR updating parser tables: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Set sizing policy for LR table
        self.lr_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.lr_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        try:
            # Fill the table (starting from row 1 because row 0 is our header)
            print(f"Populating table with {len(states)} states")
            
            for i, state in enumerate(states):
                try:
                    row = i + 1  # +1 to account for header row
                    state_key = str(state)
                    state_actions = action_table.get(state_key, {})
                    state_gotos = goto_table.get(state_key, {})
                    
                    # Debug
                    print(f"Processing state {state_key}: {len(state_actions)} actions, {len(state_gotos)} gotos")
                    
                    # Fill ACTION part (terminals)
                    for col, terminal in enumerate(terminals):
                        try:
                            if terminal in state_actions:
                                action = state_actions[terminal]
                                print(f"  Action for {terminal}: {action}")
                                
                                # Handle different action formats
                                if isinstance(action, list):
                                    action_type, action_value = action
                                elif isinstance(action, dict):
                                    action_type = action.get('type')
                                    action_value = action.get('value')
                                else:
                                    action_type, action_value = action
                                
                                if action_type == 'shift':
                                    text = f"s{action_value}"
                                elif action_type == 'reduce':
                                    text = f"r{action_value}"
                                elif action_type == 'accept':
                                    text = "acc"
                                else:
                                    text = str(action)
                                    
                                item = QTableWidgetItem(text)
                                
                                # Highlight different actions
                                if action_type == 'shift':
                                    item.setBackground(QColor("#d4edda"))  # Light green for shifts
                                elif action_type == 'reduce':
                                    item.setBackground(QColor("#fff3cd"))  # Light yellow for reduces
                                elif action_type == 'accept':
                                    item.setBackground(QColor("#cce5ff"))  # Light blue for accept
                                    
                                self.lr_table.setItem(row, col, item)
                            else:
                                self.lr_table.setItem(row, col, QTableWidgetItem(""))
                        except Exception as e:
                            print(f"Error setting ACTION cell at ({row}, {col}): {str(e)}")
                            self.lr_table.setItem(row, col, QTableWidgetItem("ERR"))
                
                    # Fill GOTO part (nonterminals)
                    for col, nonterminal in enumerate(nonterminals):
                        try:
                            table_col = len(terminals) + col  # Offset by the number of terminals
                            if nonterminal in state_gotos:
                                goto_value = state_gotos[nonterminal]
                                print(f"  Goto for {nonterminal}: {goto_value}")
                                item = QTableWidgetItem(str(goto_value))
                                item.setBackground(QColor("#e2e3e5"))  # Light gray for GOTO
                                self.lr_table.setItem(row, table_col, item)
                            else:
                                self.lr_table.setItem(row, table_col, QTableWidgetItem(""))
                        except Exception as e:
                            print(f"Error setting GOTO cell at ({row}, {len(terminals) + col}): {str(e)}")
                            self.lr_table.setItem(row, len(terminals) + col, QTableWidgetItem("ERR"))
                except Exception as e:
                    print(f"Error processing state {state}: {str(e)}")
            
            print("Resizing columns")
            self.lr_table.resizeColumnsToContents()
            print("Table updated successfully")
        except Exception as e:
            print(f"Error filling LR table: {str(e)}")
            import traceback
            traceback.print_exc()
        
    # Removed change_table_view method as tables are now displayed side by side
    
    def analyze_text(self):
        """Analyze the current text using the parser"""
        # Reset data
        self.parse_result = False
        self.parse_steps = []
        self.parse_output.clear()
        self.steps_table.setRowCount(0)
        self.tokens_output.clear()
        
        # Check if we have all the required inputs
        if not self.regex_input.toPlainText().strip():
            QMessageBox.critical(self, "Error", "No lexical definitions provided.")
            return
            
        if not self.source_input.toPlainText().strip():
            QMessageBox.critical(self, "Error", "No source text provided.")
            return
            
        # Create temporary files for regex and source
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as regex_file:
            regex_file.write(self.regex_input.toPlainText())
            regex_file_name = regex_file.name
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as source_file:
            source_file.write(self.source_input.toPlainText())
            source_file_name = source_file.name
            
        # Get current parser tables file
        if not hasattr(self, 'current_grammar_name') or not self.current_grammar_name:
            QMessageBox.critical(self, "Error", "No grammar selected. Please select or load a grammar first.")
            # Clean up temporary files
            os.unlink(regex_file_name)
            os.unlink(source_file_name)
            return
            
        base_name = os.path.splitext(self.current_grammar_name)[0]
        parser_file = os.path.join('tabelas', f"{base_name}_parser.json")
        
        if not os.path.exists(parser_file):
            QMessageBox.critical(self, "Error", f"Parser tables file '{parser_file}' not found. Generate parser tables first.")
            # Clean up temporary files
            os.unlink(regex_file_name)
            os.unlink(source_file_name)
            return
            
        # Set debug mode
        debug = (self.debug_combo.currentText() == "On")
        
        # Intercept stdout to capture parse steps
        import io
        from contextlib import redirect_stdout
        output = io.StringIO()
        
        try:
            with redirect_stdout(output):
                # Initialize analyzer
                self.analyzer = SyntaxAnalyzer()
                
                # Run analysis
                result = self.analyzer.analyze_file(
                    regex_file_name, source_file_name, None, parser_file, debug
                )
                
                self.parse_result = result
                
                # Store tokens for display (we need to get them from the lexical_analyzer)
                self.tokens = []
                if hasattr(self.analyzer, 'lexical_analyzer') and hasattr(self.analyzer.lexical_analyzer, 'token_analyzer'):
                    token_analyzer = self.analyzer.lexical_analyzer.token_analyzer
                    if token_analyzer and hasattr(token_analyzer, 'last_tokens'):
                        self.tokens = token_analyzer.last_tokens.copy()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during analysis: {str(e)}")
            # Clean up temporary files
            os.unlink(regex_file_name)
            os.unlink(source_file_name)
            return
            
        # Get captured output
        output_text = output.getvalue()
        
        # Display tokens
        if hasattr(self, 'tokens') and self.tokens:
            self.tokens_output.setText("\n".join(self.tokens))
        else:
            # Fallback to extract tokens from the output text
            tokens = []
            if output_text:
                lines = output_text.split('\n')
                in_tokens_section = False
                
                for line in lines:
                    if "Analisando arquivo" in line:
                        in_tokens_section = True
                        continue
                    if "Tabela de Símbolos" in line or "Carregando tabelas" in line:
                        in_tokens_section = False
                        continue
                    if in_tokens_section and line.strip() and '<' in line and '>' in line:
                        tokens.append(line.strip())
                        
                if tokens:
                    self.tokens = tokens
                    self.tokens_output.setText("\n".join(tokens))
                
        # Display parse result
        if self.parse_result:
            self.parse_output.setText("Syntax analysis completed successfully!")
            self.parse_output.setStyleSheet("color: green; font-weight: bold;")
        else:
            error_message = "Syntax error detected!"
            
            # Extract more detailed error information from output if available
            if output_text:
                error_lines = [line for line in output_text.split('\n') if "Erro" in line or "Error" in line]
                if error_lines:
                    error_message += "\n\nError details:\n" + "\n".join(error_lines)
                
            self.parse_output.setText(error_message)
            self.parse_output.setStyleSheet("color: red; font-weight: bold;")
            
        # Parse the output to extract parse steps
        # Always try to extract parse steps, either from debug output or generate simplified steps
        self.extract_parse_steps(output_text, debug)
            
        # Update symbol table in GUI
        self.update_symbol_table()
        
        # Clean up temporary files
        os.unlink(regex_file_name)
        os.unlink(source_file_name)
        
        # Always show the parse steps tab (either detailed or simplified steps will be shown)
        self.tabs.setCurrentIndex(2)  # Show Parse Steps tab
            
    def extract_parse_steps(self, output, debug_mode=False):
        """Extract parse steps from the console output"""
        # Clear existing data in the steps table
        self.steps_table.clearContents()
        self.steps_table.setRowCount(0)
        
        # First check if we're in non-debug mode and need to generate our own steps
        if not debug_mode or "Início da análise sintática:" not in output:
            # In non-debug mode, or if no debug info was generated,
            # we'll create our own parsing steps for display
            self.generate_parse_steps_from_tokens()
            return
            
        # Print debug information to help diagnose issues
        print("Debug output captured:")
        print(output)
        
        # Add a marker to see if we get to this point
        print("Extracting parse steps...")
        
        # Check for the start of parse steps
        if "Início da análise sintática:" not in output:
            print("No parse steps found in output")
            self.steps_table.setRowCount(1)
            self.steps_table.setItem(0, 0, QTableWidgetItem("No parse steps found in debug output"))
            return
        
        # Split the output and find the section with parse steps
        lines = output.split('\n')
        parse_start = False
        parse_lines = []
        
        for line in lines:
            if "Início da análise sintática:" in line:
                parse_start = True
                continue
            if parse_start and line.strip():
                parse_lines.append(line)
                
        if not parse_lines:
            print("Parse section found but no steps")
            self.steps_table.setRowCount(1)
            self.steps_table.setItem(0, 0, QTableWidgetItem("Parser started but no steps were recorded"))
            return
            
        # More flexible pattern for parsing steps
        stack_pattern = r"([^\s].*?)\s{2,}([^\s].*?)\s{2,}(.+)"
        
        # Extract all matches
        steps = []
        for line in parse_lines:
            # Skip header line
            if "Pilha" in line and "Entrada" in line and "Ação" in line:
                continue
                
            match = re.match(stack_pattern, line)
            if match:
                steps.append(match.groups())
            elif line.strip():
                print(f"Line did not match pattern: '{line}'")
        
        if not steps:
            print("No steps matched the pattern")
            self.steps_table.setRowCount(1)
            self.steps_table.setItem(0, 0, QTableWidgetItem("Parse steps found but format not recognized"))
            return
            
        # Fill the steps table
        self.steps_table.setRowCount(len(steps))
        self.steps_table.setAlternatingRowColors(True)
        
        for row, (stack, input_tokens, action) in enumerate(steps):
            # Stack column
            stack_item = QTableWidgetItem(stack.strip())
            self.steps_table.setItem(row, 0, stack_item)
            
            # Input column
            input_item = QTableWidgetItem(input_tokens.strip())
            self.steps_table.setItem(row, 1, input_item)
            
            # Action column
            action_item = QTableWidgetItem(action.strip())
            
            # Style the action based on content
            if "Shift" in action:
                action_item.setBackground(QColor("#d4edda"))  # Light green
            elif "Reduce" in action:
                action_item.setBackground(QColor("#fff3cd"))  # Light yellow
            elif "Accept" in action:
                action_item.setBackground(QColor("#cce5ff"))  # Light blue
                # Make Accept more prominent
                font = action_item.font()
                font.setBold(True)
                action_item.setFont(font)
            elif "Erro" in action:
                action_item.setBackground(QColor("#f8d7da"))  # Light red for errors
                
            self.steps_table.setItem(row, 2, action_item)
            
        # Adjust column widths
        self.steps_table.resizeColumnsToContents()
        self.steps_table.resizeRowsToContents()
        
    def generate_parse_steps_from_tokens(self):
        """Generate simplified parse steps for display when debug mode is off"""
        # If we don't have tokens, we can't generate steps
        if not hasattr(self, 'tokens') or not self.tokens:
            self.steps_table.setRowCount(1)
            self.steps_table.setItem(0, 0, QTableWidgetItem("No tokens available to generate parse steps"))
            self.steps_table.setSpan(0, 0, 1, 3)  # Span across all columns
            return
            
        # Create a simplified version of parse steps based on available tokens
        steps = []
        
        # Start with initial state
        if self.parse_result:
            # If parsing was successful, show a simplified trace
            steps.append(("Initial State", " ".join(self.tokens), "Start parsing"))
            
            # Add some intermediate states based on the grammar structure
            if len(self.tokens) > 1:
                mid_point = len(self.tokens) // 2
                steps.append(("Parsing...", " ".join(self.tokens[mid_point:]), 
                             f"Processing tokens {mid_point+1} to {len(self.tokens)}"))
            
            # Add the final accept state
            steps.append(("Complete", "$", "Accept"))
        else:
            # If parsing failed, show the error point
            steps.append(("Initial State", " ".join(self.tokens), "Start parsing"))
            steps.append(("Error State", "...", "Syntax Error"))
            
        # Fill the steps table
        self.steps_table.setRowCount(len(steps))
        self.steps_table.setAlternatingRowColors(True)
        
        # Add the steps to the table
        for row, (stack, input_tokens, action) in enumerate(steps):
            self.steps_table.setItem(row, 0, QTableWidgetItem(stack))
            self.steps_table.setItem(row, 1, QTableWidgetItem(input_tokens))
            
            action_item = QTableWidgetItem(action)
            if "Accept" in action:
                action_item.setBackground(QColor("#cce5ff"))
                font = action_item.font()
                font.setBold(True)
                action_item.setFont(font)
            elif "Error" in action:
                action_item.setBackground(QColor("#f8d7da"))
            else:
                action_item.setBackground(QColor("#d4edda"))
                
            self.steps_table.setItem(row, 2, action_item)
            
        # Add a note about debug mode
        note_row = len(steps)
        self.steps_table.setRowCount(note_row + 1)
        note = QTableWidgetItem("Note: For detailed parse steps, enable Debug Mode")
        note.setBackground(QColor("#e2e3e5"))  # Light gray background
        
        # Make the note span all columns
        self.steps_table.setItem(note_row, 0, note)
        self.steps_table.setSpan(note_row, 0, 1, 3)
        
        # Adjust column widths
        self.steps_table.resizeColumnsToContents()
        self.steps_table.resizeRowsToContents()
    
    def update_symbol_table(self):
        """Updates the symbol table widget with the current symbol table data"""
        if not hasattr(self.analyzer, 'lexical_analyzer') or not hasattr(self.analyzer.lexical_analyzer, 'symbol_table'):
            return
            
        # Get the symbol table from the analyzer
        symbol_table = self.analyzer.lexical_analyzer.symbol_table
        symbols = symbol_table.symbols
        
        # Set the number of rows
        self.symbol_table_widget.setRowCount(len(symbols))
        self.symbol_table_widget.setAlternatingRowColors(True)
        
        # Fill the table
        row = 0
        for lexeme, pattern in sorted(symbols.items()):
            lexeme_item = QTableWidgetItem(lexeme)
            
            # Format pattern/index appropriately
            if isinstance(pattern, tuple):
                pattern_text = f"{pattern[0]}, index={pattern[1]}"
            else:
                pattern_text = str(pattern)
                
            pattern_item = QTableWidgetItem(pattern_text)
            
            # Check if this is a reserved word (pattern is "PR")
            if pattern == "PR":
                # Apply bold formatting for reserved words
                font = lexeme_item.font()
                font.setBold(True)
                lexeme_item.setFont(font)
                pattern_item.setFont(font)
                
                # Highlight reserved words with a light blue background
                lexeme_item.setBackground(QColor("#d1ecf1"))
                pattern_item.setBackground(QColor("#d1ecf1"))
            
            # Highlight identifiers with a light yellow background
            elif isinstance(pattern, tuple) and pattern[0] == "id":
                lexeme_item.setBackground(QColor("#fff3cd"))
                pattern_item.setBackground(QColor("#fff3cd"))
            
            self.symbol_table_widget.setItem(row, 0, lexeme_item)
            self.symbol_table_widget.setItem(row, 1, pattern_item)
            row += 1
        
        # Adjust column width to content
        self.symbol_table_widget.resizeColumnsToContents()
        
    def update_first_follow_tables(self):
        """Update the FIRST and FOLLOW tables in the GUI"""
        try:
            print("Updating FIRST and FOLLOW tables...")
            # Check if we have access to the analyzer with grammar data
            if not hasattr(self.analyzer, 'parser_generator') or not hasattr(self.analyzer.parser_generator, 'grammar'):
                print("No grammar available, cannot update FIRST/FOLLOW tables")
                self.first_table.clearContents()
                self.first_table.setRowCount(0)
                self.follow_table.clearContents()
                self.follow_table.setRowCount(0)
                return

            # Get FIRST and FOLLOW sets from the analyzer
            sets = self.analyzer.get_first_follow_sets()
            first_sets = sets.get('first', {})
            follow_sets = sets.get('follow', {})
            
            print(f"Got {len(first_sets)} FIRST sets and {len(follow_sets)} FOLLOW sets")
            
            # Get terminals and nonterminals for highlighting
            terminals = set()
            if hasattr(self.analyzer.parser_generator, 'grammar'):
                terminals = self.analyzer.parser_generator.grammar.terminals
            
            # Update FIRST set table
            self.first_table.clearContents()
            self.first_table.setRowCount(len(first_sets))
            row = 0
            for symbol, first_set in sorted(first_sets.items()):
                # Symbol column
                symbol_item = QTableWidgetItem(symbol)
                
                # FIRST set column - format as {a, b, c}
                first_text = "{" + ", ".join(sorted(first_set)) + "}"
                first_item = QTableWidgetItem(first_text)
                
                # Highlight based on symbol type
                if symbol in terminals:
                    symbol_item.setBackground(QColor("#d4edda"))  # Light green for terminals
                    first_item.setBackground(QColor("#d4edda"))
                else:
                    symbol_item.setBackground(QColor("#fff3cd"))  # Light yellow for non-terminals
                    first_item.setBackground(QColor("#fff3cd"))
                
                self.first_table.setItem(row, 0, symbol_item)
                self.first_table.setItem(row, 1, first_item)
                row += 1
                
            # Update FOLLOW set table
            self.follow_table.clearContents()
            self.follow_table.setRowCount(len(follow_sets))
            row = 0
            for symbol, follow_set in sorted(follow_sets.items()):
                # Non-terminal column
                symbol_item = QTableWidgetItem(symbol)
                
                # FOLLOW set column - format as {a, b, c}
                follow_text = "{" + ", ".join(sorted(follow_set)) + "}"
                follow_item = QTableWidgetItem(follow_text)
                
                # Add special highlighting for the start symbol
                start_symbol = None
                if hasattr(self.analyzer.parser_generator, 'grammar'):
                    start_symbol = self.analyzer.parser_generator.grammar.start_symbol
                    
                if start_symbol and symbol == start_symbol:
                    font = symbol_item.font()
                    font.setBold(True)
                    symbol_item.setFont(font)
                    follow_item.setFont(font)
                    symbol_item.setBackground(QColor("#cce5ff"))  # Light blue for start symbol
                    follow_item.setBackground(QColor("#cce5ff"))
                else:
                    symbol_item.setBackground(QColor("#fff3cd"))  # Light yellow for other symbols
                    follow_item.setBackground(QColor("#fff3cd"))
                
                self.follow_table.setItem(row, 0, symbol_item)
                self.follow_table.setItem(row, 1, follow_item)
                row += 1
                
            # Resize columns to content
            self.first_table.resizeColumnsToContents()
            self.follow_table.resizeColumnsToContents()
            
            print("FIRST and FOLLOW tables updated successfully")
            
        except Exception as e:
            print(f"Error updating FIRST/FOLLOW tables: {str(e)}")
            import traceback
            traceback.print_exc()

def main():
    app = QApplication(sys.argv)
    ex = SyntaxAnalyzerGUI()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
