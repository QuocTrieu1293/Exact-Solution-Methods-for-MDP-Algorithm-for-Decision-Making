import pygame
from typing import Tuple, Callable
from config import *
import matplotlib as mpl
import matplotlib.pyplot as plt
from dataclasses import dataclass
import numpy as np

@dataclass
class ColorBar:
  screen: pygame.Surface
  vmin: float = None
  vmax: float = None
  color_bar: pygame.Surface = None
  
  def update(self, vmin: float, vmax: float):
    if self.vmin == vmin and self.vmax == vmax:
      self.screen.blit(self.color_bar, 
                       ((SCREEN_WIDTH-self.color_bar.width)/2, SCREEN_HEIGHT-self.color_bar.height-15))
      return
    self.vmin = vmin
    self.vmax = vmax
    self.render_color_bar()

  def render_color_bar(self):
    fig, ax = plt.subplots(figsize=(6, 1), layout='constrained')
    norm = mpl.colors.Normalize(self.vmin,self.vmax)
    cbar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=CMAP), cax=ax, orientation='horizontal')
    # fig.patch.set_facecolor((0, 0, 0))
    fig.patch.set_color((52/255, 49/255, 49/255))
    cbar.ax.tick_params(colors='white')

    fig.canvas.draw()
    color_bar_image = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
    color_bar_image = color_bar_image.reshape(fig.canvas.get_width_height()[::-1] + (4,))
    color_bar_surface = pygame.surfarray.make_surface(color_bar_image[:,:,:3]).convert_alpha()
    color_bar_surface = pygame.transform.rotozoom(
      pygame.transform.flip(color_bar_surface, flip_x=False, flip_y=True),
      -90, 0.75
    )
    self.color_bar = color_bar_surface
    self.screen.blit(self.color_bar, 
                     ((SCREEN_WIDTH-color_bar_surface.width)/2, SCREEN_HEIGHT-color_bar_surface.height-15))
    plt.close(fig)

class Button:
  def __init__(self, pos: Tuple[float, float], size: Tuple[float, float], text: str='', elevation: float = 0, callback: Callable = None, enable: bool = True, key: int = None):
    self.pos = pos
    self.enable = enable
    
    text_font = pygame.font.Font('freesansbold.ttf', 16)
    self.text_surf = text_font.render(text,True,(52, 49, 49))
    self.size = (max(size[0], self.text_surf.get_width() + 10), max(size[1], self.text_surf.get_height() + 10))
    
    self.top_rect = pygame.Rect(pos, self.size)
    self.color = '#faf7f0'
    
    self.text_rect = self.text_surf.get_rect(center=self.top_rect.center)
    
    self.elevation = elevation
    self.bottom_rect = pygame.Rect((pos[0], pos[1] + elevation), self.size)
    
    self.callback = callback
    
    self.key = key
    self.mouse_pressed = False
    self.first_mouse_pressed = False
    self.key_pressed = False
    
  def render(self, screen: pygame.Surface):
    if self.enable:
      self.handle_click()
    else:
      self.color = '#cccccc'
    
    pygame.draw.rect(screen, "#817E74", self.bottom_rect, border_radius=7)
    pygame.draw.rect(screen, self.color, self.top_rect, border_radius=7)
    screen.blit(self.text_surf, self.text_rect)
  
  def handle_click(self):
    if self.top_rect.collidepoint(pygame.mouse.get_pos()):
      if not pygame.mouse.get_pressed()[0]:
        self.first_mouse_pressed = True
        if self.mouse_pressed:
          self.mouse_pressed = False
          if self.callback: self.callback()
      elif self.first_mouse_pressed:
        self.mouse_pressed = True
    else:
      self.mouse_pressed = False
      self.first_mouse_pressed = False
      
    if self.key != None:
      if pygame.key.get_pressed()[self.key]:
        self.key_pressed = True
      elif self.key_pressed:
        self.key_pressed = False
        if self.callback: self.callback()
      
    if self.mouse_pressed or self.key_pressed:
      self.color = "#c8c5c0"
      self.top_rect.y = self.pos[1] + self.elevation
    else:
      self.color = '#faf7f0'
      self.top_rect.y = self.pos[1]
      
    self.text_rect.center = self.top_rect.center