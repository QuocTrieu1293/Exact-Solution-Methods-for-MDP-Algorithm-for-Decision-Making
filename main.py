import numpy as np
from typing import List, Tuple
import math
import pygame
from hexagon import HexagonTile
from HexWorldMDP import HexWorldMDP
from ch07 import PolicyIteration, ValueIteration
from elements import ColorBar, Button, ToggleButton, Dropdown
from config import *
from sys import exit

def create_hexagon(position) -> HexagonTile:
  """Creates a hexagon tile at the specified position"""
  return HexagonTile(HEX_RADIUS, position, colour=(255, 253, 246), border_colour=(55, 175, 225))

def create_text(text, font='assets/FiraCode-Medium.ttf', size=24, color=(255, 253, 246)) -> pygame.Surface:
  text_font = pygame.font.Font(font,size)
  return text_font.render(text, True, color=color)

def value_to_color(U) -> List[Tuple[List, List]]:
  min_val, max_val = np.nanmin(U), np.nanmax(U)
  
  if min_val == max_val:
    return [([int(c * 255) for c in CMAP(0.5)[:3]], [int(c * 255) for c in CMAP(1.0)[:3]])] * len(U)
  
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
  iteration_surface = create_text('Initial policy' if iteration_index == 0 and modes_dropdown.value == POLICY_ITERATION
                                  else f'Iteration {iteration_index}')
  iteration_rect = iteration_surface.get_rect(midtop=(SCREEN_WIDTH/2, 20))
  screen.blit(iteration_surface, iteration_rect)
  
  # display value and action when hover on an hexagon
  mouse_pos = pygame.mouse.get_pos()
  hovered_hex = next((hex for hex in hexagons if hex.collide_with_point(mouse_pos)), None)
  
  def displayActionReward(hex: HexagonTile):
    action_surface = create_text(f'Action: {ACTIONS[hex.action]}')
    reward_surface = create_text(f'Expected reward: {hex.value}' if iteration_index > 0 
                                 else f'Reward: {hex.value if not np.isnan(hex.value) else 0}')
    action_rect = action_surface.get_rect(midtop=(SCREEN_WIDTH/2, iteration_rect.bottom + 8))
    screen.blit(action_surface, action_rect)
    screen.blit(reward_surface, reward_surface.get_rect(midtop=(SCREEN_WIDTH/2, action_rect.bottom + 5)))
  
  if hovered_hex:
    hovered_hex.render_highlight(screen, (0, 0, 0))
    displayActionReward(hovered_hex)
  elif clicked_hex:
    displayActionReward(clicked_hex)
    
  if clicked_hex:
    clicked_hex.render_clicked_border(screen)
  
  # display params of HexWorld
  line_space, text_size = 0, 16
  
  reward_border_surf = create_text(f'Reward for bumping border: {r_bump_border}', size=text_size)
  reward_border_rect = reward_border_surf.get_rect(topleft=(8, 8))
  
  p_intended_surf = create_text(f'Prob of intended move: {p_intended}', size=text_size)
  p_intended_rect = p_intended_surf.get_rect(topleft=(8, reward_border_rect.bottom + line_space))
  
  gamma_surf = create_text(f'γ: {gamma}', size=text_size)
  gamma_rect = gamma_surf.get_rect(topleft=(8, p_intended_rect.bottom + line_space))
  
  param_box_surf = pygame.Surface(
    (max(reward_border_rect.width, p_intended_rect.width, gamma_rect.width) + 16,
      reward_border_rect.height + p_intended_rect.height + gamma_rect.height + 2*line_space + 21),
    pygame.SRCALPHA
  )
  param_box_surf.fill((0, 0, 0, 120))
  
  param_box_surf.blits([
    (reward_border_surf, reward_border_rect),
    (p_intended_surf, p_intended_rect),
    (gamma_surf, gamma_rect)
  ])
  screen.blit(param_box_surf, (SCREEN_WIDTH - param_box_surf.width, 0))

def update_hex(hex: HexagonTile, value, action, colour):
  hex.update()
  hex.value = value
  hex.action = action
  hex.colour, hex.border_colour = colour
  global clicked_hex
  if hex.check_clicked():
    clicked_hex = hex if hex is not clicked_hex else None

def run_policy_iteration():
  global policies, value_functions, hex_colors, iteration_index, total_iterations, optimal_policy
  initial_policy = HexWorld.random_policy()
  policy_iteration = PolicyIteration(initial_policy, k_max=50)
  optimal_policy = policy_iteration.solve(HexWorld)
  policies = [[initial_policy(s) for s in HexWorld.S], *policy_iteration.policies]
  value_functions = [
    np.array([special_hex_rewards[s] if s in special_hex_rewards else np.nan for s in hexes]),
    *policy_iteration.value_functions
  ]
  hex_colors = [value_to_color(U) for U in value_functions]
  iteration_index = 0
  total_iterations = len(value_functions) - 1

def run_value_iteration():
  global policies, value_functions, hex_colors, iteration_index, total_iterations, optimal_policy
  value_iteration = ValueIteration(k_max=50, delta=1e-4)
  optimal_policy = value_iteration.solve(HexWorld)
  policies = value_iteration.policies
  value_functions = value_iteration.value_functions
  hex_colors = [value_to_color(U) for U in value_functions]
  iteration_index = 0
  total_iterations = len(value_functions) - 1

def run_simulate():
  print('simulate')

# input data
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
r_bump_border, p_intended, gamma = -1.0, 0.7, 0.9 
HexWorld = HexWorldMDP(
    hexes=hexes,
    r_bump_border=r_bump_border,  # Reward for falling off hex map
    p_intended=p_intended,      # Probability of going in intended direction (same for each state)
    special_hex_rewards=special_hex_rewards,
    gamma=gamma          # Discount factor
)

pygame.init()
pygame.display.set_caption('Minh hoạ thuật toán ra quyết định Chương 7')
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
hexagons = init_hexagons(hexes)
clicked_hex = None
color_bar = ColorBar(screen)

# control button
def next_iteration():
  global iteration_index
  iteration_index += 1
def prev_iteration():
  global iteration_index
  iteration_index -= 1
def restart_algo():
  if modes_dropdown.value == POLICY_ITERATION:
    run_policy_iteration()
  elif modes_dropdown.value == VALUE_ITERATION:
    run_value_iteration()
  elif modes_dropdown.value == SIMULATE:
    run_simulate()
prev_btn = Button(pos=(10, SCREEN_HEIGHT-60), size=(60,30), content='prev', elevation=4, callback=prev_iteration, key=pygame.K_LEFT)
next_btn = Button(pos=(prev_btn.bottom_rect.right + 76, SCREEN_HEIGHT-60), size=(60,30), 
                  content='next', elevation=4, callback=next_iteration, key=pygame.K_RIGHT)
restart_btn = Button(pos=(next_btn.bottom_rect.right + 15, SCREEN_HEIGHT-60), size=(40,30), 
                     content=pygame.transform.scale(pygame.image.load('assets/restart_icon.svg').convert_alpha(), (20, 20)) , 
                     elevation=4, callback=restart_algo, key=pygame.K_r)
auto_btn = ToggleButton(pos=(restart_btn.bottom_rect.right + 15, SCREEN_HEIGHT-60), size=(80,30), 
                  content='auto run', elevation=4, key=pygame.K_a)
AUTO_RUN_EVENT = pygame.USEREVENT  + 1
auto_running = False

POLICY_ITERATION, VALUE_ITERATION, SIMULATE = 'Policy Iteration', 'Value Iteration', 'Simulate'
MODES = [POLICY_ITERATION, VALUE_ITERATION, SIMULATE]
modes_dropdown = Dropdown(pos=(30,20), border_color=(250, 177, 47), options=MODES,
                          callbacks=[run_policy_iteration, run_value_iteration, run_simulate])

run_policy_iteration()

# game loop
while True:
  # handle events
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit()
      exit()
    elif event.type in [pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
      # mouse_pos = pygame.mouse.get_pos()
      # mouse_pressed = pygame.mouse.get_pressed()
      # if event.type == pygame.MOUSEBUTTONDOWN: print('mouse down')
      # elif event.type == pygame.MOUSEBUTTONUP: print('mouse up')
      prev_btn.handle_event(event)
      next_btn.handle_event(event)
      restart_btn.handle_event(event)
      auto_btn.handle_event(event)
      modes_dropdown.handle_event(event)
    elif event.type == AUTO_RUN_EVENT:
      iteration_index += 1
      if iteration_index == total_iterations:
        auto_btn.active = False
        
  if iteration_index == total_iterations: next_btn.enable = False
  elif not auto_running: next_btn.enable = True
  
  if iteration_index == 0: prev_btn.enable = False
  elif not auto_running: prev_btn.enable = True
  
  if auto_btn.active and not auto_running:
    auto_running = True
    iteration_index = 0
    prev_btn.enable, next_btn.enable, restart_btn.enable = False, False, False
    pygame.time.set_timer(AUTO_RUN_EVENT, 1300)
  elif not auto_btn.active and auto_running:
    auto_running = False
    if iteration_index != 0: prev_btn.enable = True
    if iteration_index != total_iterations: next_btn.enable = True
    restart_btn.enable = True
    pygame.time.set_timer(AUTO_RUN_EVENT, 0)
    
  # render on screen 
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
  restart_btn.render(screen)
  auto_btn.render(screen)
  modes_dropdown.render(screen)
  
  clock.tick(50)
  pygame.display.flip()