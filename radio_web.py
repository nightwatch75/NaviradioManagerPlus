####
import streamlit as st
import requests
import hashlib
import os
import time
import random
import re
from lang import TRANSLATIONS
from genres import GENRES
from urllib.parse import unquote
st.set_page_config(
    page_title="NaviRadioManager",
    page_icon="📻",
    layout="wide",
    initial_sidebar_state="auto"
)

# Theme lives in the URL (?theme=light|dark) so it survives a page reload
if 'theme' not in st.session_state:
    st.session_state.theme = "light" if st.query_params.get("theme") == "light" else "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    st.query_params["theme"] = st.session_state.theme

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")
st.markdown(f"<style>:root {{ color-scheme: {st.session_state.theme}; }}</style>"
            f"<div class='theme-marker theme-{st.session_state.theme}'></div>",
            unsafe_allow_html=True)

NAVIDROME_URL = os.getenv("NAVIDROME_URL", "")
USERNAME = os.getenv("NAVIDROME_USER", "")
PASSWORD = os.getenv("NAVIDROME_PASS", "")
SALT = os.getenv("NAVIDROME_SALT", "")
TOKEN = hashlib.md5((PASSWORD + SALT).encode("utf-8")).hexdigest()

LANG_CODE = os.getenv("APP_LANG", "IT").upper()
T = TRANSLATIONS.get(LANG_CODE, TRANSLATIONS["IT"])
VERSION = f"7.0.0-{LANG_CODE}"

FLAGS = {"IT": "🇮🇹", "US": "🇺🇸", "GB": "🇬🇧", "FR": "🇫🇷", "DE": "🇩🇪", "ES": "🇪🇸", "CH": "🇨🇭"}

# ========== NOW PLAYING (ICY in-stream metadata) ==========
# radio-browser stores no track info. The only portable source is the stream itself:
# Shoutcast/Icecast send "Icy-MetaData: 1" -> icy-* headers + a StreamTitle block every icy-metaint bytes.
# HLS streams and stations that do not send it are reported as "not available".
NP_POLL_SECONDS = 15
NP_HISTORY_MAX = 12

def _read_exact(raw, n):
    buf = b""
    while len(buf) < n:
        chunk = raw.read(n - len(buf))
        if not chunk:
            break
        buf += chunk
    return buf

def parse_stream_title(md):
    """StreamTitle text -> {'title', 'artist'}; handles 'Artist - Title' and 'Title~Artist~...' variants."""
    m = re.search(r"StreamTitle='(.*?)';?(?:\w+='|$)", md, re.S)
    text = (m.group(1) if m else "").strip()
    if "adw_ad='true'" in md and not text:
        return {"title": "", "artist": "", "ad": True}
    if "~" in text:
        parts = text.split("~")
        return {"title": parts[0].strip(), "artist": parts[1].strip() if len(parts) > 1 else ""}
    if " - " in text:
        artist, title = text.split(" - ", 1)
        return {"title": title.strip(), "artist": artist.strip()}
    return {"title": text, "artist": ""}

def get_now_playing(url):
    """Opens the stream, reads headers and one metadata block. Never cached: it must be live."""
    if not url.lower().startswith(("http://", "https://")) or ".m3u8" in url.lower():
        return {"error": "unsupported"}
    try:
        with requests.get(url, headers={"Icy-MetaData": "1", "User-Agent": RB_HEADERS["User-Agent"]},
                          stream=True, timeout=(5, 8)) as r:
            h = {k.lower(): v for k, v in r.headers.items()}
            out = {"headers": {k: h[k] for k in ("icy-name", "icy-genre", "icy-description", "icy-br", "icy-url") if h.get(k)},
                   "title": "", "artist": ""}
            metaint = int(h.get("icy-metaint") or 0)
            if not metaint:
                out["error"] = "no_metadata"
                return out
            _read_exact(r.raw, metaint)
            length = _read_exact(r.raw, 1)
            block = _read_exact(r.raw, length[0] * 16) if length else b""
            try:
                md = block.decode("utf-8").strip("\0")
            except UnicodeDecodeError:
                md = block.decode("latin-1").strip("\0")
            out.update(parse_stream_title(md))
            return out
    except Exception as e:
        return {"error": str(e)[:120]}

def md_escape(s):
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|<>~$&])", r"\\\1", s)

@st.fragment(run_every=NP_POLL_SECONDS)
def now_playing_panel(stream_url):
    """Live panel for the selected station: current track, stream info and what was heard since opening."""
    info = get_now_playing(stream_url)
    history = st.session_state.setdefault("np_history", {}).setdefault(stream_url, [])
    err = info.get("error")
    st.markdown(f"**🎵 {T['np_title']}**")
    if err and "headers" not in info:
        st.warning(T["np_unavailable"] if err == "unsupported" else f"{T['np_unavailable']} ({err})")
        return
    if err == "no_metadata":
        st.info(T["np_no_metadata"])
    elif info.get("ad"):
        st.info(T["np_ad"])
    elif info.get("title"):
        line = md_escape(info["title"]) + (f" — {md_escape(info['artist'])}" if info["artist"] else "")
        st.markdown(f"### {line}")
        entry = f"{info['artist']} — {info['title']}" if info["artist"] else info["title"]
        if not history or history[0][1] != entry:
            history.insert(0, (time.strftime("%H:%M:%S"), entry))
            del history[NP_HISTORY_MAX:]
    else:
        st.info(T["np_none"])
    labels = {"icy-name": T["np_station"], "icy-genre": T["np_genre"], "icy-description": T["np_desc"],
              "icy-br": "kbps", "icy-url": "Web"}
    st.caption(" · ".join(f"{labels[k]}: {md_escape(v)}" for k, v in info.get("headers", {}).items()))
    if history:
        st.markdown(f"**📜 {T['np_history']}**")
        st.text("\n".join(f"{t}  {e}" for t, e in history))
    st.caption(T["np_refresh_note"].format(s=NP_POLL_SECONDS))

def station_info(s):
    """Extra fields radio-browser already returns for a station (search result dict)."""
    trend = s.get("clicktrend") or 0
    arrow = "▲" if trend > 0 else "▼" if trend < 0 else "•"
    where = ", ".join(x for x in (s.get("state"), s.get("country")) if x)
    items = [
        (T["info_language"], (s.get("language") or "—").title()),
        (T["info_place"], where or "—"),
        (T["info_clicks"], f"{s.get('clickcount', 0)} {arrow}{abs(trend) if trend else ''}"),
        (T["info_checked"], (s.get("lastcheckoktime_iso8601") or "—")[:16].replace("T", " ")),
    ]
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.caption(label)
        col.markdown(f"**{md_escape(str(value))}**")
    flags = [f for f, on in (("HLS", s.get("hls")), ("SSL error", s.get("ssl_error"))) if on]
    tags = [t.strip() for t in (s.get("tags") or "").split(",") if t.strip()][:15]
    if tags or flags:
        st.caption(" ".join(f"`{t}`" for t in tags + flags))

def fix_url(url):
    if not url:
        return url
    if url.startswith("http:") and not url.startswith("http://"):
        return url.replace("http:", "http://", 1)
    if url.startswith("https:") and not url.startswith("https://"):
        return url.replace("https:", "https://", 1)
    return url

@st.cache_data
def get_world_countries():
    try:
        response = requests.get("https://flagcdn.com/en/codes.json")
        return response.json()
    except:
        return {}

WORLD_COUNTRIES = get_world_countries()

def get_flag_emoji(country_code):
    if not country_code or len(country_code) != 2:
        return "📻"
    return "".join(chr(127397 + ord(c.upper())) for c in country_code)

def find_flag_in_string(text):
    if not text: 
        return None
    text_lower = text.lower()
    common_variants = {
        "it": ["italia", "italian", "itally"],
        "gb": ["uk", "united kingdom", "british", "england"],
        "us": ["usa", "america", "united states"],
        "br": ["brazil", "brazilian", "brasil"],
        "jp": ["japan", "japanese", "nippon"],
        "ru": ["russia", "russian"],
        "ca": ["canada", "canadian"]
    }
    for code, keywords in common_variants.items():
        if any(k in text_lower for k in keywords):
            return get_flag_emoji(code)
    for code, country_name in WORLD_COUNTRIES.items():
        if len(country_name) > 3 and country_name.lower() in text_lower:
            return get_flag_emoji(code)
    return None

# ========== RADIO-BROWSER API (https://api.radio-browser.info/) ==========
# Docs: discover the server pool via all.api.radio-browser.info/json/servers,
# pick one at random, and always send a descriptive User-Agent.
RB_HEADERS = {"User-Agent": "NaviRadioManager/7.0"}

@st.cache_data(ttl=3600)
def rb_servers():
    try:
        r = requests.get("https://all.api.radio-browser.info/json/servers", headers=RB_HEADERS, timeout=5)
        names = sorted({s["name"] for s in r.json() if s.get("name")})
        if names:
            return names
    except Exception:
        pass
    return ["de1.api.radio-browser.info"]

def rb_get(path, params=None, timeout=10):
    """GET on a random radio-browser server, falling back to the others."""
    servers = rb_servers()
    random.shuffle(servers)
    last = None
    for host in servers:
        try:
            r = requests.get(f"https://{host}/json/{path}", params=params, headers=RB_HEADERS, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = f"{host}: HTTP {r.status_code}"
        except Exception as e:
            last = f"{host}: {e}"
    raise RuntimeError(last or "radio-browser unreachable")

@st.cache_data(ttl=86400)
def get_country_codes():
    """[(ISO 3166-1 alpha-2 code, station count)] ordered by station count."""
    try:
        data = rb_get("countrycodes", {"order": "stationcount", "reverse": "true", "hidebroken": "true"})
        return [(c["name"].upper(), c["stationcount"]) for c in data if len(c.get("name", "")) == 2]
    except Exception:
        return [("IT", 0), ("US", 0), ("GB", 0), ("FR", 0), ("DE", 0), ("ES", 0)]

@st.cache_data(ttl=86400)
def get_genres():
    """Curated list merged with the tags most used on radio-browser."""
    tags = set(GENRES)
    try:
        data = rb_get("tags", {"order": "stationcount", "reverse": "true", "hidebroken": "true", "limit": 500})
        tags |= {t["name"].strip().lower() for t in data if t["stationcount"] >= 20 and 2 < len(t["name"]) < 30 and t["name"][0].isalpha()}
    except Exception:
        pass
    return sorted(tags)

# Quality presets -> bitrate range in kbps (same thresholds used by the result cards)
QUALITY = {"any": (None, None), "low": (None, 127), "std": (128, 191), "high": (192, None)}
PAGE_SIZE = 20

def get_existing_radios():
    endpoint = f"{NAVIDROME_URL}/rest/getInternetRadioStations"
    params = {"u": USERNAME, "t": TOKEN, "s": SALT, "v": VERSION, "c": "NaviRadioManager", "f": "json"}
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        if isinstance(stations, dict): 
            stations = [stations]
        return [s['streamUrl'] for s in stations if 'streamUrl' in s]
    except:
        return []

@st.cache_data(ttl=300)
def get_all_my_radios_with_details():
    """Recupera tutte le radio da Navidrome con dettagli completi"""
    endpoint = f"{NAVIDROME_URL}/rest/getInternetRadioStations"
    params = {
        "u": USERNAME,
        "t": TOKEN,
        "s": SALT,
        "v": "1.16.1",
        "c": "NaviRadioManager",
        "f": "json"
    }
    
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        
        if isinstance(stations, dict):
            return [stations]
        return stations if stations else []
    except Exception as e:
        st.error(f"Errore recupero radio: {e}")
        return []

# ========== INIZIALIZZAZIONE STATI SESSIONE ==========
if 'stage' not in st.session_state: 
    st.session_state.stage = 0 
if 'results' not in st.session_state: 
    st.session_state.results = []
if 'offset' not in st.session_state: 
    st.session_state.offset = 0
if 'search_reverse' not in st.session_state: 
    st.session_state.search_reverse = "true"
if 'search_name' not in st.session_state: 
    st.session_state.search_name = ""
if 'filters' not in st.session_state:
    st.session_state.filters = {}
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "search"
if 'my_radios' not in st.session_state:
    st.session_state.my_radios = []
if 'selected_radio' not in st.session_state:
    st.session_state.selected_radio = None
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False
if 'editing_radio' not in st.session_state:
    st.session_state.editing_radio = None

@st.cache_data(ttl=600)
def search_radio(filters, offset, reverse="true"):
    """filters: optional name, genres (list), countrycode, quality. Empty ones are ignored; the rest are ANDed."""
    params = {
        "order": "votes",
        "reverse": reverse,
        "limit": PAGE_SIZE,
        "offset": offset,
        "hidebroken": "true",
    }
    if filters.get("name"):
        params["name"] = filters["name"]
    if filters.get("genres"):
        params["tagList"] = ",".join(filters["genres"])  # station must have all the tags
    if filters.get("countrycode"):
        params["countrycode"] = filters["countrycode"]
    bmin, bmax = QUALITY.get(filters.get("quality", "any"), (None, None))
    if bmin is not None:
        params["bitrateMin"] = bmin
    if bmax is not None:
        params["bitrateMax"] = bmax
    try:
        return rb_get("stations/search", params)
    except Exception:
        return []

def run_search(offset, reverse):
    st.session_state.offset = offset
    st.session_state.search_reverse = reverse
    st.session_state.results = search_radio(st.session_state.filters, offset, reverse)

def add_to_navidrome(station):
    endpoint = f"{NAVIDROME_URL}/rest/createInternetRadioStation"
    params = {"u": USERNAME, "t": TOKEN, "s": SALT, "v": VERSION, "c": "NaviRadioManager", "f": "json",
              "name": station['name'], "streamUrl": unquote(station['url_resolved']), "homepageUrl": unquote(station.get('homepage', ''))}
    # DEBUG
    #st.write(f"🔍 Parametri inviati: {params}")
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        result = r.json()
        #st.write(f"📡 Risposta: {result}")  # DEBUG
        #time.sleep(5)
        return result
    except:
        return {"subsonic-response": {"status": "failed"}}

def get_radios():
    endpoint = f"{NAVIDROME_URL}/rest/getInternetRadioStations"
    params = {
        "u": USERNAME, "t": TOKEN, "s": SALT, 
        "v": "1.16.1", "c": "NaviRadioManager", "f": "json"
    }
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        data = r.json()
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        
        if isinstance(stations, dict):
            return [stations]
        return stations
    except Exception as e:
        st.error(f"Errore get_radios: {e}")
        return []

def delete_radio(radio_id):
    """Elimina una radio da Navidrome usando il suo ID"""
    url = f"{NAVIDROME_URL}/rest/deleteInternetRadioStation.view"
    params = {
        "u": USERNAME,
        "t": TOKEN, 
        "s": SALT,
        "v": "1.16.1",
        "c": "NaviRadioManager",
        "f": "json",
        "id": radio_id
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"subsonic-response": {"status": "failed", "error": {"message": str(e)}}}

# ========== NUOVA FUNZIONE UPDATE CORRETTA ==========
def update_radio(radio_id, name, stream_url, homepage_url):
    """
    Aggiorna una radio esistente usando l'API ufficiale updateInternetRadioStation.
    Richiede privilegi di amministratore.
    """
    endpoint = f"{NAVIDROME_URL}/rest/updateInternetRadioStation.view"
    params = {
        "u": USERNAME,
        "t": TOKEN,
        "s": SALT,
        "v": "1.16.1",
        "c": "NaviRadioManager",
        "f": "json",
        "id": radio_id,
        "name": name,
        "streamUrl": unquote(stream_url),
        "homepageUrl": unquote(homepage_url)
    }
    
    try:
        r = requests.get(endpoint, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"subsonic-response": {"status": "failed", "error": {"message": str(e)}}}


def enter_edit_mode(radio):
    st.session_state.edit_mode = True
    st.session_state.editing_radio = radio


def cancel_edit():
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None

def scroll_to_element(element_id):
    """Usa JavaScript per scrollare a un elemento specifico dopo il reload"""
    js = f"""
    <script>
    window.addEventListener('load', function() {{
        setTimeout(function() {{
            var element = document.getElementById('{element_id}');
            if (element) {{
                element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
            }}
        }}, 100);
    }});
    </script>
    """
    st.iframe(js, height=1)

def vote_for_station(uuid):
    try:
        return bool(rb_get(f"vote/{uuid}").get("ok"))
    except Exception:
        return False

def get_total_radios():
    endpoint = f"{NAVIDROME_URL}/rest/getInternetRadioStations"
    params = {
        'u': USERNAME,
        't': TOKEN,
        's': SALT,
        'v': VERSION,
        'c': 'NaviRadioManager',
        'f': 'json'
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()
        stations = data.get('subsonic-response', {}).get('internetRadioStations', {}).get('internetRadioStation', [])
        if isinstance(stations, dict):
            return 1
        return len(stations)
    except Exception as e:
        return "?"

def bulk_add_radios():
    if not st.session_state.results:
        st.toast(T.get("bulk_no_results", "⚠️ Nessuna radio da aggiungere!"), icon="⚠️")
        return

    start_label = T.get("bulk_start", "🚀 Avvio aggiunta di massa...")
    
    with st.status(start_label, expanded=True) as status:
        added = 0
        skipped = 0
        
        existing_urls = get_existing_radios() 
        
        for radio in st.session_state.results:
            name = radio.get('name', 'Unknown')
            url = radio.get('url_resolved', radio.get('url', ''))
            
            if url in existing_urls:
                skip_msg = T.get("bulk_skip", "⏩ Salto (già presente):")
                status.write(f"{skip_msg} {name}")
                skipped += 1
            else:
                proc_msg = T.get("bulk_process", "➕ Aggiunta in corso:")
                status.write(f"{proc_msg} {name}")
                
                res = add_to_navidrome(radio)
                
                if res.get('subsonic-response', {}).get('status') == 'ok':
                    added += 1
                else:
                    err_msg = T.get("err_add", "❌ Errore")
                    status.write(f"{err_msg}: {name}")
                
                time.sleep(0.1)
        
        final_msg = T.get("bulk_done", "✅ Completato! Aggiunte: {added}, Saltate: {skipped}").format(added=added, skipped=skipped)
        status.update(label=final_msg, state="complete", expanded=False)
        
        st.success(final_msg)
        toast_finish = T.get("bulk_toast", "✅ Operazione riuscita! (+{added})").format(added=added)
        st.toast(toast_finish, icon="📻")

def trigger_search():
    st.session_state.filters = {
        "name": st.session_state.get('search_name', "").strip(),
        "genres": [g.strip().lower() for g in st.session_state.get('search_genres', [])],
        "countrycode": st.session_state.get('search_cc', ""),
        "quality": st.session_state.get('search_quality', "any"),
    }
    st.session_state.stage = 1
    st.session_state.view_mode = "search"
    run_search(0, "true")

def reset_filters():
    st.session_state.search_name = ""
    st.session_state.search_genres = []
    st.session_state.search_cc = ""
    st.session_state.search_quality = "any"

def reset_home():
    st.session_state.stage = 0
    st.session_state.results = []
    st.session_state.offset = 0
    st.session_state.search_reverse = "true"
    st.session_state.view_mode = "search"
    st.session_state.selected_radio = None
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None
    st.session_state.filters = {}
    reset_filters()

def switch_to_manage_mode():
    """Passa alla modalità gestione radio e carica la lista"""
    st.session_state.view_mode = "manage"
    st.session_state.selected_radio = None
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None
    st.session_state.my_radios = get_all_my_radios_with_details()

def select_radio_for_details(radio):
    """Seleziona una radio per vedere i dettagli"""
    st.session_state.selected_radio = radio
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None

def back_to_radio_list():
    """Torna alla lista delle radio"""
    st.session_state.selected_radio = None
    st.session_state.edit_mode = False
    st.session_state.editing_radio = None

def copy_to_clipboard(text):
    """Utility per copiare testo (simulato con codice JS)"""
    js_code = f"""
    <script>
    navigator.clipboard.writeText(`{text}`);
    </script>
    """
    st.iframe(js_code, height=1)
    st.toast("📋 Copiato negli appunti!", icon="📋")

def rerun():
    st.write("")

st.markdown("<style>[data-testid='stVerticalBlock'] > div {transition: none !important; opacity: 1 !important;}</style>", unsafe_allow_html=True)

st.title(T["title"])

COUNTRY_CODES = [""] + [c for c, _ in get_country_codes()]
GENRE_OPTIONS = get_genres()

def country_label(code):
    if not code:
        return T["any"]
    return f"{get_flag_emoji(code)} {code} — {WORLD_COUNTRIES.get(code.lower(), '')}".rstrip(" —")

def quality_label(key):
    return T[f"quality_{key}"]

with st.sidebar:

    theme_icon = "☀️ " + T["theme_light"] if st.session_state.theme == "dark" else "🌙 " + T["theme_dark"]
    st.button(theme_icon, on_click=toggle_theme, use_container_width=True, key="btn_theme")

    st.header(T["search_header"])
    st.divider()
    # Bottone per gestione radio
    manage_label = T.get("btn_manage_radios", "📻 Navidrome Radio" if LANG_CODE == "IT" else "📻 Navidrome Radios")
    if st.button(manage_label, use_container_width=True, type="secondary"):
        st.cache_data.clear()
        st.session_state.my_radios = get_all_my_radios_with_details()
        switch_to_manage_mode()
        st.rerun()
    
    st.divider()
    
    # Sezione ricerca originale (visibile solo in modalità ricerca)
    if st.session_state.view_mode == "search":
        st.caption(T["filters_hint"])
        with st.form("search_form", border=False):
            st.text_input(T["name_label"], key="search_name", placeholder=T["name_placeholder"])
            st.multiselect(
                T["genre_label"],
                options=GENRE_OPTIONS,
                key="search_genres",
                accept_new_options=True,
                placeholder=T["genre_placeholder"],
                help=T["genre_help"],
            )
            st.selectbox(
                T["country_code_label"],
                options=COUNTRY_CODES,
                key="search_cc",
                format_func=country_label,
            )
            st.select_slider(
                T["quality_label"],
                options=list(QUALITY),
                key="search_quality",
                format_func=quality_label,
            )
            st.form_submit_button(T["btn_search"], on_click=trigger_search, use_container_width=True, type="primary")
        st.button(T["btn_reset_filters"], on_click=reset_filters, use_container_width=True)

        if st.session_state.get('stage') == 1:
            st.button(T["btn_home"], on_click=reset_home, use_container_width=True)
    
    # Sidebar in modalità gestione
    else:
        #st.subheader("📻 " + (T.get("my_radios_title", "Le mie Radio") if LANG_CODE == "IT" else "My Radios"))
        
        back_label = "🔙 " + (T.get("back_to_search", "Torna alla Ricerca") if LANG_CODE == "IT" else "Back to Search")
        if st.button(back_label, use_container_width=True):
            st.session_state.view_mode = "search"
            st.session_state.selected_radio = None
            st.session_state.edit_mode = False
            st.cache_data.clear()
            st.session_state.my_radios = get_all_my_radios_with_details()
            st.rerun()
        
        st.divider()
        
        if st.session_state.selected_radio:
            back_list_label = "📋 " + (T.get("back_to_list", "Torna alla Lista") if LANG_CODE == "IT" else "Back to List")
            if st.button(back_list_label, use_container_width=True, type="secondary"):
                back_to_radio_list()
                st.rerun()

main_area = st.empty()

with main_area.container():
    
    # ============================================
    # MODALITÀ GESTIONE RADIO
    # ============================================
    if st.session_state.view_mode == "manage":
        
        # --- Vista Dettaglio Singola Radio ---
        if st.session_state.selected_radio:
            radio = st.session_state.selected_radio
            hp = radio.get('homePageUrl', '').strip()
            stream_url = radio.get('streamUrl', radio.get('url', 'N/D'))
            
            # ========== HEADER CON ICONA E NOME ==========
            header_cols = st.columns([1, 4])
            with header_cols[0]:
                if hp:
                    icona = f"https://www.google.com/s2/favicons?sz=128&domain={hp}"
                    st.image(icona, width=80)
                else:
                    st.markdown("## 📻")
            with header_cols[1]:
                st.title(radio.get('name', 'Unknown'))
                st.caption(f"ID: `{radio.get('id', 'N/D')}`")
            st.divider()
            # ========== SEZIONE URL E LINK ==========
            st.subheader("🔗 " + (T.get("links", "Info") if LANG_CODE == "IT" else "Info"))
            url_cols = st.columns(2)
            with url_cols[0]:
                if hp:
                    # Recupera favicon
                    favicon_url = f"https://www.google.com/s2/favicons?sz=32&domain={hp}"
                    st.markdown(f"**<img src='{favicon_url}' width='32' style='vertical-align: middle; margin-right: 5px;'> {T.get('website', 'Sito Web') if LANG_CODE == 'IT' else 'Website'}**", unsafe_allow_html=True)
                    st.code(hp, language=None)
                else:
                    st.markdown("**🌐 " + (T.get("website", "Sito Web") if LANG_CODE == "IT" else "Website") + "**")
                    st.caption("—")
            with url_cols[1]:
                st.markdown("**<img src='https://www.google.com/s2/favicons?sz=32&domain=radio-browser.info' width='32' style='vertical-align: middle; margin-right: 5px;'> Stream URL**", unsafe_allow_html=True)
                st.code(stream_url, language=None)        
            st.divider()
            # ========== SEZIONE STATISTICHE INLINE ==========
            st.markdown(f"""
            <div style="display: flex; justify-content: space-around; align-items: center; 
                        background-color: rgba(0,0,0,0.1); padding: 8px; border-radius: 8px;
                        font-size: 14px;">
                <span>⭐ <b>{radio.get('starred', 0) or 0}</b> {T.get("votes", "Voti") if LANG_CODE == "IT" else "Votes"}</span>
                <span>🟢 {T.get("active", "Attiva") if LANG_CODE == "IT" else "Active"}</span>
                <span>📊 Radio</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # ========== SEZIONE PLAYER ==========
            st.subheader("▶️ " + (T.get("preview", "Anteprima") if LANG_CODE == "IT" else "Preview"))
            
            fixed_url = fix_url(stream_url)
            try:
                if fixed_url:
                    # Usa st.audio con meno margine
                    st.audio(fixed_url, format="audio/mp3")
                    # Aggiungi spazio negativo dopo
                    st.markdown('<div style="margin-top: -10px;"></div>', unsafe_allow_html=True)
                else:
                    st.warning(T.get("no_preview", "Anteprima non disponibile") if LANG_CODE == "IT" else "Preview not available")
            except Exception as e:
                st.error(f"Errore player: {str(e)}")

            if fixed_url:
                now_playing_panel(fixed_url)

            st.divider()
            
            # ========== SEZIONE AZIONI CON EDIT FUNZIONANTE (API CORRETTA) ============
            st.subheader("⚡ " + (T.get("actions", "Azioni") if LANG_CODE == "IT" else "Actions"))
            
            # Se siamo in modalità edit, mostra il form
            if st.session_state.edit_mode and st.session_state.editing_radio.get('id') == radio.get('id'):
                st.info("✏️ " + (T.get("edit_mode_info", "Modifica i campi e conferma") if LANG_CODE == "IT" else "Edit fields and confirm"))
                
                with st.form(key=f"edit_form_{radio.get('id')}"):
                    edit_name = st.text_input(
                        T.get("name_label", "Nome") if LANG_CODE == "IT" else "Name",
                        value=radio.get('name', '')
                    )
                    edit_url = st.text_input(
                        T.get("stream_url", "URL Stream") if LANG_CODE == "IT" else "Stream URL",
                        value=radio.get('streamUrl', radio.get('url', ''))
                    )
                    edit_homepage = st.text_input(
                        T.get("homepage_url", "Sito Web") if LANG_CODE == "IT" else "Homepage",
                        value=radio.get('homePageUrl', '')
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        submitted = st.form_submit_button(
                            "💾 " + (T.get("save", "Salva") if LANG_CODE == "IT" else "Save"),
                            use_container_width=True,
                            type="primary"
                        )
                    with col_cancel:
                        cancelled = st.form_submit_button(
                            "❌ " + (T.get("cancel", "Annulla") if LANG_CODE == "IT" else "Cancel"),
                            use_container_width=True
                        )
                    
                    if submitted:
                        if not edit_name or not edit_url:
                            st.error(T.get("err_required_fields", "Nome e URL sono obbligatori") if LANG_CODE == "IT" else "Name and URL are required")
                        else:
                            with st.spinner(T.get("saving", "Salvataggio...") if LANG_CODE == "IT" else "Saving..."):
                                res = update_radio(
                                    radio.get('id'),
                                    edit_name,
                                    edit_url,
                                    edit_homepage
                                )
                                
                                if res.get('subsonic-response', {}).get('status') == 'ok':
                                    st.success(T.get("msg_updated", "✅ Radio aggiornata con successo!") if LANG_CODE == "IT" else "✅ Radio updated successfully!")
                                    cancel_edit()
                                    time.sleep(1)
                                    st.cache_data.clear()
                                    st.session_state.my_radios = get_all_my_radios_with_details()
                                    st.rerun()
                                else:
                                    err_msg = res.get('subsonic-response', {}).get('error', {}).get('message', 'Errore sconosciuto')
                                    st.error(f"❌ Errore: {err_msg}")
                    
                    if cancelled:
                        cancel_edit()
                        st.rerun()

            else:
                # Definisci confirm_key e radio_anchor QUI
                confirm_key = f"confirm_delete_{radio.get('id')}"
                radio_anchor = f"radio_{radio.get('id')}"
                
                # INIZIALIZZA se non esiste
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False
                
                # Griglia 2x2 corretta
                row1_col1, row1_col2 = st.columns(2)
                row2_col1, row2_col2 = st.columns(2)
                
                # Prima riga
                with row1_col1:
                    if st.button("🧪 " + (T.get("test_stream", "Test Stream") if LANG_CODE == "IT" else "Test Stream"), 
                               use_container_width=True):
                        try:
                            test_resp = requests.get(fixed_url, timeout=5, stream=True)
                            if test_resp.status_code == 200:
                                st.success("✅ Stream raggiungibile!")
                            else:
                                st.warning(f"⚠️ Status: {test_resp.status_code}")
                        except Exception as e:
                            st.error(f"❌ Errore: {str(e)}")
                
                with row1_col2:
                    if st.button("✏️ " + (T.get("edit", "Modifica") if LANG_CODE == "IT" else "Edit"), 
                               use_container_width=True, 
                               type="secondary"):
                        enter_edit_mode(radio)
                        st.rerun()
                
                # Seconda riga
                with row2_col1:
                    if st.button("📋 " + (T.get("back_to_list", "Torna alla Lista") if LANG_CODE == "IT" else "Back to List"), 
                               use_container_width=True, 
                               type="secondary"):
                        back_to_radio_list()
                        st.rerun()
                
                with row2_col2:
                    # ELIMINA
                    del_label = "🗑️ " + (T.get("delete", "Elimina") if LANG_CODE == "IT" else "Delete")
                    
                    if not st.session_state[confirm_key]:
                        if st.button(del_label, use_container_width=True, type="secondary", key=f"del_btn_{radio.get('id')}"):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        st.warning("⚠️ " + (T.get("click_again_confirm", "Clicca di nuovo per confermare") if LANG_CODE == "IT" else "Click again to confirm"))
                        
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("✅ " + (T.get("confirm", "Conferma") if LANG_CODE == "IT" else "Confirm"), 
                                       use_container_width=True, 
                                       type="primary",
                                       key=f"del_confirm_{radio.get('id')}"):
                                # DEBUG
                                #st.write(f"🗑️ Tentativo eliminazione ID: {radio.get('id')}")
                                
                                res = delete_radio(radio.get('id'))
                                
                                # DEBUG - Mostra risposta completa
                                #st.write(f"📡 Risposta API: {res}")
                                
                                st.session_state[confirm_key] = False
                                
                                if res.get('subsonic-response', {}).get('status') == 'ok':
                                    st.success("🗑️ " + (T.get("msg_deleted", "Eliminata!") if LANG_CODE == "IT" else "Deleted!"))
                                    st.cache_data.clear()
                                    st.session_state.my_radios = get_all_my_radios_with_details()
                                    time.sleep(1)
                                    back_to_radio_list()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Status non è 'ok': {res.get('subsonic-response', {}).get('status')}")
                                    err = res.get('subsonic-response', {}).get('error', {}).get('message', 'Errore sconosciuto')
                                    st.error(f"❌ {err}")
                        
                        with col_cancel:
                            if st.button("❌ " + (T.get("cancel", "Annulla") if LANG_CODE == "IT" else "Cancel"),
                                       use_container_width=True,
                                       key=f"del_cancel_{radio.get('id')}"):
                                st.session_state[confirm_key] = False
                                st.rerun()
                        
                        # Esegui scroll se necessario
                        if st.session_state.get(f"scroll_to_{radio.get('id')}", False):
                            scroll_to_element(radio_anchor)
                            st.session_state[f"scroll_to_{radio.get('id')}"] = False
            # ========== FINE SEZIONE AZIONI ==========
        
        # --- Vista Lista di tutte le radio ---
        else:
            st.header(T.get("my_radios_title", "Le mie Radio" if LANG_CODE == "IT" else "My Radios"))
            
            if st.button("🔄 " + (T.get("refresh", "Aggiorna Lista") if LANG_CODE == "IT" else "Refresh List"), 
                       use_container_width=True):
                st.cache_data.clear()
                switch_to_manage_mode()
                st.rerun()
            
            st.divider()
            
            if not st.session_state.my_radios:
                st.warning(T.get("no_radios_found", "Nessuna radio trovata in Navidrome" if LANG_CODE == "IT" 
                               else "No radios found in Navidrome"))
            else:
                st.success(f"📻 {len(st.session_state.my_radios)} " + 
                          (T.get("radios_count", "radio trovate") if LANG_CODE == "IT" else "radios found"))
                
                cols_per_row = 3
                radios = st.session_state.my_radios
                
                for i in range(0, len(radios), cols_per_row):
                    cols = st.columns(cols_per_row)
                    
                    for j in range(cols_per_row):
                        idx = i + j
                        if idx < len(radios):
                            radio = radios[idx]
                            with cols[j]:
                                hp = radio.get('homePageUrl', '').strip()
                                icona = f"https://www.google.com/s2/favicons?sz=64&domain={hp}" if hp else None
                                
                                with st.container():
                                    if icona:
                                        st.image(icona, width=40)
                                    
                                    st.markdown(f"**{radio.get('name', 'Unknown')[:25]}**")
                                    
                                    det_label = T.get("btn_details", "🔍 Dettagli") if LANG_CODE == "IT" else "🔍 Details"
                                    if st.button(det_label, key=f"det_{radio.get('id')}", use_container_width=True):
                                        select_radio_for_details(radio)
                                        st.rerun()
                                    
                                    st.divider()
    
    # ============================================
    # MODALITÀ RICERCA (ORIGINALE - INVARIATA)
    # ============================================
    else:
        if st.session_state.stage == 0:
            st.info(T["welcome"])
            
        elif st.session_state.stage == 1:
            existing_urls = get_existing_radios()  
            if st.session_state.results:
                btn_label = T.get("btn_bulk_add", "➕ Add entire page to Navidrome")
                if st.button(btn_label, use_container_width=True, type="primary"):
                    bulk_add_radios()
                    
                col_home, col_top, col_low = st.columns([2, 1, 1])
                
                with col_home:
                    st.button(f"🏠 {T['btn_home']}", on_click=reset_home, use_container_width=True, key="btn_home_main")
                
                with col_top:
                    label_top = T.get("btn_sort_top", "🔥 Top Votes")
                    if st.button(label_top, use_container_width=True, key="btn_sort_top"):
                        run_search(0, "true")
                        st.rerun()
                
                with col_low:
                    label_low = T.get("btn_sort_low", "🧊 Low Votes")
                    if st.button(label_low, use_container_width=True, key="btn_sort_low"):
                        run_search(0, "false")
                        st.rerun()

                st.write(f"### {T['results']}")
                
                all_my_radios = get_radios() 

                for s in st.session_state.results:
                    raw_url = s.get('url_resolved', '')
                    stream_url = fix_url(raw_url)
                    
                    is_duplicate = False
                    navidrome_id = None
                    
                    def clean_u(u): 
                        return str(u).strip().lower().rstrip('/')

                    target_url = clean_u(stream_url)

                    for my_r in all_my_radios:
                        current_nav_url = clean_u(my_r.get('url') or my_r.get('streamUrl', ''))
                        if target_url and current_nav_url and (target_url == current_nav_url or target_url in current_nav_url or current_nav_url in target_url):
                            is_duplicate = True
                            navidrome_id = my_r.get('id')
                            break
                    
                    c_code = s.get('countrycode', '').upper()
                    if c_code and c_code != "BY_NAME" and len(c_code) == 2:
                        flag = get_flag_emoji(c_code)
                    else:
                        flag = find_flag_in_string(s.get('name', ''))
                        if not flag:
                            flag = find_flag_in_string(s.get('tags', ''))
                    if not flag:
                        flag = "📻"
                    
                    votes = s.get('votes', 0)

                    if votes > 5000:
                        top_icon = "👑 " + "[Votes: " + str(votes) + "]"
                    elif votes > 1000:
                        top_icon = "🔥 " + "[Votes: " + str(votes) + "]"
                    else:
                        top_icon = "[Votes: " + str(votes) + "]"
                    
                    is_dup_tag = " ✅" if is_duplicate else ""
                    hp = s.get('homepage', '').strip()
                    icona = f"https://www.google.com/s2/favicons?sz=64&domain={hp}" if hp else None
                    tags = s.get('tags', '')
                    genere_list = [t.strip().capitalize() for t in tags.split(',') if t.strip()]
                    genere_principale = genere_list[0] if genere_list else ("Radio" if LANG_CODE=="IT" else "Station")
                    is_dup_tag = " ✅" if is_duplicate else ""
                    titolo_elenco = f"{flag} - {s['name']} {top_icon} [{genere_principale}]{is_dup_tag}"
                    
                    with st.expander(titolo_elenco):
                        h_col1, h_col2 = st.columns([1, 6])
                        with h_col1:
                            if icona:
                                st.image(icona, width=55)
                            else:
                                st.write(f"### {flag}")
                        with h_col2:
                            st.markdown(f"""
                            <div style="display: flex; align-items: center;">
                                <span style="font-weight: bold; margin-right: 10px;">🎧 Quick Preview:</span>
                                <span style="color: var(--accent); font-size: 0.8rem; font-weight: bold;">LIVE</span>
                                <div class="eq-container">
                                    <div class="eq-bar"></div>
                                    <div class="eq-bar"></div>
                                    <div class="eq-bar"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            try:
                                if stream_url:
                                    st.audio(stream_url, format="audio/mp3")
                                else:
                                    st.warning("URL not available")
                            except Exception as e:
                                st.error(f"Unable to load audio: {stream_url}")
                        
                        d_col1, d_col2 = st.columns(2)
                        bitrate = s.get('bitrate', 0)
                        codec = s.get('codec', 'N/D')
                        if bitrate >= 192:
                            q_color, q_label = "green", ("High Quality" if LANG_CODE == "EN" else "Alta Qualità")
                        elif bitrate >= 128:
                            q_color, q_label = "blue", ("Standard Quality" if LANG_CODE == "EN" else "Qualità Standard")
                        else:
                            q_color, q_label = "orange", ("Low Quality" if LANG_CODE == "EN" else "Bassa Qualità")
                        
                        with d_col1:
                            st.markdown(f"**{codec}** @ {bitrate} kbps")
                        with d_col2:
                            st.markdown(f":{q_color}[{q_label}]")
                        
                        st.progress(min(bitrate / 320, 1.0))

                        station_info(s)

                        # One live panel at a time: polling every open card would hit every stream
                        if stream_url:
                            if st.session_state.get("np_url") == stream_url:
                                if st.button("✖ " + T["np_close"], key=f"np_close_{s['stationuuid']}", use_container_width=True):
                                    st.session_state.np_url = None
                                    st.rerun()
                                now_playing_panel(stream_url)
                            elif st.button("🎵 " + T["np_btn"], key=f"np_{s['stationuuid']}", use_container_width=True):
                                st.session_state.np_url = stream_url
                                st.rerun()

                        f_col1, f_col2 = st.columns(2)
                        with f_col1:
                            st.caption(f"⭐ {votes} votes")
                        with f_col2:
                            if hp:
                                st.caption(f"🔗 [Web Site]({hp})")
                        
                        st.divider()
                        
                        col_v, col_a = st.columns([1, 1])
                        with col_v:
                            v_label = "👍 " + ("Vota Radio" if LANG_CODE == "IT" else "Vote Radio")
                            if st.button(v_label, key=f"vote_{s['stationuuid']}", use_container_width=True):
                                if vote_for_station(s['stationuuid']):
                                    msg = "Voto inviato! Grazie! 🎉" if LANG_CODE == "IT" else "Vote sent! Thanks! 🎉"
                                    st.toast(msg)
                                else:
                                    err = "Errore nel voto" if LANG_CODE == "IT" else "Voting error"
                                    st.error(err)

                        with col_a:
                            if is_duplicate:
                                btn_del_label = T.get("btn_delete", "🗑️ Remove")
                                if st.button(btn_del_label, key=f"del_{s['stationuuid']}", use_container_width=True):
                                    if navidrome_id:
                                        res = delete_radio(navidrome_id)
                                        status = res.get('subsonic-response', {}).get('status')
                                        
                                        if status == 'ok':
                                            st.toast(T.get("msg_deleted", "Radio eliminata"), icon="🗑️")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            error_msg = res.get('subsonic-response', {}).get('error', {}).get('message', 'Unknown error')
                                            st.error(f"Navidrome Error: {error_msg}")
                                    else:
                                        st.error("Errore: ID radio non trovato nel database!")
                            else:
                                if st.button(T["add_btn"], key=f"add_{s['stationuuid']}", use_container_width=True, type="primary"):
                                    res = add_to_navidrome(s)
                                    if res.get('subsonic-response', {}).get('status') == 'ok': 
                                        st.success(T["success"])
                                        time.sleep(1)
                                        st.rerun() 
                                    else: 
                                        st.error(T.get("err_add", "❌ Error adding station"))
                        
                        if is_duplicate:
                            msg = "⚠️ Già presente in NAVIDROME" if LANG_CODE=="IT" else "⚠️ Already exists in NAVIDROME"
                            st.markdown(
                                f"""
                                <div style="text-align: center; color: gray; font-size: 0.8rem; margin-top: -10px; margin-bottom: 10px;">
                                    {msg}
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                
                st.divider()
                col_back, col_info, col_next = st.columns([1, 1, 1])

                with col_back:
                    if st.session_state.offset > 0:
                        if st.button("⬅️ " + ("Indietro" if LANG_CODE=="IT" else "Back"), use_container_width=True, key="nav_back"):
                            run_search(st.session_state.offset - PAGE_SIZE, st.session_state.search_reverse)
                            st.rerun()

                with col_info:
                    pagina_attuale = (st.session_state.offset // PAGE_SIZE) + 1
                    st.markdown(f"<div style='text-align: center; padding-top: 10px; font-weight: bold; color: var(--accent);'>Pag. {pagina_attuale}</div>", unsafe_allow_html=True)

                with col_next:
                    if len(st.session_state.results) >= PAGE_SIZE:
                        if st.button(("Avanti" if LANG_CODE=="IT" else "Next") + " ➡️", use_container_width=True, key="nav_next"):
                            run_search(st.session_state.offset + PAGE_SIZE, st.session_state.search_reverse)
                            st.rerun()
                    else:
                        st.button("🏁 " + ("Fine" if LANG_CODE=="IT" else "End"), disabled=True, use_container_width=True)

                st.write("")
                if st.button("🏠 " + T["btn_home"], on_click=reset_home, use_container_width=True):
                    st.rerun()
            else:
                st.warning(T["no_results"])
                st.button(T["btn_home"], on_click=reset_home, use_container_width=True)

# Footer
start_ping = time.time()
st.divider()
col1, col2 = st.columns([1.2, 0.8])

with col1:
    try:
        requests.get(NAVIDROME_URL, timeout=2)
        ping = int((time.time() - start_ping) * 1000)
        st.markdown(f":gray-badge[:material/check: Navidrome URL: {NAVIDROME_URL} 🟢 Connected ({ping}ms)]")
    except:
        st.markdown(f":gray-badge[:material/check: Navidrome URL: {NAVIDROME_URL} 🔴 Offline]")

with col2:
    st.markdown(f":gray-badge[:material/check: User: {USERNAME} ]")

time.sleep(.1)

with st.sidebar:  
    v_safe = str(VERSION).replace("-", "--")
    footer_html = f"""
    <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; padding: 10px;">
        <a href="https://github.com/nightwatch75/NaviradioManagerPlus" target="_blank">
            <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="Github">
        </a>
    </div>
    <div style="text-align: center; margin-top: 5px;">
        <img src="https://img.shields.io/badge/Ver.-{v_safe}-blue?style=flat-square" alt="Ver.">
        <img src="https://img.shields.io/badge/Navi Stat.-{get_total_radios()}-blue?style=flat-square" alt="Navi Stat.">
    </div>
    """

with st.sidebar:
    st.markdown(footer_html, unsafe_allow_html=True)
    time.sleep(.1)

st.divider()
st.caption("© 2026 NaviRadioManager Plus — fork of [brunopiras/naviradiomanager](https://github.com/brunopiras/naviradiomanager) (MIT)")

def inject_js(file_path):
    try:
        with open(file_path, 'r') as f:
            js_code = f.read()
            st.iframe(f"<script>{js_code}</script>", height=1)
    except FileNotFoundError:
        pass

inject_js("audio_handler.js")