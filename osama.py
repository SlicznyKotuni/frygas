import sys
import os
import random
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QApplication, QWidget, QLabel

# Ścieżka do katalogu z animacjami
ASSETS_DIR = "assets"

class AnimatedWidget(QLabel):
    def __init__(self, animations, parent=None):
        super().__init__(parent)
        self.animations = animations  # Słownik animacji
        self.current_animation = "idle"  # Domyślna animacja
        self.frame_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(100)  # Czas między klatkami (100 ms)
        self.setPixmap(self.animations[self.current_animation][0])
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setScaledContents(True)
        self.resize(100, 100)

        # Prędkość i ruch
        self.velocity = QPoint(0, 0)
        self.speed = 5

    def next_frame(self):
        """Przełącza na następną klatkę animacji."""
        frames = self.animations[self.current_animation]
        self.frame_index = (self.frame_index + 1) % len(frames)
        self.setPixmap(frames[self.frame_index])

    def set_animation(self, animation_name):
        """Ustawia rodzaj animacji."""
        if animation_name in self.animations:
            self.current_animation = animation_name
            self.frame_index = 0

    def move_towards(self, target_pos):
        """Przemieszcza widżet w kierunku pozycji myszy."""
        direction = QPoint(target_pos.x() - self.x(), target_pos.y() - self.y())
        if direction.manhattanLength() > self.speed:
            direction = direction / direction.manhattanLength() * self.speed
        self.move(self.pos() + direction)

    def mousePressEvent(self, event):
        """Zmienia animację na 'catch' po złapaniu."""
        if event.button() == Qt.LeftButton:
            self.set_animation("catch")
            self.timer.stop()

    def mouseReleaseEvent(self, event):
        """Przywraca animację 'idle' po puszczeniu."""
        if event.button() == Qt.LeftButton:
            self.set_animation("idle")
            self.timer.start(100)

    def mouseMoveEvent(self, event):
        """Przemieszcza widżet podczas przeciągania."""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.rect().center())


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Frygający Kotun")
        self.setGeometry(100, 100, 800, 600)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Tło przezroczyste
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Animowane widgety
        self.kotuns = []
        self.load_kotuns()

        # Timer do podążania za myszką
        self.mouse_pos = QPoint(0, 0)
        self.follow_timer = QTimer(self)
        self.follow_timer.timeout.connect(self.update_positions)
        self.follow_timer.start(16)  # 60 FPS

    def load_kotuns(self):
        """Ładuje zasoby animacji i tworzy widgety kotków."""
        if not os.path.exists(ASSETS_DIR):
            print("Tworzę katalog 'assets'...")
            os.makedirs(ASSETS_DIR)

        # Przeglądanie katalogów z animacjami
        kotun_dirs = [os.path.join(ASSETS_DIR, d) for d in os.listdir(ASSETS_DIR) if os.path.isdir(os.path.join(ASSETS_DIR, d))]
        for kotun_dir in kotun_dirs:
            animations = self.load_animations(kotun_dir)
            if animations:
                kotun = AnimatedWidget(animations, self)
                kotun.move(random.randint(0, self.width() - kotun.width()), random.randint(0, self.height() - kotun.height()))
                kotun.show()
                self.kotuns.append(kotun)

    def load_animations(self, directory):
        """Ładuje animacje z katalogu."""
        animations = {}
        for anim_type in ["idle", "run", "jump", "catch"]:
            anim_dir = os.path.join(directory, anim_type)
            if os.path.exists(anim_dir):
                frames = [QPixmap(os.path.join(anim_dir, f)) for f in sorted(os.listdir(anim_dir)) if f.endswith(".png")]
                if frames:
                    animations[anim_type] = frames
                else:
                    print(f"Brak klatek w animacji {anim_type} w katalogu {anim_dir}")
        return animations

    def mouseMoveEvent(self, event):
        """Śledzi pozycję myszy."""
        self.mouse_pos = event.globalPos()

    def update_positions(self):
        """Aktualizuje pozycje kotków, by podążały za myszką."""
        for kotun in self.kotuns:
            kotun.move_towards(self.mouse_pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())