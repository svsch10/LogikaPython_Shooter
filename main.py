from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.widget import MDWidget
from kivymd.uix.screen import MDScreen
from kivy import platform
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import sp, dp

FPS = 60
SHIP_SPEED = dp(5)
BULLET_SPEED = dp(10)

class MainScreen(MDScreen):
    ...

class Shot(MDWidget):
    ...

class GameScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Clock.schedule_interval(self.update, 1/FPS)
        self.cartridge = []
        self.eventkeys = {}
    
    def update(self, dt):
        for key in self.eventkeys:
            if self.eventkeys[key] == True:
                if key == 'left':
                    self.moveLeft()
                if key == 'right':
                    self.moveRight()
                if key == 'shot':
                    self.shot()
                    self.eventkeys[key] = False
                    
        for bullet in self.cartridge:
            bullet.pos[1] += BULLET_SPEED
    
    def pressKey(self, key):
        self.eventkeys[key] = True
    def releaseKey(self, key):
        self.eventkeys[key] = False
    def moveLeft(self):
        self.ids.ship.pos[0] -= SHIP_SPEED
    def moveRight(self):
        self.ids.ship.pos[0] += SHIP_SPEED
    def shot(self):
        shot = Shot(pos=(self.ids.ship.center_x,
                         self.ids.ship.top))
        self.cartridge.append(shot)
        self.ids.front.add_widget(shot)
        
        
class ShooterApp(MDApp):
    def build(self):
        # --- Стиль застосунку: світлий чи темний ---
        self.theme_cls.theme_style = "Dark"
        # --- Колір основної палітри ---
        self.theme_cls.primary_palette = "Orange"

        self.sm = MDScreenManager()

        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(GameScreen(name='game'))

        return self.sm

if platform != 'android':
    Window.size = (450, 700)
    Window.top = 100
    Window.left = 600
     
app = ShooterApp()
app.run()
