import sys
import random
import math
import json
import os

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


class SpinWheelWidget(QGraphicsView):
    def __init__(self, sectors, parent=None):
        super().__init__(parent)
        self.sectors = sectors
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setStyleSheet("background: transparent; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedSize(500, 500)

        # Запрещаем перемещение и масштабирование
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.centerOn(self.sceneRect().center())

        self._rotation = 0.0
        self.center = QPointF(200, 220)
        self._spin_callback = None

        self.anim = QPropertyAnimation(self, b"rotation")
        self.anim.setDuration(4000)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.finished.connect(self._on_spin_finished)

        self._build_wheel()

    def wheelEvent(self, event):
        # Отключаем зум колесиком мыши
        event.ignore()

    def mousePressEvent(self, event):
        # Отключаем перетаскивание барабана
        event.ignore()

    def _build_wheel(self):
        self.scene.clear()
        n = len(self.sectors)
        angle_step = 360 / n
        radius = 220
        rect = QRectF(self.center.x() - radius, self.center.y() - radius, radius * 2, radius * 2)

        self.wheel_group = self.scene.createItemGroup([])

        colors = [
            QColor("#e74c3c"), QColor("#3498db"), QColor("#2ecc71"),
            QColor("#f1c40f"), QColor("#9b59b6"), QColor("#e67e22"),
            QColor("#1abc9c"), QColor("#34495e")
        ]

        for i, sector_name in enumerate(self.sectors):
            start_angle = i * angle_step
            path = QPainterPath()
            path.moveTo(self.center)
            path.arcTo(rect, -start_angle, -angle_step)
            path.lineTo(self.center)

            sector_item = QGraphicsPathItem(path)
            sector_item.setBrush(QBrush(colors[i % len(colors)]))
            sector_item.setPen(QPen(QColor("#10131a"), 2))
            sector_item.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable, False)
            self.wheel_group.addToGroup(sector_item)

            text_item = QGraphicsTextItem(str(sector_name))
            font = QFont("Arial Black", 12)
            text_item.setFont(font)
            text_item.setDefaultTextColor(Qt.GlobalColor.white)

            mid_angle = start_angle + (angle_step / 2)
            rad = math.radians(mid_angle)

            tx = self.center.x() + (radius * 0.7) * math.cos(rad)
            ty = self.center.y() + (radius * 0.7) * math.sin(rad)

            text_rect = text_item.boundingRect()
            text_item.setTransformOriginPoint(text_rect.center())
            text_item.setRotation(mid_angle)
            text_item.setPos(tx - text_rect.width() / 2, ty - text_rect.height() / 2)
            text_item.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable, False)

            self.wheel_group.addToGroup(text_item)

        pointer_path = QPolygonF([
            QPointF(self.center.x(), 50),
            QPointF(self.center.x() - 18, 8),
            QPointF(self.center.x() + 18, 8)
        ])

        pointer = self.scene.addPolygon(
            pointer_path,
            QPen(Qt.GlobalColor.black, 2),
            QBrush(QColor("#FFD166"))
        )
        pointer.setZValue(100)
        pointer.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable, False)

        cap = self.scene.addEllipse(self.center.x() - 12, self.center.y() - 12, 24, 24,
                                    QPen(Qt.GlobalColor.black, 2), QBrush(QColor("#10131a")))
        cap.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable, False)
        self.wheel_group.addToGroup(cap)

    def getRotation(self):
        return self._rotation

    def setRotation(self, value):
        self._rotation = value
        transform = QTransform()
        transform.translate(self.center.x(), self.center.y())
        transform.rotate(value)
        transform.translate(-self.center.x(), -self.center.y())
        self.wheel_group.setTransform(transform)

    rotation = pyqtProperty(float, fget=getRotation, fset=setRotation)

    def spin(self, callback=None):
        self._spin_callback = callback
        n = len(self.sectors)
        chosen_index = random.randrange(n)

        # Угол одного сектора
        angle_per_sector = 360 / n

        # Расчет угла для остановки:
        # 1. Сектора отрисованы от 0 градусов (справа) ПО часовой стрелке.
        # 2. Стрелка находится сверху (на 270 градусах).
        # 3. Чтобы сектор 'i' оказался под стрелкой, нам нужно повернуть барабан
        #    на угол: 270 - (угол начала сектора + половина сектора)

        sector_center_angle = (chosen_index * angle_per_sector) + (angle_per_sector / 2)
        target_normalized = (270 - sector_center_angle) % 360

        # Добавляем несколько полных оборотов для эффекта анимации
        # ВАЖНО: вычитаем, так как вращение в анимации идет по нарастающей
        total_rotation = (360 * random.randint(5, 8)) + target_normalized

        self.anim.setStartValue(self._rotation)
        self.anim.setEndValue(self._rotation + total_rotation)
        self.anim.start()

        self._chosen_sector = self.sectors[chosen_index]

    def _on_spin_finished(self):
        if self._spin_callback:
            self._spin_callback(self._chosen_sector)


class PoleChudesApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поле Чудес")
        self.setMinimumSize(1400, 900)

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        self.players = [
            {"name": "Игрок 1", "score": 0},
            {"name": "Игрок 2", "score": 0},
            {"name": "Игрок 3", "score": 0}
        ]
        self.current_player_idx = 0

        # Данные для 3 раундов
        self.round_questions = []
        self.current_round = 0
        self.round_scores = [[0, 0, 0] for _ in range(3)]

        # Загрузка вопросов из JSON файла
        self.words_db = self.load_questions_from_json()

        if not self.words_db:
            QMessageBox.critical(
                self,
                "Ошибка загрузки вопросов",
                "Не удалось загрузить вопросы из файла 'questions.json'.\n"
                "Пожалуйста, создайте файл с вопросами и перезапустите игру.\n\n"
                "Формат файла:\n"
                "{\n"
                '  "questions": [\n'
                '    {"question": "Вопрос", "answer": "ОТВЕТ"}\n'
                "  ]\n"
                "}"
            )

        # Только основные сектора
        self.sectors = ["100", "200", "500", "1000", "БАНКРОТ", "0"]

        self.init_menu_screen()
        self.init_settings_screen()
        self.init_leaderboard_screen()
        self.init_game_screen()

        self.apply_styles()
        self.central_stack.setCurrentIndex(0)

    def load_questions_from_json(self):
        """Загрузка вопросов из файла questions.json"""
        try:
            json_path = "questions.json"

            if not os.path.exists(json_path):
                print(f"Файл {json_path} не найден")
                return []

            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            if isinstance(data, list):
                questions_list = data
            elif isinstance(data, dict) and "questions" in data:
                questions_list = data["questions"]
            else:
                print("Неверный формат JSON файла")
                return []

            words_db = []
            for item in questions_list:
                if "question" in item and "answer" in item:
                    words_db.append({
                        "q": item["question"],
                        "a": item["answer"].upper()
                    })

            if len(words_db) == 0:
                print("В файле нет вопросов")
                return []

            print(f"Загружено {len(words_db)} вопросов из questions.json")
            return words_db

        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            QMessageBox.critical(self, "Ошибка JSON", f"Файл questions.json содержит ошибки JSON:\n{e}")
            return []
        except Exception as e:
            print(f"Ошибка загрузки questions.json: {e}")
            return []

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
        btn_start.setEnabled(len(self.words_db) >= 3)

        if len(self.words_db) < 3:
            btn_start.setToolTip(f"Недостаточно вопросов (нужно минимум 3). Загружено: {len(self.words_db)}")
        else:
            btn_start.setToolTip("Начать игру из 3 раундов")

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

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #1f2937; border-radius: 12px; padding: 20px;")
        info_layout = QVBoxLayout(info_frame)

        info_label = QLabel("Информация о вопросах:")
        info_label.setStyleSheet("color: #ffd166; font-weight: bold; font-size: 18px;")
        info_layout.addWidget(info_label)

        questions_count = QLabel(f"Загружено вопросов: {len(self.words_db)}")
        questions_count.setStyleSheet("color: #e2e8f0; font-size: 14px;")
        info_layout.addWidget(questions_count)

        rounds_required = QLabel(f"Для игры из 3 раундов требуется минимум 3 вопроса")
        rounds_required.setStyleSheet("color: #94a3b8; font-size: 12px;")
        info_layout.addWidget(rounds_required)

        if len(self.words_db) < 3:
            warning_label = QLabel("⚠️ ВНИМАНИЕ: Недостаточно вопросов для 3 раундов!")
            warning_label.setStyleSheet("color: #ef476f; font-weight: bold; font-size: 14px;")
            info_layout.addWidget(warning_label)

        info_text = QLabel(
            "Вопросы загружаются из файла 'questions.json'\n"
            "Файл должен быть в той же папке, что и программа.\n\n"
            "Формат файла:\n"
            "{\n"
            '  "questions": [\n'
            '    {"question": "Вопрос", "answer": "ОТВЕТ"},\n'
            '    {"question": "Вопрос 2", "answer": "ОТВЕТ2"}\n'
            "  ]\n"
            "}"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #94a3b8; font-size: 12px;")
        info_layout.addWidget(info_text)

        l.addWidget(info_frame)

        btn_reload = QPushButton("Перезагрузить вопросы")
        btn_reload.clicked.connect(self.reload_questions)
        l.addWidget(btn_reload)

        btn_back = QPushButton("Назад в меню")
        btn_back.clicked.connect(lambda checked=False: self.central_stack.setCurrentIndex(0))
        l.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_stack.addWidget(page)

    def reload_questions(self):
        """Перезагрузка вопросов из JSON файла"""
        new_questions = self.load_questions_from_json()
        if new_questions:
            self.words_db = new_questions
            QMessageBox.information(self, "Успех", f"Вопросы перезагружены! Загружено {len(self.words_db)} вопросов.")
            menu_widget = self.central_stack.widget(0)
            if menu_widget:
                start_button = menu_widget.findChild(QPushButton)
                if start_button and start_button.text() == "Начать игру":
                    start_button.setEnabled(len(self.words_db) >= 3)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить вопросы. Проверьте файл questions.json")

    def init_leaderboard_screen(self):
        page = QWidget()
        l = QVBoxLayout(page)
        title = QLabel("Таблица лидеров")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        l.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.leaderboard_text = QLabel()
        self.leaderboard_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leaderboard_text.setStyleSheet("font-size: 16px; color: #e2e8f0; padding: 20px;")
        self.update_leaderboard_display()
        l.addWidget(self.leaderboard_text, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_back = QPushButton("Назад в меню")
        btn_back.clicked.connect(lambda checked=False: self.central_stack.setCurrentIndex(0))
        l.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_stack.addWidget(page)

    def update_leaderboard_display(self):
        """Обновление отображения таблицы лидеров"""
        sorted_players = sorted(self.players, key=lambda x: x["score"], reverse=True)
        text = "🏆 ТАБЛИЦА ЛИДЕРОВ 🏆\n\n"
        for i, player in enumerate(sorted_players, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
            text += f"{medal} {player['name']}: {player['score']} очков\n"
        self.leaderboard_text.setText(text)

    def init_game_screen(self):
        self.game_page = QWidget()
        self.game_layout = QVBoxLayout(self.game_page)
        self.game_page.setStyleSheet("background-color: #121826;")

        top_info_layout = QHBoxLayout()

        self.round_label = QLabel("РАУНД 1")
        self.round_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.round_label.setStyleSheet("color: #ffd166; padding: 10px;")

        self.score_info_label = QLabel("")
        self.score_info_label.setStyleSheet("color: #93c5fd; font-size: 14px;")

        top_info_layout.addWidget(self.round_label, alignment=Qt.AlignmentFlag.AlignCenter)
        top_info_layout.addWidget(self.score_info_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.game_layout.addLayout(top_info_layout)

        top_hbox = QHBoxLayout()
        header = QLabel("Поле Чудес")
        header.setFont(QFont("Arial", 28, QFont.Weight.Bold))
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
        self.player_score_labels = []

        for i in range(3):
            frame = QFrame()
            frame.setStyleSheet("background-color: #1f2937; border-radius: 12px; border: 1px solid #334155;")
            l = QVBoxLayout(frame)
            name_lbl = QLabel(f"Игрок {i + 1}")
            score_lbl = QLabel("Очки: 0")
            round_score_lbl = QLabel("В раунде: 0")
            round_score_lbl.setStyleSheet("color: #ffd166; font-size: 12px;")
            name_lbl.setStyleSheet("color: #93c5fd; font-weight: bold;")
            score_lbl.setStyleSheet("color: #f8fafc;")
            l.addWidget(name_lbl)
            l.addWidget(score_lbl)
            l.addWidget(round_score_lbl)
            players_hbox.addWidget(frame)
            self.player_widgets.append(score_lbl)
            self.player_frames.append(frame)
            self.player_score_labels.append(round_score_lbl)

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

        main_content = QHBoxLayout()

        left_panel = QVBoxLayout()
        self.lbl_sector = QLabel("Сектор: -")
        self.lbl_sector.setStyleSheet(
            "background-color: #334155; color: #ffffff; padding: 10px 18px; margin: 10px; border-radius: 10px;")
        left_panel.addWidget(self.lbl_sector, alignment=Qt.AlignmentFlag.AlignCenter)

        self.wheel = SpinWheelWidget(self.sectors)
        self.btn_spin = QPushButton("Крутите барабан!")
        self.btn_spin.setStyleSheet(
            "background-color: #22c55e; padding: 10px; border-radius: 10px; color: white; min-width: 220px;")
        self.btn_spin.clicked.connect(self.spin_drum)
        left_panel.addWidget(self.wheel, alignment=Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(self.btn_spin, alignment=Qt.AlignmentFlag.AlignCenter)

        main_content.addLayout(left_panel, 1)

        right_panel = QVBoxLayout()

        self.word_layout = QHBoxLayout()
        self.word_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addLayout(self.word_layout)

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

        right_panel.addLayout(self.alpha_grid)

        self.btn_full_word = QPushButton("Назвать слово")
        self.btn_full_word.setStyleSheet(
            "background-color: #8b5cf6; color: white; padding: 12px; min-width: 220px; border-radius: 10px;")
        self.btn_full_word.clicked.connect(self.guess_full_word)
        right_panel.addWidget(self.btn_full_word, alignment=Qt.AlignmentFlag.AlignCenter)

        main_content.addLayout(right_panel, 2)
        self.game_layout.addLayout(main_content)

        self.central_stack.addWidget(self.game_page)

    def start_new_game(self):
        if len(self.words_db) < 3:
            QMessageBox.critical(
                self,
                "Нет вопросов",
                f"Не удалось начать игру, так как недостаточно загруженных вопросов.\n"
                f"Требуется минимум 3 вопроса для 3 раундов. Загружено: {len(self.words_db)}\n"
                "Пожалуйста, добавьте вопросы в файл 'questions.json' и перезагрузите их в настройках."
            )
            self.central_stack.setCurrentIndex(0)
            return

        self.current_round = 0
        self.round_scores = [[0, 0, 0] for _ in range(3)]

        self.round_questions = random.sample(self.words_db, 3)

        for i in range(3):
            self.players[i]["score"] = 0

        self.start_round()

    def start_round(self):
        if self.current_round >= 3:
            self.show_final_results()
            return

        self.current_player_idx = 0
        for i in range(3):
            self.round_scores[self.current_round][i] = 0

        self.game_data = self.round_questions[self.current_round]
        self.current_word = self.game_data["a"]
        self.guessed_letters = []
        self.current_sector = "-"

        self.round_label.setText(f"РАУНД {self.current_round + 1}")
        self.score_info_label.setText(f"Слово из {len(self.current_word)} букв")
        self.lbl_question.setText(f"Вопрос: {self.game_data['q']}")
        self.lbl_sector.setText("Сектор: -")
        self.update_word_display()
        self.update_ui_state()
        self.toggle_alphabet(False)
        self.btn_spin.setEnabled(True)
        self.btn_full_word.setEnabled(True)

        QMessageBox.information(
            self,
            f"Начало {self.current_round + 1} раунда",
            f"Вопрос: {self.game_data['q']}\n\nСлово состоит из {len(self.current_word)} букв.\n\nПервый ходит Игрок 1."
        )

        self.central_stack.setCurrentIndex(3)

    def update_round_scores_display(self):
        for i in range(3):
            self.player_score_labels[i].setText(f"В раунде: {self.round_scores[self.current_round][i]}")

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
            self.round_scores[self.current_round][self.current_player_idx] = 0
            self.update_round_scores_display()
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

            # Проверяем, является ли сектор числовым (не БАНКРОТ и не 0)
            if str(self.current_sector).isdigit():
                # Получаем числовое значение сектора
                points_per_letter = int(self.current_sector)
                # Итоговые очки = значение сектора * количество открытых букв
                total_points = points_per_letter * count

                # Прибавляем очки в текущий раунд и в общий зачет
                self.round_scores[self.current_round][self.current_player_idx] += total_points
                self.players[self.current_player_idx]["score"] += total_points

                self.update_round_scores_display()

                QMessageBox.information(
                    self,
                    "Успех!",
                    f"Буква '{char}' есть в слове {count} раз(а)!\n"
                    f"Сектор: {points_per_letter}. Вы получили {total_points} очков!"
                )

            self.update_word_display()
            self.update_ui_state()

            # Проверка на полную победу в раунде
            if all(c in self.guessed_letters for c in self.current_word):
                bonus = 500
                self.round_scores[self.current_round][self.current_player_idx] += bonus
                self.players[self.current_player_idx]["score"] += bonus

                QMessageBox.information(
                    self,
                    "Слово отгадано!",
                    f"{self.players[self.current_player_idx]['name']} отгадал слово!\n"
                    f"Бонус за победу в раунде: {bonus} очков!"
                )

                self.current_round += 1
                self.start_round()
                return

            # Если угадал, игрок крутит барабан снова (не переключаем ход)
            self.toggle_alphabet(False)
            self.btn_spin.setEnabled(True)

        else:
            QMessageBox.warning(self, "Нет такой буквы", f"Буквы '{char}' нет в слове!")
            self.next_turn()

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
            self.round_scores[self.current_round][self.current_player_idx] += bonus
            self.players[self.current_player_idx]["score"] += bonus
            self.update_word_display()
            self.update_round_scores_display()
            self.update_ui_state()

            QMessageBox.information(
                self,
                "Победа!",
                f"Верно! {self.players[self.current_player_idx]['name']} угадал слово и получил {bonus} очков!\n\n"
                f"Переходим к следующему раунду."
            )

            self.current_round += 1
            self.start_round()
        else:
            QMessageBox.warning(self, "Неверно", "Слово не угадано. Ход переходит следующему игроку.")
            self.next_turn()

    def show_final_results(self):
        max_score = max(self.players, key=lambda x: x["score"])["score"]
        winners = [p for p in self.players if p["score"] == max_score]

        if len(winners) == 1:
            winner = winners[0]
            QMessageBox.information(
                self,
                "Игра окончена",
                f"🏆 ПОБЕДИТЕЛЬ ИГРЫ 🏆\n\n"
                f"{winner['name']} набрал {winner['score']} очков!\n\n"
                f"Поздравляем!"
            )
        else:
            QMessageBox.information(
                self,
                "Ничья!",
                f"У нескольких игроков одинаковый счет: {max_score} очков.\n"
                f"Победители: {', '.join([w['name'] for w in winners])}!"
            )

        self.save_game_results()
        self.central_stack.setCurrentIndex(0)

    def save_game_results(self):
        try:
            results_file = "game_results.json"
            results = []
            if os.path.exists(results_file):
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)

            game_result = {
                "date": str(__import__('datetime').datetime.now()),
                "players": self.players,
                "rounds": self.round_scores
            }
            results.append(game_result)

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            self.update_leaderboard_display()
        except Exception as e:
            print(f"Ошибка сохранения результатов: {e}")

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
        self.update_round_scores_display()

    def toggle_alphabet(self, state):
        for btn in self.alpha_buttons.values():
            if btn.text() not in self.guessed_letters:
                btn.setEnabled(state)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PoleChudesApp()
    window.show()
    sys.exit(app.exec())