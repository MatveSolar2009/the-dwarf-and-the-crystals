import arcade
import random
import os
import math
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, TILE_SIZE, CRYSTAL_SCALING, OBSTACLE_SCALING, GAME_MENU, GAME_PLAYING, GAME_WIN, GAME_LOSE
from hero import Hero
from hunter import Hunter


class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.game_state = GAME_MENU

        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()

        self.player_list = None
        self.crystal_list = None
        self.hunter_list = None
        self.obstacle_list = None
        self.wall_list = None
        self.particle_list = None

        self.player = None

        self.score = 0
        self.total_crystals = 0
        self.total_hunters = 0

        self.collect_sound = None
        self.game_over_sound = None
        self.win_sound = None

        self.menu_items = []
        self.selected_item = 0

        self.maps = []
        self.load_maps()

        self.keys_pressed = set()

        self.map_left = 0
        self.map_right = SCREEN_WIDTH
        self.map_bottom = 0
        self.map_top = SCREEN_HEIGHT

        self.CAMERA_LERP = 0.12
        self.DEAD_ZONE_W = int(SCREEN_WIDTH * 0.35)
        self.DEAD_ZONE_H = int(SCREEN_HEIGHT * 0.45)

        self.create_particle_textures()

        self.gui_texts = []

    def create_particle_textures(self):
        self.gold_particle_texture = arcade.make_soft_circle_texture(
            8, arcade.color.GOLD, 255, 50
        )

        self.blue_particle_texture = arcade.make_soft_circle_texture(
            8, (100, 200, 255), 255, 50
        )

        self.spark_textures = [
            arcade.make_soft_circle_texture(6, arcade.color.GOLD, 200, 40),
            arcade.make_soft_circle_texture(6, arcade.color.YELLOW, 200, 40),
            arcade.make_soft_circle_texture(6, (100, 200, 255), 200, 40),
            arcade.make_soft_circle_texture(6, arcade.color.CYAN, 200, 40),
        ]

    def load_maps(self):
        self.maps = []

        map1 = [
            "################",
            "#....C...C.....#",
            "#..O.....C..O..#",
            "#....P..C......#",
            "#..O.....C..O..#",
            "#....C...C.....#",
            "#......H.......#",
            "################"
        ]
        self.maps.append(("Маленькая карта (1 охотник)", map1))

        try:
            if os.path.exists("maps"):
                for filename in os.listdir("maps"):
                    if filename.endswith(".txt"):
                        with open(f"maps/{filename}", "r", encoding="utf-8") as f:
                            map_data = [line.strip() for line in f.readlines()]
                            map_name = filename.replace(".txt", "").replace("_", " ")
                            self.maps.append((map_name, map_data))
        except:
            pass

        self.maps.sort(key=lambda x: x[0])

        self.menu_items = []
        for i, (name, _) in enumerate(self.maps):
            self.menu_items.append(name)

    def find_valid_position(self, taken_positions, min_distance=50):
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randrange(int(self.map_left + 100), int(self.map_right - 100))
            y = random.randrange(int(self.map_bottom + 100), int(self.map_top - 100))

            valid = True
            for pos in taken_positions:
                dist = math.sqrt((x - pos[0])**2 + (y - pos[1])**2)
                if dist < min_distance:
                    valid = False
                    break

            if valid:
                return (x, y)
        return None

    def setup_game(self, map_index):
        self.game_state = GAME_PLAYING

        self.player_list = arcade.SpriteList()
        self.crystal_list = arcade.SpriteList()
        self.hunter_list = arcade.SpriteList()
        self.obstacle_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.particle_list = arcade.SpriteList()
        self.gui_texts = []

        map_name, map_data = self.maps[map_index]
        self.current_map_name = map_name

        map_height = len(map_data)
        map_width = len(map_data[0]) if map_data else 0

        map_pixel_width = map_width * TILE_SIZE
        map_pixel_height = map_height * TILE_SIZE

        self.world_width = map_pixel_width
        self.world_height = map_pixel_height

        start_x = 0
        start_y = 0

        self.map_left = start_x + TILE_SIZE // 2
        self.map_right = start_x + (map_width - 1) * TILE_SIZE + TILE_SIZE // 2
        self.map_bottom = start_y + TILE_SIZE // 2
        self.map_top = start_y + (map_height - 1) * TILE_SIZE + TILE_SIZE // 2

        player_start_positions = []
        crystal_positions = []
        hunter_positions = []
        obstacle_positions = []

        for row_index, row in enumerate(map_data):
            for col_index, cell in enumerate(row):
                x = start_x + col_index * TILE_SIZE + TILE_SIZE // 2
                y = start_y + (map_height - row_index - 1) * TILE_SIZE + TILE_SIZE // 2

                if cell == '#':
                    wall = arcade.Sprite(":resources:images/tiles/brickBrown.png", OBSTACLE_SCALING)
                    wall.center_x = x
                    wall.center_y = y
                    self.wall_list.append(wall)
                elif cell == 'O':
                    obstacle = arcade.Sprite(":resources:/images/tiles/boxCrate_double.png", OBSTACLE_SCALING)
                    obstacle.center_x = x
                    obstacle.center_y = y
                    self.obstacle_list.append(obstacle)
                    obstacle_positions.append((x, y))
                elif cell == 'P':
                    player_start_positions.append((x, y))
                elif cell == 'C':
                    crystal_positions.append((x, y))
                elif cell == 'H':
                    hunter_positions.append((x, y))

        self.all_walls = arcade.SpriteList()
        self.all_walls.extend(self.wall_list)
        self.all_walls.extend(self.obstacle_list)

        self.player = Hero()
        self.player.set_map_bounds(self.map_left, self.map_right, self.map_bottom, self.map_top)

        if player_start_positions:
            start_x, start_y = player_start_positions[0]
            self.player.center_x = start_x
            self.player.center_y = start_y

        self.player_list.append(self.player)

        self.total_crystals = len(crystal_positions)

        for x, y in crystal_positions:
            crystal = arcade.Sprite(":resources:images/items/coinGold.png", CRYSTAL_SCALING)
            crystal.color = (0, 150, 255)
            crystal.center_x = x
            crystal.center_y = y
            self.crystal_list.append(crystal)

        taken_positions = []
        if player_start_positions:
            taken_positions.append((player_start_positions[0][0], player_start_positions[0][1]))

        for pos in obstacle_positions:
            taken_positions.append(pos)

        for pos in crystal_positions:
            taken_positions.append(pos)

        for x, y in hunter_positions:
            hunter = Hunter()
            hunter.set_map_bounds(self.map_left, self.map_right, self.map_bottom, self.map_top)

            color_variation = random.randint(-30, 30)
            hunter.color = (
                min(255, max(150, 255 + color_variation)),
                min(255, max(50, 100 + color_variation)),
                min(255, max(50, 100 + color_variation))
            )

            hunter.center_x = x
            hunter.center_y = y
            self.hunter_list.append(hunter)
            taken_positions.append((x, y))

        self.total_hunters = len(self.hunter_list)

        self.collect_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.game_over_sound = arcade.load_sound(":resources:sounds/gameover2.wav")
        self.win_sound = arcade.load_sound(":resources:sounds/upgrade1.wav")

        self.score = 0

        self.crystals_text = arcade.Text(
            f"Кристаллы: {self.score}/{self.total_crystals}",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 18
        )

        self.hunters_text = arcade.Text(
            f"Охотников: {self.total_hunters}",
            10, SCREEN_HEIGHT - 60,
            arcade.color.WHITE, 16
        )

        self.map_name_text = arcade.Text(
            f"Карта: {self.current_map_name}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 16,
            anchor_x="center"
        )

        self.menu_text = arcade.Text(
            "ESC - Меню",
            SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 14
        )

        self.gui_texts.extend([self.crystals_text, self.hunters_text, self.map_name_text, self.menu_text])

        self.world_camera.position = (self.player.center_x, self.player.center_y)

    def create_collect_particles(self, x, y, count=15):
        for _ in range(count):
            particle = arcade.Sprite()
            particle.texture = random.choice(self.spark_textures)
            particle.center_x = x
            particle.center_y = y

            speed = random.uniform(1.0, 3.0)
            angle = random.uniform(0, 2 * math.pi)

            particle.change_x = math.cos(angle) * speed
            particle.change_y = math.sin(angle) * speed

            initial_scale = random.uniform(0.3, 0.6)
            particle.scale = initial_scale
            particle.alpha = random.randint(200, 255)

            particle.particle_data = {
                'change_scale': -0.02,
                'change_alpha': -8,
                'lifetime': random.uniform(0.5, 1.0)
            }

            self.particle_list.append(particle)

    def create_score_particles(self, x, y, count=8):
        for _ in range(count):
            particle = arcade.Sprite()
            particle.texture = self.blue_particle_texture
            particle.center_x = x
            particle.center_y = y

            target_x = SCREEN_WIDTH // 2
            target_y = SCREEN_HEIGHT - 30

            dx = target_x - x
            dy = target_y - y
            distance = max(math.sqrt(dx*dx + dy*dy), 1)

            speed = random.uniform(3.0, 5.0)

            particle.change_x = (dx / distance) * speed
            particle.change_y = (dy / distance) * speed

            initial_scale = random.uniform(0.2, 0.4)
            particle.scale = initial_scale
            particle.alpha = 220

            particle.particle_data = {
                'change_scale': -0.01,
                'change_alpha': -5,
                'lifetime': 1.5
            }

            self.particle_list.append(particle)

    def on_draw(self):
        self.clear()

        if self.game_state == GAME_MENU:
            self.draw_menu()
        elif self.game_state == GAME_PLAYING:
            self.draw_game()
        elif self.game_state == GAME_WIN:
            self.draw_win_screen()
        elif self.game_state == GAME_LOSE:
            self.draw_lose_screen()

    def draw_menu(self):
        arcade.set_background_color(arcade.color.DARK_BLUE)

        title_text = arcade.Text(
            "ГНОМ И КРИСТАЛЛЫ",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
            arcade.color.GOLD, 48,
            anchor_x="center"
        )

        subtitle_text = arcade.Text(
            "Выберите карту:",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180,
            arcade.color.WHITE, 32,
            anchor_x="center"
        )

        menu_texts = []
        for i, item in enumerate(self.menu_items):
            color = arcade.color.YELLOW if i == self.selected_item else arcade.color.WHITE
            y_pos = SCREEN_HEIGHT - 250 - i * 50

            text = arcade.Text(
                f"{i + 1}. {item}",
                SCREEN_WIDTH // 2, y_pos,
                color, 28,
                anchor_x="center"
            )
            menu_texts.append(text)

        instruction_text = arcade.Text(
            "↑↓ - Выбор, ENTER - Начать, ESC - Выход",
            SCREEN_WIDTH // 2, 100,
            arcade.color.LIGHT_GRAY, 20,
            anchor_x="center"
        )

        title_text.draw()
        subtitle_text.draw()
        for text in menu_texts:
            text.draw()
        instruction_text.draw()

    def draw_game(self):
        arcade.set_background_color(arcade.color.DARK_GREEN)

        self.world_camera.use()

        self.wall_list.draw()
        self.obstacle_list.draw()
        self.crystal_list.draw()
        self.hunter_list.draw()
        self.player_list.draw()
        self.particle_list.draw()

        self.gui_camera.use()

        self.crystals_text.text = f"Кристаллы: {self.score}/{self.total_crystals}"
        self.hunters_text.text = f"Охотников: {self.total_hunters}"
        for text in self.gui_texts:
            text.draw()

    def draw_win_screen(self):
        arcade.set_background_color(arcade.color.DARK_GREEN)

        texts = []
        texts.append(arcade.Text(
            "ПОБЕДА!",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
            arcade.color.GREEN, 60,
            anchor_x="center", bold=True
        ))

        texts.append(arcade.Text(
            f"Карта: {self.current_map_name}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40,
            arcade.color.WHITE, 24,
            anchor_x="center"
        ))

        texts.append(arcade.Text(
            f"Собрано кристаллов: {self.score}/{self.total_crystals}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            arcade.color.WHITE, 28,
            anchor_x="center"
        ))

        texts.append(arcade.Text(
            f"Избежано охотников: {self.total_hunters}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40,
            arcade.color.WHITE, 24,
            anchor_x="center"
        ))

        texts.append(arcade.Text(
            "ESC - Меню",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 90,
            arcade.color.LIGHT_GRAY, 22,
            anchor_x="center"
        ))

        texts.append(arcade.Text(
            "R - Рестарт",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 130,
            arcade.color.LIGHT_GRAY, 22,
            anchor_x="center"
        ))

        for text in texts:
            text.draw()

    def draw_lose_screen(self):
        arcade.set_background_color(arcade.color.DARK_RED)

        texts = []
        texts.append(arcade.Text(
            "GAME OVER",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
            arcade.color.RED, 60,
            anchor_x="center", bold=True
        ))

        texts.append(arcade.Text(
            f"Охотников на карте: {self.total_hunters}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40,
            arcade.color.WHITE, 24,
            anchor_x="center"
        ))

        texts.append(arcade.Text(
            "Вы были пойманы охотником!",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
            arcade.color.WHITE, 28,
            anchor_x="center"
        ))

        texts.append(arcade.Text(
            f"Собрано кристаллов: {self.score}/{self.total_crystals}",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40,
            arcade.color.WHITE, 24,
            anchor_x="center"
        ))

        texts.append(arcade.Text(
            "ESC - Меню",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 90,
            arcade.color.LIGHT_GRAY, 22,
            anchor_x="center"
        ))

        texts.append(arcade.Text(
            "R - Рестарт",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 130,
            arcade.color.LIGHT_GRAY, 22,
            anchor_x="center"
        ))

        for text in texts:
            text.draw()

    def on_update(self, delta_time):
        if self.game_state != GAME_PLAYING:
            return

        if self.player:
            self.player.update_movement(delta_time, self.keys_pressed, self.all_walls)
            self.player.update_animation(delta_time)

        for hunter in self.hunter_list:
            hunter.update_movement(delta_time, self.player, self.all_walls)
            hunter.update_animation(delta_time)

            if arcade.check_for_collision(hunter, self.player):
                self.game_state = GAME_LOSE
                try:
                    arcade.play_sound(self.game_over_sound)
                except:
                    pass
                return

        crystals_hit = arcade.check_for_collision_with_list(self.player, self.crystal_list)

        for crystal in crystals_hit:
            self.create_collect_particles(crystal.center_x, crystal.center_y)
            self.create_score_particles(crystal.center_x, crystal.center_y)

            crystal.remove_from_sprite_lists()
            self.score += 1

            try:
                arcade.play_sound(self.collect_sound)
            except:
                pass

        if self.score >= self.total_crystals:
            self.game_state = GAME_WIN
            try:
                arcade.play_sound(self.win_sound)
            except:
                pass

        particles_to_remove = []
        for particle in self.particle_list:
            particle.center_x += particle.change_x
            particle.center_y += particle.change_y

            if hasattr(particle, 'particle_data'):
                data = particle.particle_data

                current_scale = particle.scale
                if isinstance(current_scale, tuple):
                    new_scale = max(0.01, current_scale[0] + data['change_scale'])
                    particle.scale = (new_scale, new_scale)
                    scale_check = new_scale
                else:
                    new_scale = max(0.01, current_scale + data['change_scale'])
                    particle.scale = new_scale
                    scale_check = new_scale

                particle.alpha = max(0, particle.alpha + data['change_alpha'])

                data['lifetime'] -= delta_time

                if data['lifetime'] <= 0 or scale_check <= 0.01 or particle.alpha <= 0:
                    particles_to_remove.append(particle)

        for particle in particles_to_remove:
            particle.remove_from_sprite_lists()

        if self.player and self.world_camera:
            cam_x, cam_y = self.world_camera.position

            dz_left = cam_x - self.DEAD_ZONE_W // 2
            dz_right = cam_x + self.DEAD_ZONE_W // 2
            dz_bottom = cam_y - self.DEAD_ZONE_H // 2
            dz_top = cam_y + self.DEAD_ZONE_H // 2

            px, py = self.player.center_x, self.player.center_y

            target_x, target_y = cam_x, cam_y

            if px < dz_left:
                target_x = px + self.DEAD_ZONE_W // 2
            elif px > dz_right:
                target_x = px - self.DEAD_ZONE_W // 2

            if py < dz_bottom:
                target_y = py + self.DEAD_ZONE_H // 2
            elif py > dz_top:
                target_y = py - self.DEAD_ZONE_H // 2

            half_w = self.width / 2 / self.world_camera.zoom
            half_h = self.height / 2 / self.world_camera.zoom

            target_x = max(half_w, min(self.world_width - half_w, target_x))
            target_y = max(half_h, min(self.world_height - half_h, target_y))

            new_x = cam_x + (target_x - cam_x) * self.CAMERA_LERP
            new_y = cam_y + (target_y - cam_y) * self.CAMERA_LERP
            self.world_camera.position = (new_x, new_y)

    def on_key_press(self, key, modifiers):
        if self.game_state == GAME_MENU:
            if key == arcade.key.UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
            elif key == arcade.key.DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            elif key == arcade.key.ENTER or key == arcade.key.SPACE:
                self.setup_game(self.selected_item)
            elif key == arcade.key.ESCAPE:
                arcade.close_window()
        elif self.game_state == GAME_PLAYING:
            self.keys_pressed.add(key)
            if key == arcade.key.ESCAPE:
                self.game_state = GAME_MENU
        elif self.game_state in (GAME_WIN, GAME_LOSE):
            if key == arcade.key.R:
                self.setup_game(self.selected_item)
            elif key == arcade.key.ESCAPE:
                self.game_state = GAME_MENU

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def on_resize(self, width, height):
        super().on_resize(width, height)

        if hasattr(self, 'crystals_text') and self.crystals_text:
            self.crystals_text.y = height - 30

        if hasattr(self, 'hunters_text') and self.hunters_text:
            self.hunters_text.y = height - 60

        if hasattr(self, 'map_name_text') and self.map_name_text:
            self.map_name_text.x = width // 2
            self.map_name_text.y = height - 30

        if hasattr(self, 'menu_text') and self.menu_text:
            self.menu_text.x = width - 100
            self.menu_text.y = height - 30

        self.DEAD_ZONE_W = int(width * 0.35)
        self.DEAD_ZONE_H = int(height * 0.45)


def main():
    game = MyGame()
    arcade.run()


if __name__ == "__main__":
    main()