import sys
import json
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                             QGridLayout, QMessageBox, QFrame, QInputDialog)
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen


# --- ВИДЖЕТ БАРАБАНА (Анимированный графический элемент) ---
class SpinningDrum(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(260, 260)
        self._angle = 0
        self.sectors = ["100", "500", "0", "1000", "БАНКРОТ", "ПЛЮС", "200", "ПРИЗ"]
        self.colors = [QColor("#FF5733"), QColor("#33FF57"), QColor("#3357FF"),
                       QColor("#F333FF"), QColor("#111111"), QColor("#FFD700"),
                       QColor("#33FFF3"), QColor("#FF8C00")]

    @pyqtProperty(float)
    def angle(self): return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.contentsRect()
        center = rect.center()
        radius = rect.width() // 2 - 15

        num = len(self.sectors)
        span = 360 / num

        for i in range(num):
            painter.setBrush(QBrush(self.colors[i]))
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            start_angle = int((self._angle + i * span) * 16)
            painter.drawPie(center.x() - radius, center.y() - radius, radius * 2, radius * 2,
                            start_angle, int(span * 16))

        # Указатель барабана
        painter.setBrush(QBrush(QColor("red")))
        painter.drawPolygon(center.x(), 5, center.x() - 15, 30, center.x() + 15, 30)


# --- ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ ---
class PoleChudesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_data()
        self.init_ui()

    def load_data(self):
        try:
            with open('data.json', 'r', encoding='utf-8') as f:
                self.game_data = json.load(f)
        except:
            self.game_data = {"questions": [{"q": "Ошибка загрузки", "a": "JSON"}], "leaders": []}

    def init_ui(self):
        self.setWindowTitle("Поле Чудес - Колледж ВятГУ")
        self.setMinimumSize(1024, 768)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Индексы экранов: 0 - Меню, 1 - Игра, 2 - Лидеры, 3 - Настройки
        self.setup_menu()
        self.setup_game_screen()
        self.setup_leaders()
        self.setup_settings()

        self.stack.setCurrentIndex(0)

    # --- ЭКРАН 0: ГЛАВНОЕ МЕНЮ (согласно Рисунку 4) ---
    def setup_menu(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("ПОЛЕ ЧУДЕС\nГлавное меню")
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_style = "QPushButton { padding: 15px; font-size: 18px; min-width: 300px; background: #E0E0E0; border: 1px solid gray; }"

        btns = [
            ("Начать игру", lambda: self.start_new_game()),
            ("Настройки", lambda: self.stack.setCurrentIndex(3)),
            ("Таблица лидеров", lambda: self.stack.setCurrentIndex(2)),
            ("Выход", self.close)
        ]

        layout.addStretch()
        layout.addWidget(title)
        layout.addSpacing(40)
        for text, func in btns:
            btn = QPushButton(text)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(func)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            layout.addSpacing(10)
        layout.addStretch()
        self.stack.addWidget(page)

    # --- ЭКРАН 1: ИГРОВОЕ ПОЛЕ (согласно Рисунку 5) ---
    def setup_game_screen(self):
        self.game_page = QWidget()
        main_layout = QVBoxLayout(self.game_page)

        # Верхняя панель: Игроки и Выход
        top_hbox = QHBoxLayout()
        self.p_labels = []
        for i in range(3):
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
            v = QVBoxLayout(frame)
            name = QLabel(f"Игрок {i + 1}")
            score = QLabel("Очки: 0")
            v.addWidget(name);
            v.addWidget(score)
            top_hbox.addWidget(frame)
            self.p_labels.append({"name": name, "score": score, "frame": frame})

        btn_exit = QPushButton("Выход")
        btn_exit.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        top_hbox.addWidget(btn_exit, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(top_hbox)

        # Вопрос
        self.lbl_question = QLabel("Вопрос: ...")
        self.lbl_question.setStyleSheet("background: #E0E0E0; padding: 20px; font-size: 18px; border: 1px solid gray;")
        self.lbl_question.setWordWrap(True)
        main_layout.addWidget(self.lbl_question)

        # Сектор и Табло слова
        self.lbl_sector = QLabel("Сектор на барабане: ---")
        self.lbl_sector.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_sector)

        self.word_layout = QHBoxLayout()
        main_layout.addLayout(self.word_layout)

        # Центр: Барабан и Алфавит
        mid_layout = QHBoxLayout()

        # Лево: Барабан
        drum_vbox = QVBoxLayout()
        self.drum_widget = SpinningDrum()
        self.btn_spin = QPushButton("Крутите барабан!")
        self.btn_spin.setFixedHeight(50)
        self.btn_spin.clicked.connect(self.spin_drum)
        drum_vbox.addWidget(self.drum_widget)
        drum_vbox.addWidget(self.btn_spin)
        mid_layout.addLayout(drum_vbox)

        # Право: Алфавит
        self.alpha_grid = QGridLayout()
        self.letter_btns = {}
        alphabet = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
        for i, char in enumerate(alphabet):
            btn = QPushButton(char)
            btn.setFixedSize(40, 40)
            btn.clicked.connect(lambda ch=char: self.guess_letter(ch))
            btn.setEnabled(False)
            self.alpha_grid.addWidget(btn, i // 11, i % 11)
            self.letter_btns[char] = btn

        alpha_vbox = QVBoxLayout()
        alpha_vbox.addLayout(self.alpha_grid)
        btn_solve = QPushButton("Назвать слово")
        btn_solve.clicked.connect(self.solve_word_entirely)
        alpha_vbox.addWidget(btn_solve)
        mid_layout.addLayout(alpha_vbox)

        main_layout.addLayout(mid_layout)
        self.stack.addWidget(self.game_page)

    # --- ЛОГИКА ИГРЫ ---
    def start_new_game(self):
        self.current_player = 0
        self.player_scores = [0, 0, 0]
        question_data = random.choice(self.game_data["questions"])
        self.current_answer = question_data["a"].upper()
        self.lbl_question.setText(f"Вопрос: {question_data['q']}")
        self.revealed_letters = []

        self.update_word_display()
        self.update_turn_ui()
        self.btn_spin.setEnabled(True)
        for btn in self.letter_btns.values(): btn.setEnabled(False)
        self.stack.setCurrentIndex(1)

    def update_word_display(self):
        # Очистка старых букв
        for i in reversed(range(self.word_layout.count())):
            self.word_layout.itemAt(i).widget().setParent(None)

        for char in self.current_answer:
            box = QLabel(char if char in self.revealed_letters else "?")
            box.setFixedSize(50, 50)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.setStyleSheet("border: 2px solid black; font-weight: bold; font-size: 20px; background: white;")
            self.word_layout.addWidget(box)

    def spin_drum(self):
        self.btn_spin.setEnabled(False)
        self.anim = QPropertyAnimation(self.drum_widget, b"angle")
        self.anim.setDuration(2000)
        self.anim.setStartValue(self.drum_widget.angle)
        # Случайное вращение минимум на 2 круга
        target = self.drum_widget.angle + 720 + random.randint(0, 360)
        self.anim.setEndValue(target)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.finished.connect(self.handle_spin_result)
        self.anim.start()

    def handle_spin_result(self):
        # Расчет выпавшего сектора
        angle = self.drum_widget.angle % 360
        idx = int((360 - angle + 22.5) % 360 // 45)
        self.current_sector = self.drum_widget.sectors[idx % 8]
        self.lbl_sector.setText(f"Выпало: {self.current_sector}")

        if self.current_sector == "БАНКРОТ":
            self.player_scores[self.current_player] = 0
            self.next_turn()
        else:
            for btn in self.letter_btns.values():
                if btn.text() not in self.revealed_letters: btn.setEnabled(True)

    def guess_letter(self, char):
        for btn in self.letter_btns.values(): btn.setEnabled(False)

        if char in self.current_answer:
            count = self.current_answer.count(char)
            self.revealed_letters.append(char)

            # Расчет очков S = P x N
            points = int(self.current_sector) if self.current_sector.isdigit() else 100
            self.player_scores[self.current_player] += points * count

            self.update_word_display()
            self.update_turn_ui()

            if all(c in self.revealed_letters for c in self.current_answer):
                self.win_game()
            else:
                self.btn_spin.setEnabled(True)
        else:
            self.next_turn()

    def solve_word_entirely(self):
        text, ok = QInputDialog.getText(self, "Ваш ответ", "Введите слово целиком:")
        if ok and text.upper() == self.current_answer:
            self.player_scores[self.current_player] += 5000
            self.win_game()
        elif ok:
            QMessageBox.warning(self, "Ошибка", "Неверно! Переход хода.")
            self.next_turn()

    def next_turn(self):
        self.current_player = (self.current_player + 1) % 3
        self.update_turn_ui()
        self.btn_spin.setEnabled(True)
        QMessageBox.information(self, "Переход хода", f"Теперь ходит Игрок {self.current_player + 1}")

    def update_turn_ui(self):
        for i in range(3):
            self.p_labels[i]["score"].setText(f"Очки: {self.player_scores[i]}")
            color = "#A5D6A7" if i == self.current_player else "#ecf0f1"
            self.p_labels[i]["frame"].setStyleSheet(f"background: {color}; border: 2px solid gray;")

    def win_game(self):
        winner_idx = self.current_player
        score = self.player_scores[winner_idx]
        QMessageBox.information(self, "Победа!", f"Игрок {winner_idx + 1} угадал слово!\nСчет: {score}")
        self.save_score(f"Игрок {winner_idx + 1}", score)
        self.stack.setCurrentIndex(0)

    def save_score(self, name, score):
        self.game_data["leaders"].append({"name": name, "score": score})
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(self.game_data, f, ensure_ascii=False)

    # --- ЭКРАНЫ ТАБЛИЦЫ И НАСТРОЕК ---
    def setup_leaders(self):
        page = QWidget();
        lay = QVBoxLayout(page)
        lay.addWidget(QLabel("ТАБЛИЦА ЛИДЕРОВ"), alignment=Qt.AlignmentFlag.AlignCenter)
        self.leader_list = QLabel("Загрузка...")
        lay.addWidget(self.leader_list)
        btn = QPushButton("Назад");
        btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        lay.addWidget(btn)
        self.stack.addWidget(page)

    def setup_settings(self):
        page = QWidget();
        lay = QVBoxLayout(page)
        lay.addWidget(QLabel("НАСТРОЙКИ\n\nРазработчик: Бушмакин А.А.\nКолледж ВятГУ 2026"))
        btn = QPushButton("Назад");
        btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        lay.addWidget(btn)
        self.stack.addWidget(page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PoleChudesApp()
    window.show()
    sys.exit(app.exec())