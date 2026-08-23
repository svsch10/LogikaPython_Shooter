from kivymd.app import MDApp
from kivymd.uix.widget import MDWidget
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from kivy.metrics import sp, dp
from kivy.core.window import Window
from kivy import platform
from kivy.uix.image import Image
from random import randint
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Keyboard


class MainScreen(MDScreen):
    ...

class GameOverScreen(MDScreen):
    pass

FPS = 60

BULLET_SPEED = dp(10)
SHIP_SPEED = dp(5)
DIR_UP = 1
DIR_DOWN = -1
SPAWN_ENEMY_TIME = 2


class Shot(MDWidget):
    def __init__(self, direction, owner, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        self.owner = owner


class Ship(Image):
    def __init__(self, direction = DIR_UP, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction

    def moveLeft(self):
        self.pos[0] -= SHIP_SPEED

    def moveRight(self):
        self.pos[0] += SHIP_SPEED

    def shot(self):
        shot = Shot(self.direction, owner=self)
        shot.center_x = self.center_x
        shot.y = (
            self.top
            if self.direction == DIR_UP
            else self.y - shot.height
        )
        '''
        Т.зв. "тернарний вираз" - інший спосіб запису розгалуження.
        "Тернарний" - "тричастинний": дія-True → if умова → else дія-False.
        
        Традиційний спосіб запису:
        if self.direction == DIR_UP:
            shot.y = self.top
        else:
            shot.y = self.y - shot.height
        '''
        # --- Створення кулі на екрані ---
        self.parent.parent.parent.parent.bullets.append(shot)
        '''
        Дерево kv таке:
        GameScreen
        └── MDFloatLayout
            ├── MDFloatLayout id="game"
            │   ├── MDFloatLayout id="back"
            │   └── MDFloatLayout id="front"
            │       ├── PlayerShip
            │       └── EnemyShip
            └── MDFloatLayout id="interface"
        Тому, оскільки кулі обробляються в GameScreen, то потрібно
        перейти на 4 рівні вгору, щоб туди потрапити:
            self
             ↓
            front
             ↓
            game
             ↓
            MDFloatLayout (кореневий)
             ↓
            GameScreen
        '''
        self.parent.add_widget(shot) # Віджет shot додається на екран
        '''
        Нова структура:
            front
            ├── PlayerShip
            ├── EnemyShip
            └── Shot
        '''

    def update(self):          
        pass


class PlayerShip(Ship):
    def __init__(self, **kwargs):
        super().__init__(direction=DIR_UP, **kwargs)

    def update(self, keys):
        for key in keys:
            if keys[key] == True:
                if key == 'left' and self.center_x > 0:
                    self.moveLeft()
                if key == 'right' and self.center_x < Window.width:
                    self.moveRight()
                if key == 'shot':
                    self.shot()
                    keys[key] = False


class EnemyShip(Ship):
    def __init__(self, *args, **kwargs):
        super().__init__(direction=DIR_DOWN, **kwargs)
        self.frame = 0 # Початковий кадр

    def update(self):
        super().update()
        self.pos[1] -= dp(3)
        if self.frame % 100 == 0:
            self.shot() # Постріл кожні 100 оновлень кадру (frame)
        self.frame += 1


class GameScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ship = None
        self.eventkeys = {}
        self.ship = self.ids.ship
        self.enemyShips = []

        self.bullets = []

        self.pauseMenu = None

        self.spawn_delay = SPAWN_ENEMY_TIME
        self.time_last_spawn = 0

        # Керування з клавіатури для тестування з комп'ютера
        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)

    def on_enter(self, *args):
        self.updateEvent = Clock.schedule_interval(self.update, 1/FPS)
        self.ship = self.ids.ship
        return super().on_enter(*args)

    def spawn_enemy(self):
        enemy = EnemyShip()
        enemy.pos = (randint(0, int(Window.size[0] - enemy.size[0])),
                    Window.size[1])
        self.enemyShips.append(enemy)
        self.ids.front.add_widget(enemy)

    def update(self, dt):
        # Головний корабель
        self.ship.update(self.eventkeys)

        self.time_last_spawn += dt
        if self.time_last_spawn >= self.spawn_delay:
            self.spawn_enemy()
            self.time_last_spawn = 0

        # Логіка ворогів
        for ship in self.enemyShips:
            ship.update()
            if ship.top < 0:
                self.enemyShips.remove(ship)
                self.ids.front.remove_widget(ship)
            
            if ship.collide_widget(self.ship):
                self.game_over()

        # Керування кулями
        self.manage_bullets()

    # Рух всіх куль гри
    def manage_bullets(self):
        for bullet in self.bullets:
            bullet.y += BULLET_SPEED * bullet.direction
            self.check_collisions(bullet)
            
            # Видалення куль при виході за рамки вікна
            if bullet.y > Window.height or bullet.top < 0:
                self.ids.front.remove_widget(bullet)
                self.bullets.remove(bullet)
            

    def check_collisions(self, bullet):
        if bullet.owner == self.ship:
            for enemy in self.enemyShips:
                if bullet.collide_widget(enemy):
                    self.enemyShips.remove(enemy)
                    self.ids.front.remove_widget(enemy)
                    self.remove_bullet(bullet)
                    break
        else:
            if bullet.collide_widget(self.ship):
                self.game_over()
                self.remove_bullet(bullet)
    
    def remove_bullet(self, bullet):
        if bullet in self.bullets:
            self.bullets.remove(bullet)
            self.ids.front.remove_widget(bullet)

    def game_over(self):
        self.updateEvent.cancel()
        for enemy in self.enemyShips:
            self.enemyShips.remove(enemy)
            self.ids.front.remove_widget(enemy)
        for bullet in self.bullets:
            self.bullets.remove(bullet)
            self.ids.front.remove_widget(bullet)
        self.manager.current = 'game_over'

    def pressKey(self, key):
        self.eventkeys[key] = True

    def releaseKey(self, key):
        self.eventkeys[key] = False

    def show_menu(self):
        self.updateEvent.cancel()
        
        if not self.pauseMenu:
            self.pauseMenu = MDDialog(
                title="Game Paused",
                text="Resume the game?",
                on_dismiss=self.resumeGame,
                buttons=[
                    MDFlatButton(
                        text="RESUME",
                        theme_text_color="Custom",
                        text_color=app.theme_cls.primary_color,
                        on_press=self.pauseStop
                    )
                ]
            )
        self.pauseMenu.open()

    def pauseStop(self, *args):
        self.pauseMenu.dismiss()

    def resumeGame(self, *args):
        self.updateEvent = Clock.schedule_interval(self.update, 1 / FPS)

    # Керування з клавіатури під час тестування з комп'ютера
    def _on_key_down(self, window, keycode, *args, **kwargs):
        key = (
            key
            if (key:=Keyboard.keycode_to_string(window, keycode))!='spacebar'
            else 'shot'
        )
        # Завдяки оператору присвоєння := можна надати значення змінній і тут же її порівняти
        
        # Простіше так:
        '''
        key = Keyboard.keycode_to_string(window, keycode)
        key = 'shot' if key == 'spacebar' else key
        '''
        
        self.eventkeys[key] = True

    def _on_key_up(self, window, keycode, *args, **kwargs):
        key = (
            key
            if (key := Keyboard.keycode_to_string(window, keycode)) != 'spacebar'
            else 'shot'
        )

        self.eventkeys[key] = False


class ShooterApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.accent_palette = "Purple"
        self.sm = MDScreenManager()

        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(GameScreen(name='game'))
        self.sm.add_widget(GameOverScreen(name='game_over'))

        return self.sm
    

if platform != 'android':
    Window.size = (450, 700)
    Window.top = 100
    Window.left = 600

app = ShooterApp()
app.run()
