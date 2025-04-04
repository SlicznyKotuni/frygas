import sys
import os
import random
import math
from PySide6.QtCore import Qt, QTimer, QPoint, QRect, QSize
from PySide6.QtGui import QPixmap, QPainter, QTransform, QGuiApplication
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
        self.original_frames = {}
        
        # Zapisujemy oryginalne klatki animacji
        for anim_name, frames in self.animations.items():
            self.original_frames[anim_name] = frames.copy()
            
        self.setPixmap(self.animations[self.current_animation][0])
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setScaledContents(True)
        self.resize(100, 100)

        # Prędkość i ruch
        self.velocity = QPoint(0, 0)
        self.speed = 5
        self.is_caught = False
        self.animation_repeat_count = 0
        self.animation_repeats = 3  # Ile razy ma się powtórzyć animacja
        self.facing_right = True  # Czy kotek jest zwrócony w prawo
        self.rotation = 0  # Kąt obrotu kotka (w stopniach)
        
    def next_frame(self):
        """Przełącza na następną klatkę animacji."""
        frames = self.animations[self.current_animation]
        self.frame_index = (self.frame_index + 1) % len(frames)
        self.setPixmap(frames[self.frame_index])
        
        # Jeśli dotarliśmy do końca animacji, sprawdzamy czy trzeba ją powtórzyć
        if self.frame_index == len(frames) - 1:
            self.animation_repeat_count += 1
            if self.animation_repeat_count >= self.animation_repeats and not self.is_caught:
                self.animation_repeat_count = 0
                if self.current_animation != "idle":
                    self.set_animation("idle")

    def set_animation(self, animation_name):
        """Ustawia rodzaj animacji."""
        if animation_name in self.animations and self.current_animation != animation_name:
            self.current_animation = animation_name
            self.frame_index = 0
            self.animation_repeat_count = 0
            # Aktualizujemy kierunek animacji
            self.update_direction()

    def update_direction(self):
        """Aktualizuje kierunek animacji na podstawie prędkości."""
        if self.velocity.x() == 0 and self.velocity.y() == 0:
            return  # Nie zmieniamy kierunku, gdy kotek stoi
            
        # Określamy czy kotek ma być zwrócony w prawo czy w lewo
        new_facing_right = self.velocity.x() >= 0
        
        # Obliczamy kąt obrotu na podstawie kierunku ruchu
        # Dla ruchu w górę/dół
        if abs(self.velocity.y()) > abs(self.velocity.x()):
            # Kąt od -30 do 30 stopni w zależności od kierunku pionowego
            angle = -30 if self.velocity.y() < 0 else 30
        else:
            angle = 0  # Bez obrotu dla ruchu poziomego
            
        # Aktualizujemy klatki animacji tylko jeśli zmienił się kierunek lub kąt
        if new_facing_right != self.facing_right or angle != self.rotation:
            self.facing_right = new_facing_right
            self.rotation = angle
            self.update_animation_frames()
    
    def update_animation_frames(self):
        """Aktualizuje klatki animacji zgodnie z kierunkiem i obrotem."""
        for anim_name, original_frames in self.original_frames.items():
            # Tworzymy nowe transformowane klatki
            transformed_frames = []
            for frame in original_frames:
                # Tworzymy obraz o tym samym rozmiarze co oryginał
                original_size = frame.size()
                
                # Tworzymy nowy pixmap z przezroczystym tłem
                transformed_frame = QPixmap(original_size)
                transformed_frame.fill(Qt.transparent)
                
                # Przygotowujemy painter do rysowania na pixmapie
                painter = QPainter(transformed_frame)
                
                # Ustawiamy transformację
                painter.translate(original_size.width() / 2, original_size.height() / 2)
                
                # Obracamy obraz
                if self.rotation != 0:
                    painter.rotate(self.rotation)
                
                # Odbijamy obraz jeśli kotek ma być zwrócony w lewo
                if not self.facing_right:
                    painter.scale(-1, 1)
                
                # Rysujemy obraz z powrotem z przesunięciem, aby był wycentrowany
                painter.drawPixmap(-original_size.width() / 2, -original_size.height() / 2, frame)
                
                # Kończymy rysowanie
                painter.end()
                
                transformed_frames.append(transformed_frame)
            
            # Aktualizujemy klatki animacji
            self.animations[anim_name] = transformed_frames
        
        # Aktualizujemy bieżącą klatkę
        if self.animations[self.current_animation]:
            self.setPixmap(self.animations[self.current_animation][self.frame_index])

    def move_randomly(self):
        """Losowy ruch kotka po ekranie z animacją run."""
        if not self.is_caught:
            self.velocity = QPoint(random.randint(-10, 10), random.randint(-10, 10))
            if self.velocity.manhattanLength() > 0:
                self.set_animation("run")
                self.update_direction()

    def move_towards(self, target_pos):
        """Przemieszcza widżet w kierunku pozycji myszy."""
        if self.is_caught:
            self.move(target_pos - QPoint(self.width() // 2, self.height() // 2))

    def jump(self):
        """Skakanie z większym przemieszczeniem."""
        if not self.is_caught:
            self.velocity = QPoint(random.randint(-15, 15), random.randint(-15, 15))
            self.set_animation("jump")
            self.update_direction()

    def catch(self, caught=True):
        """Łapanie kotka."""
        self.is_caught = caught
        if caught:
            self.set_animation("catch")
        else:
            self.set_animation("idle")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Frygający Kotun")
        
        # Ustawiamy okno na cały ekran
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)
        
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Tło przezroczyste
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        # Animowane widgety
        self.kotuns = []
        self.load_kotuns()
        
        # Zmienne do śledzenia złapanego kotka
        self.caught_kotun = None
        self.mouse_pos = QPoint(0, 0)

        # Timer do aktualizacji ruchów kotków
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_kotuns)
        self.update_timer.start(1000)  # Co 1 sekundę aktualizujemy zachowanie kotków
        
        # Timer do aktualizacji pozycji kotków
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.update_positions)
        self.position_timer.start(50)  # Częsta aktualizacja dla płynnego ruchu
        
        # Dodajemy klawisz wyjścia
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        """Obsługa klawiszy - Escape zamyka aplikację."""
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

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

    def update_kotuns(self):
        """Aktualizuje zachowanie kotków: losowe ruchy, odpoczynek, skakanie."""
        for kotun in self.kotuns:
            if not kotun.is_caught:
                action = random.choice(["move", "jump", "idle"])
                if action == "move":
                    kotun.move_randomly()
                elif action == "jump":
                    kotun.jump()
                elif action == "idle":
                    kotun.velocity = QPoint(0, 0)
                    kotun.set_animation("idle")

    def move_kotun(self, kotun):
        """Przesuwa kotka zgodnie z jego prędkością."""
        if not kotun.is_caught and kotun.velocity.manhattanLength() > 0:
            new_pos = kotun.pos() + kotun.velocity
            
            # Ograniczamy ruch do obszaru ekranu z możliwością wyjścia poza krawędzie
            screen_width = self.width()
            screen_height = self.height()
            
            # Jeśli kotek wyszedł poza ekran, przenosimy go na przeciwną stronę
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
        """Obsługa kliknięcia myszy - łapanie kotka."""
        if event.button() == Qt.LeftButton:
            for kotun in self.kotuns:
                if kotun.geometry().contains(event.pos()):
                    self.caught_kotun = kotun
                    kotun.catch(True)
                    break

    def mouseReleaseEvent(self, event):
        """Obsługa zwolnienia przycisku myszy - puszczanie kotka."""
        if event.button() == Qt.LeftButton and self.caught_kotun:
            self.caught_kotun.catch(False)
            self.caught_kotun = None

    def mouseMoveEvent(self, event):
        """Śledzi pozycję myszy."""
        self.mouse_pos = event.pos()

    def update_positions(self):
        """Aktualizuje pozycje kotków."""
        # Aktualizacja pozycji złapanego kotka
        if self.caught_kotun:
            self.caught_kotun.move_towards(self.mouse_pos)
        
        # Aktualizacja pozycji pozostałych kotków
        for kotun in self.kotuns:
            if not kotun.is_caught:
                self.move_kotun(kotun)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())