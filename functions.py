import os
import random
from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtGui import QPixmap, QCursor, QTransform
from PyQt5.QtCore import Qt, QTimer, QObject, QEvent
from stats import CAT_STATS, DEFAULT_STATS


class CatWidget(QLabel):
    all_cats = []

    def __init__(self, asset_path):
        super().__init__()
        self.asset_path = asset_path
        self.name = os.path.basename(asset_path)
        self.stats = CAT_STATS.get(self.name, DEFAULT_STATS.copy())

        self.animations = self.load_animations(asset_path)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setScaledContents(True)
        self.setFixedSize(128, 128)

        self.state = "idle"
        self.direction = 1
        self.dragging = False
        self.avoid_cursor = False
        self.sleeping = False

        self.current_frame = 0
        self.frames = []
        self.load_animation("idle")

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(100)

        self.behavior_timer = QTimer()
        self.behavior_timer.timeout.connect(self.random_behavior)
        self.behavior_timer.start(3000)

        self.hunt_timer = QTimer()
        self.hunt_timer.timeout.connect(self.start_hunting)
        self.hunt_timer.start(random.randint(10000, 30000))

        self.chasing = False
        self.chase_target_cat = None
        self.fleeing = False
        self.chase_timer = QTimer()

        self.move(random.randint(0, 800), random.randint(0, 600))

        CatWidget.all_cats.append(self)

        if len(CatWidget.all_cats) == 1:
            self.global_chase_timer = QTimer()
            self.global_chase_timer.timeout.connect(self.start_random_chase)
            self.global_chase_timer.start(15000)

    def load_animations(self, path):
        anims = {}
        for anim in os.listdir(path):
            anim_dir = os.path.join(path, anim)
            if os.path.isdir(anim_dir):
                frames = sorted(os.listdir(anim_dir))
                anims[anim] = [os.path.join(anim_dir, frame) for frame in frames]
        return anims

    def load_animation(self, name):
        if name not in self.animations:
            return
        self.state = name
        self.frames = self.animations.get(name, [])
        self.current_frame = 0
        self.update_pixmap()

    def update_frame(self):
        if not self.frames:
            return

        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.update_pixmap()

        if self.dragging:
            if self.state != "catch":
                self.load_animation("catch")
            return

        if self.state == "win":
            return

        if self.avoid_cursor:
            self.flee_from_cursor()
            return

        if self.sleeping:
            return

        if self.state in ["run", "jump"]:
            speed = self.stats["speed"] if self.state == "run" else self.stats["flee_speed"]
            self.move_cat(speed)
        elif self.state == "hunt":
            self.hunt_cursor()
        elif self.chasing and self.chase_target_cat:
            self.chase_target()
        elif self.fleeing and self.chase_target_cat:
            self.flee_from()

    def update_pixmap(self):
        pixmap = QPixmap(self.frames[self.current_frame])
        if self.direction == -1:
            transform = QTransform().scale(-1, 1)
            pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
        self.setPixmap(pixmap)

    def move_cat(self, speed):
        pos = self.pos()
        x = pos.x() + speed * self.direction
        y = pos.y()

        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # Wrap-around poprawiony — teleportuje na drugą stronę
        if x > screen_width:
            x = -self.width()
        elif x + self.width() < 0:
            x = screen_width

        if y < 0:
            y = 0
        elif y > screen_height - self.height():
            y = screen_height - self.height()

        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_offset = event.pos()
            self.load_animation("catch")

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToGlobal(event.pos() - self.drag_offset))

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.load_animation("idle")

    def start_hunting(self):
        if self.sleeping:
            return
        if random.random() < self.stats.get("attack_chance", 0.0):
            self.load_animation("hunt")

    def hunt_cursor(self):
        cursor_pos = QCursor.pos()
        cat_rect = self.geometry()

        if cat_rect.contains(cursor_pos):
            self.load_animation("attack")
            QTimer.singleShot(500, lambda: self.play_win_animation(3))
            return

        cat_pos = self.pos()
        dx = cursor_pos.x() - cat_pos.x()
        dy = cursor_pos.y() - cat_pos.y()
        distance = (dx**2 + dy**2)**0.5

        if distance < 80:
            self.load_animation("idle")
            QTimer.singleShot(1000, lambda: self.load_animation("attack"))
            QTimer.singleShot(1500, lambda: self.play_win_animation(3))
        else:
            self.direction = 1 if dx > 0 else -1
            step_x = int(dx / max(distance, 1) * self.stats["speed"])
            step_y = int(dy / max(distance, 1) * self.stats["speed"])
            self.move(cat_pos.x() + step_x, cat_pos.y() + step_y)

    def play_win_animation(self, repeat=3):
        self.state = "win"
        self.frames = self.animations.get("win", [])
        self.current_frame = 0
        self.update_pixmap()

        for i in range(repeat):
            QTimer.singleShot(i * 500, lambda i=i: self.load_animation("win"))
        QTimer.singleShot(repeat * 500, lambda: self.load_animation("idle"))

    def random_behavior(self):
        if self.dragging or self.state in ["hunt", "attack", "catch", "win"] or self.chasing or self.fleeing or self.avoid_cursor:
            return

        # Szansa na sen
        if random.random() < self.stats.get("sleep_chance", 0.0):
            self.start_sleeping()
            return

        action = random.choice(["idle", "run", "jump"])
        self.direction = random.choice([-1, 1])
        self.load_animation(action)

    def start_sleeping(self):
        self.sleeping = True
        self.load_animation("sleep")
        repeat = random.randint(4, 10)
        duration = repeat * len(self.frames) * 100  # 100 ms per frame
        QTimer.singleShot(duration, self.stop_sleeping)

    def stop_sleeping(self):
        self.sleeping = False
        self.load_animation("idle")

    def start_random_chase(self):
        if len(CatWidget.all_cats) < 2:
            return

        chaser, target = random.sample(CatWidget.all_cats, 2)

        if chaser.chasing or target.fleeing:
            return

        chaser.chasing = True
        chaser.chase_target_cat = target
        chaser.load_animation("attack")

        if target.sleeping:
            target.stop_sleeping()

        target.fleeing = True
        target.chase_target_cat = chaser
        target.load_animation("jump")

        duration = random.randint(3000, 8000)
        chaser.chase_timer.singleShot(duration, lambda: self.end_chase(chaser, target))

    def chase_target(self):
        if not self.chase_target_cat:
            return

        chaser_pos = self.pos()
        target_pos = self.chase_target_cat.pos()
        dx = target_pos.x() - chaser_pos.x()
        dy = target_pos.y() - chaser_pos.y()
        distance = (dx**2 + dy**2)**0.5

        if distance < 40:
            self.play_win_animation(3)
            self.chase_target_cat.load_animation("idle")
            self.chase_target_cat.sleeping = False
            self.reset_chase()
            return

        self.direction = 1 if dx > 0 else -1
        step_x = int(dx / max(distance, 1) * self.stats["attack_speed"])
        step_y = int(dy / max(distance, 1) * self.stats["attack_speed"])
        self.move(chaser_pos.x() + step_x, chaser_pos.y() + step_y)

    def flee_from(self):
        if not self.chase_target_cat:
            return

        my_pos = self.pos()
        chaser_pos = self.chase_target_cat.pos()
        dx = my_pos.x() - chaser_pos.x()
        dy = my_pos.y() - chaser_pos.y()
        distance = (dx**2 + dy**2)**0.5

        self.direction = 1 if dx > 0 else -1
        step_x = int(dx / max(distance, 1) * self.stats["flee_speed"])
        step_y = int(dy / max(distance, 1) * self.stats["flee_speed"])
        self.move(my_pos.x() + step_x, my_pos.y() + step_y)

    def end_chase(self, chaser, target):
        if chaser.chasing and target.fleeing:
            target.play_win_animation(3)
        chaser.reset_chase()
        target.reset_chase()

    def reset_chase(self):
        self.chasing = False
        self.fleeing = False
        self.chase_target_cat = None
        self.load_animation("idle")

    def start_avoiding_cursor(self):
        if self.dragging or self.chasing or self.fleeing:
            return
        self.avoid_cursor = True
        self.load_animation("jump")
        QTimer.singleShot(5000, self.stop_avoiding_cursor)

    def stop_avoiding_cursor(self):
        self.avoid_cursor = False
        self.load_animation("idle")

    def flee_from_cursor(self):
        cursor_pos = QCursor.pos()
        cat_pos = self.pos()
        dx = cat_pos.x() - cursor_pos.x()
        dy = cat_pos.y() - cursor_pos.y()
        distance = (dx**2 + dy**2)**0.5

        self.direction = 1 if dx > 0 else -1
        step_x = int(dx / max(distance, 1) * self.stats["flee_speed"])
        step_y = int(dy / max(distance, 1) * self.stats["flee_speed"])
        self.move(cat_pos.x() + step_x, cat_pos.y() + step_y)


class MousePressWatcher(QObject):
    def __init__(self):
        super().__init__()
        self.mouse_hold_timer = QTimer()
        self.mouse_hold_timer.setSingleShot(True)
        self.mouse_hold_timer.timeout.connect(self.trigger_avoidance)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.mouse_hold_timer.start(2000)
        elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
            self.mouse_hold_timer.stop()
        return False

    def trigger_avoidance(self):
        for cat in CatWidget.all_cats:
            cat.start_avoiding_cursor()


def load_cat_folders(base_path):
    return [os.path.join(base_path, folder) for folder in os.listdir(base_path)
            if os.path.isdir(os.path.join(base_path, folder))]