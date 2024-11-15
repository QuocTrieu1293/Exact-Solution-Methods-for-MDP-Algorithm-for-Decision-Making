import matplotlib as mpl
import math

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 500
HEX_RADIUS = 40
MIN_HEX_RADIUS = HEX_RADIUS * math.cos(math.radians(30))
CMAP = mpl.colormaps.get_cmap('RdBu')
ACTIONS = ['East →', 'Northeast ↗', 'Northwest ↖', 'West ←', 'Southwest ↙', 'Southeast ↘']