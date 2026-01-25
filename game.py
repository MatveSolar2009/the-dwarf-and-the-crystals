import arcade
import random
import os
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, TILE_SIZE, CRYSTAL_SCALING, OBSTACLE_SCALING, GAME_MENU, GAME_PLAYING, GAME_WIN, GAME_LOSE
from hero import Hero
from hunter import Hunter

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        self.game_state = GAME_MENU

        self.player_list = None
        self.crystal_list = None
        self.hunter_list = None
        self.obstacle_list = None
        self.wall_list = None

        self.player = None

        self.score = 0
        self.total_crystals = 0

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
        self.maps.append(("Маленькая карта", map1))


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

    def setup_game(self, map_index):
        self.game_state = GAME_PLAYING

        self.player_list = arcade.SpriteList()
        self.crystal_list = arcade.SpriteList()
        self.hunter_list = arcade.SpriteList()
        self.obstacle_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()

        map_name, map_data = self.maps[map_index]
        self.current_map_name = map_name

        map_height = len(map_data)
        map_width = len(map_data[0]) if map_data else 0

        start_x = (SCREEN_WIDTH - map_width * TILE_SIZE) // 2
        start_y = (SCREEN_HEIGHT - map_height * TILE_SIZE) // 2

        self.map_left = start_x + TILE_SIZE // 2
        self.map_right = start_x + (map_width - 1) * TILE_SIZE + TILE_SIZE // 2
        self.map_bottom = start_y + TILE_SIZE // 2
        self.map_top = start_y + (map_height - 1) * TILE_SIZE + TILE_SIZE // 2

        player_start_positions = []
        crystal_positions = []
        hunter_positions = []

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

        for i in range(min(2, len(hunter_positions))):
            hunter = Hunter()
            hunter.set_map_bounds(self.map_left, self.map_right, self.map_bottom, self.map_top)
            hunter.color = (255, 100, 100)

            if i < len(hunter_positions):
                hunter_x, hunter_y = hunter_positions[i]
                hunter.center_x = hunter_x
                hunter.center_y = hunter_y

            self.hunter_list.append(hunter)

        if not self.hunter_list:
            for i in range(2):
                hunter = Hunter()
                hunter.set_map_bounds(self.map_left, self.map_right, self.map_bottom, self.map_top)
                hunter.color = (255, 100, 100)

                hunter.center_x = random.randrange(int(self.map_left + 50), int(self.map_right - 50))
                hunter.center_y = random.randrange(int(self.map_bottom + 50), int(self.map_top - 50))

                self.hunter_list.append(hunter)

        self.collect_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.game_over_sound = arcade.load_sound(":resources:sounds/gameover2.wav")
        self.win_sound = arcade.load_sound(":resources:sounds/upgrade1.wav")

        self.score = 0

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

        arcade.draw_text("ГНОМ И КРИСТАЛЛЫ",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                         arcade.color.GOLD, 48, anchor_x="center")

        arcade.draw_text("Выберите карту:",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180,
                         arcade.color.WHITE, 32, anchor_x="center")

        for i, item in enumerate(self.menu_items):
            color = arcade.color.YELLOW if i == self.selected_item else arcade.color.WHITE
            y_pos = SCREEN_HEIGHT - 250 - i * 50

            arcade.draw_text(f"{i + 1}. {item}",
                             SCREEN_WIDTH // 2, y_pos,
                             color, 28, anchor_x="center")

        arcade.draw_text("↑↓ - Выбор, ENTER - Начать, ESC - Выход",
                         SCREEN_WIDTH // 2, 100,
                         arcade.color.LIGHT_GRAY, 20, anchor_x="center")

    def draw_game(self):
        arcade.set_background_color(arcade.color.DARK_GREEN)

        self.wall_list.draw()
        self.obstacle_list.draw()
        self.crystal_list.draw()
        self.hunter_list.draw()
        self.player_list.draw()

        arcade.draw_text(f"Кристаллы: {self.score}/{self.total_crystals}",
                         10, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 18)

        arcade.draw_text(f"Карта: {self.current_map_name}",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 16, anchor_x="center")

        arcade.draw_text("ESC - Меню",
                         SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 14)

    def draw_win_screen(self):
        arcade.set_background_color(arcade.color.DARK_GREEN)

        arcade.draw_text("ПОБЕДА!",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
                         arcade.color.GREEN, 60, anchor_x="center", bold=True)

        arcade.draw_text(f"Карта: {self.current_map_name}",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40,
                         arcade.color.WHITE, 24, anchor_x="center")

        arcade.draw_text(f"Собрано кристаллов: {self.score}/{self.total_crystals}",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                         arcade.color.WHITE, 28, anchor_x="center")

        arcade.draw_text("ESC - Меню",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60,
                         arcade.color.LIGHT_GRAY, 22, anchor_x="center")

        arcade.draw_text("R - Рестарт",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100,
                         arcade.color.LIGHT_GRAY, 22, anchor_x="center")

    def draw_lose_screen(self):
        arcade.set_background_color(arcade.color.DARK_RED)

        arcade.draw_text("GAME OVER",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
                         arcade.color.RED, 60, anchor_x="center", bold=True)

        arcade.draw_text("Охотник поймал гнома!",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30,
                         arcade.color.WHITE, 28, anchor_x="center")

        arcade.draw_text(f"Собрано кристаллов: {self.score}/{self.total_crystals}",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20,
                         arcade.color.WHITE, 24, anchor_x="center")

        arcade.draw_text("ESC - Меню",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80,
                         arcade.color.LIGHT_GRAY, 22, anchor_x="center")

        arcade.draw_text("R - Рестарт",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120,
                         arcade.color.LIGHT_GRAY, 22, anchor_x="center")

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