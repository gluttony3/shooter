import random
import math
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import ListProperty, NumericProperty
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.app import MDApp
from kivy.uix.label import Label
from kivy.uix.widget import Widget


class GameSettings:
    SHIP_SPEED   = 10
    BULLET_SPEED = 15
    FPS          = 60

class Bullet:
    def __init__(self, x, y, canvas):
        self.x = x
        self.y = y
        self.speed = GameSettings.BULLET_SPEED
        with canvas:
            Color(1, 1, 0, 1)
            self.rect = Rectangle(pos=(x, y), size=(5, 10))

    def move(self):
        self.y += self.speed
        self.rect.pos = (self.x, self.y)

class EnemyBullet:
    def __init__(self, x, y, canvas):
        self.x = x
        self.y = y
        self.speed = GameSettings.BULLET_SPEED
        with canvas:
            Color(1, 0.3, 0.3, 1)
            self.rect = Rectangle(pos=(x, y), size=(5, 10))

    def move(self):
        self.y -= self.speed
        self.rect.pos = (self.x, self.y)

class EnemyShip:
    def __init__(self, x, y, canvas):
        self.x = x
        self.y = y
        self.speed = 2
        self.direction_x = random.choice([-1, 1])
        self.shoot_delay = 1.5
        self._shoot_acc  = 0
        self.xp = 2
        with canvas:
            Color(1, 0, 0, 1)
            self.rect = Rectangle(pos=(self.x, self.y), size=(50, 30))

    def update(self, dt):
        self.move()
        self._shoot_acc += dt
        if self._shoot_acc >= self.shoot_delay:
            self._shoot_acc = 0
            return True
        return False

    def move(self):
        self.x += self.speed * self.direction_x
        if self.x <= 0:
            self.x = 0
            self.direction_x *= -1
        elif self.x + 50 >= Window.width:
            self.x = Window.width - 50
            self.direction_x *= -1
        self.rect.pos = (self.x, self.y)

class Player:
    def __init__(self, x, y, canvas):
        self.x = x
        self.y = y
        self.width  = 50
        self.height = 30
        self.xp = 2
        with canvas:
            Color(0, 1, 0, 1)
            self.rect = Rectangle(pos=(self.x, self.y), size=(self.width, self.height))

class VirtualJoystick(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_touch = None
        self.joy_x = 0.0
        self.joy_y = 0.0
        self.RADIUS = 60

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.active_touch = touch.uid
            self._update_joy(touch)
            return True

    def on_touch_move(self, touch):
        if touch.uid == self.active_touch:
            self._update_joy(touch)
            return True

    def on_touch_up(self, touch):
        if touch.uid == self.active_touch:
            self.active_touch = None
            self.joy_x = 0.0
            self.joy_y = 0.0
            return True

    def _update_joy(self, touch):
        dx = touch.x - self.center_x
        dy = touch.y - self.center_y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > self.RADIUS:
            dx = dx / dist * self.RADIUS
            dy = dy / dist * self.RADIUS
        self.joy_x = dx / self.RADIUS
        self.joy_y = dy / self.RADIUS

class MainScreen(Screen):
    pass

class GameScreen(Screen):
    score = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None
        self.bullets = []
        self.enemies = []
        self.shoot_cooldown = 0.2
        self._shoot_timer = 0.0
        self.enemy_bullets = []
        self.shooting = False
        self._update_event = None

    def shoot(self):
        bullet_x = self.player.x + self.player.width / 2 - 2.5
        bullet_y = self.player.y + self.player.height
        self.bullets.append(Bullet(bullet_x, bullet_y, self.ids.game_field.canvas))

    def on_enter(self):
        self.score = 0
        self.ids.score_label.text = "Score: 0"

        field = self.ids.game_field
        self.player = Player(
            x=field.width / 2 - 25,
            y=100,
            canvas=field.canvas
        )
        self.player.xp = 2
        self.ids.hp_label.text = f"HP: {self.player.xp}"
        for _ in range(3):
            x = random.randint(0, int(field.width - 50))
            self.enemies.append(EnemyShip(x, field.height - 80, field.canvas))
        if self._update_event is None:
            self._update_event = Clock.schedule_interval(self.update, 1 / GameSettings.FPS)

    def game_over(self):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        self._message_label = Label(
            text="GAME OVER",
            color=(1, 0, 0, 1),
            font_size=60,
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        self.ids.game_field.add_widget(self._message_label)
        Clock.schedule_once(self.back_to_menu, 2)

    def game_won(self):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        self._message_label = Label(
            text="YOU WIN!",
            color=(0, 1, 0, 1),
            font_size=60,
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        self.ids.game_field.add_widget(self._message_label)
        Clock.schedule_once(self.back_to_menu, 2)

    def back_to_menu(self, dt):
        if hasattr(self, "_message_label") and self._message_label:
            self.ids.game_field.remove_widget(self._message_label)
            self._message_label = None
        for b in self.bullets:
            self.ids.game_field.canvas.remove(b.rect)
        for b in self.enemy_bullets:
            self.ids.game_field.canvas.remove(b.rect)
        for e in self.enemies:
            self.ids.game_field.canvas.remove(e.rect)
        if self.player:
            self.ids.game_field.canvas.remove(self.player.rect)
            self.player = None
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.enemies.clear()
        App.get_running_app().root.current = "main"

    def rects_collide(self, r1, r2):
        return not (
            r1.pos[0] + r1.size[0] < r2.pos[0] or
            r1.pos[0] > r2.pos[0] + r2.size[0] or
            r1.pos[1] + r1.size[1] < r2.pos[1] or
            r1.pos[1] > r2.pos[1] + r2.size[1]
        )

    def update(self, dt):
        if not self.player:
            return
        if not self.enemies:
            self.game_won()

        joystick = self.ids.joystick
        speed = GameSettings.SHIP_SPEED
        self.player.x += joystick.joy_x * speed
        self.player.y += joystick.joy_y * speed

        field = self.ids.game_field
        self.player.x = max(0, min(field.width - self.player.width, self.player.x))
        self.player.y = max(0, min(field.height - self.player.height, self.player.y))
        self.player.rect.pos = (self.player.x, self.player.y)

        if self.shooting:
            self._shoot_timer += dt
            if self._shoot_timer >= self.shoot_cooldown:
                self.shoot()
                self._shoot_timer = 0.0

        for enemy in self.enemies[:]:
            want_shoot = enemy.update(dt)
            if want_shoot:
                bullet_x = enemy.x + 25 - 2.5
                bullet_y = enemy.y
                self.enemy_bullets.append(
                    EnemyBullet(bullet_x, bullet_y, self.ids.game_field.canvas)
                )

        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.y > Window.height:
                self.ids.game_field.canvas.remove(bullet.rect)
                self.bullets.remove(bullet)

        for bullet in self.enemy_bullets[:]:
            bullet.move()
            if bullet.y < 0:
                self.ids.game_field.canvas.remove(bullet.rect)
                self.enemy_bullets.remove(bullet)

        for bullet in self.bullets[:]:
            bullet_removed = False
            for enemy in self.enemies[:]:
                if self.rects_collide(bullet.rect, enemy.rect):
                    enemy.xp -= 1
                    self.ids.game_field.canvas.remove(bullet.rect)
                    self.bullets.remove(bullet)
                    bullet_removed = True
                    if enemy.xp <= 0:
                        self.ids.game_field.canvas.remove(enemy.rect)
                        self.enemies.remove(enemy)
                        self.score += 10
                        self.ids.score_label.text = f"Score: {self.score}"
                    break
            if bullet_removed:
                continue

        for bullet in self.enemy_bullets[:]:
            if self.rects_collide(bullet.rect, self.player.rect):
                self.ids.game_field.canvas.remove(bullet.rect)
                self.enemy_bullets.remove(bullet)
                self.player.xp -= 1
                self.ids.hp_label.text = f"HP: {self.player.xp}"
                if self.player.xp <= 0:
                    self.game_over()


class ShooterApp(MDApp):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(GameScreen(name="game"))
        return sm

    def start_game(self):
        self.root.current = "game"

Builder.load_file("shooter.kv")

if __name__ == "__main__":
    ShooterApp().run()