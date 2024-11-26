import pygame
import pygame.gfxdraw
from typing import List, Tuple, Callable
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
                       ((SCREEN_WIDTH - self.color_bar.width) / 2 + 100, SCREEN_HEIGHT - self.color_bar.height - 15))
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
                     ((SCREEN_WIDTH - color_bar_surface.width) / 2 + 100, SCREEN_HEIGHT - color_bar_surface.height - 15))
    plt.close(fig)

class Button:
  def __init__(self, pos: Tuple[float, float], size: Tuple[float, float], content: str | pygame.Surface = '', 
               elevation: float = 0, callback: Callable = None, enable: bool = True, key: int = None, text_size:int = 16):
    self.pos = pos
    self.enable = enable
    self.text_size = text_size
    
    if type(content) == str:
      self.content_surf = pygame.font.Font('freesansbold.ttf', self.text_size).render(content,True,(52, 49, 49))
    else:
      self.content_surf = content
    self.size = (max(size[0], self.content_surf.get_width() + 10), max(size[1], self.content_surf.get_height() + 10))
    
    self.top_rect = pygame.Rect(pos, self.size)
    self.color = '#faf7f0'
    
    self.content_rect = self.content_surf.get_rect(center=self.top_rect.center)
    
    self.elevation = elevation
    self.bottom_rect = pygame.Rect((pos[0], pos[1] + elevation), self.size)
    
    self.callback = callback
    
    self.key = key
    self.mouse_pressed = False
    self.mouse_entered = False
    self.key_pressed = False
    
  def render(self, screen: pygame.Surface):
    if not self.enable:
      self.color = '#cccccc'
    elif self.mouse_pressed or self.key_pressed:
      self.color = "#c8c5c0"
      self.top_rect.y = self.pos[1] + self.elevation
    else:
      self.color = '#faf7f0'
      self.top_rect.y = self.pos[1]
    
    self.content_rect.center = self.top_rect.center
    
    pygame.draw.rect(screen, "#817E74", self.bottom_rect, border_radius=7)
    pygame.draw.rect(screen, self.color, self.top_rect, border_radius=7)
    screen.blit(self.content_surf, self.content_rect)
  
  def handle_event(self, event: pygame.Event):
    if not self.enable:
      return
    if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]: 
      if self.top_rect.collidepoint(event.pos):
        left_mouse_pressed = (event.buttons[0] if event.type == pygame.MOUSEMOTION 
                              else event.button == 1 if event.type == pygame.MOUSEBUTTONDOWN 
                              else False)
        if not left_mouse_pressed:
          self.mouse_entered = True
          if self.mouse_pressed:
            self.mouse_pressed = False
            if self.callback: self.callback()
        elif self.mouse_entered:
          self.mouse_pressed = True
      else:
        self.mouse_pressed = False
        self.mouse_entered = False
    elif event.type in [pygame.KEYDOWN, pygame.KEYUP] and event.key == self.key:
      if event.type == pygame.KEYDOWN:
        self.key_pressed = True
      else:
        self.key_pressed = False
        if self.callback: self.callback()

class ToggleButton(Button):
  def __init__(self, pos: Tuple[float, float], size: Tuple[float, float], content: str | pygame.Surface = '', 
               elevation: float = 0, key: int = None, text_size:int = 16, active: bool = False, active_color = '#399918', active_text_color = '#F4CE14'):
    super().__init__(pos=pos, size=size, content=content, elevation=elevation, key=key, text_size=text_size)    
    self.active = active
    self.content = content
    self.active_color = active_color
    self.active_text_color = active_text_color

  def render(self, screen: pygame.Surface):
    if not self.enable:
      self.color = '#cccccc'  
    elif self.active:
      self.color = self.active_color
      self.top_rect.y = self.pos[1] + self.elevation
      if type(self.content) == str: 
        self.content_surf = pygame.font.Font('freesansbold.ttf', self.text_size).render(self.content, True, self.active_text_color)
        self.content_rect = self.content_surf.get_rect()
    else:
      self.color = '#faf7f0'
      self.top_rect.y = self.pos[1]
      if type(self.content) == str: 
        self.content_surf = pygame.font.Font('freesansbold.ttf', self.text_size).render(self.content, True, (52, 49, 49))
        self.content_rect = self.content_surf.get_rect()
    
    self.content_rect.center = self.top_rect.center
    
    pygame.draw.rect(screen, "#817E74", self.bottom_rect, border_radius=7)
    pygame.draw.rect(screen, self.color, self.top_rect, border_radius=7)
    screen.blit(self.content_surf, self.content_rect)

  def handle_event(self, event: pygame.Event):
    if not self.enable: 
      return
    if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
      if self.top_rect.collidepoint(event.pos):
        left_mouse_pressed = (event.buttons[0] if event.type == pygame.MOUSEMOTION 
                              else event.button == 1 if event.type == pygame.MOUSEBUTTONDOWN 
                              else False)
        if not left_mouse_pressed:
          self.mouse_entered = True
          if self.mouse_pressed:
            self.mouse_pressed = False
            self.active = not self.active
        elif self.mouse_entered:
          self.mouse_pressed = True
      else:
        self.mouse_pressed = False
        self.mouse_entered = False
    elif event.type in [pygame.KEYDOWN, pygame.KEYUP] and event.key == self.key:
      if pygame.KEYDOWN and not self.key_pressed:
        self.key_pressed = True
        self.active = not self.active
      else:
        self.key_pressed = False

class Dropdown:
    def __init__(self, pos: Tuple[int, int], options: List[str], size: Tuple[int, int]=(0, 0), color=(250, 247, 240), border_color=(52, 49, 49),
                 text_size=18, font='assets/FiraCode-Medium.ttf', font_bold='assets/FiraCode-SemiBold.ttf', text_color = (52, 49, 49), callbacks: List[Callable | None] = []):
        self.options = options
        self.expanded = False
        self.callbacks = callbacks + [None] * (len(options) - len(callbacks)) if len(options) > len(callbacks) else callbacks
        self.color = color
        self.border_color = border_color
        self.text_color = text_color
        self.font = font
        self.text_size = text_size
        self.sub_text_surfs = [pygame.font.Font(font,text_size-2).render(s, True, (255, 253, 246)) for s in options]
        self.main_text_surfs = [pygame.font.Font(font_bold,text_size).render(s, True, text_color) for s in options]
        size = (max(size[0], max([surf.get_width() for surf in self.main_text_surfs]) + 44*2), 
                     max(size[1], max([surf.get_height() for surf in self.main_text_surfs]) + 10))
        item_size = (size[0], self.sub_text_surfs[0].get_height() + 10)
        self.main_rect = pygame.Rect(pos, size)
        self.sub_rects = [pygame.Rect((pos[0], self.main_rect.bottom + i * item_size[1]), item_size) for i in range(len(options))]
        
        self.update(0)
        self.hovered_index = -1
    
    def update(self, idx):
      self.value = self.options[idx]
      self.selected_index = idx
    
    def render(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.color, self.main_rect)
        pygame.draw.rect(screen, self.border_color, self.main_rect, 3)
        screen.blit(self.main_text_surfs[self.selected_index], 
                    self.main_text_surfs[self.selected_index].get_rect(center=self.main_rect.center))
        pygame.gfxdraw.filled_trigon(screen, self.main_rect.right-34, self.main_rect.centery-5,
                                     self.main_rect.right-27, self.main_rect.centery+5,
                                     self.main_rect.right-20, self.main_rect.centery-5,
                                     self.text_color)
        pygame.gfxdraw.aatrigon(screen, self.main_rect.right-34, self.main_rect.centery-5,
                                     self.main_rect.right-27, self.main_rect.centery+5,
                                     self.main_rect.right-20, self.main_rect.centery-5,
                                     self.text_color)
        
        if not self.expanded:
            return
        for i, rect in enumerate(self.sub_rects):
            rect_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
            rect_surf.fill((0, 0, 0, 120) if i != self.hovered_index else (200, 197, 192, 120))
            screen.blit(rect_surf, rect)
            pygame.draw.rect(screen, (200, 197, 192, 120), rect, 1)
            screen.blit(self.sub_text_surfs[i], self.sub_text_surfs[i].get_rect(center=rect.center))
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION and self.expanded:
          self.hovered_index = -1
          for i, rect in enumerate(self.sub_rects):
            if rect.collidepoint(event.pos):
              self.hovered_index = i
              break
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
          if self.main_rect.collidepoint(event.pos):
              self.expanded = not self.expanded
          elif self.expanded:
              for i, rect in enumerate(self.sub_rects):
                  if rect.collidepoint(event.pos):
                      self.update(i)
                      if self.callbacks[i]:
                          self.callbacks[i]()
                      break
              self.expanded = False
        
        if not self.expanded: self.hovered_index = -1
        