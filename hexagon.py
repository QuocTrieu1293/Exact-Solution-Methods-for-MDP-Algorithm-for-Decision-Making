from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

import pygame
from pygame import gfxdraw
import numpy as np
import pygame.gfxdraw

@dataclass
class HexagonTile:
  """Hexagon class"""

  radius: float
  position: Tuple[float, float]
  colour: Tuple[int, ...]
  border_colour: Tuple[int, ...]
  highlight_offset: int = 3
  max_highlight_ticks: int = 15
  value: float = None
  action: int = None
  clicked: bool = False
  first_hovered: bool = False

  def __post_init__(self):
    self.vertices = self.compute_vertices()
    self.highlight_tick = 0

  def update(self):
    """Updates tile highlights"""
    if self.highlight_tick > 0:
      self.highlight_tick -= 1

  def compute_vertices(self) -> List[Tuple[float, float]]:
    """Returns a list of the hexagon's vertices as x, y tuples"""
    x, y = self.position
    half_radius = self.radius / 2
    minimal_radius = self.minimal_radius
    return [
      (x + minimal_radius, y + 3 * half_radius),
      (x + minimal_radius, y + half_radius),
      (x, y),
      (x - minimal_radius, y + half_radius),
      (x - minimal_radius, y + 3 * half_radius),
      (x, y + 2 * self.radius),
    ]

  # def compute_neighbours(self, hexagons: List[HexagonTile]) -> List[HexagonTile]:
  #   """Returns hexagons whose centres are two minimal radiuses away from self.centre"""
  #   # could cache results for performance
  #   return [hexagon for hexagon in hexagons if self.is_neighbour(hexagon)]

  def collide_with_point(self, point: Tuple[float, float]) -> bool:
    """Returns True if distance from centre to point is less than horizontal_length"""
    return math.dist(point, self.centre) < self.minimal_radius

  # def is_neighbour(self, hexagon: HexagonTile) -> bool:
  #   """Returns True if hexagon centre is approximately
  #   2 minimal radiuses away from own centre
  #   """
  #   distance = math.dist(hexagon.centre, self.centre)
  #   return math.isclose(distance, 2 * self.minimal_radius, rel_tol=0.05)

  def render(self, screen:pygame.Surface) -> None:
    """Renders the hexagon on the screen"""
    pygame.draw.polygon(screen, self.highlight_colour, self.vertices)
    pygame.draw.polygon(screen, self.border_colour, self.vertices, 3)
    
    if not np.isnan(self.value) and self.value != None:
      font = pygame.font.Font(None, 23)
      value = round(self.value, 2)
      text_surface = font.render(str(int(value) if value.is_integer() else value), True, (0, 0, 0))
      text_rect = text_surface.get_rect(center=self.centre)
      screen.blit(text_surface, text_rect)
      
    if self.action != None:
      pygame.gfxdraw.aapolygon(screen, self.actions_arrows[self.action], (250, 177, 47))
      pygame.gfxdraw.filled_polygon(screen, self.actions_arrows[self.action], (250, 177, 47))
      
      # font = pygame.font.Font(None, 16)
      # for i in range(6):
      #   text_surface = font.render(str(i), True, (243, 198, 35))
      #   text_rect = text_surface.get_rect(center=self.actions_arrows[i][0])
      #   screen.blit(text_surface, text_rect)
      
      

  def render_highlight(self, screen, border_colour) -> None:
    """Draws a border around the hexagon with the specified colour"""
    self.highlight_tick = self.max_highlight_ticks
    pygame.gfxdraw.aapolygon(screen, self.vertices, border_colour)

  @property
  def centre(self) -> Tuple[float, float]:
    """Centre of the hexagon"""
    x, y = self.position
    return (x, y + self.radius)

  @property
  def minimal_radius(self) -> float:
    """Horizontal length of the hexagon"""
    return self.radius * math.cos(math.radians(30))

  @property
  def highlight_colour(self) -> Tuple[int, ...]:
    """Colour of the hexagon tile when rendering highlight"""
    offset = self.highlight_offset * self.highlight_tick
    brighten = lambda x, y: x + y if x + y < 255 else 255
    return tuple(brighten(x, offset) for x in self.colour)
  
  @property
  def actions_arrows(self) -> List[List[Tuple[float, float]]]:
    cx, cy = self.centre
    right_arrow = [
      (cx + self.minimal_radius - 5, cy),  # đầu mũi tên
      (cx + self.minimal_radius - 12, cy - self.minimal_radius/6),
      (cx + self.minimal_radius - 10, cy), # đích mũi tên
      (cx + self.minimal_radius - 12, cy + self.minimal_radius/6),
    ]
    
    return [
      [(
        math.cos(math.radians(deg)) * (x - cx) - math.sin(math.radians(deg)) * (y - cy) + cx, 
        math.sin(math.radians(deg)) * (x - cx) + math.cos(math.radians(deg)) * (y - cy) + cy
      ) for x,y in right_arrow] for deg in range(-0, -360, -60) # phải dùng góc âm vì gốc toạ độ của chương trình là góc trên bên trái
    ]
    
  def check_clicked(self) -> bool:
    pressed_mouse = pygame.mouse.get_pressed()
    if self.collide_with_point(pygame.mouse.get_pos()):
      if not pressed_mouse[0]:
        self.first_hovered = True
        if self.mouse_pressed:
          self.mouse_pressed = False
          return True
      elif self.first_hovered:
        self.mouse_pressed = True
    else:
      self.mouse_pressed = False
      self.first_hovered = False
    
    return False
  
  def render_clicked_border(self, screen) -> None:
    pygame.draw.polygon(screen, '#399918', self.vertices, 5)