import arcade
import os
from game import MyGame

def create_example_map():
    if not os.path.exists("maps"):
        os.makedirs("maps")

    example_map = """################################
#....C...C.........C...C.......#
#..O.....C..O......C...C.......#
#....P..C..........C...C.......#
#..O.....C..O......C...C..O....#
#....C...C.........C...C.......#
#....C...C.......O.C...C...H...#
#....C.O.C.........C...C.......#
#....C...C.........C...C...H...#
#....C...C.....O...C...C.......#
#....C.O.C.........C...C.......#
#....C...C..O......C...C...O...#
#....C...C.........C...C.......#
#......H...........C...C.......#
################################"""

    with open("maps/example_map.txt", "w", encoding="utf-8") as f:
        f.write(example_map)

if __name__ == "__main__":
    create_example_map()

    window = MyGame()
    arcade.run()