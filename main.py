import numpy as np
from typing import List, Tuple
import math
import pygame
from hexagon import HexagonTile
from HexWorldMDP import HexWorldMDP
from ch07 import PolicyIteration
from elements import ColorBar, Button
from config import *
from sys import exit

def create_hexagon(position) -> HexagonTile:
  """Creates a hexagon tile at the specified position"""
  return HexagonTile(HEX_RADIUS, position, colour=(255, 253, 246), border_colour=(55, 175, 225))

def create_text(text, font='FiraCode-Medium.ttf', size=24, color=(255, 253, 246)) -> pygame.Surface:
  text_font = pygame.font.Font(font,size)
  return text_font.render(text, True, color=color)

def value_to_color(U) -> List[Tuple[int, int, int]]:
  min_val, max_val = np.nanmin(U), np.nanmax(U)
  
  colors = []
  for val in U:
    if np.isnan(val):
      normalized_val = 0.5
    else:
      normalized_val = (val - min_val) / (max_val - min_val)
    color = CMAP(normalized_val)
    
    # # lighten color
    # alpha, white = 0.15, np.array([1,1,1])  
    # color = (1 - alpha) * np.array(color[:3]) + alpha * white
    
    colors.append((
      [int(c * 255) for c in color[:3]], 
      [int(c * 255) for c in CMAP(1.0 if normalized_val >= 0.5 else 0.0)[:3]]
    ))
    
  return colors

def init_hexagons(hexes) -> List[HexagonTile]:
  # """Creates a hexagonal tile map"""
  hexagons = []
  
  i_min, j_min = float('inf'), float('inf')
  for i, j in hexes:
    i_min = min(i_min, i)
    j_min = min(j_min, j)
  
  MARGIN_LEFT = 30
  MARGIN_BOTTOM = 120
  MARGIN = 5
  x_start, y_start = MIN_HEX_RADIUS + MARGIN_LEFT, SCREEN_HEIGHT - 2 * HEX_RADIUS - MARGIN_BOTTOM
  for i, j in hexes:
    diff_i, diff_j = i - i_min, j - j_min
    x = x_start + diff_i * (2 * MIN_HEX_RADIUS + MARGIN * math.sqrt(2)) + diff_j * (MIN_HEX_RADIUS + MARGIN) 
    y = y_start - diff_j * (3/2 * HEX_RADIUS + MARGIN)
    hexagons.append(create_hexagon((x,y)))
    
  return hexagons

def render(screen: pygame.Surface, hexagons: List[HexagonTile]):
  """Renders hexagons on the screen"""
  for hexagon in hexagons:
    hexagon.render(screen)
    
  # display Iteration
  iteration_surface = create_text(f'Iteration {iteration_index}' if iteration_index > 0 else 'Initial policy')
  iteration_rect = iteration_surface.get_rect(midtop=(SCREEN_WIDTH/2, 20))
  screen.blit(iteration_surface, iteration_rect)

  # display value and action when hover on an hexagon
  mouse_pos = pygame.mouse.get_pos()
  hovered_hex = next((hex for hex in hexagons if hex.collide_with_point(mouse_pos)), None)
  if hovered_hex:
    hovered_hex.render_highlight(screen, (0, 0, 0))
    action_surface = create_text(f'Action: {ACTIONS[hovered_hex.action]}')
    reward_surface = create_text(f'Expected reward: {hovered_hex.value}' if iteration_index > 0 
                                 else f'Reward: {hovered_hex.value if not np.isnan(hovered_hex.value) else 0}')
    action_rect = action_surface.get_rect(midtop=(SCREEN_WIDTH/2, iteration_rect.bottom + 8))
    screen.blit(action_surface, action_rect)
    screen.blit(reward_surface, reward_surface.get_rect(midtop=(SCREEN_WIDTH/2, action_rect.bottom + 5)))

def update_hex(hex: HexagonTile, value, action, colour):
  hex.update()
  hex.value = value
  hex.action = action
  hex.colour, hex.border_colour = colour

hexes = [
  (0,0),(1,0),(2,0),(3,0),(0,1),(1,1),(2,1),(-1,2),
  (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),
  (8,2),(4,1),(5,0),(6,0),(7,0),(7,1),(8,1),(9,0)
]

special_hex_rewards = {
  (0,1): 5.0,    # left side reward
  (2,0): -10.0,  # left side hazard
  (9,0): 10.0    # right side reward
}

HexWorld = HexWorldMDP(
    hexes=hexes,
    r_bump_border=-1.0,  # Reward for falling off hex map
    p_intended=0.7,      # Probability of going in intended direction (same for each state)
    special_hex_rewards=special_hex_rewards,
    gamma=0.9          # Discount factor
)

initial_policy = HexWorld.random_policy()
policy_iteration = PolicyIteration(initial_policy, 50)
optimal_policy = policy_iteration.solve(HexWorld)
policies = [[initial_policy(s) for s in HexWorld.S], *policy_iteration.policies]
value_functions = [
  np.array([special_hex_rewards[s] if s in special_hex_rewards else np.nan for s in hexes]),
  *policy_iteration.value_functions
]
hex_colors = [value_to_color(U) for U in value_functions]
iteration_index = 0
total_iterations = len(value_functions) - 1
active = True

pygame.init()
pygame.display.set_caption('Minh hoạ thuật toán ra quyết định Chương 7')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
hexagons = init_hexagons(hexes)
color_bar = ColorBar(screen)

def next_iteration():
  global iteration_index
  iteration_index += 1
def prev_iteration():
  global iteration_index
  iteration_index -= 1
prev_btn = Button(pos=(10, SCREEN_HEIGHT-60), size=(60,30), text='prev', elevation=4, callback=prev_iteration, key=pygame.K_LEFT)
next_btn = Button(pos=(150, SCREEN_HEIGHT-60), size=(60,30), text='next', elevation=4, callback=next_iteration, key=pygame.K_RIGHT)

while True:
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit()
      exit()
  if iteration_index == total_iterations: next_btn.enable = False
  else: next_btn.enable = True
  if iteration_index == 0: prev_btn.enable = False
  else: prev_btn.enable = True
  
  screen.fill((52, 49, 49))
  for i in range(len(hexagons)):
    update_hex(hexagons[i], 
              value=value_functions[iteration_index][i], 
              action=policies[iteration_index][i], 
              colour=hex_colors[iteration_index][i])
  
  render(screen, hexagons)
  color_bar.update(vmin=np.nanmin(value_functions[iteration_index]), vmax=np.nanmax(value_functions[iteration_index]))
  prev_btn.render(screen)
  itr_text = create_text(f'{iteration_index} / {total_iterations}', font='freesansbold.ttf', size=20)
  itr_text_rect = itr_text.get_rect(center=((prev_btn.bottom_rect.right+next_btn.bottom_rect.left)/2, prev_btn.bottom_rect.centery))
  screen.blit(itr_text, itr_text_rect)
  next_btn.render(screen)
  
  clock.tick(50)
  pygame.display.flip()
  
    