import os
import random
import win32gui
import win32con
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.config import Config
from kivy.graphics import Rectangle, Color
from kivy.core.image import Image  # Dodajemy import Image

# Ustawienia przezroczystości okna (tylko działają na niektórych systemach)
Config.set('graphics', 'transparent', '1')
Config.write()

def set_window_transparent():
    hwnd = win32gui.FindWindow(None, "Frygający Kotuń")  # Znajdź okno po tytule
    if hwnd:
        # Ustawienie stylu okna na przezroczyste
        wl = win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, wl)
        # Ustawienie koloru przezroczystości (tutaj czarny)
        win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 255, win32con.LWA_COLORKEY)
    else:
        print("Nie znaleziono okna!")

class Kotun(Widget):
    anim_delay = 0.1

    def __init__(self, kotun_dir, **kwargs):  # Dodajemy argument kotun_dir
        super(Kotun, self).__init__(**kwargs)
        print("Tworzę kotunia!")  # Dodajemy print, żeby sprawdzić, czy kotuń się tworzy
        self.kotun_dir = kotun_dir  # Zapamiętujemy ścieżkę do katalogu kotunia
        self.size_hint = (None, None) # Ustawiamy size_hint
        self.size = (100, 100) # Ustawiamy rozmiar
        # Załaduj animacje
        self.load_animations()
        # Ustaw animację idle na start
        self.set_animation('idle')

        # Ustaw teksturę na pierwszą klatkę animacji idle
        if self.animation_frames:
            self.texture = self.load_texture(self.animation_frames[0])
        else:
            print("Brak klatek animacji!")

        # Uruchom animację
        Clock.schedule_interval(self.animate, self.anim_delay)
        Clock.schedule_interval(self.update, 1 / 60)  # Aktualizacja 60 razy na sekundę
        self.velocity = Vector(0, 0)  # Początkowa prędkość
        self.speed = 5  # Prędkość poruszania się kotuna
        self.frame_index = 0  # Indeks aktualnej klatki animacji

    def load_animations(self):
        # Załaduj obrazki z folderów (tutaj trzeba podać poprawne ścieżki)
        self.idle_frames = self.load_animation_frames(os.path.join(self.kotun_dir, "idle"))
        self.run_frames = self.load_animation_frames(os.path.join(self.kotun_dir, "run"))
        self.jump_frames = self.load_animation_frames(os.path.join(self.kotun_dir, "jump"))
        self.catch_frames = self.load_animation_frames(os.path.join(self.kotun_dir, "catch"))

        if not self.idle_frames:
            print(f"Warning: No idle frames found in {os.path.join(self.kotun_dir, 'idle')}")
        if not self.run_frames:
            print(f"Warning: No run frames found in {os.path.join(self.kotun_dir, 'run')}")
        if not self.jump_frames:
            print(f"Warning: No jump frames found in {os.path.join(self.kotun_dir, 'jump')}")
        if not self.catch_frames:
            print(f"Warning: No catch frames found in {os.path.join(self.kotun_dir, 'catch')}")

    def load_animation_frames(self, animation_dir):
        """Ładuje klatki animacji z podanego katalogu."""
        frames = []
        if os.path.exists(animation_dir):  # Sprawdzamy, czy katalog istnieje
            try:
                for i in range(1, 100):  # Zakładamy, że mamy maksymalnie 99 klatek
                    filename = os.path.join(animation_dir, f"{i}.png")
                    if os.path.exists(filename):
                        frames.append(filename)
                    else:
                        break  # Przerywamy, jeśli nie znaleziono kolejnej klatki
            except FileNotFoundError:
                print(f"Warning: Directory not found: {animation_dir}")
        else:
            print(f"Warning: Directory not found: {animation_dir}")
        return frames

    def set_animation(self, anim_type):
        """Ustawia animację."""
        if anim_type == 'idle':
            self.animation_frames = self.idle_frames
        elif anim_type == 'run':
            self.animation_frames = self.run_frames
        elif anim_type == 'jump':
            self.animation_frames = self.jump_frames
        elif anim_type == 'catch':
            self.animation_frames = self.catch_frames
        else:
            self.animation_frames = self.idle_frames  # Domyślnie idle
        self.frame_index = 0  # Resetujemy indeks klatki

    def animate(self, dt):
        """Animuje kotuna."""
        if not self.animation_frames:
            return  # Nic do animowania

        self.frame_index = (self.frame_index + 1) % len(self.animation_frames)
        self.texture = self.load_texture(self.animation_frames[self.frame_index])

    def load_texture(self, filename):
        """Ładuje teksturę z pliku."""
        try:
            im = Image(filename) # Używamy Image z kivy.core.image
            return im.texture
        except Exception as e:
            print(f"Error loading texture {filename}: {e}")
            return None

    def on_mouse_pos(self, *args):
        """Aktualizuje prędkość kotuna w zależności od położenia myszki."""
        mouse_x, mouse_y = args[1]
        self.velocity = Vector(mouse_x - self.center_x, mouse_y - self.center_y).normalize() * self.speed

    def update(self, dt):
        """Aktualizuje pozycję kotuna."""
        self.pos = Vector(*self.pos) + self.velocity
        # Ograniczenie do okna
        self.x = max(0, min(self.x, Window.width - self.width))
        self.y = max(0, min(self.y, Window.height - self.height))

    def on_touch_down(self, touch):
        # Zmiana animacji na "catch" po dotknięciu
        self.set_animation('catch')

    def on_touch_up(self, touch):
        # Powrót do animacji "idle" po zakończeniu dotyku
        self.set_animation('idle')

class KotunApp(App):
    def build(self):
        Window.title = "Frygający Kotuń"
        # Znajdź wszystkie katalogi Frygasiów
        assets_dir = "assets"
        if not os.path.exists(assets_dir):
            print("Creating assets directory...")
            os.makedirs(assets_dir)

        kotun_dirs = [os.path.join(assets_dir, d) for d in os.listdir(assets_dir) if os.path.isdir(os.path.join(assets_dir, d))]
        kotuny = []
        for kotun_dir in kotun_dirs:
            kotun = Kotun(kotun_dir=kotun_dir,
                          pos=(random.randint(0, Window.width - 100), random.randint(0, Window.height - 100)))  # Losowa pozycja początkowa
            Window.bind(mouse_pos=kotun.on_mouse_pos)  # Śledzenie myszki
            kotuny.append(kotun)

        # Ustaw przezroczystość okna
        Window.clearcolor = (0, 0, 0, 0)
        set_window_transparent()

        # Dodaj wszystkie kotuny do okna
        root = Widget()  # Stwórz główny widget
        for kotun in kotuny:
            root.add_widget(kotun)  # Dodaj kotuna do głównego widgetu

        return root

if __name__ == '__main__':
    print("Starting KotunApp...")
    KotunApp().run()
    print("KotunApp finished.")