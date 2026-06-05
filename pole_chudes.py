import sys
import random
import math
import json
import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QGridLayout, QMessageBox, QFrame, QGraphicsView,
    QGraphicsScene, QGraphicsPathItem, QGraphicsTextItem,
    QInputDialog, QComboBox, QScrollArea,QCheckBox, QGroupBox
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

        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        self.scene.setSceneRect(0, 0, 500, 500)
        self.centerOn(250, 250)

        self._rotation = 0.0
        self.center = QPointF(250, 250)
        self._spin_callback = None

        self.anim = QPropertyAnimation(self, b"rotation")
        self.anim.setDuration(4000)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.finished.connect(self._on_spin_finished)

        self._build_wheel()

    def wheelEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.centerOn(self.scene.sceneRect().center())
        self.center = QPointF(self.width() / 2, self.height() / 2)
        self._build_wheel()

    def showEvent(self, event):
        super().showEvent(event)
        self.centerOn(self.scene.sceneRect().center())
        self.center = QPointF(self.width() / 2, self.height() / 2)
        self._build_wheel()

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

        self._rotation = 0
        self.wheel_group.setTransform(QTransform())

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

        pointer_angle = 270
        angle_per_sector = 360 / n
        sector_center_angle = chosen_index * angle_per_sector + angle_per_sector / 2
        target_rotation = (pointer_angle - sector_center_angle) % 360
        full_rotations = random.randint(3, 8) * 360
        total_rotation = full_rotations + target_rotation

        current_rot = self._rotation % 360
        delta = total_rotation - current_rot
        if delta < 0:
            delta += 360

        self.anim.setStartValue(self._rotation)
        self.anim.setEndValue(self._rotation + delta)
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

        # Простые настройки (только тема)
        self.settings = {
            "theme": "dark"
        }
        self.load_settings()

        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)

        # Добавили поле "is_active": True для отслеживания статуса игрока в раунде
        self.players = [
            {"name": "Игрок 1", "score": 0, "is_active": True},
            {"name": "Игрок 2", "score": 0, "is_active": True},
            {"name": "Игрок 3", "score": 0, "is_active": True}
        ]
        self.current_player_idx = 0

        self.round_questions = []
        self.current_round = 0
        self.round_scores = [[0, 0, 0] for _ in range(3)]

        self.words_db = self.load_questions_from_json()
        # Измененный порядок секторов - БАНКРОТ и 0 не рядом
        self.sectors = ["100", "200", "500", "БАНКРОТ", "1000", "0"]

        self.init_menu_screen()
        self.init_settings_screen()
        self.init_leaderboard_screen()
        self.init_game_screen()

        self.apply_theme()
        self.central_stack.setCurrentIndex(0)

    def load_settings(self):
        """Загрузка простых настроек"""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    self.settings.update(loaded)
        except:
            pass

    def save_settings(self):
        """Сохранение простых настроек"""
        try:
            with open("settings.json", 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except:
            pass

    def apply_theme(self):
        """Применение темы"""
        if self.settings["theme"] == "dark":
            # Тёмная тема
            self.setStyleSheet("""
                QMainWindow { background-color: #10131a; }
                QWidget { color: #f5f7ff; font-size: 16px; }
                QLabel { color: #f5f7ff; }
                QLabel#titleLabel { color: #ffd166; }
                QPushButton {
                    background-color: #2d6cdf;
                    color: white;
                    border: none;
                    padding: 12px 18px;
                    border-radius: 10px;
                    font-size: 16px;
                }
                QPushButton:hover { background-color: #3f7df0; }
                QPushButton:disabled { background-color: #5a6475; color: #d8dde8; }

                /* Стилизация QMessageBox и QInputDialog для тёмной темы */
                QMessageBox, QInputDialog { background-color: #1e293b; }
                QMessageBox QLabel, QInputDialog QLabel { color: #f5f7ff; font-size: 15px; }
                QMessageBox QPushButton, QInputDialog QPushButton { background-color: #2d6cdf; color: white; min-width: 80px; }
                QInputDialog QLineEdit { 
                    background-color: #1f2937; 
                    color: #f5f7ff; 
                    border: 1px solid #334155; 
                    border-radius: 6px; 
                    padding: 5px; 
                }

                QGroupBox { 
                    font-weight: bold; 
                    border: 2px solid #334155; 
                    border-radius: 10px; 
                    margin-top: 10px; 
                    padding-top: 10px;
                    color: #f5f7ff;
                }
                QGroupBox::title { 
                    subcontrol-origin: margin; 
                    left: 10px; 
                    padding: 0 5px 0 5px;
                    color: #ffd166;
                }
                QComboBox { 
                    background-color: #1f2937; 
                    border: 1px solid #334155; 
                    border-radius: 6px; 
                    padding: 5px;
                    color: #f5f7ff;
                }
                QComboBox QAbstractItemView {
                    background-color: #1f2937;
                    color: #f5f7ff;
                }
                QScrollArea { background: transparent; border: none; }
            """)

            if hasattr(self, 'game_page'):
                self.game_page.setStyleSheet("""
                    background-color: #121826;
                    QLabel { color: #f5f7ff; }
                    QFrame { color: #f5f7ff; }
                """)

            if hasattr(self, 'btn_spin'):
                self.btn_spin.setStyleSheet("""
                    QPushButton {
                        background-color: #22c55e;
                        color: white;
                        padding: 10px;
                        border-radius: 10px;
                        font-size: 16px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover { background-color: #16a34a; }
                    QPushButton:disabled { background-color: #4ade80; color: #bbf7d0; }
                """)

            if hasattr(self, 'btn_full_word'):
                self.btn_full_word.setStyleSheet("""
                    QPushButton {
                        background-color: #8b5cf6;
                        color: white;
                        padding: 12px;
                        border-radius: 10px;
                        font-size: 16px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover { background-color: #7c3aed; }
                    QPushButton:disabled { background-color: #a78bfa; color: #e9d5ff; }
                """)

            if hasattr(self, 'question_frame'):
                self.question_frame.setStyleSheet("""
                    background-color: #1e293b;
                    min-height: 100px;
                    border-radius: 12px;
                    border: 1px solid #334155;
                """)
                self.lbl_question.setStyleSheet("color: #e2e8f0; font-size: 18px;")

            if hasattr(self, 'lbl_sector'):
                self.lbl_sector.setStyleSheet("""
                    background-color: #334155; color: white; padding: 10px; border-radius: 10px;
                """)

            if hasattr(self, 'round_label'):
                self.round_label.setStyleSheet("color: #ffd166; padding: 10px;")

            if hasattr(self, 'score_info_label'):
                self.score_info_label.setStyleSheet("color: #93c5fd; font-size: 14px;")

            if hasattr(self, 'alpha_buttons'):
                for btn in self.alpha_buttons.values():
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #475569; color: white; border-radius: 10px;
                            border: 2px solid #94a3b8; font-weight: bold;
                        }
                        QPushButton:hover { background-color: #64748b; }
                        QPushButton:disabled { background-color: #1f2937; color: #94a3b8; border: 2px solid #334155; }
                    """)

            if hasattr(self, 'player_frames'):
                for i, frame in enumerate(self.player_frames):
                    if i == self.current_player_idx:
                        frame.setStyleSheet(
                            "background-color: #14532d; border-radius: 12px; border: 2px solid #22c55e;")
                    else:
                        frame.setStyleSheet(
                            "background-color: #1f2937; border-radius: 12px; border: 1px solid #334155;")
        else:
            # Светлая тема
            self.setStyleSheet("""
                QMainWindow { background-color: #f0f2f5; }
                QWidget { color: #1a1a2e; font-size: 16px; }
                QLabel { color: #1a1a2e; }
                QLabel#titleLabel { color: #e67e22; }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 12px 18px;
                    border-radius: 10px;
                    font-size: 16px;
                }
                QPushButton:hover { background-color: #2980b9; }
                QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }

                /* Стилизация QMessageBox и QInputDialog для светлой темы — исправляет невидимый текст */
                QMessageBox, QInputDialog { background-color: #ffffff; }
                QMessageBox QLabel, QInputDialog QLabel { color: #1a1a2e; font-size: 15px; }
                QMessageBox QPushButton, QInputDialog QPushButton { background-color: #3498db; color: white; min-width: 80px; }

                /* Стилизация поля ввода внутри окна "Назвать слово" */
                QInputDialog QLineEdit { 
                    background-color: #ffffff; 
                    color: #1a1a2e; 
                    border: 2px solid #bdc3c7; 
                    border-radius: 8px; 
                    padding: 6px; 
                }

                QGroupBox { 
                    font-weight: bold; 
                    border: 2px solid #d0d3d4; 
                    border-radius: 10px; 
                    margin-top: 10px; 
                    padding-top: 10px;
                    color: #1a1a2e;
                }
                QGroupBox::title { 
                    subcontrol-origin: margin; 
                    left: 10px; 
                    padding: 0 5px 0 5px;
                    color: #e67e22;
                }
                QComboBox { 
                    background-color: #ffffff; 
                    border: 1px solid #d0d3d4; 
                    border-radius: 6px; 
                    padding: 5px;
                    color: #1a1a2e;
                }
                QComboBox QAbstractItemView {
                    background-color: #ffffff;
                    color: #1a1a2e;
                }
                QScrollArea { background: transparent; border: none; }
            """)

            if hasattr(self, 'game_page'):
                self.game_page.setStyleSheet("""
                    background-color: #f0f2f5;
                    QLabel { color: #1a1a2e; }
                    QFrame { color: #1a1a2e; }
                """)

            if hasattr(self, 'btn_spin'):
                self.btn_spin.setStyleSheet("""
                    QPushButton {
                        background-color: #10b981;
                        color: white;
                        padding: 10px;
                        border-radius: 10px;
                        font-size: 16px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover { background-color: #059669; }
                    QPushButton:disabled { background-color: #6ee7b7; color: #ecfdf5; }
                """)

            if hasattr(self, 'btn_full_word'):
                self.btn_full_word.setStyleSheet("""
                    QPushButton {
                        background-color: #8b5cf6;
                        color: white;
                        padding: 12px;
                        border-radius: 10px;
                        font-size: 16px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover { background-color: #7c3aed; }
                    QPushButton:disabled { background-color: #c4b5fd; color: #ede9fe; }
                """)

            if hasattr(self, 'question_frame'):
                self.question_frame.setStyleSheet("""
                    background-color: #ffffff;
                    min-height: 100px;
                    border-radius: 12px;
                    border: 2px solid #e5e7eb;
                """)
                self.lbl_question.setStyleSheet("color: #1a1a2e; font-size: 18px;")

            if hasattr(self, 'lbl_sector'):
                self.lbl_sector.setStyleSheet("""
                    background-color: #e0e0e0; color: #1a1a2e; padding: 10px; border-radius: 10px; font-weight: bold;
                """)

            if hasattr(self, 'round_label'):
                self.round_label.setStyleSheet("color: #e67e22; padding: 10px; font-weight: bold;")

            if hasattr(self, 'score_info_label'):
                self.score_info_label.setStyleSheet("color: #2980b9; font-size: 14px;")

            if hasattr(self, 'alpha_buttons'):
                for btn in self.alpha_buttons.values():
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #ecf0f1; color: #1a1a2e; border-radius: 10px;
                            border: 2px solid #bdc3c7; font-weight: bold;
                        }
                        QPushButton:hover { background-color: #d5dbdb; }
                        QPushButton:disabled { background-color: #e0e0e0; color: #7f8c8d; border: 2px solid #d0d3d4; }
                    """)

            if hasattr(self, 'player_frames'):
                for i, frame in enumerate(self.player_frames):
                    if i == self.current_player_idx:
                        frame.setStyleSheet(
                            "background-color: #d4efdf; border-radius: 12px; border: 2px solid #27ae60;")
                    else:
                        frame.setStyleSheet(
                            "background-color: #ffffff; border-radius: 12px; border: 2px solid #e5e7eb;")

    def load_questions_from_json(self):
        """Загрузка вопросов"""
        try:
            if not os.path.exists("questions.json"):
                return []
            with open("questions.json", 'r', encoding='utf-8') as file:
                data = json.load(file)
            if isinstance(data, list):
                questions_list = data
            elif isinstance(data, dict) and "questions" in data:
                questions_list = data["questions"]
            else:
                return []
            words_db = []
            for item in questions_list:
                if "question" in item and "answer" in item:
                    words_db.append({"q": item["question"], "a": item["answer"].upper()})
            return words_db
        except:
            return []

    # ==================== ТАБЛИЦА ЛИДЕРОВ ====================

    def load_leaderboard(self):
        """Загрузка таблицы лидеров из файла (только топ-3)"""
        try:
            if os.path.exists("leaderboard.json"):
                with open("leaderboard.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data[:3]
            return []
        except:
            return []

    def save_to_leaderboard(self):
        """Сохраняет результат победителя, обновляет топ-3"""
        # Определяем победителя
        max_score = max(self.players, key=lambda x: x["score"])["score"]
        winners = [p for p in self.players if p["score"] == max_score]

        if not winners:
            return

        winner = winners[0]

        # Загружаем существующую таблицу
        leaderboard = self.load_leaderboard()

        # Добавляем нового победителя
        leaderboard.append({
            "name": winner["name"],
            "score": winner["score"],
            "date": datetime.now().strftime("%d.%m.%Y")
        })

        # Сортируем по очкам (по убыванию)
        leaderboard.sort(key=lambda x: x["score"], reverse=True)

        # Оставляем только топ-3
        leaderboard = leaderboard[:3]

        # Сохраняем
        try:
            with open("leaderboard.json", 'w', encoding='utf-8') as f:
                json.dump(leaderboard, f, ensure_ascii=False, indent=2)
        except:
            pass

        # Обновляем отображение
        self.update_leaderboard_display()

        # Проверяем, побит ли рекорд
        if leaderboard and winner["score"] == leaderboard[0]["score"] and len(leaderboard) > 0:
            QMessageBox.information(self, "🏆 НОВЫЙ РЕКОРД! 🏆",
                                    f"{winner['name']} установил(а) новый рекорд!\n\n"
                                    f"{winner['score']} очков - это лучший результат за всё время!")

    def update_leaderboard_display(self):
        """Обновляет отображение таблицы лидеров (только топ-3)"""
        leaderboard = self.load_leaderboard()

        if not leaderboard:
            self.leaderboard_text.setText("🏆 ТАБЛИЦА ЛИДЕРОВ 🏆\n\n"
                                          "Пока нет результатов.\n"
                                          "Сыграйте и установите рекорд!")
            return

        text = "🏆 ТАБЛИЦА ЛИДЕРОВ 🏆\n\n"
        text += "═══ ЛУЧШИЕ РЕЗУЛЬТАТЫ ═══\n\n"

        for i, entry in enumerate(leaderboard, 1):
            if i == 1:
                medal = "🥇 1-е место"
                medal_color = "🏆"
            elif i == 2:
                medal = "🥈 2-е место"
                medal_color = "⭐"
            else:
                medal = "🥉 3-е место"
                medal_color = "✨"

            name = entry["name"][:20]
            score = entry["score"]
            date = entry.get("date", "")

            text += f"{medal_color} {medal}\n"
            text += f"   👤 {name}\n"
            text += f"   📊 {score} очков\n"
            if date:
                text += f"   📅 {date}\n"
            text += "\n"
            text += "────────────────────\n\n"

        # Рекордная информация
        if leaderboard:
            record = leaderboard[0]["score"]
            text += f"\n🔥 РЕКОРД ВСЕХ ВРЕМЕН: {record} очков 🔥"

        self.leaderboard_text.setText(text)

    def clear_leaderboard(self):
        """Очищает таблицу лидеров"""
        reply = QMessageBox.question(
            self,
            "Очистка таблицы",
            "Вы уверены, что хотите очистить таблицу лидеров?\nЭто действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open("leaderboard.json", 'w', encoding='utf-8') as f:
                    json.dump([], f)
                self.update_leaderboard_display()
                QMessageBox.information(self, "Готово", "Таблица лидеров очищена!")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось очистить таблицу: {e}")

    # ==================== ЭКРАНЫ ====================

    def init_menu_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("ПОЛЕ ЧУДЕС")
        title.setObjectName("titleLabel")
        title.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Главное меню")
        subtitle.setFont(QFont("Arial", 18))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buttons_layout = QVBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.setSpacing(12)

        btn_start = QPushButton("Начать игру")
        btn_start.setEnabled(len(self.words_db) >= 3)
        btn_start.clicked.connect(self.start_new_game)
        btn_start.setFixedWidth(250)

        btn_settings = QPushButton("Настройки")
        btn_settings.clicked.connect(lambda: self.central_stack.setCurrentIndex(1))
        btn_settings.setFixedWidth(250)

        btn_leaders = QPushButton("Таблица лидеров")
        btn_leaders.clicked.connect(lambda: self.central_stack.setCurrentIndex(2))
        btn_leaders.setFixedWidth(250)

        btn_exit = QPushButton("Выход")
        btn_exit.clicked.connect(self.close)
        btn_exit.setFixedWidth(250)

        buttons_layout.addWidget(btn_start)
        buttons_layout.addWidget(btn_settings)
        buttons_layout.addWidget(btn_leaders)
        buttons_layout.addWidget(btn_exit)

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(subtitle)
        layout.addSpacing(40)
        layout.addLayout(buttons_layout)
        layout.addStretch(2)

        self.central_stack.addWidget(page)

    def init_settings_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(20)

        title = QLabel("Настройки")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        display_group = QGroupBox("🖥️ Параметры экрана")
        display_layout = QVBoxLayout(display_group)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Тёмная", "Светлая"])
        self.theme_combo.setCurrentText("Тёмная" if self.settings["theme"] == "dark" else "Светлая")
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        display_layout.addLayout(theme_layout)

        layout.addWidget(display_group)

        btn_back = QPushButton("Назад в меню")
        btn_back.clicked.connect(lambda: self.central_stack.setCurrentIndex(0))
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)

        self.central_stack.addWidget(page)

    def on_theme_changed(self, theme):
        self.settings["theme"] = "dark" if theme == "Тёмная" else "light"
        self.save_settings()
        self.apply_theme()

    def init_leaderboard_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("🏆 ТАБЛИЦА ЛИДЕРОВ 🏆")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.leaderboard_text = QLabel()
        self.leaderboard_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leaderboard_text.setWordWrap(True)

        if self.settings["theme"] == "dark":
            self.leaderboard_text.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    padding: 30px;
                    background-color: #1e293b;
                    border-radius: 20px;
                    margin: 20px;
                    font-family: 'Arial';
                }
            """)
        else:
            self.leaderboard_text.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    padding: 30px;
                    background-color: #ffffff;
                    border-radius: 20px;
                    margin: 20px;
                    font-family: 'Arial';
                    border: 2px solid #e5e7eb;
                }
            """)

        scroll.setWidget(self.leaderboard_text)
        layout.addWidget(scroll)

        self.update_leaderboard_display()

        btn_layout = QHBoxLayout()

        btn_refresh = QPushButton("🔄 Обновить")
        btn_refresh.clicked.connect(self.update_leaderboard_display)

        btn_clear = QPushButton("🗑️ Очистить всё")
        btn_clear.setStyleSheet("background-color: #ef476f;")
        btn_clear.clicked.connect(self.clear_leaderboard)

        btn_back = QPushButton("◀ Назад в меню")
        btn_back.clicked.connect(lambda: self.central_stack.setCurrentIndex(0))

        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_back)

        layout.addLayout(btn_layout)

        self.central_stack.addWidget(page)

    def init_game_screen(self):
        self.game_page = QWidget()
        self.game_layout = QVBoxLayout(self.game_page)

        # === ВЕРХНЯЯ ПАНЕЛЬ С НАЗВАНИЕМ И РАУНДОМ ПО ЦЕНТРУ ===
        header_main_layout = QHBoxLayout()
        header_main_layout.setContentsMargins(20, 10, 20, 10)

        # Пустышка слева для идеальной центровки заголовка
        header_main_layout.addStretch(1)

        # Центральный контейнер для Названия и Раунда
        title_block = QVBoxLayout()
        title_block.setSpacing(5)  # Расстояние между названием и раундом

        header = QLabel("Поле Чудес")
        header.setFont(QFont("Arial", 80, QFont.Weight.Bold))  # Увеличенный шрифт
        header.setStyleSheet("color: #ffd166;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.round_label = QLabel("РАУНД 1")
        self.round_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))  # Шрифт для раунда чуть меньше
        self.round_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_block.addWidget(header)
        title_block.addWidget(self.round_label)
        header_main_layout.addLayout(title_block, stretch=2)

        # Правая часть: кнопка выхода и информация об очках
        right_block = QVBoxLayout()
        right_block.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right_block.setSpacing(5)

        btn_exit_game = QPushButton("Выход")
        btn_exit_game.setStyleSheet(
            "background-color: #ef476f; color: white; padding: 8px 20px; border-radius: 10px; max-width: 120px;")
        btn_exit_game.clicked.connect(lambda: self.central_stack.setCurrentIndex(0))

        self.score_info_label = QLabel("")
        self.score_info_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        right_block.addWidget(btn_exit_game)
        right_block.addWidget(self.score_info_label)

        header_main_layout.addLayout(right_block, stretch=1)

        self.game_layout.addLayout(header_main_layout)
        # ======================================================

        players_hbox = QHBoxLayout()
        self.player_widgets = []
        self.player_frames = []
        self.player_score_labels = []

        for i in range(3):
            frame = QFrame()
            l = QVBoxLayout(frame)
            name_lbl = QLabel(f"Игрок {i + 1}")
            score_lbl = QLabel("Очки: 0")
            round_score_lbl = QLabel("В раунде: 0")
            round_score_lbl.setStyleSheet("font-size: 12px;")
            name_lbl.setStyleSheet("font-weight: bold;")
            l.addWidget(name_lbl)
            l.addWidget(score_lbl)
            l.addWidget(round_score_lbl)
            players_hbox.addWidget(frame)
            self.player_widgets.append(score_lbl)
            self.player_frames.append(frame)
            self.player_score_labels.append(round_score_lbl)

        self.game_layout.addLayout(players_hbox)

        self.question_frame = QFrame()
        q_l = QVBoxLayout(self.question_frame)
        self.lbl_question = QLabel("Вопрос: ...")
        self.lbl_question.setWordWrap(True)
        q_l.addWidget(self.lbl_question, alignment=Qt.AlignmentFlag.AlignCenter)
        self.game_layout.addWidget(self.question_frame)

        main_content = QHBoxLayout()
        left_panel = QVBoxLayout()
        self.lbl_sector = QLabel("Сектор: -")
        left_panel.addWidget(self.lbl_sector, alignment=Qt.AlignmentFlag.AlignCenter)

        self.wheel = SpinWheelWidget(self.sectors)
        self.btn_spin = QPushButton("Крутите барабан!")
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
        self.btn_full_word.clicked.connect(self.guess_full_word)
        right_panel.addWidget(self.btn_full_word, alignment=Qt.AlignmentFlag.AlignCenter)
        main_content.addLayout(right_panel, 2)
        self.game_layout.addLayout(main_content)

        self.central_stack.addWidget(self.game_page)
        self.apply_theme()

    # ==================== ИГРОВАЯ ЛОГИКА ====================

    def start_new_game(self):
        if len(self.words_db) < 3:
            QMessageBox.critical(self, "Ошибка", f"Недостаточно вопросов! Нужно минимум 3.")
            self.central_stack.setCurrentIndex(0)
            return

        self.current_round = 0
        self.round_scores = [[0, 0, 0] for _ in range(3)]
        self.round_questions = random.sample(self.words_db, 3)
        for i in range(3):
            self.players[i]["score"] = 0
            self.players[i]["is_active"] = True  # Возвращаем всех в игру
        self.start_round()

    def start_round(self):
        if self.current_round >= 3:
            self.show_final_results()
            return

        self.current_player_idx = 0
        for i in range(3):
            self.round_scores[self.current_round][i] = 0
            self.players[i]["is_active"] = True  # Сброс флага активности: в новом раунде снова играют ВСЕ

        self.game_data = self.round_questions[self.current_round]
        self.current_word = self.game_data["a"]
        self.guessed_letters = []
        self.current_sector = "-"

        self.round_label.setText(f"РАУНД {self.current_round + 1}")
        self.lbl_question.setText(f"Вопрос: {self.game_data['q']}")
        self.lbl_sector.setText("Сектор: -")

        self.update_word_display()
        self.update_ui_state()
        self.toggle_alphabet(False)
        self.btn_spin.setEnabled(True)
        self.btn_full_word.setEnabled(True)

        QMessageBox.information(self, f"Раунд {self.current_round + 1}",
                                f"Вопрос: {self.game_data['q']}\n\nСлово из {len(self.current_word)} букв.\n\nХодит Игрок 1.")
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
            display_char = char if char in self.guessed_letters else ""
            lbl = QLabel(display_char)
            lbl.setFixedSize(54, 54)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.settings["theme"] == "dark":
                lbl.setStyleSheet("""
                    background-color: #334155;
                    color: white;
                    border: 2px solid #64748b;
                    font-size: 22px;
                    font-weight: bold;
                    border-radius: 10px;
                """)
            else:
                lbl.setStyleSheet("""
                    background-color: #e0e0e0;
                    color: #1a1a2e;
                    border: 2px solid #bdc3c7;
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
            total_score = 0
            for round_num in range(3):
                total_score += self.round_scores[round_num][self.current_player_idx]
            self.players[self.current_player_idx]["score"] = total_score
            self.update_round_scores_display()
            self.update_ui_state()
            QMessageBox.warning(self, "БАНКРОТ!", f"{self.players[self.current_player_idx]['name']} - банкрот!")
            self.next_turn()
            return

        if sector == "0":
            QMessageBox.information(self, "Сектор 0", "Ход переходит следующему игроку.")
            self.next_turn()
            return

        self.toggle_alphabet(True)

    def guess_letter(self, char):
        if char in self.guessed_letters:
            QMessageBox.warning(self, "Ошибка", f"Буква '{char}' уже открыта!")
            return

        self.alpha_buttons[char].setEnabled(False)
        self.guessed_letters.append(char)

        if char in self.current_word:
            count = self.current_word.count(char)
            if str(self.current_sector).isdigit():
                points_per_letter = int(self.current_sector)
                total_points = points_per_letter * count
                self.round_scores[self.current_round][self.current_player_idx] += total_points
                total_score = 0
                for round_num in range(3):
                    total_score += self.round_scores[round_num][self.current_player_idx]
                self.players[self.current_player_idx]["score"] = total_score
                self.update_round_scores_display()
                self.update_ui_state()
                QMessageBox.information(self, "Успех!", f"Буква '{char}' есть {count} раз! +{total_points} очков!")

            self.update_word_display()
            self.update_ui_state()

            if all(c in self.guessed_letters for c in self.current_word):
                bonus = 500
                self.round_scores[self.current_round][self.current_player_idx] += bonus
                total_score = 0
                for round_num in range(3):
                    total_score += self.round_scores[round_num][self.current_player_idx]
                self.players[self.current_player_idx]["score"] = total_score
                self.update_round_scores_display()
                self.update_ui_state()
                QMessageBox.information(self, "Победа!", f"Слово отгадано! +{bonus} очков!")
                self.current_round += 1
                self.start_round()
                return

            self.toggle_alphabet(False)
            self.btn_spin.setEnabled(True)
        else:
            QMessageBox.warning(self, "Ошибка", f"Буквы '{char}' нет в слове!")
            self.next_turn()

    def guess_full_word(self):
        text, ok = QInputDialog.getText(self, "Назвать слово", "Введите слово:")
        if not ok or not text:
            return

        answer = text.strip().upper()
        if answer == self.current_word:
            self.guessed_letters = list(set(self.current_word))
            bonus = 1000
            self.round_scores[self.current_round][self.current_player_idx] += bonus
            total_score = 0
            for round_num in range(3):
                total_score += self.round_scores[round_num][self.current_player_idx]
            self.players[self.current_player_idx]["score"] = total_score
            self.update_word_display()
            self.update_round_scores_display()
            self.update_ui_state()
            QMessageBox.information(self, "Победа!", f"Верно! +{bonus} очков!")
            self.current_round += 1
            self.start_round()
        else:
            # ИГРОК ОШИБСЯ: Исключаем его из текущего раунда
            self.players[self.current_player_idx]["is_active"] = False
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Слово не угадано!\n{self.players[self.current_player_idx]['name']} выбывает до конца этого раунда."
            )
            self.next_turn()

    def show_final_results(self):
        max_score = max(self.players, key=lambda x: x["score"])["score"]
        winners = [p for p in self.players if p["score"] == max_score]

        # Проверяем, побит ли рекорд
        leaderboard = self.load_leaderboard()
        is_record = False
        if leaderboard:
            current_record = leaderboard[0]["score"] if leaderboard else 0
            if max_score > current_record:
                is_record = True
        else:
            is_record = True

        results_text = "РЕЗУЛЬТАТЫ:\n\n"
        for i, player in enumerate(sorted(self.players, key=lambda x: x["score"], reverse=True), 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
            results_text += f"{medal} {player['name']}: {player['score']} очков\n"

        if len(winners) == 1:
            message = f"🏆 ПОБЕДИТЕЛЬ: {winners[0]['name']}!\n\n{results_text}"
            if is_record:
                message += f"\n🔥 НОВЫЙ РЕКОРД! {max_score} очков! 🔥"
        else:
            message = f"🤝 НИЧЬЯ!\n\n{results_text}"

        QMessageBox.information(self, "Игра окончена", message)

        # Сохраняем в таблицу лидеров
        self.save_to_leaderboard()

        self.reset_game_state()
        self.central_stack.setCurrentIndex(0)

    def reset_game_state(self):
        for i in range(3):
            self.players[i]["score"] = 0
            self.players[i]["is_active"] = True
        self.current_round = 0
        self.round_scores = [[0, 0, 0] for _ in range(3)]
        self.round_questions = []
        self.current_word = ""
        self.guessed_letters = []
        self.current_sector = "-"
        self.current_player_idx = 0
        self.update_word_display()
        self.update_ui_state()
        self.toggle_alphabet(False)
        self.btn_spin.setEnabled(False)
        self.btn_full_word.setEnabled(False)
        self.update_leaderboard_display()

    def next_turn(self):
        """Переход хода к следующему АКТИВНОМУ игроку в раунде"""
        # Проверяем, остался ли вообще хоть один активный игрок в раунде
        active_players = [p for p in self.players if p["is_active"]]

        if not active_players:
            QMessageBox.information(
                self,
                "Раунд окончен",
                "Все игроки выбыли из раунда, так как не угадали слово! Переходим к следующему раунду."
            )
            self.current_round += 1
            self.start_round()
            return

        # Ищем следующего активного игрока по кругу
        attempts = 0
        while attempts < 3:
            self.current_player_idx = (self.current_player_idx + 1) % 3
            if self.players[self.current_player_idx]["is_active"]:
                break
            attempts += 1

        self.update_ui_state()
        self.toggle_alphabet(False)
        self.btn_spin.setEnabled(True)
        QMessageBox.information(self, "Смена хода", f"Ходит {self.players[self.current_player_idx]['name']}")

    def update_ui_state(self):
        for i, lbl in enumerate(self.player_widgets):
            lbl.setText(f"Очки: {self.players[i]['score']}")
            parent = lbl.parent()

            # Визуально затеняем карточку игрока, если он выбыл в этом раунде
            if not self.players[i]["is_active"]:
                if self.settings["theme"] == "dark":
                    parent.setStyleSheet("background-color: #0f172a; border-radius: 12px; border: 2px dashed #334155;")
                else:
                    parent.setStyleSheet("background-color: #f3f4f6; border-radius: 12px; border: 2px dashed #d1d5db;")
            else:
                if self.settings["theme"] == "dark":
                    parent.setStyleSheet(
                        f"background-color: {'#14532d' if i == self.current_player_idx else '#1f2937'}; "
                        f"border-radius: 12px; border: 2px solid {'#22c55e' if i == self.current_player_idx else '#334155'};"
                    )
                else:
                    parent.setStyleSheet(
                        f"background-color: {'#d4efdf' if i == self.current_player_idx else '#ffffff'}; "
                        f"border-radius: 12px; border: 2px solid {'#27ae60' if i == self.current_player_idx else '#e5e7eb'};"
                    )
        self.update_round_scores_display()

    def toggle_alphabet(self, state):
        for btn in self.alpha_buttons.values():
            char = btn.text()
            if char not in self.guessed_letters:
                btn.setEnabled(state)
            else:
                btn.setEnabled(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PoleChudesApp()
    window.show()
    sys.exit(app.exec())