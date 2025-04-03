import kivy
kivy.require('2.0.0')  # Upewnij się, że masz Kivy w wersji 2.0.0 lub nowszej

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ListProperty, StringProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.vector import Vector
import random

import win32gui
import win32con

def set_window_transparent():
    hwnd = win32gui.GetHwnd(Window.hwnd)
    # Ustawienie stylu okna na przezroczyste
    wl = win32con.WS_EX_LAYERED
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, wl)
    # Ustawienie koloru przezroczystości (tutaj czarny)
    win32gui.SetLayeredWindowAttributes(hwnd, 0x000000, 255, win32con.LWA_COLORKEY)

class Kotun(Widget):
    # Właściwości kotunia
    idle_frames = ListProperty([])
    run_frames = ListProperty([])
    jump_frames = ListProperty([])
    catch_frames = ListProperty([])
    current_frame = ObjectProperty(None) # Obecna klatka animacji
    anim_delay = 0.1  # Opóźnienie między klatkami
    source = StringProperty('') # Ścieżka do obrazka
    is_catched = BooleanProperty(False)
    speed = 100 # Bazowa prędkość ruchu
    follow_distance = 200 # Promień śledzenia myszki
    # Metody kotunia
    def __init__(self, **kwargs):
        super(Kotun, self).__init__(**kwargs)
        # Załaduj animacje
        self.load_animations()
        # Ustaw animację idle na start
        self.set_animation('idle')
        # Uruchom animację
        Clock.schedule_interval(self.animate, self.anim_delay)
        Clock.schedule_interval(self.update, 1/60) # Aktualizacja 60 razy na sekundę
        self.velocity = Vector(0, 0) # Początkowa prędkość

    def load_animations(self):
        # Załaduj obrazki z folderów (tutaj trzeba podać poprawne ścieżki)
        self.idle_frames = [f"assets/idle/frame_{i}.png" for i in range(1, 5)] # Przykładowe 4 klatki
        self.run_frames = [f"assets/run/frame_{i}.png" for i in range(1, 5)]  # Przykładowe 4 klatki
        self.jump_frames = [f"assets/jump/frame_{i}.png" for i in range(1, 5)] # Przykładowe 4 klatki
        self.catch_frames = [f"assets/catch/frame_{i}.png" for i in range(1, 5)]# Przykładowe 4 klatki

    def set_animation(self, animation_name):
        if animation_name == 'idle':
            self.animation_frames = self.idle_frames
        elif animation_name == 'run':
            self.animation_frames = self.run_frames
        elif animation_name == 'jump':
            self.animation_frames = self.jump_frames
        elif animation_name == 'catch':
            self.animation_frames = self.catch_frames
        self.current_frame_index = 0
        if self.animation_frames: # Upewnij się, że animacja ma klatki
            self.source = self.animation_frames[self.current_frame_index] # Ustaw pierwszy obrazek
        else:
            self.source = "assets/icon.png" # Domyślny obrazek, jeśli brak animacji

    def animate(self, dt):
        # Animacja kotunia
        if not self.animation_frames:
            return # Nic do animowania
        self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)
        self.source = self.animation_frames[self.current_frame_index]

    def on_touch_down(self, touch):
        # Reakcja na dotyk
        if self.collide_point(*touch.pos):
            self.is_catched = True
            touch.grab(self)
            self.set_animation('catch')
            return True # Przejmujemy dotyk

    def on_touch_move(self, touch):
        # Przenoszenie kotunia
        if touch.grab_current is self:
            self.center = touch.pos # Przesuwaj kotunia za dotykiem

    def on_touch_up(self, touch):
        # Puszczenie kotunia
        if touch.grab_current is self:
            self.is_catched = False
            touch.ungrab(self)
            self.set_animation('idle') # Powrót do animacji idle

    def on_mouse_pos(self, *args):
        # Śledzenie pozycji myszki
        if not self.get_root_window():
            return
        pos = args[1]
        cat_pos = Vector(*self.pos) + Vector(self.size[0] / 2, self.size[1] / 2) # Środek kotka
        mouse_vector = Vector(*pos) - cat_pos

        if mouse_vector.length() < self.follow_distance and not self.is_catched:
            # Ucieczka przed myszką
            self.velocity = -mouse_vector.normalize() * self.speed
            self.set_animation('run')
        else:
            # Losowe poruszanie się
            if random.random() < 0.01: # 1% szansy na ruch
                angle = random.uniform(0, 360)
                self.velocity = Vector(1, 0).rotate(angle) * self.speed
            elif self.velocity.length() > 0 :
                self.velocity *= 0.95 # Zwalnianie
                if self.velocity.length() < 5:
                  self.velocity = Vector(0,0)
                  self.set_animation('idle')

    def update(self, dt):
        # Aktualizacja pozycji
        if self.velocity.length() > 0 and not self.is_catched:
            self.pos = Vector(*self.pos) + self.velocity * dt # Przesuń kotka

            # Ograniczenie do granic ekranu
            self.x = max(0, min(self.x, Window.width - self.width))
            self.y = max(0, min(self.y, Window.height - self.height))

class KotunApp(App):
    def build(self):
        # Stwórz kotunia i dodaj go do okna
        kotun = Kotun(size_hint=(None, None), size=(100, 100), pos=(100, 100)) # Rozmiar i pozycja początkowa
        Window.bind(mouse_pos=kotun.on_mouse_pos) # Śledzenie myszki
        Window.clearcolor = (0,0,0,0) # Ustawienie przezroczystości koloru okna
        set_window_transparent() # Ustawienie przezroczystości okna
        return kotun

if __name__ == '__main__':
    KotunApp().run()