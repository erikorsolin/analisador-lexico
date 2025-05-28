#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt5 GUI for Lexical Analyzer with simple, pleasant styling
"""
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QLabel, QSplitter,
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from lexical_analyzer import LexicalAnalyzer
import tempfile

class LexicalAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.init_ui()
        self.apply_styles()
        
        self.analyzer = LexicalAnalyzer()
        self.automata = []
        self.combined_automaton = None
        self.determinized_automaton = None
        self.tokens = []

    def init_ui(self):
        self.setWindowTitle("Lexical Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # Create a horizontal splitter for input/output
        splitter = QSplitter(Qt.Horizontal)
        
        # Input section - left side
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # Regular definitions input
        input_layout.addWidget(QLabel("Regular Definitions:"))
        self.regex_input = QTextEdit()
        self.regex_input.setPlaceholderText("Enter regular definitions (one per line):\nExample:\npr: if | else | while | for\nid: [a-zA-Z]([a-zA-Z]|[0-9])*\nnum: [0-9]+")
        input_layout.addWidget(self.regex_input)
        
        # Source text input
        input_layout.addWidget(QLabel("Source Text:"))
        self.source_input = QTextEdit()
        self.source_input.setPlaceholderText("Enter source text to analyze")
        input_layout.addWidget(self.source_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.analyze_text)
        button_layout.addWidget(self.analyze_btn)
        
        self.load_regex_btn = QPushButton("Load Definitions")
        self.load_regex_btn.clicked.connect(self.load_regex_file)
        button_layout.addWidget(self.load_regex_btn)
        
        self.load_source_btn = QPushButton("Load Source")
        self.load_source_btn.clicked.connect(self.load_source_file)
        button_layout.addWidget(self.load_source_btn)
        
        input_layout.addLayout(button_layout)
        
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
        
        # Tab for symbol table
        self.symbol_table_tab = QWidget()
        symbol_table_layout = QVBoxLayout(self.symbol_table_tab)
        self.symbol_table_widget = QTableWidget()
        self.symbol_table_widget.setColumnCount(2)
        self.symbol_table_widget.setHorizontalHeaderLabels(["Lexeme", "Pattern"])
        symbol_table_layout.addWidget(self.symbol_table_widget)
        self.tabs.addTab(self.symbol_table_tab, "Symbol Table")
        
        # Tab for automata
        self.automata_tabs = QTabWidget()
        self.tabs.addTab(self.automata_tabs, "Automata")
        
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

    def load_regex_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Regular Definitions File", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.regex_input.setText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def load_source_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Source Text File", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.source_input.setText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def analyze_text(self):
        # Reset data
        self.automata = []
        self.combined_automaton = None
        self.determinized_automaton = None
        self.tokens = []
        
        # Clear previous results
        self.tokens_output.clear()
        self.symbol_table_widget.setRowCount(0)
        while self.automata_tabs.count() > 0:
            self.automata_tabs.removeTab(0)
        
        # Create temporary files for regex and source
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as regex_file:
            regex_file.write(self.regex_input.toPlainText())
            regex_file_name = regex_file.name
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as source_file:
            source_file.write(self.source_input.toPlainText())
            source_file_name = source_file.name
        
        # Initialize analyzer
        self.analyzer = LexicalAnalyzer()
        
        # Load regex definitions
        if not self.analyzer.load_regex_definitions(regex_file_name):
            QMessageBox.critical(self, "Error", "Failed to load regular definitions.")
            os.unlink(regex_file_name)
            os.unlink(source_file_name)
            return
        
        # Generate lexical analyzer
        if not self.analyzer.generate_lexical_analyzer():
            QMessageBox.critical(self, "Error", "Failed to generate lexical analyzer.")
            os.unlink(regex_file_name)
            os.unlink(source_file_name)
            return
        
        # Process each automaton
        for i, automaton in enumerate(self.analyzer.automata):
            pattern = self.analyzer.patterns[i]
            self.automata.append((pattern, automaton))
            self.create_automaton_tab(automaton, f"AFD: {pattern}")
        
        # Process combined automaton
        self.combined_automaton = self.analyzer.combined_automaton
        self.create_automaton_tab(self.combined_automaton, "AFND Combined")
        
        # Process determinized automaton
        self.determinized_automaton = self.analyzer.determinized_automaton
        self.create_automaton_tab(self.determinized_automaton, "AFD Determinized")
        
        # Analyze the source text
        self.tokens = self.analyzer.analyze_file(source_file_name)
        
        # Show tokens
        self.tokens_output.setText("\n".join(self.tokens))
        
        # Update symbol table
        self.update_symbol_table()
        
        # Clean up temporary files
        os.unlink(regex_file_name)
        os.unlink(source_file_name)
        
        # Show success message
        QMessageBox.information(self, "Success", "Lexical analysis completed successfully!")
    
    def update_symbol_table(self):
        """Updates the symbol table widget with the current symbol table data"""
        # Get the symbol table from the analyzer
        symbols = self.analyzer.symbol_table.symbols
        
        # Set the number of rows
        self.symbol_table_widget.setRowCount(len(symbols))
        self.symbol_table_widget.setAlternatingRowColors(True)
        
        # Fill the table
        for row, (lexeme, pattern) in enumerate(sorted(symbols.items())):
            lexeme_item = QTableWidgetItem(lexeme)
            pattern_item = QTableWidgetItem(pattern)
            
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
            
            self.symbol_table_widget.setItem(row, 0, lexeme_item)
            self.symbol_table_widget.setItem(row, 1, pattern_item)
        
        # Adjust column width to content
        self.symbol_table_widget.resizeColumnsToContents()
        
    def create_automaton_tab(self, automaton, title):
        """Creates a tab to display an automaton's information"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Add basic info
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        
        # Format automaton info
        info = f"States: {len(automaton.states)}\n"
        info += f"Initial State: {automaton.initial_state}\n"
        
        # Format final states
        if isinstance(automaton.final_states, set) and all(isinstance(fs, tuple) for fs in automaton.final_states):
            final_states_str = ", ".join([f"{state}({pattern})" for state, pattern in automaton.final_states])
            info += f"Final States: {final_states_str}\n"
        else:
            info += f"Final States: {', '.join(map(str, automaton.final_states))}\n"
        
        info += f"Alphabet: {', '.join(sorted(automaton.alphabet - {'&'}))}\n"
        
        info_text.setText(info)
        layout.addWidget(info_text)
        
        # Create transition table
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        
        # Get all states and symbols (excluding epsilon '&')
        states = sorted(automaton.states)
        symbols = sorted(automaton.alphabet - {'&'})
        
        # Set up the table
        table.setRowCount(len(states))
        table.setColumnCount(len(symbols))
        table.setHorizontalHeaderLabels(symbols)
        
        # Set vertical headers (states)
        state_labels = []
        for state in states:
            # Mark final states with an asterisk
            is_final = False
            if isinstance(automaton.final_states, set):
                for final_state in automaton.final_states:
                    if isinstance(final_state, tuple) and final_state[0] == state:
                        is_final = True
                        break
                    elif not isinstance(final_state, tuple) and final_state == state:
                        is_final = True
                        break
            
            label = f"{state}" + ("*" if is_final else "")
            if state == automaton.initial_state:
                label = "→" + label
            
            state_labels.append(label)
        
        table.setVerticalHeaderLabels(state_labels)
        
        # Fill the table with transitions
        for row, state in enumerate(states):
            for col, symbol in enumerate(symbols):
                transitions = automaton.transitions.get(state, {}).get(symbol, set())
                if transitions:
                    # For AFD: single state
                    if len(transitions) == 1:
                        item_text = str(next(iter(transitions)))
                    # For AFND: multiple states
                    else:
                        item_text = "{" + ",".join(map(str, sorted(transitions))) + "}"
                    
                    table.setItem(row, col, QTableWidgetItem(item_text))
                else:
                    table.setItem(row, col, QTableWidgetItem("-"))
        
        # Adjust table appearance
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        layout.addWidget(table)
        
        # Add the tab
        self.automata_tabs.addTab(tab, title)

def main():
    app = QApplication(sys.argv)
    ex = LexicalAnalyzerGUI()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()