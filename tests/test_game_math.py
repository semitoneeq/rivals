"""Fast pure Python tests (no pygame required)."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game_math import LEVEL, can_stand, cast_ray, line_of_sight, move_colliding, nav_direction

class GeometryTests(unittest.TestCase):
    def test_map_rectangular(self):
        self.assertEqual(len({len(row) for row in LEVEL}), 1)
    def test_spawn_points_clear(self):
        self.assertTrue(can_stand(LEVEL, 3.5, 6.5))
        self.assertTrue(can_stand(LEVEL, 16.5, 6.5))
    def test_cannot_walk_through_wall(self):
        x, y = move_colliding(LEVEL, 1.5, 1.5, -2.0, 0.0)
        self.assertEqual(x, 1.5)
        self.assertEqual(y, 1.5)
    def test_line_of_sight(self):
        self.assertTrue(line_of_sight(LEVEL, 3.5, 6.5, 16.5, 6.5))
        self.assertFalse(line_of_sight(LEVEL, 7.5, 2.5, 7.5, 5.5))
    def test_bot_finds_path(self):
        dx, dy = nav_direction(LEVEL, 3.5, 3.5, 9.5, 3.5)
        self.assertTrue(-1 <= dx <= 1)
        self.assertTrue(-1 <= dy <= 1)
        self.assertNotEqual((dx,dy), (0,0))
    def test_raycast_hits_east_boundary(self):
        dist, side, u = cast_ray(LEVEL, 16.5, 6.5, 1.0, 0.0)
        self.assertAlmostEqual(dist, 2.5)
        self.assertEqual(side, 0)
        self.assertTrue(0 <= u < 1)

if __name__ == '__main__':
    unittest.main()
