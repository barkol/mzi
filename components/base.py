"""Base component class."""
import pygame
from utils.vector import Vector2
from config.settings import COMPONENT_RADIUS

class Component:
    """Base class for all optical components."""
    
    def __init__(self, x, y, component_type):
        self.position = Vector2(x, y)
        self.component_type = component_type
        self.rotation = 0
        self.radius = COMPONENT_RADIUS
        self.placed_time = pygame.time.get_ticks()
    
    def draw(self, screen):
        """Draw the component. Override in subclasses."""
        raise NotImplementedError
    
    def contains_point(self, x, y):
        """Check if point is within component."""
        return self.position.distance_to(Vector2(x, y)) <= self.radius
    
    def process_beam(self, beam):
        """Process incoming beam. Override in subclasses."""
        raise NotImplementedError
