"""2D Vector operations utility."""
import math

class Vector2:
    """2D Vector class for physics calculations."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __str__(self):
        """String representation for debugging."""
        return f"({self.x:.1f}, {self.y:.1f})"
    
    def __repr__(self):
        """Representation for debugging."""
        return f"Vector2({self.x:.1f}, {self.y:.1f})"
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            return Vector2(self.x / mag, self.y / mag)
        return Vector2(0, 0)
    
    def distance_to(self, other):
        return (self - other).magnitude()
    
    def tuple(self):
        return (int(self.x), int(self.y))
