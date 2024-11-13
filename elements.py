import pygame
from typing import Tuple
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
      -90, 0.85
    )
    self.color_bar = color_bar_surface
    self.screen.blit(self.color_bar, 
                     ((SCREEN_WIDTH-color_bar_surface.width)/2, SCREEN_HEIGHT-color_bar_surface.height-15))
    plt.close(fig)