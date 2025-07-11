# Theme data for API-only mode
THEME_DATA = {
    "dark": {
        "name": "dark",
        "colors": {
            "primary": "#1a1a1a",
            "secondary": "#2d2d2d",
            "accent": "#4a9eff",
            "text": "#ffffff",
            "background": "#0f0f0f"
        }
    },
    "light": {
        "name": "light",
        "colors": {
            "primary": "#ffffff",
            "secondary": "#f5f5f5",
            "accent": "#0066cc",
            "text": "#333333",
            "background": "#ffffff"
        }
    },
    "royal_blue": {
        "name": "royal_blue",
        "colors": {
            "primary": "#1e3a8a",
            "secondary": "#3b82f6",
            "accent": "#60a5fa",
            "text": "#ffffff",
            "background": "#0f172a"
        }
    },
    "cream": {
        "name": "cream",
        "colors": {
            "primary": "#f5f5dc",
            "secondary": "#fffdd0",
            "accent": "#d4a574",
            "text": "#3d3d3d",
            "background": "#faf9f6"
        }
    },
    "light_red": {
        "name": "light_red",
        "colors": {
            "primary": "#ff6b6b",
            "secondary": "#ff8787",
            "accent": "#fa5252",
            "text": "#ffffff",
            "background": "#2d0a0a"
        }
    },
    "dark_pink": {
        "name": "dark_pink",
        "colors": {
            "primary": "#c2185b",
            "secondary": "#e91e63",
            "accent": "#f48fb1",
            "text": "#ffffff",
            "background": "#1a0a0f"
        }
    },
    "faint_yellow": {
        "name": "faint_yellow",
        "colors": {
            "primary": "#fff9c4",
            "secondary": "#fff59d",
            "accent": "#fdd835",
            "text": "#424242",
            "background": "#fffef7"
        }
    }
}

def get_theme_from_name(theme_name: str) -> dict:
    """Get theme data by name"""
    return THEME_DATA.get(theme_name, THEME_DATA["light"])