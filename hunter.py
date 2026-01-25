import arcade
import math
from constants import HUNTER_SCALING, HUNTER_SPEED, FaceDirection

class Hunter(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self.scale = HUNTER_SCALING
        self.speed = HUNTER_SPEED

        self.idle_texture = arcade.load_texture(
            ":resources:/images/animated_characters/female_person/femalePerson_idle.png")
        self.texture = self.idle_texture

        self.walk_textures = []
        for i in range(0, 8):
            texture = arcade.load_texture(
                f":resources:/images/animated_characters/female_person/femalePerson_walk{i}.png")
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

    def update_movement(self, delta_time, player, wall_list):
        old_x = self.center_x
        old_y = self.center_y

        x_diff = player.center_x - self.center_x
        y_diff = player.center_y - self.center_y
        distance = math.sqrt(x_diff ** 2 + y_diff ** 2)

        if distance > 0:
            dx = (x_diff / distance) * self.speed * delta_time
            dy = (y_diff / distance) * self.speed * delta_time

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

            if x_diff < 0:
                self.face_direction = FaceDirection.LEFT
            elif x_diff > 0:
                self.face_direction = FaceDirection.RIGHT

            self.is_walking = True
        else:
            self.is_walking = False

        if arcade.check_for_collision_with_list(self, wall_list):
            self.center_x = old_x
            self.center_y = old_y