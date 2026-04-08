import streamlit as st
import sqlite3
import time
import math

DB = "gchat.db"

# ─── Grid config ──────────────────────────────────────────────────────────────
GRID_SIZE = 20
GRID_ROWS = GRID_SIZE
GRID_COLS = GRID_SIZE
TOTAL_CELLS = GRID_ROWS * GRID_COLS

# Income tick: every N seconds players collect rent from their cells
INCOME_INTERVAL = 3
# Leader cash bonus every tick
LEADER_BONUS = 15
# Starting cash
STARTING_CASH = 100
# Vote-to-reset threshold
RESET_VOTE_THRESHOLD = 0.75

# ─── Cell cost / income helpers ───────────────────────────────────────────────
def cell_cost(row, col):
    """Cost increases toward the centre. Edge is $25, Center is $400 (16x)."""
    edge_price = 25
    center_price = 400
    price_range = center_price - edge_price # This is 375
    
    cx = (GRID_COLS - 1) / 2
    cy = (GRID_ROWS - 1) / 2
    dist = math.sqrt((col - cx) ** 2 + (row - cy) ** 2)
    max_dist = math.sqrt(cx ** 2 + cy ** 2)
    
    # norm is 1 at corners (furthest) and 0 at center
    norm = dist / max_dist          
    
    # (1 - norm) makes it 1 at center and 0 at corners
    # We multiply the range by the center-closeness and add the base price
    cost = round((1 - norm) * price_range + edge_price)
    
    return max(edge_price, cost)

def cell_income(row, col):
    """Income per tick ~10% of cost, min $1."""
    return max(1, round(cell_cost(row, col) * 0.10))

def is_edge_cell(row, col):
    return row == 0 or row == GRID_ROWS - 1 or col == 0 or col == GRID_COLS - 1

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
    "Neon": {
        "bg": "#050505", "surface": "#0c0c0c", "surface2": "#141414",
        "border": "#2affd5", "accent": "#ff00ff", "accent2": "#00ffff",
        "green": "#39ff14", "text": "#ffffff", "muted": "#888",
        "dm_color": "#00ffff", "own_bubble": "#1a0033", "own_text": "#ffccff",
    },
    "Light": {
        "bg": "#f5f7fb", "surface": "#ffffff", "surface2": "#eef1f7",
        "border": "#d6dbe6", "accent": "#4a6cff", "accent2": "#ff5c7a",
        "green": "#2ecc71", "text": "#111", "muted": "#666",
        "dm_color": "#ff7a18", "own_bubble": "#e6ecff", "own_text": "#111",
    },
    "Cyber": {
        "bg": "#020617", "surface": "#020617", "surface2": "#0f172a",
        "border": "#22c55e", "accent": "#22c55e", "accent2": "#06b6d4",
        "green": "#4ade80", "text": "#e2e8f0", "muted": "#64748b",
        "dm_color": "#38bdf8", "own_bubble": "#052e16", "own_text": "#bbf7d0",
     },
"Dracula": {
    "bg": "#000000",         # black background
    "surface": "#330000",    # dark red surfaces
    "surface2": "#550000",   # slightly lighter dark red
    "border": "#ff0000",     # red borders
    "accent": "#ff0000",     # red accents
    "accent2": "#ff4d4d",    # lighter red accent
    "green": "#ff3333",      # "green" replaced with red
    "text": "#ff0000",       # red text
    "muted": "#990000",      # muted/darker red
    "dm_color": "#ff3333",   # red DM color
    "own_bubble": "#550000", # chat bubble background
    "own_text": "#ff6666",   # chat bubble text
},

"Nord": {
    "bg": "#2e3440",
    "surface": "#3b4252",
    "surface2": "#434c5e",
    "border": "#1e90ff",     # bright blue outlines
    "accent": "#88c0d0",
    "accent2": "#81a1c1",
    "green": "#a3be8c",
    "text": "#eceff4",
    "muted": "#81a1c1",
    "dm_color": "#b48ead",
    "own_bubble": "#434c5e",
    "own_text": "#eceff4",
},
"Matrix": {
    "bg": "#000000", "surface": "#050505", "surface2": "#0a0a0a",
    "border": "#00ff41", "accent": "#00ff41", "accent2": "#39ff14",
    "green": "#00ff41", "text": "#00ff41", "muted": "#008f11",
    "dm_color": "#39ff14", "own_bubble": "#001a00", "own_text": "#00ff41",
},
"Cherry": {
    "bg": "#140d11", "surface": "#1f141a", "surface2": "#2a1b23",
    "border": "#3d2630", "accent": "#ff4d6d", "accent2": "#ff758f",
    "green": "#4ade80", "text": "#ffe5ec", "muted": "#a86a7b",
    "dm_color": "#ff8fab", "own_bubble": "#3b1f2a", "own_text": "#ffd6e0",
},
"Amber": {
    "bg": "#1a1205", "surface": "#241807", "surface2": "#2e1f0a",
    "border": "#4d320f", "accent": "#f59e0b", "accent2": "#fbbf24",
    "green": "#84cc16", "text": "#fef3c7", "muted": "#b0892d",
    "dm_color": "#facc15", "own_bubble": "#3a250c", "own_text": "#fde68a",
},
}
THEME_ICONS = {
    "Default":"🟣",
    "Midnight":"🌙",
    "Sunset":"🌅",
    "Forest":"🌿",
    "Ocean":"🌊",
    "Neon":"🟢",
    "Light":"☀️",
    "Cyber":"⚡",
    "Dracula":"🧛",
    "Nord":"❄️",
    "Matrix":"💻",
    "Cherry":"🍒",
    "Amber":"🟠"
}

st.set_page_config(page_title="GChat", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

if "theme" not in st.session_state:
    st.session_state.theme = "Default"
t = THEMES[st.session_state.theme]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

#MainMenu, footer {{visibility: hidden;}}
header[data-testid="stHeader"] {{background-color:rgba(0,0,0,0)!important;visibility:visible!important;display:flex!important;}}
[data-testid="collapsedControl"] {{
    visibility:visible!important;display:flex!important;background:var(--surface2)!important;
    border:1px solid var(--border)!important;border-radius:10px!important;color:var(--text)!important;
    margin:10px!important;transition:all .2s ease!important;z-index:999999!important;
}}
[data-testid="collapsedControl"]:hover {{border-color:var(--accent)!important;transform:scale(1.05);}}
.block-container {{padding-top:1rem!important;}}

/* Prevent flash/flicker on reruns — keep background consistent */
.stApp, .main, .block-container {{transition:none!important;}}
[data-testid="stAppViewContainer"] {{background:var(--bg)!important;}}
/* Suppress Streamlit's built-in skeleton/spinner flash */
[data-testid="stStatusWidget"] {{display:none!important;}}
.stSpinner {{display:none!important;}}

:root {{
    --bg:{t['bg']};--surface:{t['surface']};--surface2:{t['surface2']};
    --border:{t['border']};--accent:{t['accent']};--accent2:{t['accent2']};
    --green:{t['green']};--text:{t['text']};--muted:{t['muted']};
    --dm-color:{t['dm_color']};--own-bubble:{t['own_bubble']};--own-text:{t['own_text']};
}}

.stApp {{background:var(--bg)!important;font-family:'DM Sans',sans-serif;color:var(--text);}}
section[data-testid="stSidebar"] {{background:var(--surface)!important;border-right:1px solid var(--border)!important;}}
section[data-testid="stSidebar"] > div {{padding-top:1.5rem;}}

.gchat-title {{font-family:'Space Mono',monospace;font-size:1.6rem;font-weight:700;color:var(--accent);letter-spacing:-1px;margin-bottom:.2rem;}}
.gchat-sub {{font-size:.72rem;color:var(--muted);font-family:'Space Mono',monospace;letter-spacing:1px;text-transform:uppercase;margin-bottom:1.5rem;}}
.section-label {{font-family:'Space Mono',monospace;font-size:.65rem;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin:1rem 0 .5rem 0;padding-left:2px;}}

.chat-header {{font-family:'Space Mono',monospace;font-size:1rem;font-weight:700;padding:.8rem 0;border-bottom:1px solid var(--border);margin-bottom:1rem;color:var(--text);display:flex;align-items:center;gap:8px;}}
.chat-channel {{color:var(--accent);}} .chat-dm {{color:var(--dm-color);}}

.msg-row {{display:flex;align-items:flex-start;gap:10px;margin-bottom:.8rem;}}
.msg-avatar {{width:34px;height:34px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-family:'Space Mono',monospace;font-size:.75rem;font-weight:700;flex-shrink:0;color:#fff;}}
.msg-body {{flex:1;}}
.msg-sender {{font-size:.82rem;font-weight:600;color:var(--text);margin-bottom:2px;}}
.msg-sender span.ts {{font-size:.68rem;color:var(--muted);font-weight:400;margin-left:8px;font-family:'Space Mono',monospace;}}
.msg-text {{font-size:.9rem;color:#c8cad8;line-height:1.5;background:var(--surface);padding:8px 12px;border-radius:0 10px 10px 10px;display:inline-block;max-width:100%;word-break:break-word;}}
.msg-text.own {{background:var(--own-bubble);border-radius:10px 0 10px 10px;color:var(--own-text);}}

.join-box {{max-width:400px;margin:6rem auto;text-align:center;}}
.join-title {{font-family:'Space Mono',monospace;font-size:2.5rem;color:var(--accent);font-weight:700;letter-spacing:-2px;margin-bottom:.3rem;}}
.join-sub {{color:var(--muted);font-size:.9rem;margin-bottom:2rem;}}

.stTextInput input,.stChatInput textarea {{background:var(--surface2)!important;border:1px solid var(--border)!important;color:var(--text)!important;border-radius:10px!important;font-family:'DM Sans',sans-serif!important;}}
.stTextInput input:focus,.stChatInput textarea:focus {{border-color:var(--accent)!important;box-shadow:0 0 0 2px rgba(100,100,255,.15)!important;}}
.stButton button {{background:var(--accent)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-family:'DM Sans',sans-serif!important;font-weight:600!important;transition:opacity .15s!important;}}
.stButton button:hover {{opacity:.85!important;}}
hr {{border-color:var(--border)!important;margin:1rem 0;}}
.stRadio label {{color:var(--text)!important;font-size:.88rem!important;}}
.stRadio > div {{gap:2px!important;}}

.reaction-bar {{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;}}
.reaction-pill {{display:inline-flex;align-items:center;gap:4px;background:var(--surface2);border:1px solid var(--border);border-radius:20px;padding:3px 10px;font-size:1.3rem;cursor:pointer;transition:background .15s,border-color .15s;line-height:1.4;}}
.reaction-pill:hover {{border-color:var(--accent);background:var(--own-bubble);}}
.reaction-pill.reacted {{border-color:var(--accent);background:var(--own-bubble);}}
.reaction-count {{font-size:.78rem;color:var(--muted);font-family:'Space Mono',monospace;}}

/* Reaction picker buttons — transparent */
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {{
    background:transparent!important;border:none!important;padding:0px 1px!important;
    font-size:1.1rem!important;min-height:unset!important;height:auto!important;
    line-height:1!important;box-shadow:none!important;opacity:.38;
    transition:opacity .12s,transform .12s!important;color:unset!important;
    margin:0!important;min-width:unset!important;
}}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {{opacity:1!important;transform:scale(1.2)!important;background:transparent!important;}}

/* ── Game grid — bigger cells ── */
div[data-testid="stHorizontalBlock"] button[kind="primary"],
div[data-testid="stHorizontalBlock"] button[kind="secondary"].game-cell {{
   min-height:26px!important;
    height:26px!important;
    font-size:0.1rem!important; font-family:'Space Mono',monospace!important;
    border-radius:6px!important; line-height:1.2!important;
    padding:2px 1px!important;
}}

.stat-box {{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:8px 16px;}}
.stat-label {{color:var(--muted);font-size:.65rem;letter-spacing:1px;text-transform:uppercase;}}
.stat-val {{font-size:1.1rem;font-weight:700;color:var(--accent);margin-top:2px;font-family:'Space Mono',monospace;}}
.vote-bar {{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin:8px 0;}}

/* Admin gold name tag */
.admin-name {{color:#ffd700!important;font-weight:700!important;text-shadow:0 0 8px rgba(255,215,0,.4);}}
.admin-badge {{font-size:.65rem;background:linear-gradient(135deg,#b8860b,#ffd700);color:#000;padding:1px 6px;border-radius:4px;font-family:'Space Mono',monospace;font-weight:700;margin-left:6px;vertical-align:middle;}}

/* Delete button for admin */
.delete-btn button {{background:transparent!important;border:none!important;color:#ff6b6b!important;
    font-size:.75rem!important;padding:0 4px!important;min-height:unset!important;height:auto!important;
    opacity:.45;transition:opacity .12s!important;box-shadow:none!important;}}
.delete-btn button:hover {{opacity:1!important;background:rgba(255,107,107,.15)!important;}}

/* Update these sections in your <style> block */

button.game-cell, 
div[data-testid="stHorizontalBlock"] button[kind="primary"],
div[data-testid="stHorizontalBlock"] button[kind="secondary"].game-cell {{
    font-size: 0.65rem !important; 
    height: 30px !important;      /* Keep it short */
    min-height: 30px !important;  /* Keep it short */
    padding: 0px !important;      /* Remove top/bottom padding to keep it slim */
    width: 100% !important;
    line-height: 1 !important;
}}

/* This is the most important part for width */
div[data-testid="stHorizontalBlock"] {{
    gap: 2px !important; /* Tiny gap between buttons means more room for the button itself */
}}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════
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
    con.execute("""CREATE TABLE IF NOT EXISTS land_board (
        cell_id     INTEGER PRIMARY KEY,
        owner       TEXT,
        color       TEXT,
        captured_at REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS player_cash (
        username         TEXT PRIMARY KEY,
        cash             REAL NOT NULL DEFAULT 0,
        last_income_tick REAL NOT NULL DEFAULT 0)""")
    con.execute("""CREATE TABLE IF NOT EXISTS reset_votes (
        username TEXT PRIMARY KEY,
        voted_at REAL NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS accounts (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL)""")
    # Ensure default admin account exists (password: admin)
    con.execute("INSERT OR IGNORE INTO accounts VALUES(?,?)", ("admin", "admin"))
    con.commit(); con.close()

def register_account(username, password):
    """Returns True if registered, False if username taken."""
    con = get_conn()
    existing = con.execute("SELECT 1 FROM accounts WHERE username=?", (username,)).fetchone()
    if existing:
        con.close(); return False
    con.execute("INSERT INTO accounts VALUES(?,?)", (username, password))
    con.commit(); con.close()
    return True

def check_password(username, password):
    """Returns True if credentials match."""
    con = get_conn()
    row = con.execute("SELECT password FROM accounts WHERE username=?", (username,)).fetchone()
    con.close()
    if not row:
        return False
    return row[0] == password

def account_exists(username):
    con = get_conn()
    row = con.execute("SELECT 1 FROM accounts WHERE username=?", (username,)).fetchone()
    con.close()
    return row is not None

def delete_message(msg_id):
    con = get_conn()
    con.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    con.execute("DELETE FROM reactions WHERE msg_id=?", (msg_id,))
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
    con.execute("INSERT INTO messages(sender,recipient,content,ts) VALUES(?,?,?,?)",
                (sender, recipient, content, time.time()))
    con.commit(); con.close()

def get_global_messages(limit=100):
    con = get_conn()
    rows = con.execute(
        "SELECT id,sender,content,ts FROM messages WHERE recipient IS NULL ORDER BY ts DESC LIMIT ?",
        (limit,)).fetchall()
    con.close()
    return list(reversed(rows))

def get_dm_messages(user_a, user_b, limit=100):
    con = get_conn()
    rows = con.execute("""SELECT id,sender,content,ts FROM messages
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
        con.execute("INSERT INTO reactions VALUES(?,?,?)", (msg_id, emoji, username))
    con.commit(); con.close()

def get_reactions(msg_ids):
    if not msg_ids:
        return {}
    con = get_conn()
    rows = con.execute(
        f"SELECT msg_id,emoji,username FROM reactions WHERE msg_id IN ({','.join('?'*len(msg_ids))})",
        msg_ids).fetchall()
    con.close()
    result = {}
    for mid, emoji, uname in rows:
        result.setdefault(mid, {}).setdefault(emoji, []).append(uname)
    return result

# ── Cash helpers ──────────────────────────────────────────────────────────────
def ensure_player(username):
    con = get_conn()
    con.execute("INSERT OR IGNORE INTO player_cash VALUES(?,?,?)",
                (username, STARTING_CASH, time.time()))
    con.commit(); con.close()

def get_cash(username):
    con = get_conn()
    row = con.execute("SELECT cash FROM player_cash WHERE username=?", (username,)).fetchone()
    con.close()
    val = row[0] if row else STARTING_CASH
    # This is the "Live Link" - it saves the value to session state
    st.session_state.my_cash = val
    return val
    
def add_cash(username, amount):
    con = get_conn()
    con.execute("INSERT INTO player_cash(username,cash,last_income_tick) VALUES(?,?,?) "
                "ON CONFLICT(username) DO UPDATE SET cash=cash+?",
                (username, amount, time.time(), amount))
    con.commit(); con.close()

def deduct_cash(username, amount):
    """Returns True if successful, False if insufficient funds."""
    con = get_conn()
    row = con.execute("SELECT cash FROM player_cash WHERE username=?", (username,)).fetchone()
    if not row or row[0] < amount:
        con.close(); return False
    con.execute("UPDATE player_cash SET cash=cash-? WHERE username=?", (amount, username))
    con.commit(); con.close()
    return True

def collect_income(username, board):
    con = get_conn()
    row = con.execute("SELECT last_income_tick, cash FROM player_cash WHERE username=?",
                      (username,)).fetchone()
    if not row:
        con.close(); return 0
    
    last_tick, current_balance = row
    now = time.time()
    
    if now - last_tick < INCOME_INTERVAL:
        con.close(); return 0
        
    # Calculate earnings...
    earned = 0
    for cell_id, cell in board.items():
        if cell["owner"] == username:
            r, c = divmod(cell_id, GRID_COLS)
            earned += cell_income(r, c)
            
    new_cash = current_balance + earned
    con.execute("UPDATE player_cash SET cash=?, last_income_tick=? WHERE username=?",
                (new_cash, now, username))
    con.commit(); con.close()
    
    # Immediately update the UI state
    st.session_state.my_cash = new_cash
    return earned

# ── Board helpers ──────────────────────────────────────────────────────────────
def init_board():
    con = get_conn()
    for i in range(TOTAL_CELLS):
        con.execute("INSERT OR IGNORE INTO land_board VALUES(?,NULL,NULL,NULL)", (i,))
    con.commit(); con.close()

def get_board():
    con = get_conn()
    rows = con.execute("SELECT cell_id,owner,color FROM land_board ORDER BY cell_id").fetchall()
    con.close()
    return {r[0]: {"owner": r[1], "color": r[2]} for r in rows}

def claim_cell(cell_id, username, color):
    con = get_conn()
    con.execute("UPDATE land_board SET owner=?,color=?,captured_at=? WHERE cell_id=?",
                (username, color, time.time(), cell_id))
    con.commit(); con.close()

def reset_board():
    con = get_conn()
    con.execute("UPDATE land_board SET owner=NULL,color=NULL,captured_at=NULL")
    con.execute("DELETE FROM reset_votes")
    con.execute("UPDATE player_cash SET cash=?", (STARTING_CASH,))
    con.commit(); con.close()

def get_territory_counts():
    con = get_conn()
    rows = con.execute(
        "SELECT owner,COUNT(*) FROM land_board WHERE owner IS NOT NULL "
        "GROUP BY owner ORDER BY COUNT(*) DESC").fetchall()
    con.close()
    return rows

# ── Vote-to-reset ──────────────────────────────────────────────────────────────
def cast_reset_vote(username):
    con = get_conn()
    con.execute("INSERT OR REPLACE INTO reset_votes VALUES(?,?)", (username, time.time()))
    con.commit(); con.close()

def remove_reset_vote(username):
    con = get_conn()
    con.execute("DELETE FROM reset_votes WHERE username=?", (username,))
    con.commit(); con.close()

def get_reset_votes():
    con = get_conn()
    rows = con.execute("SELECT username FROM reset_votes").fetchall()
    con.close()
    return [r[0] for r in rows]

# ── Misc helpers ───────────────────────────────────────────────────────────────
AVATAR_COLORS = ["#5b6aff","#ff6b6b","#3ddc97","#ff9f43","#a29bfe",
                 "#fd79a8","#00cec9","#e17055","#74b9ff","#55efc4","#fdcb6e","#b2bec3"]

def avatar_color(name):
    return AVATAR_COLORS[sum(ord(c) for c in name) % len(AVATAR_COLORS)]

def avatar_initials(name):
    parts = name.strip().split()
    return (parts[0][0]+parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

def fmt_time(ts):
    return time.strftime("%I:%M %p", time.localtime(ts)).lstrip("0")

def cost_color(cost):
    """Update this to match your new $25 to $400 scale."""
    # norm = (Current - Min) / (Max - Min)
    norm = min(1.0, (cost - 25) / (400 - 25))
    
    r = int(norm * 200)
    g = int((1 - norm) * 160)
    return f"rgb({r},{g},30)"
    
REACTION_EMOJIS = ["❤️","😂","👍","🔥","😮","😢","🎉","💀"]

def render_messages(messages, me):
    is_admin = me == "admin"
    if not messages:
        st.markdown("<div style='text-align:center;color:#6b7080;font-size:.85rem;"
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
        # Admin gets gold name + badge; others normal
        if sender == "admin":
            sender_html = f'<span class="admin-name">👑 {sender}</span><span class="admin-badge">ADMIN</span>'
        else:
            sender_html = sender
        st.markdown(f"""<div class="msg-row">
            <div class="msg-avatar" style="background:{color if sender != 'admin' else '#b8860b'}">{initials}</div>
            <div class="msg-body">
                <div class="msg-sender">{sender_html}<span class="ts">{fmt_time(ts)}</span></div>
                <div class="{msg_class}">{content}</div>
                {reaction_html}
            </div></div>""", unsafe_allow_html=True)
        # Reaction buttons + optional admin delete button
        if is_admin:
            cols = st.columns([0.25]+[0.32]*len(REACTION_EMOJIS)+[0.8]+[10])
            del_col = cols[len(REACTION_EMOJIS)+1]
        else:
            cols = st.columns([0.25]+[0.32]*len(REACTION_EMOJIS)+[10])
        for i, emoji in enumerate(REACTION_EMOJIS):
            already = me in reactions.get(emoji, [])
            label = f"{emoji}·" if already else emoji
            if cols[i+1].button(label, key=f"react_{msg_id}_{emoji}", help=f"React {emoji}"):
                toggle_reaction(msg_id, emoji, me)
                st.rerun()
        if is_admin:
            with del_col:
                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{msg_id}", help="Delete message (admin)"):
                    delete_message(msg_id)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LAND GAME RENDERER
# ══════════════════════════════════════════════════════════════════════════════
def get_adjacent_cells(cell_id):
    row, col = divmod(cell_id, GRID_COLS)
    adj = []
    if row > 0:           adj.append((row-1)*GRID_COLS+col)
    if row < GRID_ROWS-1: adj.append((row+1)*GRID_COLS+col)
    if col > 0:           adj.append(row*GRID_COLS+col-1)
    if col < GRID_COLS-1: adj.append(row*GRID_COLS+col+1)
    return adj

def player_has_adjacent(cell_id, board, me):
    for adj in get_adjacent_cells(cell_id):
        if board.get(adj, {}).get("owner") == me:
            return True
    return False

def render_land_game(me):
    my_color = avatar_color(me)
    ensure_player(me)
    init_board()

    board = get_board()

    # Passive income tick
    earned = collect_income(me, board)
    if earned > 0:
        st.toast(f"💰 +${earned} income collected!", icon="💰")

    my_cash = get_cash(me)
    territory_counts = get_territory_counts()
    my_cells = sum(1 for c in board.values() if c["owner"] == me)
    total_claimed = sum(1 for c in board.values() if c["owner"])
    pct = round(my_cells / TOTAL_CELLS * 100, 1)
    my_income_rate = sum(cell_income(*divmod(cid, GRID_COLS))
                         for cid, c in board.items() if c["owner"] == me)
    is_leader = bool(territory_counts and territory_counts[0][0] == me)
    leader_tag = f" +${LEADER_BONUS} 👑" if is_leader else ""

    st.markdown('<div class="chat-header">🌍 Land Capture — Expand Your Territory</div>',
                unsafe_allow_html=True)

    # Stats row
    get_cash(me) # This forces an update of st.session_state.my_cash
    sc = st.columns(5)
    sc[0].markdown(f'<div class="stat-box"><div class="stat-label">Your Cash</div>'
                   f'<div class="stat-val">${st.session_state.my_cash:.0f}</div></div>', unsafe_allow_html=True)
    sc[1].markdown(f'<div class="stat-box"><div class="stat-label">Territory</div>'
                   f'<div class="stat-val">{my_cells} cells</div></div>', unsafe_allow_html=True)
    sc[2].markdown(f'<div class="stat-box"><div class="stat-label">Income/tick</div>'
                   f'<div class="stat-val">${my_income_rate}{leader_tag}</div></div>', unsafe_allow_html=True)
    sc[3].markdown(f'<div class="stat-box"><div class="stat-label">World Claimed</div>'
                   f'<div class="stat-val">{total_claimed}/{TOTAL_CELLS}</div></div>', unsafe_allow_html=True)
    sc[4].markdown(f'<div class="stat-box"><div class="stat-label">Your Share</div>'
                   f'<div class="stat-val">{pct}%</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("📖 How to Play"):
        st.markdown(f"""
**Goal:** Own the most valuable territory and accumulate the most cash.

- 🟢 **Start on the outer edge only** (cheap cells, ~$5).
- 💵 **Each cell costs money** — shown on the button. Centre cells cost up to ~$80.
- 🔗 **Expand adjacently** after your first claim.
- ⚔️ **Attack** enemy cells adjacent to yours — costs the same as buying.
- 💰 **Income every {INCOME_INTERVAL}s** — ~10% of each owned cell's cost per tick.
- 👑 **Leader bonus** — the #1 player earns an extra ${LEADER_BONUS}/tick.
- 🗳️ **Vote to reset** — 75% of online players must agree.

**Cell colours:** 🟢 cheap edge → 🟡 mid-range → 🔴 expensive centre
        """)

    # Territory legend
    leg_cols = st.columns(min(len(territory_counts)+1, 7))
    leg_cols[0].markdown('<span style="background:#2a2d3a;color:#aaa;padding:3px 10px;'
                         'border-radius:6px;font-size:.75rem;font-family:monospace;">⬜ Unclaimed</span>',
                         unsafe_allow_html=True)
    for i, (owner, count) in enumerate(territory_counts[:6]):
        col_hex = avatar_color(owner)
        marker = " ← YOU" if owner == me else ""
        leg_cols[i+1].markdown(
            f'<span style="background:{col_hex};color:#fff;padding:3px 10px;border-radius:6px;'
            f'font-size:.75rem;font-family:monospace;">{owner}: {count}{marker}</span>',
            unsafe_allow_html=True)

    st.markdown("---")

    owned_any = my_cells > 0
    action_taken = False

    # ── Grid ──────────────────────────────────────────────────────────────────
    for row in range(GRID_ROWS):
        cols_w = st.columns(GRID_COLS)
        for col in range(GRID_COLS):
            cell_id = row * GRID_COLS + col
            cell = board[cell_id]
            owner = cell["owner"]
            cell_color_hex = cell["color"]
            cost = cell_cost(row, col)
            inc = cell_income(row, col)
            edge = is_edge_cell(row, col)
            affordable = my_cash >= cost
            bg = cost_color(cost)

            if owner is None:
                if not owned_any:
                    can_click = edge
                else:
                    can_click = player_has_adjacent(cell_id, board, me)

                if can_click:
                    label = f"${cost}\n+{inc}"
                    tip = f"Buy: ${cost} | Earns +${inc}/tick"
                    if affordable:
                        if cols_w[col].button(label, key=f"cell_{cell_id}", help=tip,
                                              use_container_width=True):
                            if deduct_cash(me, cost):
                                claim_cell(cell_id, me, my_color)
                                action_taken = True
                    else:
                        # Can't afford — show greyed
                        cols_w[col].markdown(
                            f'<div style="background:#1c1c1c;color:#444;border-radius:6px;'
                            f'text-align:center;padding:6px 2px;font-size:.65rem;'
                            f'font-family:monospace;min-height:26px;line-height:1.3;'
                            f'border:1px dashed #333;">💸<br>${cost}</div>',
                            unsafe_allow_html=True)
                else:
                    # Unreachable unclaimed
                    opacity = "0.30" if not edge and not owned_any else "0.45"
                    cols_w[col].markdown(
                        f'<div style="background:{bg};opacity:{opacity};color:#fff;'
                        f'border-radius:6px;text-align:center;padding:6px 2px;'
                        f'font-size:.6rem;font-family:monospace;min-height:26px;'
                        f'line-height:1.3;">${cost}</div>',
                        unsafe_allow_html=True)

            elif owner == me:
                # Owned by player
                cols_w[col].markdown(
                    f'<div style="background:{my_color};color:#fff;border-radius:6px;'
                    f'text-align:center;padding:6px 2px;font-size:.65rem;'
                    f'font-family:monospace;min-height:26px;line-height:1.3;'
                    f'border:2px solid rgba(255,255,255,.35);">▣<br>+{inc}</div>',
                    unsafe_allow_html=True)

            else:
                # Enemy cell
                if player_has_adjacent(cell_id, board, me):
                    label = f"⚔${cost}"
                    tip = f"Attack! Cost ${cost}"
                    if affordable:
                        if cols_w[col].button(label, key=f"cell_{cell_id}", help=tip,
                                              use_container_width=True):
                            if deduct_cash(me, cost):
                                claim_cell(cell_id, me, my_color)
                                action_taken = True
                    else:
                        cols_w[col].markdown(
                            f'<div style="background:{cell_color_hex};opacity:.45;color:#fff;'
                            f'border-radius:6px;text-align:center;padding:6px 2px;'
                            f'font-size:.6rem;font-family:monospace;min-height:26px;'
                            f'line-height:1.3;border:1px dashed #fff;">💸⚔</div>',
                            unsafe_allow_html=True)
                else:
                    cols_w[col].markdown(
                        f'<div style="background:{cell_color_hex};color:#fff;border-radius:6px;'
                        f'text-align:center;padding:6px 2px;font-size:.65rem;'
                        f'font-family:monospace;min-height:26px;line-height:1.3;'
                        f'opacity:.8;">■<br>+{inc}</div>',
                        unsafe_allow_html=True)

    if action_taken:
        st.rerun()

    st.markdown("---")

    # ── Leaderboard ────────────────────────────────────────────────────────────
    st.markdown("**🏆 Leaderboard**")
    if territory_counts:
        for rank, (owner, count) in enumerate(territory_counts, 1):
            col_hex = avatar_color(owner)
            pct_own = round(count / TOTAL_CELLS * 100, 1)
            cash_val = get_cash(owner)
            marker = " 👈 You" if owner == me else ""
            crown = " 👑" if rank == 1 else ""
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0;">'
                f'<span style="font-family:monospace;color:#888;width:28px;">#{rank}{crown}</span>'
                f'<div style="background:{col_hex};width:12px;height:12px;border-radius:3px;flex-shrink:0;"></div>'
                f'<span style="font-size:.9rem;">{owner}{marker}</span>'
                f'<span style="margin-left:auto;font-family:monospace;font-size:.8rem;color:#888;">'
                f'{count} cells ({pct_own}%) · ${cash_val:.0f}</span>'
                f'</div>',
                unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#6b7080;font-size:.85rem;">No territory yet — claim the edge!</div>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # ── Vote to reset ──────────────────────────────────────────────────────────
    online_users_now = get_online_users()
    n_online = max(1, len(online_users_now))
    votes = get_reset_votes()
    n_votes = len(votes)
    needed = math.ceil(n_online * RESET_VOTE_THRESHOLD)
    already_voted = me in votes

    # Auto-reset if threshold already met
    if n_votes >= needed and n_votes > 0:
        reset_board()
        st.success("✅ Vote passed — board has been reset!")
        st.rerun()

    st.markdown(
        f'<div class="vote-bar"><b>🗳️ Vote to Reset</b>'
        f'<span style="font-family:monospace;font-size:.8rem;color:#888;margin-left:12px;">'
        f'{n_votes}/{n_online} votes · need {needed} (75%)</span></div>',
        unsafe_allow_html=True)

    # Admin gets an instant reset button — no vote needed
    if me == "admin":
        if st.button("⚡ Admin: Reset Board Instantly", key="admin_reset",
                     help="Admin power — resets board immediately without a vote"):
            reset_board()
            st.success("✅ Board reset by admin!")
            st.rerun()

    vc1, vc2 = st.columns([1, 4])
    if already_voted:
        if vc1.button("✅ Withdraw Vote", key="vote_reset"):
            remove_reset_vote(me)
            st.rerun()
        vc2.markdown('<span style="color:#888;font-size:.8rem;line-height:2.5;">You voted to reset.</span>',
                     unsafe_allow_html=True)
    else:
        if vc1.button("🗳️ Vote Reset", key="vote_reset"):
            cast_reset_vote(me)
            st.rerun()

    if votes:
        st.markdown(f'<span style="font-size:.75rem;color:#6b7080;">Voters: {", ".join(votes)}</span>',
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CHAT PANEL HELPER
# ══════════════════════════════════════════════════════════════════════════════
def render_chat_panel(me):
    active_dm = st.session_state.active_dm
    if active_dm:
        st.markdown(f'<div class="chat-header"><span class="chat-dm">⇄ DM</span> · {active_dm}</div>',
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


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
init_db()
for k, v in [("username", None), ("active_dm", None), ("last_msg_id", 0),
             ("active_tab", "game"), ("show_game", True), ("show_chat", True),
             ("side_chat", True)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Join screen ───────────────────────────────────────────────────────────────
if not st.session_state.username:
    st.markdown('<div class="join-box"><div class="join-title">gchat</div>'
                '<div class="join-sub">real-time group messaging</div></div>',
                unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        if "join_mode" not in st.session_state:
            st.session_state.join_mode = "login"

        tab_login, tab_reg = st.tabs(["🔑 Login", "✨ Register"])

        with tab_login:
            li_name = st.text_input("Username", placeholder="e.g. cooluser42",
                                    max_chars=24, key="li_name")
            li_pass = st.text_input("Password", type="password", key="li_pass")
            if st.button("Login →", use_container_width=True, key="li_btn"):
                name = li_name.strip()
                pw = li_pass.strip()
                if not name or not pw:
                    st.error("Please enter username and password.")
                elif not account_exists(name):
                    st.error("Account not found. Register first.")
                elif not check_password(name, pw):
                    st.error("Incorrect password.")
                else:
                    st.session_state.username = name
                    ensure_player(name)
                    heartbeat(name)
                    st.rerun()

        with tab_reg:
            reg_name = st.text_input("Choose a username", placeholder="e.g. cooluser42",
                                     max_chars=24, key="reg_name")
            reg_pass = st.text_input("Choose a password", type="password", key="reg_pass")
            reg_pass2 = st.text_input("Confirm password", type="password", key="reg_pass2")
            if st.button("Create Account →", use_container_width=True, key="reg_btn"):
                name = reg_name.strip()
                pw = reg_pass.strip()
                pw2 = reg_pass2.strip()
                if not name or not pw:
                    st.error("Please fill in all fields.")
                elif name.lower() == "admin":
                    st.error("That username is reserved.")
                elif len(name) < 2:
                    st.error("Name must be at least 2 characters.")
                elif pw != pw2:
                    st.error("Passwords don't match.")
                elif len(pw) < 4:
                    st.error("Password must be at least 4 characters.")
                elif not register_account(name, pw):
                    st.error("Username already taken.")
                else:
                    st.session_state.username = name
                    ensure_player(name)
                    heartbeat(name)
                    st.rerun()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
me = st.session_state.username
heartbeat(me)
ensure_player(me)

current_id = get_last_msg_id()
if current_id != st.session_state.last_msg_id:
    st.session_state.last_msg_id = current_id

online_users = get_online_users()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="gchat-title">gchat</div>', unsafe_allow_html=True)
    if me == "admin":
        st.markdown(f'<div class="gchat-sub"><span style="color:#ffd700;font-weight:700;">👑 {me}</span> <span style="background:linear-gradient(135deg,#b8860b,#ffd700);color:#000;padding:1px 6px;border-radius:4px;font-size:.6rem;font-family:Space Mono,monospace;font-weight:700;">ADMIN</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="gchat-sub">logged in as {me}</div>', unsafe_allow_html=True)

    # ── DM / channel nav ─────────────────────────────────────────────────────
    st.markdown('<div class="section-label">💬 Chat</div>', unsafe_allow_html=True)
    if st.button("# global", use_container_width=True, key="global_btn"):
        st.session_state.active_dm = None; st.rerun()
    st.markdown('<div class="section-label">🟢 Online Now</div>', unsafe_allow_html=True)
    others = [u for u in online_users if u != me]
    if not others:
        st.markdown('<div style="color:#6b7080;font-size:.82rem;padding-left:4px;">No one else online</div>',
                    unsafe_allow_html=True)
    else:
        for user in others:
            if st.button(f"💬 {user}", key=f"dm_{user}", use_container_width=True):
                st.session_state.active_dm = user; st.rerun()

    st.markdown("---")

    # Theme picker
    st.markdown('<div class="section-label">🎨 Theme</div>', unsafe_allow_html=True)
    theme_names = list(THEMES.keys())
    theme_labels = [f"{THEME_ICONS[n]}  {n}" for n in theme_names]
    current_idx = theme_names.index(st.session_state.theme)
    selected_label = st.radio("theme_radio", theme_labels, index=current_idx,
                               label_visibility="collapsed")
    selected_name = theme_names[theme_labels.index(selected_label)]
    if selected_name != st.session_state.theme:
        st.session_state.theme = selected_name; st.rerun()

    st.markdown("---")
    st.markdown(f'<div style="color:#6b7080;font-size:.75rem;font-family:Space Mono,monospace;">'
                f'{len(online_users)} online</div>', unsafe_allow_html=True)

    if st.button("Leave GChat", key="leave"):
        con = get_conn()
        con.execute("DELETE FROM presence WHERE username=?", (me,))
        con.commit(); con.close()
        st.session_state.username = None
        st.session_state.active_dm = None
        st.session_state.active_tab = "chat"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT ROUTING — always split screen (game left, chat right)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""<style>
button[title="View fullscreen"],[data-testid="StyledFullScreenButton"]{display:none!important;}
</style>""", unsafe_allow_html=True)

# 1. Update the local cash variable from the DB at the start of every "pulse"
my_cash = get_cash(me) 

# 2. Render the Split Screen Layout
game_col, chat_col = st.columns(2)

with game_col:
    # We simply render the game; the 'my_cash' variable inside is now 
    # being updated by the global pulse below.
    render_land_game(me)

with chat_col:
    render_chat_panel(me)

# ══════════════════════════════════════════════════════════════════════════════
# THE REFRESH ENGINE (The "Pulse")
# ══════════════════════════════════════════════════════════════════════════════
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Calculate how long since the last database fetch
time_since_last = time.time() - st.session_state.last_refresh

if time_since_last >= 3:
    # 3 seconds have passed: Reset timer and rerun to pull new cash/income
    st.session_state.last_refresh = time.time()
    st.rerun()
else:
    # Less than 3 seconds: Wait 1 second and check again.
    # This keeps the app alive and responsive without lagging the server.
    time.sleep(1)
    st.rerun()
