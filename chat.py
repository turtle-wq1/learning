import streamlit as st
import sqlite3
import time

DB = "gchat.db"

# ─── Themes ───────────────────────────────────────────────────────────────────
THEMES = {
    "Default": {
        "bg": "#0e0f14", "surface": "#16181f", "surface2": "#1e2029",
        "border": "#2a2d3a", "accent": "#5b6aff", "accent2": "#ff6b6b",
        "green": "#3ddc97", "text": "#e8eaf0", "muted": "#6b7080",
        "dm_color": "#ff9f43", "own_bubble": "#1e2350", "own_text": "#d0d4f5",
    },
    "Midnight": {
        "bg": "#0d0b1a", "surface": "#13112a", "surface2": "#1c1940",
        "border": "#2e2a50", "accent": "#a78bfa", "accent2": "#f472b6",
        "green": "#34d399", "text": "#ede9fe", "muted": "#7c6fa0",
        "dm_color": "#f472b6", "own_bubble": "#231e4a", "own_text": "#c4b5fd",
    },
    "Sunset": {
        "bg": "#160d0a", "surface": "#1f1210", "surface2": "#2a1a16",
        "border": "#3d2520", "accent": "#fb923c", "accent2": "#f43f5e",
        "green": "#4ade80", "text": "#fef3ee", "muted": "#9a6a5a",
        "dm_color": "#fbbf24", "own_bubble": "#3b1f10", "own_text": "#fed7aa",
    },
    "Forest": {
        "bg": "#080f0a", "surface": "#0e1a10", "surface2": "#152318",
        "border": "#1e3524", "accent": "#4ade80", "accent2": "#34d399",
        "green": "#86efac", "text": "#ecfdf5", "muted": "#4d7a5a",
        "dm_color": "#fbbf24", "own_bubble": "#0f2e18", "own_text": "#bbf7d0",
    },
    "Ocean": {
        "bg": "#060e14", "surface": "#0b1520", "surface2": "#101e2c",
        "border": "#1a3040", "accent": "#22d3ee", "accent2": "#38bdf8",
        "green": "#4ade80", "text": "#ecfeff", "muted": "#4a7a8a",
        "dm_color": "#818cf8", "own_bubble": "#0c2233", "own_text": "#a5f3fc",
    },
}

THEME_ICONS = {
    "Default": "🟣",
    "Midnight": "🌙",
    "Sunset": "🌅",
    "Forest": "🌿",
    "Ocean": "🌊",
}

st.set_page_config(
    page_title="Classes", 
    page_icon="https://vignette.wikia.nocookie.net/logopedia/images/d/d5/Google_Classroom_2020.svg/revision/latest?cb=20201015124036", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
if "theme" not in st.session_state:
    st.session_state.theme = "Default"

t = THEMES[st.session_state.theme]

st.markdown(f"""
<style>
@import url('https://upload.wikimedia.org/wikipedia/commons/5/59/Google_Classroom_Logo.png');

# --- Replace your existing CSS header/collapsed control lines with this ---

#MainMenu, footer {{visibility: hidden;}}


header[data-testid="stHeader"] {{
    background-color: rgba(0,0,0,0) !important;
    visibility: visible !important;
    display: flex !important;
}}


[data-testid="collapsedControl"] {{
    visibility: visible !important;
    display: flex !important;
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    margin: 10px !important;
    transition: all 0.2s ease !important;
    z-index: 999999 !important;
}}

[data-testid="collapsedControl"]:hover {{
    border-color: var(--accent) !important;
    transform: scale(1.05);
}}
.block-container {{padding-top: 1rem !important;}}

:root {{
    --bg: {t['bg']};
    --surface: {t['surface']};
    --surface2: {t['surface2']};
    --border: {t['border']};
    --accent: {t['accent']};
    --accent2: {t['accent2']};
    --green: {t['green']};
    --text: {t['text']};
    --muted: {t['muted']};
    --dm-color: {t['dm_color']};
    --own-bubble: {t['own_bubble']};
    --own-text: {t['own_text']};
}}

.stApp {{
    background: var(--bg) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text);
}}
section[data-testid="stSidebar"] {{
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}}
section[data-testid="stSidebar"] > div {{padding-top: 1.5rem;}}
[data-testid="collapsedControl"] {{
    visibility: visible !important;
    display: flex !important;
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 50% !important;
    color: var(--text) !important;
}}

.gchat-title {{
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem; font-weight: 700;
    color: var(--accent); letter-spacing: -1px; margin-bottom: 0.2rem;
}}
.gchat-sub {{
    font-size: 0.72rem; color: var(--muted);
    font-family: 'Space Mono', monospace;
    letter-spacing: 1px; text-transform: uppercase; margin-bottom: 1.5rem;
}}
.section-label {{
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem; letter-spacing: 2px; text-transform: uppercase;
    color: var(--muted); margin: 1rem 0 0.5rem 0; padding-left: 2px;
}}
.chat-header {{
    font-family: 'Space Mono', monospace;
    font-size: 1rem; font-weight: 700;
    padding: 0.8rem 0; border-bottom: 1px solid var(--border);
    margin-bottom: 1rem; color: var(--text);
    display: flex; align-items: center; gap: 8px;
}}
.chat-channel {{color: var(--accent);}}
.chat-dm {{color: var(--dm-color);}}

.msg-row {{
    display: flex; align-items: flex-start; gap: 10px;
    margin-bottom: 0.8rem; animation: fadeIn 0.2s ease;
}}
@keyframes fadeIn {{from {{opacity:0;transform:translateY(4px);}} to {{opacity:1;transform:translateY(0);}}}}
.msg-avatar {{
    width: 34px; height: 34px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem; font-weight: 700; flex-shrink: 0; color: #fff;
}}
.msg-body {{flex: 1;}}
.msg-sender {{font-size: 0.82rem; font-weight: 600; color: var(--text); margin-bottom: 2px;}}
.msg-sender span.ts {{
    font-size: 0.68rem; color: var(--muted); font-weight: 400;
    margin-left: 8px; font-family: 'Space Mono', monospace;
}}
.msg-text {{
    font-size: 0.9rem; color: #c8cad8; line-height: 1.5;
    background: var(--surface); padding: 8px 12px;
    border-radius: 0 10px 10px 10px;
    display: inline-block; max-width: 100%; word-break: break-word;
}}
.msg-text.own {{
    background: var(--own-bubble);
    border-radius: 10px 0 10px 10px;
    color: var(--own-text);
}}

.join-box {{max-width: 400px; margin: 6rem auto; text-align: center;}}
.join-title {{
    font-family: 'Space Mono', monospace; font-size: 2.5rem;
    color: var(--accent); font-weight: 700; letter-spacing: -2px; margin-bottom: 0.3rem;
}}
.join-sub {{color: var(--muted); font-size: 0.9rem; margin-bottom: 2rem;}}

.stTextInput input, .stChatInput textarea {{
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
}}
.stTextInput input:focus, .stChatInput textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(100,100,255,0.15) !important;
}}
.stButton button {{
    background: var(--accent) !important; color: #fff !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; transition: opacity 0.15s !important;
}}
.stButton button:hover {{opacity: 0.85 !important;}}

hr {{border-color: var(--border) !important; margin: 1rem 0;}}
.stRadio label {{color: var(--text) !important; font-size: 0.88rem !important;}}
.stRadio > div {{gap: 2px !important;}}

.reaction-bar {{display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px;}}
.reaction-pill {{
    display: inline-flex; align-items: center; gap: 4px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 20px; padding: 3px 10px; font-size: 1.3rem;
    cursor: pointer; transition: background 0.15s, border-color 0.15s; line-height: 1.4;
}}
.reaction-pill:hover {{ border-color: var(--accent); background: var(--own-bubble); }}
.reaction-pill.reacted {{ border-color: var(--accent); background: var(--own-bubble); }}
.reaction-count {{font-size: 0.78rem; color: var(--muted); font-family: 'Space Mono', monospace;}}

/* Very tight reaction picker buttons */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {{
    background: transparent !important; border: none !important;
    padding: 0px 1px !important; font-size: 1.1rem !important;
    min-height: unset !important; height: auto !important;
    line-height: 1 !important; box-shadow: none !important;
    opacity: 0.38; transition: opacity 0.12s, transform 0.12s !important;
    color: unset !important; margin: 0 !important; min-width: unset !important;
}}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {{
    opacity: 1 !important; transform: scale(1.2) !important;
    background: transparent !important;
}}
</style>
""", unsafe_allow_html=True)

# ─── Database ─────────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    con = get_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT NOT NULL,
        recipient TEXT, content TEXT NOT NULL, ts REAL NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS presence (
        username TEXT PRIMARY KEY, last_seen REAL NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS reactions (
        msg_id INTEGER NOT NULL, emoji TEXT NOT NULL, username TEXT NOT NULL,
        PRIMARY KEY (msg_id, emoji, username))""")
    con.commit(); con.close()

def heartbeat(username):
    con = get_conn()
    con.execute("INSERT OR REPLACE INTO presence VALUES (?,?)", (username, time.time()))
    con.commit(); con.close()

def get_online_users(timeout=15):
    con = get_conn()
    rows = con.execute("SELECT username FROM presence WHERE last_seen > ? ORDER BY username",
                       (time.time() - timeout,)).fetchall()
    con.close()
    return [r[0] for r in rows]

def send_message(sender, content, recipient=None):
    con = get_conn()
    con.execute("INSERT INTO messages (sender, recipient, content, ts) VALUES (?,?,?,?)",
                (sender, recipient, content, time.time()))
    con.commit(); con.close()

def get_global_messages(limit=100):
    con = get_conn()
    rows = con.execute(
        "SELECT id, sender, content, ts FROM messages WHERE recipient IS NULL ORDER BY ts DESC LIMIT ?",
        (limit,)).fetchall()
    con.close()
    return list(reversed(rows))

def get_dm_messages(user_a, user_b, limit=100):
    con = get_conn()
    rows = con.execute("""SELECT id, sender, content, ts FROM messages
        WHERE recipient IS NOT NULL
          AND ((sender=? AND recipient=?) OR (sender=? AND recipient=?))
        ORDER BY ts DESC LIMIT ?""", (user_a, user_b, user_b, user_a, limit)).fetchall()
    con.close()
    return list(reversed(rows))

def get_last_msg_id():
    con = get_conn()
    row = con.execute("SELECT MAX(id) FROM messages").fetchone()
    con.close()
    return row[0] or 0

def toggle_reaction(msg_id, emoji, username):
    con = get_conn()
    existing = con.execute("SELECT 1 FROM reactions WHERE msg_id=? AND emoji=? AND username=?",
                           (msg_id, emoji, username)).fetchone()
    if existing:
        con.execute("DELETE FROM reactions WHERE msg_id=? AND emoji=? AND username=?",
                    (msg_id, emoji, username))
    else:
        con.execute("INSERT INTO reactions VALUES (?,?,?)", (msg_id, emoji, username))
    con.commit(); con.close()

def get_reactions(msg_ids):
    if not msg_ids:
        return {}
    con = get_conn()
    rows = con.execute(
        f"SELECT msg_id, emoji, username FROM reactions WHERE msg_id IN ({','.join('?'*len(msg_ids))})",
        msg_ids).fetchall()
    con.close()
    result = {}
    for mid, emoji, uname in rows:
        result.setdefault(mid, {}).setdefault(emoji, []).append(uname)
    return result

# ─── Helpers ──────────────────────────────────────────────────────────────────
AVATAR_COLORS = ["#5b6aff","#ff6b6b","#3ddc97","#ff9f43","#a29bfe",
                 "#fd79a8","#00cec9","#e17055","#74b9ff","#55efc4","#fdcb6e","#b2bec3"]

def avatar_color(name):
    return AVATAR_COLORS[sum(ord(c) for c in name) % len(AVATAR_COLORS)]

def avatar_initials(name):
    parts = name.strip().split()
    return (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

def fmt_time(ts):
    return time.strftime("%I:%M %p", time.localtime(ts)).lstrip("0")

REACTION_EMOJIS = ["❤️","😂","👍","🔥","😮","😢","🎉","💀"]

def render_messages(messages, me):
    if not messages:
        st.markdown("<div style='text-align:center;color:#6b7080;font-size:0.85rem;"
                    "padding:3rem 0;font-family:Space Mono,monospace;'>No messages yet. Say hello! 👋</div>",
                    unsafe_allow_html=True)
        return
    msg_ids = [r[0] for r in messages]
    all_reactions = get_reactions(msg_ids)

    for msg_id, sender, content, ts in messages:
        color = avatar_color(sender)
        initials = avatar_initials(sender)
        msg_class = "msg-text own" if sender == me else "msg-text"
        reactions = all_reactions.get(msg_id, {})

        reaction_html = '<div class="reaction-bar">'
        for emoji, users in reactions.items():
            pill_class = "reaction-pill reacted" if me in users else "reaction-pill"
            reaction_html += (f'<span class="{pill_class}">{emoji}'
                              f'<span class="reaction-count">{len(users)}</span></span>')
        reaction_html += '</div>'

        st.markdown(f"""
        <div class="msg-row">
            <div class="msg-avatar" style="background:{color}">{initials}</div>
            <div class="msg-body">
                <div class="msg-sender">{sender}<span class="ts">{fmt_time(ts)}</span></div>
                <div class="{msg_class}">{content}</div>
                {reaction_html}
            </div>
        </div>""", unsafe_allow_html=True)

        # Tight picker: very narrow columns so buttons sit close together
        cols = st.columns([0.25] + [0.32] * len(REACTION_EMOJIS) + [10])
        for i, emoji in enumerate(REACTION_EMOJIS):
            already = me in reactions.get(emoji, [])
            label = f"{emoji}·" if already else emoji
            if cols[i + 1].button(label, key=f"react_{msg_id}_{emoji}", help=f"React {emoji}"):
                toggle_reaction(msg_id, emoji, me)
                st.rerun()

# ─── Init ─────────────────────────────────────────────────────────────────────
init_db()
if "username" not in st.session_state:
    st.session_state.username = None
if "active_dm" not in st.session_state:
    st.session_state.active_dm = None
if "last_msg_id" not in st.session_state:
    st.session_state.last_msg_id = 0

# ─── Join screen ──────────────────────────────────────────────────────────────
if not st.session_state.username:
    st.markdown('<div class="join-box"><div class="join-title">gchat</div>'
                '<div class="join-sub">real-time group messaging</div></div>',
                unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        name_input = st.text_input("Choose a display name", placeholder="e.g. cooluser42",
                                   max_chars=24, label_visibility="visible")
        if st.button("Join GChat →", use_container_width=True):
            name = name_input.strip()
            if not name:
                st.error("Please enter a name.")
            elif len(name) < 2:
                st.error("Name must be at least 2 characters.")
            else:
                st.session_state.username = name
                heartbeat(name)
                st.rerun()
    st.stop()

# ─── Main app ─────────────────────────────────────────────────────────────────
me = st.session_state.username
heartbeat(me)

current_id = get_last_msg_id()
if current_id != st.session_state.last_msg_id:
    st.session_state.last_msg_id = current_id

online_users = get_online_users()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="gchat-title">gchat</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="gchat-sub">logged in as {me}</div>', unsafe_allow_html=True)

    if st.button("# global", use_container_width=True, key="global_btn"):
        st.session_state.active_dm = None
        st.rerun()

    st.markdown('<div class="section-label">🟢 Online Now</div>', unsafe_allow_html=True)
    others = [u for u in online_users if u != me]
    if not others:
        st.markdown('<div style="color:#6b7080;font-size:0.82rem;padding-left:4px;">No one else online</div>',
                    unsafe_allow_html=True)
    else:
        for user in others:
            if st.button(f"💬 {user}", key=f"dm_{user}", use_container_width=True):
                st.session_state.active_dm = user
                st.rerun()

    st.markdown("---")

    # ── Theme picker ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">🎨 Theme</div>', unsafe_allow_html=True)
    theme_names = list(THEMES.keys())
    theme_labels = [f"{THEME_ICONS[n]}  {n}" for n in theme_names]
    current_idx = theme_names.index(st.session_state.theme)

    selected_label = st.radio(
        "theme_radio",
        theme_labels,
        index=current_idx,
        label_visibility="collapsed",
    )
    selected_name = theme_names[theme_labels.index(selected_label)]
    if selected_name != st.session_state.theme:
        st.session_state.theme = selected_name
        st.rerun()

    st.markdown("---")
    st.markdown(f'<div style="color:#6b7080;font-size:0.75rem;font-family:Space Mono,monospace;">'
                f'{len(online_users)} online</div>', unsafe_allow_html=True)

    if st.button("Leave GChat", key="leave"):
        con = get_conn()
        con.execute("DELETE FROM presence WHERE username=?", (me,))
        con.commit(); con.close()
        st.session_state.username = None
        st.session_state.active_dm = None
        st.rerun()

# ─── Main chat area ───────────────────────────────────────────────────────────
active_dm = st.session_state.active_dm
if active_dm:
    st.markdown(f'<div class="chat-header"><span class="chat-dm">⇄ Direct Message</span> · {active_dm}</div>',
                unsafe_allow_html=True)
    messages = get_dm_messages(me, active_dm)
else:
    st.markdown('<div class="chat-header"><span class="chat-channel">#</span> global</div>',
                unsafe_allow_html=True)
    messages = get_global_messages()

render_messages(messages, me)

placeholder_text = f"Message {active_dm}..." if active_dm else "Message #global..."
if prompt := st.chat_input(placeholder_text):
    send_message(me, prompt, recipient=active_dm if active_dm else None)
    st.rerun()

time.sleep(0.5)
st.rerun()
