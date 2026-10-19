# Color palettes of the new UI.
# The nine palettes with a light variant (Ayu ... Tokyo-Night) use the colors of the built-in palettes of
# Noctalia (https://github.com/noctalia-dev/noctalia, MIT). The other ones are dark only.
# "default" (Claude-like) lives in style_new.css, so it has no color data here, only the preview colors.
import base64

PALETTES = {
    "default": {"name": "Default", "dots": ["#d97757", "#788c5d", "#6a9bcc", "#c6613f"], "dark": None, "light": None, "preview": ("#262624", "#43423e", "#faf9f5", "#e3e0d3")},
    "ayu": {"name": "Ayu", "dots": ['#E6B450', '#AAD94C', '#39BAE6', '#D95757'],
        "dark": dict(bg="#0B0E14", card="#1e222a", input="#151920", border="#565B66", text="#D1D1C7", muted="#8E959E", accent="#E6B450", accent2="#AAD94C", onaccent="#0B0E14"),
        "light": dict(bg="#F8F9FA", card="#E4E6E9", input="#edeff1", border="#8A9199", text="#42474C", muted="#6E757C", accent="#FF8F40", accent2="#86B300", onaccent="#F8F9FA")},
    "catppuccin": {"name": "Catppuccin", "dots": ['#cba6f7', '#fab387', '#94e2d5', '#f38ba8'],
        "dark": dict(bg="#1e1e2e", card="#313244", input="#28293a", border="#4c4f69", text="#cdd6f4", muted="#a3b4eb", accent="#cba6f7", accent2="#fab387", onaccent="#11111b"),
        "light": dict(bg="#eff1f5", card="#ccd0da", input="#dcdfe6", border="#a5adcb", text="#4c4f69", muted="#6c6f85", accent="#8839ef", accent2="#fe640b", onaccent="#eff1f5")},
    "dracula": {"name": "Dracula", "dots": ['#bd93f9', '#ff79c6', '#8be9fd', '#FF5555'],
        "dark": dict(bg="#282A36", card="#44475A", input="#373a4a", border="#5a5e77", text="#F8F8F2", muted="#d6d8e0", accent="#bd93f9", accent2="#ff79c6", onaccent="#282A36"),
        "light": dict(bg="#f8f8f2", card="#e6e6ea", input="#eeeeee", border="#cacad3", text="#282a36", muted="#44475a", accent="#8332f4", accent2="#ff1399", onaccent="#ffffff")},
    "eldritch": {"name": "Eldritch", "dots": ['#37f499', '#04d1f9', '#a48cf2', '#f16c75'],
        "dark": dict(bg="#212337", card="#292e42", input="#25293d", border="#3b4261", text="#ebfafa", muted="#ABB4DA", accent="#37f499", accent2="#04d1f9", onaccent="#171928"),
        "light": dict(bg="#f0f3f4", card="#d5d9db", input="#e1e5e6", border="#c9cbcd", text="#1e2029", muted="#1e2029", accent="#fb5bb6", accent2="#0ad6ff", onaccent="#1e2029")},
    "everforest": {"name": "Everforest", "dots": ['#a7c080', '#83c092', '#dbbc7f', '#e67e80'],
        "dark": dict(bg="#2d353b", card="#343f44", input="#232a2e", border="#475258", text="#d3c6aa", muted="#9da9a0", accent="#a7c080", accent2="#a7c080", onaccent="#2d353b"),
        "light": None},
    "github": {"name": "GitHub Dark", "dots": ["#58a6ff", "#3fb950", "#ab7df8", "#f85149"],
        "dark": dict(bg="#0d1117", card="#151b23", input="#010409", border="#3d444d", text="#f0f6fc", muted="#9198a1", accent="#58a6ff", accent2="#58a6ff", onaccent="#0d1117"),
        "light": None},
    "gruvbox": {"name": "Gruvbox", "dots": ['#b8bb26', '#fabd2F', '#83a598', '#fb4934'],
        "dark": dict(bg="#282828", card="#3c3836", input="#333130", border="#57514e", text="#fbf1c7", muted="#ebdbb2", accent="#b8bb26", accent2="#fabd2F", onaccent="#282828"),
        "light": dict(bg="#fbf1c7", card="#ebdbb2", input="#f2e5bb", border="#bdae93", text="#3c3836", muted="#7c6f64", accent="#98971a", accent2="#d79921", onaccent="#fbf1c7")},
    "kanagawa": {"name": "Kanagawa", "dots": ['#76946a', '#c0a36e', '#7e9cd8', '#c34043'],
        "dark": dict(bg="#1f1f28", card="#2a2a37", input="#252530", border="#363646", text="#c8c093", muted="#717c7c", accent="#76946a", accent2="#c0a36e", onaccent="#1f1f28"),
        "light": dict(bg="#f2ecbc", card="#e5ddb0", input="#ebe4b5", border="#cfc49c", text="#545464", muted="#8a8980", accent="#6f894e", accent2="#77713F", onaccent="#f2ecbc")},
    "material": {"name": "Material Dark", "dots": ['#80cbc4', '#c3e88d', '#82aaff', '#f07178'],
        "dark": dict(bg="#212121", card="#2a2a2a", input="#1a1a1a", border="#343434", text="#eeffff", muted="#8f93a2", accent="#80cbc4", accent2="#80cbc4", onaccent="#212121"),
        "light": None},
    "monokai": {"name": "Monokai", "dots": ['#f92672', '#a6e22e', '#66d9ef', '#e6db74'],
        "dark": dict(bg="#272822", card="#31322b", input="#1e1f1c", border="#49483e", text="#f8f8f2", muted="#8f908a", accent="#f92672", accent2="#f92672", onaccent="#272822"),
        "light": None},
    "monokai-pro": {"name": "Monokai Pro", "dots": ['#ff6188', '#a9dc76', '#78dce8', '#ffd866'],
        "dark": dict(bg="#2d2a2e", card="#363337", input="#221f22", border="#5b595c", text="#fcfcfa", muted="#939293", accent="#ff6188", accent2="#ff6188", onaccent="#2d2a2e"),
        "light": None},
    "nord": {"name": "Nord", "dots": ['#8fbcbb', '#88c0d0', '#5e81ac', '#bf616a'],
        "dark": dict(bg="#2e3440", card="#3b4252", input="#353c4a", border="#505a70", text="#eceff4", muted="#d8dee9", accent="#8fbcbb", accent2="#88c0d0", onaccent="#2e3440"),
        "light": dict(bg="#eceff4", card="#e5e9f0", input="#e8ecf2", border="#c5cedd", text="#2e3440", muted="#4c566a", accent="#5e81ac", accent2="#64adc2", onaccent="#eceff4")},
    "onedark": {"name": "One Dark", "dots": ['#61afef', '#98c379', '#c678dd', '#e06c75'],
        "dark": dict(bg="#282c34", card="#2c323c", input="#21252b", border="#3e4452", text="#abb2bf", muted="#7f848e", accent="#61afef", accent2="#61afef", onaccent="#282c34"),
        "light": None},
    "palenight": {"name": "Palenight", "dots": ["#c792ea", "#c3e88d", "#82b1ff", "#ff5370"],
        "dark": dict(bg="#292d3e", card="#32364a", input="#232635", border="#444267", text="#a6accd", muted="#7f85a8", accent="#c792ea", accent2="#c792ea", onaccent="#292d3e"),
        "light": None},
    "rosepine": {"name": "Rosé Pine", "dots": ['#ebbcba', '#9ccfd8', '#31748F', '#eb6f92'],
        "dark": dict(bg="#191724", card="#26233a", input="#201e30", border="#403d52", text="#e0def4", muted="#908caa", accent="#ebbcba", accent2="#9ccfd8", onaccent="#191724"),
        "light": dict(bg="#fffaf3", card="#f2e9e1", input="#f8f1e9", border="#dfdad9", text="#575279", muted="#797593", accent="#d7827e", accent2="#56949F", onaccent="#faf4ed")},
    "rosepine-moon": {"name": "Rosé Pine Moon", "dots": ['#c4a7e7', '#9ccfd8', '#ea9a97', '#eb6f92'],
        "dark": dict(bg="#232136", card="#2a273f", input="#393552", border="#44415a", text="#e0def4", muted="#908caa", accent="#c4a7e7", accent2="#c4a7e7", onaccent="#232136"),
        "light": None},
    "solarized": {"name": "Solarized Dark", "dots": ['#268bd2', '#859900', '#b58900', '#dc322f'],
        "dark": dict(bg="#002b36", card="#073642", input="#00212b", border="#1c4a57", text="#93a1a1", muted="#839496", accent="#268bd2", accent2="#268bd2", onaccent="#002b36"),
        "light": None},
    "tokyonight": {"name": "Tokyo-Night", "dots": ['#7aa2f7', '#bb9af7', '#9ece6a', '#f7768e'],
        "dark": dict(bg="#1a1b26", card="#24283b", input="#202232", border="#353D57", text="#c0caf5", muted="#9aa5ce", accent="#7aa2f7", accent2="#bb9af7", onaccent="#16161e"),
        "light": dict(bg="#e1e2e7", card="#d0d5e3", input="#d8dbe5", border="#b4b5b9", text="#3760bf", muted="#6172b0", accent="#2e7de9", accent2="#9854f1", onaccent="#e1e2e7")},
}

def has_light(key):
    p = PALETTES[key]
    return p["dark"] is None or p["light"] is not None

def _variant(key, theme):
    p = PALETTES[key]
    return p["light"] if theme == "light" and p["light"] else p["dark"]

def palette_css(key, theme="dark"):
    c = _variant(key, theme)
    if not c:
        return ""
    # :root:root beats the specificity of ':root:has(.theme-light)' in style.css
    return (f"<style>:root:root {{ --bg:{c['bg']}; --bg-elev:{c['card']}; --bg-input:{c['input']}; --border:{c['border']}; "
            f"--text:{c['text']}; --text-muted:{c['muted']}; --accent:{c['accent']}; --accent-2:{c['accent2']}; "
            f"--accent-contrast:{c['onaccent']}; --shadow:0 2px 14px rgba(0,0,0,.30); }}</style>")

def _swatch_uri(key, theme):
    """Flat capsule with four discs (like the palette picker of Noctalia), as an SVG data URI."""
    p = PALETTES[key]
    c = _variant(key, theme)
    if c:
        surface, outline = c["bg"], c["border"]
    else:
        surface, outline = (p["preview"][0], p["preview"][1]) if theme != "light" else (p["preview"][2], p["preview"][3])
    discs = "".join(f'<circle cx="{11 + i * 19}" cy="11" r="7" fill="{col}"/>' for i, col in enumerate(p["dots"]))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="86" height="22" viewBox="0 0 86 22">'
           f'<rect x=".75" y=".75" width="84.5" height="20.5" rx="10.25" fill="{surface}" stroke="{outline}" stroke-width="1.5"/>{discs}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

def swatch_css(current, theme="dark"):
    """Background image of every picker button (.st-key-pal_<key>) and of the picker trigger (.st-key-palpop)."""
    rules = [f'.st-key-pal_{k} button[kind] {{ background-image: url("{_swatch_uri(k, theme)}") !important; }}' for k in PALETTES]
    rules.append(f'.st-key-palpop button {{ background-image: url("{_swatch_uri(current, theme)}") !important; }}')
    return "<style>" + "\n".join(rules) + "</style>"
