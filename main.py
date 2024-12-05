import numpy as np
from typing import List, Tuple, Callable
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
  return HexagonTile(HEX_RADIUS, position, colour=(255, 253, 246), border_colour=(55, 175, 225), border_size=HEX_BORDER_SIZE)

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

def handleClickHex(event: pygame.Event):
  if event.type != pygame.MOUSEBUTTONDOWN:
    return
  global clicked_hex, start_s
  hex = next((hex for hex in hexagons if hex.collide_with_point(event.pos)), None)
  if modes_dropdown.value == SIMULATE and choose_state_btn.active and hex:
    start_s = hexagons.index(hex)
    run_simulate()
  elif modes_dropdown.value != SIMULATE:
    if hex is clicked_hex:
      clicked_hex = None
    elif hex:
      clicked_hex = hex
  
  # if hex:
  #   idx = hexagons.index(hex) 
  #   print(f'{hexes[idx]}: {idx}')

def render(screen: pygame.Surface, hexagons: List[HexagonTile]):
  """Renders hexagons on the screen"""
  for hexagon in hexagons:
    hexagon.render(screen)
  
  # display Title
  if modes_dropdown.value == POLICY_ITERATION:
    if iteration_index == 0: title_surf = create_text('Hex World problem')
    elif iteration_index == 1: title_surf = create_text('Initial policy')
    else: title_surf = create_text(f'Iteration {iteration_index-1}')
  elif modes_dropdown.value == VALUE_ITERATION:
    if iteration_index == 0: title_surf = create_text('Hex World problem')
    elif iteration_index == 1: title_surf = create_text('Initial value function')
    else: title_surf = create_text(f'Iteration {iteration_index-1}')
  elif modes_dropdown.value == SIMULATE:
    title_surf = create_text(f'Step {iteration_index}')
  
  title_rect = title_surf.get_rect(midtop=(SCREEN_WIDTH/2, 20))
  screen.blit(title_surf, title_rect)
  
  # display value and action when hover on an hexagon
  mouse_pos = pygame.mouse.get_pos()
  hovered_hex = next((hex for hex in hexagons if hex.collide_with_point(mouse_pos)), None)
  
  def displayActionReward(hex: HexagonTile = None):
    if not hex and modes_dropdown.value != SIMULATE: 
      return
    action_surface = create_text(f'Action: {ACTIONS[hex.action if modes_dropdown.value != SIMULATE else simulate_rs[iteration_index][1]]}')
    reward_surface = create_text(
      f'Reward: {hex.value if not np.isnan(hex.value) else 0}' if iteration_index == 1 and modes_dropdown.value == POLICY_ITERATION 
      else f'Cumulative reward: {cumulative_reward[iteration_index]}' if modes_dropdown.value == SIMULATE 
      else f'Expected reward: {hex.value}')
    action_rect = action_surface.get_rect(midtop=(SCREEN_WIDTH/2, title_rect.bottom + 8))
    screen.blit(action_surface, action_rect)
    screen.blit(reward_surface, reward_surface.get_rect(midtop=(SCREEN_WIDTH/2, action_rect.bottom + 5)))
  
  def displayReward(hex: HexagonTile = None):
    if not hex:
      return
    text_surfs, text_rects = [], []
    for i, r in enumerate(hex.rewards):
      text_surfs.append(create_text(f'{ACTIONS[i]}: {r}', size=18))
      text_rects.append(text_surfs[-1].get_rect(
        topleft=(0, text_rects[-1].bottom + 2 if i > 0 else 0)))
    surf = pygame.Surface((max([rect.width for rect in text_rects]), sum([rect.height for rect in text_rects]) + 5*2), pygame.SRCALPHA)
    surf.fill((0,0,0,0))
    surf.blits(zip(text_surfs, text_rects))
    screen.blit(surf, surf.get_rect(midtop=(SCREEN_WIDTH/2, title_rect.bottom + 8)))
  
  if iteration_index == 0 and modes_dropdown.value != SIMULATE:
    displayReward(hovered_hex or clicked_hex)
  else:
    displayActionReward(hovered_hex or clicked_hex)
  
  if hovered_hex:
    hovered_hex.render_highlight(screen, (0,0,0))
  if modes_dropdown.value != SIMULATE and clicked_hex:
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

def updateHexagons():
  if modes_dropdown.value == SIMULATE:
    cur_s = simulate_rs[iteration_index][0]
    if iteration_index < total_iterations - 1:
      next_s = simulate_rs[iteration_index+1][0]
      hexagons[next_s].border_colour = hex_colors[next_s][1]
      hexagons[next_s].border_size = HEX_BORDER_SIZE
      hexagons[next_s].move_dir = None
      if next_s == cur_s:
        a = simulate_rs[iteration_index][1]
        a_left = (a + 1) % len(HexWorld.A)
        a_right = (a - 1) % len(HexWorld.A)
        neighbor_left = HexWorldMDP.hex_neighbors(hexes[cur_s])[a_left]
        hexagons[cur_s].move_dir = a_left if neighbor_left not in hexes else a_right
        hexagons[cur_s].move_dir_color = (255, 30, 30)
      else:
        hexagons[cur_s].move_dir = HexWorldMDP.hex_neighbors(hexes[cur_s]).index(hexes[next_s])
        hexagons[cur_s].move_dir_color = (6, 208, 1) 
        
    hexagons[cur_s].border_colour = (6, 208, 1) # green
    hexagons[cur_s].border_size = 5
    if iteration_index > 0:
      pre_s = simulate_rs[iteration_index-1][0]
      if pre_s == cur_s:
        hexagons[cur_s].border_colour = (255, 30, 30) # red
      else:
        hexagons[pre_s].border_colour = (101, 69, 32) # brown
        hexagons[pre_s].move_dir = None
  elif modes_dropdown.value in [POLICY_ITERATION, VALUE_ITERATION]:
    for i, hex in enumerate(hexagons):
      hex.value = values[iteration_index][i]
      hex.colour, hex.border_colour = hex_colors[iteration_index][i]
      hex.action = actions[iteration_index][i]

def run_policy_iteration():
  reset_btn()
  
  global optimal_policy, values, actions, hex_colors, iteration_index, total_iterations
  initial_policy = HexWorld.random_policy() # Callable[[int], int]
  policy_iteration = PolicyIteration(initial_policy, k_max=50)
  optimal_policy = policy_iteration.solve(HexWorld)
  actions = [[None] * len(HexWorld.S), [initial_policy(s) for s in HexWorld.S], *policy_iteration.policies]
  values = [
    np.array([special_hex_rewards[s] if s in special_hex_rewards else np.nan for s in hexes]),
    np.array([special_hex_rewards[s] if s in special_hex_rewards else np.nan for s in hexes]),
    *policy_iteration.value_functions
  ]
  hex_colors = [value_to_color(U) for U in values]
  iteration_index = 0
  total_iterations = len(values)
  
  updateHexagons()

def run_value_iteration():
  reset_btn()
  
  global optimal_policy, values, actions, hex_colors, iteration_index, total_iterations
  value_iteration = ValueIteration(k_max=50, delta=1e-4)
  optimal_policy = value_iteration.solve(HexWorld)
  actions = [[None] * len(HexWorld.S), *value_iteration.policies]
  values = [
    np.array([special_hex_rewards[s] if s in special_hex_rewards else np.nan for s in hexes]), 
    *value_iteration.value_functions
  ]
  hex_colors = [value_to_color(U) for U in values]
  iteration_index = 0
  total_iterations = len(values)
  
  updateHexagons()

def run_simulate():
  reset_btn()
  
  global values, actions, hex_colors, iteration_index, total_iterations, start_s, simulate_rs, clicked_hex, cumulative_reward
  actions = [optimal_policy(s) for s in HexWorld.S]
  values = np.array([special_hex_rewards[s] if s in special_hex_rewards else np.nan for s in hexes])
  hex_colors = value_to_color(values)
  
  for i, hex in enumerate(hexagons):
    hex.action = actions[i]
    hex.value = values[i]
    hex.colour, hex.border_colour = hex_colors[i]
    hex.move_dir = None
  
  simulate_rs = HexWorld.simulate(s=start_s, policy=optimal_policy, d=50) # list of (s, a, r)
  iteration_index = 0
  total_iterations = len(simulate_rs)
  
  cumulative_reward = []
  r = 0
  for step in range(total_iterations):
    s = simulate_rs[step][0]
    next_s = simulate_rs[step+1][0] if step < total_iterations-1 else HexWorld.terminal_state
    
    reward = 0
    if next_s == s:
      reward = r_bump_border
    elif hexes[s] in special_hex_rewards:
      reward = special_hex_rewards[hexes[s]]
      
    r += (gamma**step) * reward
    cumulative_reward.append(r)
  
  updateHexagons()

# Init HexWorld problem
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
  updateHexagons()
def prev_iteration():
  global iteration_index
  iteration_index -= 1
  updateHexagons()
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

choose_state_btn = ToggleButton(pos=((SCREEN_WIDTH-230)/2, 150), size=(230, 40), content='choose starting state', 
                                elevation=4, text_size=18, active_color="#0079FF")

def reset_btn():
  auto_btn.active, choose_state_btn.active = False, False

# global variables
rewards: List[List[int]] = [[HexWorld.R(s,a) for a in HexWorld.A] for s in HexWorld.S] # R(s,a)
for i, hex in enumerate(hexagons): hex.rewards = [round(r,2) for r in rewards[i]]
optimal_policy: Callable[[int], int]
values: List[np.array] | np.array
actions: List[List[int]] | List[int]
hex_colors: List[Tuple] # (background color, border color)
iteration_index: int
total_iterations: int
start_s: int = 17
simulate_rs: List[Tuple[int, int, float]] # list of (s, a, r)
cumulative_reward: List[float]

run_policy_iteration()

# game loop
while True:
  # handle events
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit()
      exit()
    elif event.type in [pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
      prev_btn.handle_event(event)
      next_btn.handle_event(event)
      restart_btn.handle_event(event)
      auto_btn.handle_event(event)
      modes_dropdown.handle_event(event)
      if modes_dropdown.value != SIMULATE or choose_state_btn.active:
        handleClickHex(event)
      if modes_dropdown.value == SIMULATE:
        choose_state_btn.handle_event(event)
    elif event.type == AUTO_RUN_EVENT:
      next_iteration()
      if iteration_index == total_iterations - 1:
        auto_btn.active = False
  
  for hex in hexagons: hex.update()
  
  if iteration_index == 0: prev_btn.enable = False
  elif not (auto_running or choose_state_btn.active): prev_btn.enable = True
  
  if auto_btn.active and not auto_running:
    auto_running = True
    if modes_dropdown.value in [POLICY_ITERATION, VALUE_ITERATION]:
      iteration_index = 1
      updateHexagons()
    elif modes_dropdown.value == SIMULATE:
      while iteration_index > 0:
        prev_iteration()
    pygame.time.set_timer(AUTO_RUN_EVENT, 1200)
  elif not auto_btn.active and auto_running:
    auto_running = False
    pygame.time.set_timer(AUTO_RUN_EVENT, 0)
  
  # check buttons enable
  next_btn.enable = not (auto_running or choose_state_btn.active or iteration_index == total_iterations - 1)
  prev_btn.enable = not (auto_running or choose_state_btn.active or iteration_index == 0)
  restart_btn.enable = not (auto_running or choose_state_btn.active)
  auto_btn.enable = not choose_state_btn.active
  choose_state_btn.enable = not auto_running
  
  # render on screen 
  screen.fill((64, 62, 62))
  
  render(screen, hexagons)
  
  if (modes_dropdown.value != SIMULATE and 
      not (modes_dropdown.value == VALUE_ITERATION and iteration_index == 1)):
    color_bar.update(vmin=np.nanmin(values[iteration_index]), vmax=np.nanmax(values[iteration_index]))
  
  prev_btn.render(screen)
  itr_text = create_text(f'{iteration_index+1} / {total_iterations}', font='freesansbold.ttf', size=20)
  itr_text_rect = itr_text.get_rect(center=((prev_btn.bottom_rect.right+next_btn.bottom_rect.left)/2, prev_btn.bottom_rect.centery))
  screen.blit(itr_text, itr_text_rect)
  next_btn.render(screen)
  restart_btn.render(screen)
  auto_btn.render(screen)
  modes_dropdown.render(screen)
  
  if modes_dropdown.value == SIMULATE:
    choose_state_btn.render(screen)
  
  clock.tick(50)
  pygame.display.flip()