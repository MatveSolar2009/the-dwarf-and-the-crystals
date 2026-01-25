import arcade
import math
from constants import PLAYER_SCALING, PLAYER_SPEED, FaceDirection

class Hero(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.scale = PLAYER_SCALING
        self.speed = PLAYER_SPEED
        self.health = 100

        self.idle_texture = arcade.load_texture(
            ":resources:/images/animated_characters/male_person/malePerson_idle.png")
        self.texture = self.idle_texture

        self.walk_textures = []
        for i in range(0, 8):
            texture = arcade.load_texture(f":resources:/images/animated_characters/male_person/malePerson_walk{i}.png")
            self.walk_textures.append(texture)

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1

        self.is_walking = False
        self.face_direction = FaceDirection.RIGHT

        self.map_left = 0
        self.map_right = 1000
        self.map_bottom = 0
        self.map_top = 1000

    def set_map_bounds(self, left, right, bottom, top):
        self.map_left = left
        self.map_right = right
        self.map_bottom = bottom
        self.map_top = top

    def update_animation(self, delta_time: float = 1 / 60):
        if self.is_walking:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.walk_textures):
                    self.current_texture = 0
                if self.face_direction == FaceDirection.RIGHT:
                    self.texture = self.walk_textures[self.current_texture]
                else:
                    self.texture = self.walk_textures[self.current_texture].flip_horizontally()
        else:
            if self.face_direction == FaceDirection.RIGHT:
                self.texture = self.idle_texture
            else:
                self.texture = self.idle_texture.flip_horizontally()

    def update_movement(self, delta_time, keys_pressed, wall_list):
        old_x = self.center_x
        old_y = self.center_y

        dx, dy = 0, 0
        if arcade.key.LEFT in keys_pressed or arcade.key.A in keys_pressed:
            dx -= self.speed * delta_time
        if arcade.key.RIGHT in keys_pressed or arcade.key.D in keys_pressed:
            dx += self.speed * delta_time
        if arcade.key.UP in keys_pressed or arcade.key.W in keys_pressed:
            dy += self.speed * delta_time
        if arcade.key.DOWN in keys_pressed or arcade.key.S in keys_pressed:
            dy -= self.speed * delta_time

        if dx != 0 and dy != 0:
            factor = 0.7071
            dx *= factor
            dy *= factor

        self.center_x += dx
        self.center_y += dy

        half_width = self.width / 2
        half_height = self.height / 2

        if self.center_x - half_width < self.map_left:
            self.center_x = self.map_left + half_width
        elif self.center_x + half_width > self.map_right:
            self.center_x = self.map_right - half_width

        if self.center_y - half_height < self.map_bottom:
            self.center_y = self.map_bottom + half_height
        elif self.center_y + half_height > self.map_top:
            self.center_y = self.map_top - half_height

        if arcade.check_for_collision_with_list(self, wall_list):
            self.center_x = old_x
            self.center_y = old_y

        if dx < 0:
            self.face_direction = FaceDirection.LEFT
        elif dx > 0:
            self.face_direction = FaceDirection.RIGHT

        self.is_walking = dx != 0 or dy != 0