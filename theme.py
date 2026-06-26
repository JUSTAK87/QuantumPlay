"""
QuantumPlay — Thème visuel
Correspond exactement aux variables CSS :root du fichier HTML original
"""

# Couleurs principales (hex sans #)
THEME = {
    # Fonds
    'bg_deep':    '#03050f',
    'bg_surface': '#070d1a',
    'bg_panel':   '#0c1425',
    'bg_card':    '#101d30',
    'bg_hover':   '#162338',

    # Accents
    'accent_cyan':   '#00e5ff',
    'accent_violet': '#7b2fff',
    'accent_pink':   '#ff2d78',
    'accent_green':  '#00ff9d',
    'accent_amber':  '#ffb800',

    # Textes
    'text_primary':   '#e8f4ff',
    'text_secondary': '#7aa5cc',
    'text_muted':     '#3a5a7a',

    # Bordures
    'border':        '#00e5ff1e',   # rgba(0,229,255,0.12)
    'border_bright': '#00e5ff59',   # rgba(0,229,255,0.35)
}

# Raccourcis Kivy rgba (r,g,b,a) 0..1
def hex_to_kivy(hex_color: str, alpha: float = 1.0):
    h = hex_color.lstrip('#')
    r = int(h[0:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    return (r, g, b, alpha)


C = {k: hex_to_kivy(v) for k, v in THEME.items()
     if v.startswith('#') and len(v.lstrip('#')) == 6}

# Couleurs spéciales avec alpha
C['border']        = hex_to_kivy('#00e5ff', 0.12)
C['border_bright'] = hex_to_kivy('#00e5ff', 0.35)
C['bg_deep']       = hex_to_kivy('#03050f', 1.0)
C['bg_surface']    = hex_to_kivy('#070d1a', 1.0)
C['bg_panel']      = hex_to_kivy('#0c1425', 1.0)
C['bg_card']       = hex_to_kivy('#101d30', 1.0)
C['bg_hover']      = hex_to_kivy('#162338', 1.0)
C['accent_cyan']   = hex_to_kivy('#00e5ff', 1.0)
C['accent_violet'] = hex_to_kivy('#7b2fff', 1.0)
C['accent_pink']   = hex_to_kivy('#ff2d78', 1.0)
C['accent_green']  = hex_to_kivy('#00ff9d', 1.0)
C['accent_amber']  = hex_to_kivy('#ffb800', 1.0)
C['text_primary']  = hex_to_kivy('#e8f4ff', 1.0)
C['text_secondary']= hex_to_kivy('#7aa5cc', 1.0)
C['text_muted']    = hex_to_kivy('#3a5a7a', 1.0)

# Tailles
SIZES = {
    'sidebar_w':  220,
    'right_panel_w': 260,
    'topbar_h':   48,
    'player_h':   130,
    'radius':     6,
    'radius_lg':  12,
}

# Polices (Kivy utilise les polices système ou les fichiers .ttf)
FONTS = {
    'main': 'Roboto',   # police par défaut Kivy
    'mono': 'RobotoMono',
}

# Presets EQ
EQ_PRESETS = {
    'flat':   [0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    'bass':   [8,  7,  5,  3,  1,  0,  0, -1, -1, -2],
    'club':   [0,  0,  4,  5,  4,  3,  3,  2,  0,  0],
    'vocal':  [-2,-2,  0,  3,  5,  5,  3,  1, -1, -2],
    'cinema': [5,  4,  3,  2,  0, -1, -1,  2,  3,  4],
    'gaming': [4,  3,  2,  0,  0,  1,  2,  3,  4,  5],
    'studio': [0,  0,  0,  1,  2,  2,  1,  0,  0,  0],
    'live':   [3,  2,  0,  0,  1,  2,  3,  3,  2,  1],
}

EQ_FREQS_10 = [32, 64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
EQ_FREQS_20 = [
    20, 32, 40, 63, 80, 125, 160, 250, 315, 500,
    630, 1000, 1250, 2000, 2500, 4000, 5000, 8000, 10000, 16000
]