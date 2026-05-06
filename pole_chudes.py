import sys
import random
import math

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QGridLayout, QMessageBox, QFrame, QGraphicsView,
    QGraphicsScene, QGraphicsPathItem, QGraphicsTextItem,
    QInputDialog
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPointF, pyqtProperty, QRectF
from PyQt6.QtGui import (
    QFont, QPen, QBrush, QColor, QTransform, QPainter,
    QPainterPath, QPolygonF
)




class PoleChudesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поле Чудес")
        self.setMinimumSize(1024, 768)

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        self.players = [
            {"name": "Игрок 1", "score": 0},
            {"name": "Игрок 2", "score": 0},
            {"name": "Игрок 3", "score": 0}
        ]
        self.current_player_idx = 0

        self.words_db = [
            {"q": "Столица России?", "a": "МОСКВА"},
            {"q": "Студент, разработавший это ПО?", "a": "БУШМАКИН"}
        ]

        self.sectors = ["100", "200", "500", "1000", "БАНКРОТ", "ПЛЮС", "0"]

        self.init_menu_screen()
        self.init_settings_screen()
        self.init_leaderboard_screen()
        self.init_game_screen()

        self.apply_styles()
        self.central_stack.setCurrentIndex(0)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #10131a;
            }
            QWidget {
                color: #f5f7ff;
                font-size: 16px;
            }
            QLabel#titleLabel {
                color: #ffd166;
            }
            QPushButton {
                background-color: #2d6cdf;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 10px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #3f7df0;
            }
            QPushButton:disabled {
                background-color: #5a6475;
                color: #d8dde8;
            }
        """)

    def init_menu_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("ПОЛЕ ЧУДЕС")
        title.setObjectName("titleLabel")
        title.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        subtitle = QLabel("Главное меню")
        subtitle.setFont(QFont("Arial", 18))

        btn_style = """
            QPushButton {
                background-color: #2d6cdf;
                color: white;
                border: none;
                padding: 15px;
                font-size: 18px;
                min-width: 300px;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #3f7df0;
            }
        """

        btn_start = QPushButton("Начать игру")
        btn_start.clicked.connect(self.start_new_game)

        btn_settings = QPushButton("Настройки")
        btn_settings.clicked.connect(lambda checked=False: self.central_stack.setCurrentIndex(1))

        btn_leaders = QPushButton("Таблица лидеров")
        btn_leaders.clicked.connect(lambda checked=False: self.central_stack.setCurrentIndex(2))

        btn_exit = QPushButton("Выход")
        btn_exit.clicked.connect(self.close)

        for btn in [btn_start, btn_settings, btn_leaders, btn_exit]:
            btn.setStyleSheet(btn_style)

        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(40)
        layout.addWidget(btn_start)
        layout.addSpacing(10)
        layout.addWidget(btn_settings)
        layout.addSpacing(10)
        layout.addWidget(btn_leaders)
        layout.addSpacing(10)
        layout.addWidget(btn_exit)

        self.central_stack.addWidget(page)

    def init_settings_screen(self):
        page = QWidget()
        l = QVBoxLayout(page)
        title = QLabel("Настройки")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        l.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_back = QPushButton("Назад в меню")
        btn_back.clicked.connect(lambda checked=False: self.central_stack.setCurrentIndex(0))
        l.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_stack.addWidget(page)

    def init_leaderboard_screen(self):
        page = QWidget()
        l = QVBoxLayout(page)
        title = QLabel("Таблица лидеров")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        l.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        l.addWidget(QLabel("1. Игрок 1 - 5000\n2. Игрок 2 - 3000"), alignment=Qt.AlignmentFlag.AlignCenter)

        btn_back = QPushButton("Назад в меню")
        btn_back.clicked.connect(lambda checked=False: self.central_stack.setCurrentIndex(0))
        l.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_stack.addWidget(page)

    def init_game_screen(self):
        self.game_page = QWidget()
        self.game_layout = QVBoxLayout(self.game_page)
        self.game_page.setStyleSheet("background-color: #121826;")

        top_hbox = QHBoxLayout()
        header = QLabel("Поле Чудес")
        header.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffd166;")

        btn_exit_game = QPushButton("Выход")
        btn_exit_game.setStyleSheet("background-color: #ef476f; color: white; padding: 8px 20px; border-radius: 10px;")
        btn_exit_game.clicked.connect(lambda checked=False: self.central_stack.setCurrentIndex(0))

        top_hbox.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)
        top_hbox.addWidget(btn_exit_game, alignment=Qt.AlignmentFlag.AlignRight)
        self.game_layout.addLayout(top_hbox)

        players_hbox = QHBoxLayout()
        self.player_widgets = []
        self.player_frames = []

        for i in range(3):
            frame = QFrame()
            frame.setStyleSheet("background-color: #1f2937; border-radius: 12px; border: 1px solid #334155;")
            l = QVBoxLayout(frame)
            name_lbl = QLabel(f"Игрок {i + 1}")
            score_lbl = QLabel("Очки: 0")
            name_lbl.setStyleSheet("color: #93c5fd; font-weight: bold;")
            score_lbl.setStyleSheet("color: #f8fafc;")
            l.addWidget(name_lbl)
            l.addWidget(score_lbl)
            players_hbox.addWidget(frame)
            self.player_widgets.append(score_lbl)
            self.player_frames.append(frame)

        self.game_layout.addLayout(players_hbox)

        self.question_frame = QFrame()
        self.question_frame.setStyleSheet(
            "background-color: #1e293b; min-height: 100px; border-radius: 12px; border: 1px solid #334155;")
        q_l = QVBoxLayout(self.question_frame)
        self.lbl_question = QLabel("Вопрос: ...")
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setStyleSheet("color: #e2e8f0; font-size: 18px;")
        q_l.addWidget(self.lbl_question, alignment=Qt.AlignmentFlag.AlignCenter)
        self.game_layout.addWidget(self.question_frame)

        self.lbl_sector = QLabel("Сектор: -")
        self.lbl_sector.setStyleSheet(
            "background-color: #334155; color: #ffffff; padding: 10px 18px; margin: 10px; border-radius: 10px;")
        self.game_layout.addWidget(self.lbl_sector, alignment=Qt.AlignmentFlag.AlignCenter)

        self.word_layout = QHBoxLayout()
        self.word_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.game_layout.addLayout(self.word_layout)

        bottom_hbox = QHBoxLayout()



        alpha_vbox = QVBoxLayout()
        self.alpha_grid = QGridLayout()
        alphabet = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        self.alpha_buttons = {}
        row, col = 0, 0

        for char in alphabet:
            btn = QPushButton(char)
            btn.setFixedSize(52, 52)
            btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #475569;
                    color: white;
                    border-radius: 10px;
                    border: 2px solid #94a3b8;
                }
                QPushButton:hover {
                    background-color: #64748b;
                }
                QPushButton:disabled {
                    background-color: #1f2937;
                    color: #94a3b8;
                    border: 2px solid #334155;
                }
            """)
            btn.clicked.connect(lambda checked=False, c=char: self.guess_letter(c))
            btn.setEnabled(False)
            self.alpha_grid.addWidget(btn, row, col)
            self.alpha_buttons[char] = btn
            col += 1
            if col > 10:
                col = 0
                row += 1

        alpha_vbox.addLayout(self.alpha_grid)

        self.btn_full_word = QPushButton("Назвать слово")
        self.btn_full_word.setStyleSheet(
            "background-color: #8b5cf6; color: white; padding: 12px; min-width: 220px; border-radius: 10px;")
        self.btn_full_word.clicked.connect(self.guess_full_word)
        alpha_vbox.addWidget(self.btn_full_word, alignment=Qt.AlignmentFlag.AlignCenter)

        bottom_hbox.addLayout(alpha_vbox)
        self.game_layout.addLayout(bottom_hbox)

        self.central_stack.addWidget(self.game_page)

    def start_new_game(self):
        self.current_player_idx = 0
        self.players = [
            {"name": "Игрок 1", "score": 0},
            {"name": "Игрок 2", "score": 0},
            {"name": "Игрок 3", "score": 0}
        ]
        self.game_data = random.choice(self.words_db)
        self.current_word = self.game_data["a"]
        self.guessed_letters = []
        self.current_sector = "-"

        self.lbl_question.setText(f"Вопрос: {self.game_data['q']}")
        self.lbl_sector.setText("Сектор: -")
        self.update_word_display()
        self.update_ui_state()
        self.toggle_alphabet(False)
        self.btn_spin.setEnabled(True)
        self.btn_full_word.setEnabled(True)
        self.central_stack.setCurrentIndex(3)

    def update_word_display(self):
        for i in reversed(range(self.word_layout.count())):
            item = self.word_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)

        for char in self.current_word:
            lbl = QLabel(char if char in self.guessed_letters else "")
            lbl.setFixedSize(54, 54)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                background-color: #334155;
                color: white;
                border: 2px solid #64748b;
                font-size: 22px;
                font-weight: bold;
                border-radius: 10px;
            """)
            self.word_layout.addWidget(lbl)

    def spin_drum(self):
        self.btn_spin.setEnabled(False)
        self.toggle_alphabet(False)
        self.wheel.spin(callback=self.on_wheel_stopped)

    def on_wheel_stopped(self, sector):
        self.current_sector = sector
        self.lbl_sector.setText(f"Сектор: {sector}")

        if sector == "БАНКРОТ":
            self.players[self.current_player_idx]["score"] = 0
            self.update_ui_state()
            self.next_turn()
            return

        if sector == "0":
            self.next_turn()
            return

        self.toggle_alphabet(True)

    def guess_letter(self, char):
        self.alpha_buttons[char].setEnabled(False)

        if char in self.current_word:
            self.guessed_letters.append(char)
            count = self.current_word.count(char)

            if str(self.current_sector).isdigit():
                self.players[self.current_player_idx]["score"] += int(self.current_sector) * count

            self.update_word_display()
            self.update_ui_state()

            if all(c in self.guessed_letters for c in self.current_word):
                QMessageBox.information(self, "Победа!", f"Победил {self.players[self.current_player_idx]['name']}!")
                self.central_stack.setCurrentIndex(0)
                return
        else:
            self.next_turn()
            return

        self.toggle_alphabet(False)
        self.btn_spin.setEnabled(True)

    def guess_full_word(self):
        text, ok = QInputDialog.getText(self, "Назвать слово", "Введите слово целиком:")
        if not ok:
            return

        answer = text.strip().upper()
        if not answer:
            QMessageBox.warning(self, "Ошибка", "Введите слово.")
            return

        if answer == self.current_word:
            self.guessed_letters = list(set(self.current_word))
            bonus = 1000
            self.players[self.current_player_idx]["score"] += bonus
            self.update_word_display()
            self.update_ui_state()

            QMessageBox.information(
                self,
                "Победа!",
                f"Верно! {self.players[self.current_player_idx]['name']} угадал слово и получил {bonus} очков!"
            )
            self.central_stack.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "Неверно", "Слово не угадано. Ход переходит следующему игроку.")
            self.next_turn()

    def next_turn(self):
        self.current_player_idx = (self.current_player_idx + 1) % 3
        self.update_ui_state()
        self.toggle_alphabet(False)
        self.btn_spin.setEnabled(True)
        QMessageBox.information(self, "Смена хода", f"Ходит {self.players[self.current_player_idx]['name']}")

    def update_ui_state(self):
        for i, lbl in enumerate(self.player_widgets):
            lbl.setText(f"Очки: {self.players[i]['score']}")
            parent = lbl.parent()
            parent.setStyleSheet(
                f"background-color: {'#14532d' if i == self.current_player_idx else '#1f2937'}; "
                f"border-radius: 12px; border: 1px solid {'#22c55e' if i == self.current_player_idx else '#334155'};"
            )

    def toggle_alphabet(self, state):
        for btn in self.alpha_buttons.values():
            if btn.text() not in self.guessed_letters:
                btn.setEnabled(state)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PoleChudesApp()
    window.show()
    sys.exit(app.exec())