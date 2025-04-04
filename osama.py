import sys
import os
import random
import math
import time
from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QSize
from PySide6.QtGui import QPixmap, QPainter, QTransform, QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget, QLabel

ASSETS_DIR = "assets"

class AnimatedWidget(QLabel):
    def __init__(self, animations, parent=None):
        super().__init__(parent)
        self.animations = animations  # Słownik animacji
        self.current_animation = "idle"  # Domyślna animacja
        self.frame_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)
        self.timer.start(100)  # zmiana klatki co 100 ms
        self.original_frames = {}
        for anim_name, frames in self.animations.items():
            self.original_frames[anim_name] = frames.copy()
        self.setPixmap(self.animations[self.current_animation][0])
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setScaledContents(True)
        self.resize(100, 100)

        # Ruch i kierunek
        self.velocity = QPoint(0, 0)
        self.speed = 5
        self.is_caught = False
        self.animation_repeat_count = 0
        self.animation_repeats = 3
        self.facing_right = True
        self.rotation = 0

        # Nowe flagi i timery dla polowania
        self.hunting = False  # czy kotek właśnie poluje
        # Ustalamy pierwszy możliwy start polowania za 60 sekund od startu aplikacji
        self.hunt_next_time = time.time() + 60  
        
    def next_frame(self):
        frames = self.animations[self.current_animation]
        self.frame_index = (self.frame_index + 1) % len(frames)
        self.setPixmap(frames[self.frame_index])
        if self.frame_index == len(frames) - 1:
            self.animation_repeat_count += 1
            if self.animation_repeat_count >= self.animation_repeats and not self.is_caught:
                self.animation_repeat_count = 0
                if self.current_animation not in ["idle", "hunt"]:
                    self.set_animation("idle")

    def set_animation(self, animation_name):
        if animation_name in self.animations and self.current_animation != animation_name:
            self.current_animation = animation_name
            self.frame_index = 0
            self.animation_repeat_count = 0
            self.update_direction()

    def update_direction(self):
        if self.velocity.x() == 0 and self.velocity.y() == 0:
            return
        new_facing_right = self.velocity.x() >= 0
        if abs(self.velocity.y()) > abs(self.velocity.x()):
            angle = -30 if self.velocity.y() < 0 else 30
        else:
            angle = 0
        if new_facing_right != self.facing_right or angle != self.rotation:
            self.facing_right = new_facing_right
            self.rotation = angle
            self.update_animation_frames()
    
    def update_animation_frames(self):
        for anim_name, original_frames in self.original_frames.items():
            transformed_frames = []
            for frame in original_frames:
                original_size = frame.size()
                transformed_frame = QPixmap(original_size)
                transformed_frame.fill(Qt.transparent)
                painter = QPainter(transformed_frame)
                painter.translate(original_size.width() / 2, original_size.height() / 2)
                if self.rotation != 0:
                    painter.rotate(self.rotation)
                if not self.facing_right:
                    painter.scale(-1, 1)
                painter.drawPixmap(-original_size.width() / 2, -original_size.height() / 2, frame)
                painter.end()
                transformed_frames.append(transformed_frame)
            self.animations[anim_name] = transformed_frames
        if self.animations[self.current_animation]:
            self.setPixmap(self.animations[self.current_animation][self.frame_index])

    def move_randomly(self):
        if not self.is_caught and not self.hunting:
            self.velocity = QPoint(random.randint(-10, 10), random.randint(-10, 10))
            if self.velocity.manhattanLength() > 0:
                self.set_animation("run")
                self.update_direction()

    def move_towards(self, target_pos):
        if self.is_caught:
            self.move(target_pos - QPoint(self.width() // 2, self.height() // 2))

    def jump(self):
        if not self.is_caught and not self.hunting:
            self.velocity = QPoint(random.randint(-15, 15), random.randint(-15, 15))
            self.set_animation("jump")
            self.update_direction()

    def catch(self, caught=True):
        self.is_caught = caught
        if caught:
            self.set_animation("catch")
        else:
            self.set_animation("idle")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Frygający Kotun")
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self.kotuns = []
        self.load_kotuns()
        self.caught_kotun = None
        self.mouse_pos = QPoint(0, 0)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_kotuns)
        self.update_timer.start(1000)  # co 1 sekunda

        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.update_positions)
        self.position_timer.start(50)  # płynny ruch

        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def load_kotuns(self):
        if not os.path.exists(ASSETS_DIR):
            print("Tworzę katalog 'assets'...")
            os.makedirs(ASSETS_DIR)
        kotun_dirs = [os.path.join(ASSETS_DIR, d) for d in os.listdir(ASSETS_DIR)
                      if os.path.isdir(os.path.join(ASSETS_DIR, d))]
        for kotun_dir in kotun_dirs:
            animations = self.load_animations(kotun_dir)
            if animations:
                kotun = AnimatedWidget(animations, self)
                kotun.move(random.randint(0, self.width() - kotun.width()),
                           random.randint(0, self.height() - kotun.height()))
                kotun.show()
                self.kotuns.append(kotun)

    def load_animations(self, directory):
        animations = {}
        for anim_type in ["idle", "run", "jump", "catch", "hunt", "attack", "win"]:
            anim_dir = os.path.join(directory, anim_type)
            if os.path.exists(anim_dir):
                frames = [QPixmap(os.path.join(anim_dir, f))
                          for f in sorted(os.listdir(anim_dir))
                          if f.endswith(".png")]
                if frames:
                    animations[anim_type] = frames
                else:
                    print(f"Brak klatek w animacji {anim_type} w katalogu {anim_dir}")
        return animations

    def update_kotuns(self):
        now = time.time()
        for kotun in self.kotuns:
            # Jeśli kotek nie jest łapany i nie poluje, sprawdzamy czy może rozpocząć polowanie.
            if not kotun.is_caught and not kotun.hunting:
                if now >= kotun.hunt_next_time:
                    # Na potrzeby testów dajemy wysoką szansę - zawsze rozpoczyna polowanie.
                    kotun.hunting = True
                    kotun.set_animation("hunt")
                else:
                    # Normalne zachowanie: losowy ruch lub skok.
                    action = random.choice(["move", "jump", "idle"])
                    if action == "move":
                        kotun.move_randomly()
                    elif action == "jump":
                        kotun.jump()
                    elif action == "idle":
                        kotun.velocity = QPoint(0, 0)
                        kotun.set_animation("idle")

    def move_kotun(self, kotun):
        if not kotun.is_caught and not kotun.hunting and kotun.velocity.manhattanLength() > 0:
            new_pos = kotun.pos() + kotun.velocity
            screen_width = self.width()
            screen_height = self.height()
            if new_pos.x() < -kotun.width():
                new_pos.setX(screen_width)
            elif new_pos.x() > screen_width:
                new_pos.setX(-kotun.width())
            if new_pos.y() < -kotun.height():
                new_pos.setY(screen_height)
            elif new_pos.y() > screen_height:
                new_pos.setY(-kotun.height())
            kotun.move(new_pos)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for kotun in self.kotuns:
                if kotun.geometry().contains(event.pos()):
                    self.caught_kotun = kotun
                    kotun.catch(True)
                    break

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.caught_kotun:
            self.caught_kotun.catch(False)
            self.caught_kotun = None

    def mouseMoveEvent(self, event):
        self.mouse_pos = event.pos()

    def update_positions(self):
        # Jeśli kotek jest złapany, podążamy za myszą
        if self.caught_kotun:
            self.caught_kotun.move_towards(self.mouse_pos)

        for kotun in self.kotuns:
            if kotun.hunting:
                # W trybie polowania, kotek podąża za kursorem
                cat_center = kotun.pos() + QPoint(kotun.width() // 2, kotun.height() // 2)
                dx = self.mouse_pos.x() - cat_center.x()
                dy = self.mouse_pos.y() - cat_center.y()
                distance = math.hypot(dx, dy)
                attack_threshold = 50  # próg odległości do wykonania ataku
                
                if distance < attack_threshold:
                    # Gdy kotek jest wystarczająco blisko, wykonaj atak
                    kotun.set_animation("attack")
                    # Przeskocz dokładnie na pozycję kursora
                    kotun.move(self.mouse_pos - QPoint(kotun.width() // 2, kotun.height() // 2))
                    # Przyjmujemy, że atak zawsze się udaje – wyświetlamy animację "win"
                    kotun.set_animation("win")
                    # Zakoncz polowanie i ustaw cooldown na 120 sekund
                    kotun.hunting = False
                    kotun.hunt_next_time = time.time() + 120
                else:
                    # Ruch w kierunku myszy
                    if distance != 0:
                        step_x = int(kotun.speed * dx / distance)
                        step_y = int(kotun.speed * dy / distance)
                        new_pos = kotun.pos() + QPoint(step_x, step_y)
                        kotun.move(new_pos)
            elif not kotun.is_caught:
                self.move_kotun(kotun)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())