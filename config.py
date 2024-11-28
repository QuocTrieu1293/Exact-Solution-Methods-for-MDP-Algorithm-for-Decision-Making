import matplotlib as mpl
import math

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 563
HEX_RADIUS = 40
MIN_HEX_RADIUS = HEX_RADIUS * math.cos(math.radians(30))
HEX_BORDER_SIZE = 3
CMAP = mpl.colormaps.get_cmap('RdBu')
ACTIONS = ['East →', 'Northeast ↗', 'Northwest ↖', 'West ←', 'Southwest ↙', 'Southeast ↘']