import os
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.vector import Vector

# Konfiguracja przezroczystości okna (określamy przezroczyste tło)
Window.clearcolor = (0, 0, 0, 0)

class CatWidget(Widget):
    """
    Widżet wyświetlający animowanego kotka.
    Obsługuje animacje, podążanie za myszką oraz możliwość przenoszenia przez użytkownika.
    """
    def __init__(self, asset_dir, **kwargs):
        super().__init__(**kwargs)
        self.asset_dir = asset_dir
        self.animations = {}         # Słownik przechowujący animacje (lista klatek) dla danego typu
        self.current_animation = []  # Aktualnie wybrana animacja
        self.frame_index = 0         # Indeks aktualnej klatki
        self.anim_delay = 0.1        # Opóźnienie między kolejnymi klatkami animacji
        self.speed = 5               # Prędkość poruszania się kotka
        self.velocity = Vector(0, 0) # Aktualna prędkość (wektor)
        self.dragging = False        # Flaga określająca, czy użytkownik przeciąga widżet
        self._touch_offset = (0, 0)  # Offset dotyku przy przeciąganiu

        # Utwórz Image jako dziecko widżetu; dzięki niemu wyświetlamy kotka
        self.image = Image(size_hint=(None, None), size=self.size, pos=self.pos)
        self.add_widget(self.image)

        # Załaduj wszystkie animacje ("idle", "run", "jump", "catch")
        self.load_animations()
        self.set_animation('idle')

        # Harmonogram odświeżania animacji oraz logiki ruchu
        Clock.schedule_interval(self.animate, self.anim_delay)
        Clock.schedule_interval(self.update, 1 / 60)

        # Reaguj na ruch myszki (podążanie za kursorem)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def load_animations(self):
        """
        Dla każdej animacji w podkatalogach asset_dir ładuje wszystkie klatki (PNG).
        """
        for anim in ['idle', 'run', 'jump', 'catch']:
            dir_path = os.path.join(self.asset_dir, anim)
            frames = []
            if os.path.exists(dir_path):
                # Zakładamy, że nazwy plików są takie, że przy sortowaniu alfabetycznym uzyskamy właściwą kolejność
                for filename in sorted(os.listdir(dir_path)):
                    if filename.lower().endswith('.png'):
                        frames.append(os.path.join(dir_path, filename))
            if not frames:
                print(f"Warning: Brak klatek animacji dla '{anim}' w {dir_path}")
            self.animations[anim] = frames

    def set_animation(self, anim_name):
        """
        Ustawia animację na podstawie nazwy. Jeśli animacja nie została znaleziona, pozostaje 'idle'.
        """
        if anim_name in self.animations and self.animations[anim_name]:
            self.current_animation = self.animations[anim_name]
            self.frame_index = 0
        else:
            print(f"Animacja '{anim_name}' nie została znaleziona – ustawiam 'idle'")
            self.current_animation = self.animations.get('idle', [])
            self.frame_index = 0

    def animate(self, dt):
        """
        Zmiana klatki animacji według zdefiniowanego interwału czasu.
        """
        if not self.current_animation:
            return
        self.frame_index = (self.frame_index + 1) % len(self.current_animation)
        self.image.source = self.current_animation[self.frame_index]
        self.image.reload()  # Odświeża obraz

    def update(self, dt):
        """
        Aktualizacja pozycji widżetu oraz jego ograniczenie do obszaru okna.
        Jeśli widżet nie jest przeciągany, porusza się według wektora velocity.
        """
        if not self.dragging:
            new_pos = Vector(*self.pos) + self.velocity
            # Ograniczenia do granic okna
            new_x = max(0, min(new_pos[0], Window.width - self.width))
            new_y = max(0, min(new_pos[1], Window.height - self.height))
            self.pos = (new_x, new_y)
            self.image.pos = self.pos

    def on_mouse_pos(self, window, pos):
        """
        Ustawia wektor ruchu tak, aby kotek podążał za kursorem.
        Jeśli widżet jest przeciągany, nie aktualizujemy velocity.
        """
        if self.dragging:
            return
        mouse_x, mouse_y = pos
        direction = Vector(mouse_x - self.center_x, mouse_y - self.center_y)
        # Upewnij się, że długość wektora nie wynosi 0 (aby uniknąć dzielenia przez 0)
        if direction.length() > 1:
            self.velocity = direction.normalize() * self.speed
        else:
            self.velocity = Vector(0, 0)

    def on_touch_down(self, touch):
        """
        Jeśli dotknięcie nastąpiło w obrębie widżetu, rozpoczynamy przeciąganie i ustawiamy animację 'catch'.
        """
        if self.collide_point(*touch.pos):
            self.dragging = True
            self.set_animation('catch')
            # Obliczamy offset, aby widżet "przyklejał się" do pozycji kursora z zatrzymaniem różnicy
            self._touch_offset = (self.x - touch.x, self.y - touch.y)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        """
        Jeśli przeciągamy widżet, aktualizujemy jego pozycję zgodnie z nową pozycją touch.
        """
        if self.dragging:
            self.x = touch.x + self._touch_offset[0]
            self.y = touch.y + self._touch_offset[1]
            # Zapewniamy, że obrazek podąża za widżetem
            self.image.pos = self.pos
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        """
        Po puszczeniu dotyku kończymy przeciąganie i przywracamy animację 'idle'.
        """
        if self.dragging:
            self.dragging = False
            self.set_animation('idle')
            return True
        return super().on_touch_up(touch)

class CatApp(App):
    """
    Główna aplikacja.
    """
    def build(self):
        # Zakładamy, że folder z assetami to assets/frygas1 (możesz łatwo zmienić na inny)
        asset_dir = os.path.join("assets", "frygas1")
        cat = CatWidget(asset_dir=asset_dir, pos=(100, 100), size=(100, 100))
        return cat

if __name__ == '__main__':
    CatApp().run()