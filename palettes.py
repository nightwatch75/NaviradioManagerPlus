# Color palettes for the new UI (dark only). Values: bg, card, input, border, text, muted, accent, dot emoji.
# "default" is the Claude-like palette in style_new.css (it also has the light variant).
PALETTES = {
    "default":         ("Default",           None, "🟠"),
    "catppuccin":      ("Catppuccin Mocha",  ("#1e1e2e", "#2a2b3c", "#181825", "#45475a", "#cdd6f4", "#a6adc8", "#cba6f7"), "🟣"),
    "dracula":         ("Dracula",           ("#282a36", "#343746", "#21222c", "#44475a", "#f8f8f2", "#8b93b8", "#bd93f9"), "🟣"),
    "rosepine":        ("Rosé Pine",         ("#191724", "#1f1d2e", "#26233a", "#403d52", "#e0def4", "#908caa", "#c4a7e7"), "🟣"),
    "rosepine-moon":   ("Rosé Pine Moon",    ("#232136", "#2a273f", "#393552", "#44415a", "#e0def4", "#908caa", "#c4a7e7"), "🟣"),
    "tokyonight":      ("Tokyo Night",       ("#1a1b26", "#24283b", "#16161e", "#3b4261", "#c0caf5", "#787c99", "#7aa2f7"), "🔵"),
    "nord":            ("Nord",              ("#2e3440", "#3b4252", "#2b303b", "#4c566a", "#eceff4", "#9aa5b8", "#88c0d0"), "🔵"),
    "onedark":         ("One Dark",          ("#282c34", "#2f343e", "#21252b", "#3e4451", "#abb2bf", "#7f848e", "#61afef"), "🔵"),
    "gruvbox":         ("Gruvbox Dark",      ("#282828", "#32302f", "#1d2021", "#504945", "#ebdbb2", "#a89984", "#b8bb26"), "🟡"),
    "solarized":       ("Solarized Dark",    ("#002b36", "#073642", "#00212b", "#1c4a57", "#93a1a1", "#7f9296", "#268bd2"), "🔵"),
    "everforest":      ("Everforest",        ("#2d353b", "#343f44", "#232a2e", "#475258", "#d3c6aa", "#9da9a0", "#a7c080"), "🟢"),
    "kanagawa":        ("Kanagawa",          ("#1f1f28", "#2a2a37", "#16161d", "#363646", "#dcd7ba", "#8a8a9a", "#7e9cd8"), "🔵"),
    "monokai":         ("Monokai",           ("#272822", "#31322b", "#1e1f1c", "#49483e", "#f8f8f2", "#a6a68f", "#f92672"), "🔴"),
    "monokai-pro":     ("Monokai Pro",       ("#2d2a2e", "#363337", "#221f22", "#5b595c", "#fcfcfa", "#939293", "#ff6188"), "🔴"),
    "material":        ("Material Dark",     ("#212121", "#2a2a2a", "#1a1a1a", "#424242", "#eeffff", "#8f93a2", "#80cbc4"), "🟢"),
    "palenight":       ("Palenight",         ("#292d3e", "#32364a", "#232635", "#444267", "#a6accd", "#7f85a8", "#c792ea"), "🟣"),
    "github":          ("GitHub Dark",       ("#0d1117", "#161b22", "#010409", "#30363d", "#e6edf3", "#8b949e", "#58a6ff"), "🔵"),
}

def palette_css(key):
    c = PALETTES[key][1]
    if not c:
        return ""
    bg, card, inp, border, text, muted, accent = c
    # :root:root beats the specificity of ':root:has(.theme-light)' in style.css
    return (f"<style>:root:root {{ --bg:{bg}; --bg-elev:{card}; --bg-input:{inp}; --border:{border}; --text:{text}; "
            f"--text-muted:{muted}; --accent:{accent}; --accent-2:{accent}; --accent-contrast:{bg}; "
            f"--shadow:0 2px 14px rgba(0,0,0,.35); }}</style>")
