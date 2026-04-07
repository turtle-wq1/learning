import streamlit as st
import sqlite3
import time
import math

DB = "gchat.db"

# ─── Grid config ──────────────────────────────────────────────────────────────
GRID_ROWS = 12
GRID_COLS = 16
TOTAL_CELLS = GRID_ROWS * GRID_COLS
INCOME_INTERVAL = 30
LEADER_BONUS = 15
STARTING_CASH = 100
RESET_VOTE_THRESHOLD = 0.75

# ─── Cell cost / income helpers ───────────────────────────────────────────────
def cell_cost(row, col):
    cx = (GRID_COLS - 1) / 2
    cy = (GRID_ROWS - 1) / 2
    dist = math.sqrt((col - cx) ** 2 + (row - cy) ** 2)
    max_dist = math.sqrt(cx ** 2 + cy ** 2)
    norm = dist / max_dist
    return max(5, round((1 - norm) * 75 + 5))

def cell_income(row, col):
    return max(1, round(cell_cost(row, col) * 0.10))

def is_edge_cell(row, col):
    return row == 0 or row == GRID_ROWS - 1 or col == 0 or col == GRID_COLS - 1

# ─── Themes ───────────────────────────────────────────────────────────────────
THEMES = {
    "Default": {"bg": "#0e0f14", "surface": "#16181f", "surface2": "#1e2029", "border": "#2a2d3a", "accent": "#5b6aff", "accent2": "#ff6b6b", "green": "#3ddc97", "text": "#e8eaf0", "muted": "#6b7080", "dm_color": "#ff9f43", "own_bubble": "#1e2350", "own_text": "#d0d4f5"},
    "Midnight": {"bg": "#0d0b1a", "surface": "#13112a", "surface2": "#1c1940", "border": "#2e2a50", "accent": "#a78bfa", "accent2": "#f472b6", "green": "#34d399", "text": "#ede9fe", "muted": "#7c6fa0", "dm_color": "#f472b6", "own_bubble": "#231e4a", "own_text": "#c4b5fd"},
    "Sunset": {"bg": "#160d0a", "surface": "#1f1210", "surface2": "#2a1a16", "border": "#3d2520", "accent": "#fb923c", "accent2": "#f43f5e", "green": "#4ade80", "text": "#fef3ee", "muted": "#9a6a5a", "dm_color": "#fbbf24", "own_bubble": "#3b1f10", "own_text": "#fed7aa"},
    "Forest": {"bg": "#080f0a", "surface": "#0e1a10", "surface2": "#152318", "border": "#1e3524", "accent": "#4ade80", "accent2": "#34d399", "green": "#86efac", "text": "#ecfdf5", "muted": "#4d7a5a", "dm_color": "#fbbf24", "own_bubble": "#0f2e18", "own_text": "#bbf7d0"},
    "Ocean": {"bg": "#060e14", "surface": "#0b1520", "surface2": "#101e2c", "border": "#1a3040", "accent": "#22d3ee", "accent2": "#38bdf8", "green": "#4ade80", "text": "#ecfeff", "muted": "#4a7a8a", "dm_color": "#818cf8", "own_bubble": "#0c2233", "own_text": "#a5f3fc"}
}
THEME_ICONS = {"Default":"🟣","Midnight":"🌙","Sunset":"🌅","Forest":"🌿","Ocean":"🌊"}

# ─── Page Config (Stealth Mode) ──────────────────────────────────────────────
st.set_page_config(page_title="Classes", page_icon="https://vignette.wikia.nocookie.net/logopedia/images/d/d5/Google_Classroom_2020.svg/revision/latest?cb=20201015124036", layout="wide", initial_sidebar_state="expanded")

if "theme" not in st.session_state:
    st.session_state.theme = "Default"
t = THEMES[st.session_state.theme]

# ─── CSS Styles ──────────────────────────────────────────────────────────────
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

:root {{
    --bg:{t['bg']};--surface:{t['surface']};--surface2:{t['surface2']};
    --border:{t['border']};--accent:{t['accent']};--accent2:{t['accent2']};
    --green:{t['green']};--text:{t['text']};--muted:{t['muted']};
    --dm-color:{t['dm_color']};--own-bubble:{t['own_bubble']};--own-text:{t['own_text']};
}}

.stApp {{background:var(--bg)!important;font-family:'DM Sans',sans-serif;color:var(--text);}}
section[data-testid="stSidebar"] {{background:var(--surface)!important;border-right:1px solid var(--border)!important;}}
.msg-text {{font-size:.9rem;color:#c8cad8;line-height:1.5;background:var(--surface);padding:8px 12px;border-radius:0 10px 10px 10px;display:inline-block;max-width:100%;word-break:break-word;}}
.msg-text.own {{background:var(--own-bubble);border-radius:10px 0 10px 10px;color:var(--own-text);}}

/* Stealth Overlay */
.fake-classroom {{
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
    background-color: white; background-image: url('https://magicschool.ai/images/google-classroom-screenshot.png');
    background-size: cover; background-position: center; z-index: 9999999;
}}
.hidden-btn {{ display: none !important; }}

/* Admin UI */
.admin-name {{ color: #FFD700 !important; font-weight: bold; text-shadow: 0 0 8px rgba(255,215,0,0.4); }}
</style>
""", unsafe_allow_html=True)

# ─── Database Logic ──────────────────────────────────────────────────────────
def get_conn(): return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    con = get_conn()
    con.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, recipient TEXT, content TEXT, ts REAL)")
    con.execute("CREATE TABLE IF NOT EXISTS presence (username TEXT PRIMARY KEY, last_seen REAL)")
    con.execute("CREATE TABLE IF NOT EXISTS reactions (msg_id INTEGER, emoji TEXT, username TEXT, PRIMARY KEY (msg_id, emoji, username))")
    con.execute("CREATE TABLE IF NOT EXISTS land_board (cell_id INTEGER PRIMARY KEY, owner TEXT, color TEXT, captured_at REAL)")
    con.execute("CREATE TABLE IF NOT EXISTS player_cash (username TEXT PRIMARY KEY, password TEXT, cash REAL DEFAULT 100, last_income_tick REAL DEFAULT 0)")
    con.execute("CREATE TABLE IF NOT EXISTS reset_votes (username TEXT PRIMARY KEY, voted_at REAL)")
    con.commit(); con.close()

def ensure_player(username, password=None):
    con = get_conn()
    row = con.execute("SELECT password FROM player_cash WHERE username=?", (username,)).fetchone()
    if not row:
        con.execute("INSERT INTO player_cash (username, password, cash, last_income_tick) VALUES (?,?,?,?)", (username, password, STARTING_CASH, time.time()))
        con.commit(); con.close(); return True
    con.close(); return row[0] == password

def delete_message(msg_id):
    con = get_conn(); con.execute("DELETE FROM messages WHERE id=?", (msg_id,)); con.commit(); con.close()

# (Include all your other existing DB helper functions here: get_online_users, send_message, etc.)
# ... [Keeping original DB functions for brevity] ...

def heartbeat(username):
    con = get_conn(); con.execute("INSERT OR REPLACE INTO presence VALUES (?,?)", (username, time.time())); con.commit(); con.close()

def get_online_users(timeout=15):
    con = get_conn(); rows = con.execute("SELECT username FROM presence WHERE last_seen > ?", (time.time() - timeout,)).fetchall(); con.close()
    return [r[0] for r in rows]

def send_message(sender, content, recipient=None):
    con = get_conn(); con.execute("INSERT INTO messages(sender,recipient,content,ts) VALUES(?,?,?,?)", (sender, recipient, content, time.time())); con.commit(); con.close()

def get_global_messages(limit=100):
    con = get_conn(); rows = con.execute("SELECT id,sender,content,ts FROM messages WHERE recipient IS NULL ORDER BY ts DESC LIMIT ?", (limit,)).fetchall(); con.close()
    return list(reversed(rows))

def get_last_msg_id():
    con = get_conn(); row = con.execute("SELECT MAX(id) FROM messages").fetchone(); con.close(); return row[0] or 0

def get_cash(username):
    con = get_conn(); row = con.execute("SELECT cash FROM player_cash WHERE username=?", (username,)).fetchone(); con.close(); return row[0] if row else STARTING_CASH

def collect_income(username, board):
    con = get_conn(); row = con.execute("SELECT last_income_tick FROM player_cash WHERE username=?", (username,)).fetchone()
    if not row or (time.time() - row[0] < INCOME_INTERVAL): con.close(); return 0
    earned = sum(cell_income(*divmod(cid, GRID_COLS)) for cid, c in board.items() if c["owner"] == username)
    con.execute("UPDATE player_cash SET cash=cash+?, last_income_tick=? WHERE username=?", (earned, time.time(), username)); con.commit(); con.close(); return earned

def deduct_cash(username, amount):
    con = get_conn(); row = con.execute("SELECT cash FROM player_cash WHERE username=?", (username,)).fetchone()
    if not row or row[0] < amount: con.close(); return False
    con.execute("UPDATE player_cash SET cash=cash-? WHERE username=?", (amount, username)); con.commit(); con.close(); return True

def init_board():
    con = get_conn()
    for i in range(TOTAL_CELLS): con.execute("INSERT OR IGNORE INTO land_board VALUES(?,NULL,NULL,NULL)", (i,))
    con.commit(); con.close()

def get_board():
    con = get_conn(); rows = con.execute("SELECT cell_id,owner,color FROM land_board ORDER BY cell_id").fetchall(); con.close()
    return {r[0]: {"owner": r[1], "color": r[2]} for r in rows}

def claim_cell(cell_id, username, color):
    con = get_conn(); con.execute("UPDATE land_board SET owner=?,color=?,captured_at=? WHERE cell_id=?", (username, color, time.time(), cell_id)); con.commit(); con.close()

def reset_board():
    con = get_conn(); con.execute("UPDATE land_board SET owner=NULL,color=NULL,captured_at=NULL"); con.execute("DELETE FROM reset_votes"); con.execute("UPDATE player_cash SET cash=?", (STARTING_CASH,)); con.commit(); con.close()

def avatar_color(name):
    COLORS = ["#5b6aff","#ff6b6b","#3ddc97","#ff9f43","#a29bfe"]
    return "#D4AF37" if name.lower() == "admin" else COLORS[sum(ord(c) for c in name) % len(COLORS)]

def avatar_initials(name): return name[:2].upper()
def fmt_time(ts): return time.strftime("%I:%M %p", time.localtime(ts)).lstrip("0")
def cost_color(cost):
    norm = min(1.0, (cost - 5) / 75)
    return f"rgb({int(norm * 200)},{int((1 - norm) * 160)},30)"

# ─── Chat Rendering ──────────────────────────────────────────────────────────
def render_messages(messages, me):
    if not messages: st.write("No messages yet."); return
    for msg_id, sender, content, ts in messages:
        is_msg_admin = sender.lower() == "admin"
        name_class = "admin-name" if is_msg_admin else ""
        st.markdown(f"""<div style="display:flex; gap:10px; margin-bottom:10px;">
            <div style="background:{avatar_color(sender)}; width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center; color:white; font-weight:bold;">{avatar_initials(sender)}</div>
            <div><div class="{name_class}">{sender} <span style="color:gray; font-size:0.7rem;">{fmt_time(ts)}</span></div>
            <div class="{'msg-text own' if sender == me else 'msg-text'}">{content}</div></div></div>""", unsafe_allow_html=True)
        if me.lower() == "admin":
            if st.button("🗑️", key=f"del_{msg_id}"): delete_message(msg_id); st.rerun()

# ─── Main App Logic ──────────────────────────────────────────────────────────
init_db()
if "username" not in st.session_state: st.session_state.username = None
if "undercover" not in st.session_state: st.session_state.undercover = False

# Join Screen
if not st.session_state.username:
    st.markdown("<h1 style='text-align:center;'>Classes Login</h1>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Enter"):
            if u and p and ensure_player(u, p):
                st.session_state.username = u; st.rerun()
            else: st.error("Invalid credentials.")
    st.stop()

me = st.session_state.username
heartbeat(me)

# Panic Button (F Key)
if st.button("panic_trigger", key="panic_btn", help=""):
    st.session_state.undercover = not st.session_state.undercover; st.rerun()

st.markdown("""<script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key.toLowerCase() === 'f') {
            const btns = doc.querySelectorAll('button');
            for (const b of btns) { if (b.innerText === "panic_trigger") b.click(); }
        }
    });
</script>""", unsafe_allow_html=True)

if st.session_state.undercover:
    st.markdown('<div class="fake-classroom"></div>', unsafe_allow_html=True); st.stop()

# ─── Sidebar Navigation ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("Classes")
    tab = st.radio("Nav", ["Chat", "Land Game"])
    if st.button("Logout"): st.session_state.username = None; st.rerun()
    if me.lower() == "admin":
        st.divider()
        if st.button("☢️ RESET WORLD"): reset_board(); st.rerun()

# ─── Game Rendering (With Scroll Fix) ────────────────────────────────────────
if tab == "Land Game":
    init_board()
    board = get_board()
    collect_income(me, board)
    
    # Wrap in a container to fix split-screen ghosting
    main_view = st.container()
    with main_view:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"Territory - ${get_cash(me)}")
            # [Insert your existing GRID loop here from the previous code]
            # Shortened for space:
            for r in range(GRID_ROWS):
                cols = st.columns(GRID_COLS)
                for c in range(GRID_COLS):
                    cid = r * GRID_COLS + c
                    cell = board[cid]
                    if cols[c].button(f"${cell_cost(r,c)}", key=f"c_{cid}"):
                        if deduct_cash(me, cell_cost(r,c)): claim_cell(cid, me, avatar_color(me)); st.rerun()
        with col2:
            st.subheader("Live Chat")
            render_messages(get_global_messages(), me)
            if prompt := st.chat_input("Msg..."): send_message(me, prompt); st.rerun()
    
    time.sleep(1); st.rerun()

else:
    render_messages(get_global_messages(), me)
    if prompt := st.chat_input("Message..."): send_message(me, prompt); st.rerun()
    time.sleep(2); st.rerun()
