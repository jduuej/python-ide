import sys
import os
from pathlib import Path
from typing import Optional, Dict, List

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtCore import Qt

QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

import jedi


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.formats = {}
        self._setup_formats()
        self._setup_rules()

    def _setup_formats(self):
        self.formats = {
            'keyword': self._make_format('#569cd6', bold=True),
            'builtin': self._make_format('#4ec9b0'),
            'string': self._make_format('#ce9178'),
            'docstring': self._make_format('#ce9178', italic=True),
            'comment': self._make_format('#6a9955', italic=True),
            'decorator': self._make_format('#dcdcaa'),
            'number': self._make_format('#b5cea8'),
            'self': self._make_format('#569cd6', italic=True),
            'function': self._make_format('#dcdcaa'),
            'class': self._make_format('#4ec9b0', bold=True),
        }

    def _make_format(self, color, bold=False, italic=False):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def _setup_rules(self):
        self.rules = []
        keywords = [
            '\\bdef\\b', '\\bclass\\b', '\\bif\\b', '\\belif\\b', '\\belse\\b',
            '\\bfor\\b', '\\bwhile\\b', '\\breturn\\b', '\\bimport\\b', '\\bfrom\\b',
            '\\bas\\b', '\\btry\\b', '\\bexcept\\b', '\\bfinally\\b', '\\bwith\\b',
            '\\bpass\\b', '\\bbreak\\b', '\\bcontinue\\b', '\\bglobal\\b', '\\bnonlocal\\b',
            '\\blambda\\b', '\\bassert\\b', '\\braise\\b', '\\bdel\\b', '\\bin\\b',
            '\\bnot\\b', '\\band\\b', '\\bor\\b', '\\bis\\b', '\\bNone\\b',
            '\\bTrue\\b', '\\bFalse\\b', '\\byield\\b', '\\basync\\b', '\\bawait\\b'
        ]
        for pattern in keywords:
            self.rules.append((QRegularExpression(pattern), self.formats['keyword']))
        builtins = [
            '\\bprint\\b', '\\blen\\b', '\\brange\\b', '\\btype\\b', '\\bint\\b',
            '\\bstr\\b', '\\bfloat\\b', '\\blist\\b', '\\bdict\\b', '\\bset\\b',
            '\\btuple\\b', '\\bbool\\b', '\\bsuper\\b', '\\bobject\\b', '\\bisinstance\\b',
            '\\bissubclass\\b', '\\bhasattr\\b', '\\bgetattr\\b', '\\bsetattr\\b',
            '\\bdelattr\\b', '\\bcallable\\b', '\\biter\\b', '\\bnext\\b', '\\bzip\\b',
            '\\benumerate\\b', '\\bmap\\b', '\\bfilter\\b', '\\breduce\\b', '\\bsorted\\b',
            '\\breversed\\b', '\\bmin\\b', '\\bmax\\b', '\\bsum\\b', '\\babs\\b',
            '\\bround\\b', '\\bdivmod\\b', '\\bpow\\b', '\\bhex\\b', '\\boct\\b',
            '\\bbin\\b', '\\bformat\\b', '\\brepr\\b', '\\binput\\b', '\\bopen\\b',
            '\\bread\\b', '\\breadline\\b', '\\breadlines\\b', '\\bwrite\\b', '\\bclose\\b',
            '\\bappend\\b', '\\binsert\\b', '\\bremove\\b', '\\bpop\\b', '\\bindex\\b',
            '\\bcount\\b', '\\bjoin\\b', '\\bsplit\\b', '\\breplace\\b', '\\bstrip\\b',
            '\\bformat\\b', '\\bkeys\\b', '\\bvalues\\b', '\\bitems\\b', '\\bupdate\\b'
        ]
        for pattern in builtins:
            self.rules.append((QRegularExpression(pattern), self.formats['builtin']))
        self.rules.append((QRegularExpression('\\bself\\b'), self.formats['self']))
        self.rules.append((QRegularExpression('@\\w+'), self.formats['decorator']))
        self.rules.append((QRegularExpression('\\b\\d+(\\.\\d+)?\\b'), self.formats['number']))
        self.rules.append((QRegularExpression('\\b\\w+(?=\\()'), self.formats['function']))

    def highlightBlock(self, text):
        for pattern, format in self.rules:
            matches = pattern.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
        self._highlight_strings_and_comments(text)

    def _highlight_strings_and_comments(self, text):
        in_string = False
        string_char = None
        string_start = 0
        is_docstring = False
        for i, char in enumerate(text):
            if not in_string and char == '#':
                self.setFormat(i, len(text) - i, self.formats['comment'])
                break
            if not in_string:
                if text[i:i+3] in ['"""', "'''"]:
                    in_string = True
                    string_char = text[i:i+3]
                    string_start = i
                    is_docstring = True
                    i += 2
                    continue
                elif char in ['"', "'"]:
                    in_string = True
                    string_char = char
                    string_start = i
            else:
                if text[i:i+len(string_char)] == string_char:
                    if is_docstring:
                        length = i + 3 - string_start
                        self.setFormat(string_start, length, self.formats['docstring'])
                        in_string = False
                        string_char = None
                        is_docstring = False
                        i += len(string_char) - 1
                    else:
                        length = i + 1 - string_start
                        self.setFormat(string_start, length, self.formats['string'])
                        in_string = False
                        string_char = None


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = PythonHighlighter(self.document())
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.setup_editor()
        self.setup_bracket_matching()

    def setup_editor(self):
        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)
        self.setTabStopDistance(QFontMetricsF(self.font()).horizontalAdvance(' ') * 4)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
        """)

    def setup_bracket_matching(self):
        self.bracket_pairs = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}

    def keyPressEvent(self, event):
        if event.text() in self.bracket_pairs:
            cursor = self.textCursor()
            if cursor.hasSelection():
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                cursor.setPosition(start)
                cursor.insertText(event.text())
                cursor.setPosition(end + 1)
                cursor.insertText(self.bracket_pairs[event.text()])
                cursor.setPosition(start + 1)
                cursor.setPosition(end + 1, QTextCursor.MoveMode.KeepAnchor)
                self.setTextCursor(cursor)
                return
            cursor.insertText(event.text() + self.bracket_pairs[event.text()])
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor)
            self.setTextCursor(cursor)
            return
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            if cursor.hasSelection():
                self.indent_selection()
                return
            else:
                self.insertPlainText("    ")
                return
        if event.key() == Qt.Key.Key_Backtab:
            self.dedent_selection()
            return
        super().keyPressEvent(event)

    def indent_selection(self):
        cursor = self.textCursor()
        start = cursor.document().findBlock(cursor.selectionStart()).blockNumber()
        end = cursor.document().findBlock(cursor.selectionEnd()).blockNumber()
        cursor.beginEditBlock()
        for i in range(start, end + 1):
            block = cursor.document().findBlockByNumber(i)
            cursor.setPosition(block.position())
            cursor.insertText("    ")
        cursor.endEditBlock()

    def dedent_selection(self):
        cursor = self.textCursor()
        start = cursor.document().findBlock(cursor.selectionStart()).blockNumber()
        end = cursor.document().findBlock(cursor.selectionEnd()).blockNumber()
        cursor.beginEditBlock()
        for i in range(start, end + 1):
            block = cursor.document().findBlockByNumber(i)
            text = block.text()
            if text.startswith("    "):
                cursor.setPosition(block.position())
                cursor.setPosition(block.position() + 4, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
        cursor.endEditBlock()

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e1e"))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(),
                               Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2a2a2a")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)


class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.process = None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas;
                font-size: 11pt;
                border: none;
            }
        """)
        self.input_widget = QWidget()
        input_layout = QHBoxLayout(self.input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        self.prompt_label = QLabel(">>> ")
        self.prompt_label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                color: #d4d4d4;
                border: none;
                padding: 5px;
                font-family: Consolas;
                font-size: 11pt;
            }
        """)
        self.input_field.returnPressed.connect(self.send_input)
        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.input_field)
        layout.addWidget(self.output)
        layout.addWidget(self.input_widget)
        self.input_widget.hide()

    def append_output(self, text, color="#d4d4d4"):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        cursor.insertText(text, format)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def run_command(self, command, working_dir=None):
        self.output.clear()
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        if working_dir:
            self.process.setWorkingDirectory(working_dir)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.readyReadStandardError.connect(self._read_error)
        self.process.finished.connect(self._process_finished)
        self.process.start(command[0], command[1:])
        self.append_output(f"$ {' '.join(command)}\n", "#4ec9b0")

    def _read_output(self):
        if self.process:
            data = self.process.readAllStandardOutput()
            text = bytes(data).decode('utf-8', errors='replace')
            self.append_output(text, "#d4d4d4")

    def _read_error(self):
        if self.process:
            data = self.process.readAllStandardError()
            text = bytes(data).decode('utf-8', errors='replace')
            self.append_output(text, "#f48771")

    def _process_finished(self, exit_code, exit_status):
        self.input_widget.hide()
        status_color = "#4ec9b0" if exit_code == 0 else "#f48771"
        self.append_output(f"\nProcess finished with exit code {exit_code}\n", status_color)

    def send_input(self):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            text = self.input_field.text() + '\n'
            self.process.write(text.encode())
            self.append_output(text, "#ffffff")
            self.input_field.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python IDE")
        self.setGeometry(100, 100, 1400, 900)
        self.current_file_path = None
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("Project")
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                font-size: 12pt;
            }
        """)
        
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        
        self.editor = CodeEditor()
        self.editor_tabs.addTab(self.editor, "main.py")
        
        self.terminal = TerminalWidget()
        
        self.right_splitter.addWidget(self.editor_tabs)
        self.right_splitter.addWidget(self.terminal)
        self.right_splitter.setSizes([600, 300])
        
        self.main_splitter.addWidget(self.file_tree)
        self.main_splitter.addWidget(self.right_splitter)
        self.main_splitter.setSizes([250, 1150])
        
        main_layout.addWidget(self.main_splitter)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QMenuBar { background-color: #2d2d2d; color: #cccccc; padding: 3px; }
            QMenuBar::item { padding: 5px 10px; }
            QMenuBar::item:selected { background-color: #3e3e3e; }
            QMenu { background-color: #2d2d2d; color: #cccccc; border: 1px solid #3e3e3e; }
            QMenu::item:selected { background-color: #094771; }
            QTabWidget::pane { border: none; }
            QTabBar::tab { background-color: #2d2d2d; color: #cccccc; padding: 8px 15px; }
            QTabBar::tab:selected { background-color: #1e1e1e; color: #ffffff; border-top: 2px solid #007acc; }
            QStatusBar { background-color: #007acc; color: #ffffff; }
            QSplitter::handle { background-color: #2d2d2d; }
        """)

    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        run_menu = menubar.addMenu("&Run")
        run_action = QAction("&Run Python File", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.run_file)
        run_menu.addAction(run_action)

    def setup_status_bar(self):
        status_bar = self.statusBar()
        self.line_col_label = QLabel("Ln 1, Col 1")
        status_bar.addPermanentWidget(self.line_col_label)
        
        self.encoding_label = QLabel("UTF-8")
        status_bar.addPermanentWidget(self.encoding_label)
        
        self.python_label = QLabel("Python: System")
        status_bar.addPermanentWidget(self.python_label)
        
        self.editor.cursorPositionChanged.connect(self.update_status_bar)

    def update_status_bar(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.line_col_label.setText(f"Ln {line}, Col {col}")

    def new_file(self):
        editor = CodeEditor()
        index = self.editor_tabs.addTab(editor, "Untitled")
        self.editor_tabs.setCurrentIndex(index)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Python File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            editor = CodeEditor()
            editor.setPlainText(content)
            editor.setProperty('file_path', file_path)
            index = self.editor_tabs.addTab(editor, os.path.basename(file_path))
            self.editor_tabs.setCurrentIndex(index)
            self.current_file_path = file_path

    def save_file(self):
        editor = self.editor_tabs.currentWidget()
        if not editor:
            return
        file_path = editor.property('file_path')
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Python File", "", "Python Files (*.py)")
            if not file_path:
                return
            editor.setProperty('file_path', file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(editor.toPlainText())
        self.statusBar().showMessage("File saved", 2000)

    def close_tab(self, index):
        if self.editor_tabs.count() > 1:
            self.editor_tabs.removeTab(index)

    def detect_python_interpreter(self):
        venv_path = Path.cwd() / '.venv'
        if venv_path.exists():
            if os.name == 'nt':
                python_path = venv_path / 'Scripts' / 'python.exe'
            else:
                python_path = venv_path / 'bin' / 'python'
            if python_path.exists():
                return str(python_path)
        return "python" if os.name == 'nt' else "python3"

    def run_file(self):
        editor = self.editor_tabs.currentWidget()
        if not editor:
            return
        file_path = editor.property('file_path')
        if not file_path:
            self.save_file()
            file_path = editor.property('file_path')
            if not file_path:
                return
        interpreter = self.detect_python_interpreter()
        working_dir = os.path.dirname(file_path)
        self.terminal.run_command([interpreter, file_path], working_dir)


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("Python IDE")
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()