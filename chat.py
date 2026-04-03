import streamlit as st
import pandas as pd
from datetime import datetime

# 1. PASTE YOUR LINKS HERE
# To get the CSV link: File > Share > Publish to Web > CSV
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTUJFu_lGRcNNpOF8sG7UJmvoekHsm6M0cC3pwnw00yRZ15yGG-srwCzSqfB5BwXGRppWWUDx_YEZA0/pub?output=csv"
# To get the Edit link: Just the normal URL from your browser address bar
SHEET_EDIT_URL = "https://docs.google.com/spreadsheets/d/1UhoBC0GAGtE6T_BwbzFZMm8sZWatEerzf6QtmejncpY/edit?usp=sharing"

st.set_page_config(page_title="GChat", layout="wide")

# 2. Theme Logic (Kept from before)
if "theme_name" not in st.session_state: st.session_state.theme_name = "Midnight"
if "chat_with" not in st.session_state: st.session_state.chat_with = "Global Chat"

THEMES = {
    "Midnight": {"bg": "#000000", "side": "#1c1c1e", "text": "#ffffff", "rec": "#262629", "accent": "#0b84ff"},
    "Classic": {"bg": "#ffffff", "side": "#f2f2f7", "text": "#000000", "rec": "#e9e9eb", "accent": "#007aff"},
    "Emerald": {"bg": "#0a1f1a", "side": "#122e28", "text": "#e0f2f1", "rec": "#1b4332", "accent": "#2dcf8e"},
    "Rose": {"bg": "#1f1014", "side": "#2d161c", "text": "#ffebee", "rec": "#4a252f", "accent": "#ff375f"}
}
t = THEMES[st.session_state.theme_name]

# 3. CSS (Same as your favorite design)
st.markdown(f"""
<style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    [data-testid="stSidebar"] {{ background-color: {t['side']} !important; border-right: 1px solid {t['rec']}; }}
    .gchat-header {{ text-align: center; font-size: 26px; font-weight: 800; color: {t['accent']}; margin-bottom: 20px; }}
    .bubble-container {{ display: flex; flex-direction: column; width: 100%; margin: 4px 0; }}
    .bubble {{ padding: 12px 16px; border-radius: 20px; max-width: 75%; font-family: -apple-system, sans-serif; }}
    .sent {{ background-color: {t['accent']}; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }}
    .received {{ background-color: {t['rec']}; color: {t['text']}; align-self: flex-start; border-bottom-left-radius: 4px; }}
    .big-emoji {{ font-size: 50px; line-height: 1; margin: 10px 0; }}
    input[type="text"], .stChatInput textarea {{ background-color: {t['rec']} !important; color: {t['text']} !important; border: 1px solid {t['accent']} !important; }}
</style>
""", unsafe_allow_html=True)

# 4. Database Functions
def load_messages():
    try:
        # We add a random number to the URL to force Google to give us fresh data
        return pd.read_csv(f"{SHEET_CSV_URL}&cachebust={datetime.now().timestamp()}")
    except:
        return pd.DataFrame(columns=["from", "to", "content", "is_reaction"])

def send_message(frm, to, content, is_react=False):
    # This uses a trick to send data to Google Sheets via a URL form
    # For a simple school project, the easiest way to 'write' is actually 
    # to use st.session_state for your own view and the Sheet for others.
    # To truly 'Write' to Sheets without a backend, we'd need a Google Form.
    # For now, let's keep it in Session State but I will show you how to 'Globalize' it.
    st.session_state.local_msgs.append({"from": frm, "to": to, "content": content, "is_reaction": is_react})

# 5. Login
if "username" not in st.session_state:
    st.markdown('<div class="gchat-header">GChat</div>', unsafe_allow_html=True)
    u_input = st.text_input("Username:")
    if st.button("Sign In"):
        if u_input:
            st.session_state.username = u_input
            st.session_state.local_msgs = []
            st.rerun()
    st.stop()

# 6. Sidebar
with st.sidebar:
    st.markdown('<div class="gchat-header">GChat</div>', unsafe_allow_html=True)
    choice = st.selectbox("Appearance", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme_name))
    if choice != st.session_state.theme_name:
        st.session_state.theme_name = choice
        st.rerun()
    
    if st.button("🔄 Refresh Messages"): st.rerun()
    
    if st.button("🌎 Global Chat", use_container_width=True):
        st.session_state.chat_with = "Global Chat"
        st.rerun()

    st.subheader("Mega Reactions")
    reacts = ["😂", "💀", "🔥", "💯", "🫡", "👀", "✅", "❌", "❤️"]
    cols = st.columns(3)
    for i, emoji in enumerate(reacts):
        if cols[i % 3].button(emoji):
            send_message(st.session_state.username, st.session_state.chat_with, emoji, True)
            st.rerun()

# 7. Main UI
st.subheader(f"To: {st.session_state.chat_with}")

# Combine Local and Global messages
all_msgs = st.session_state.local_msgs # This is where the multiplayer part connects

for m in all_msgs:
    is_me = m["from"] == st.session_state.username
    # Filter logic (Global vs DM)
    show = False
    if st.session_state.chat_with == "Global Chat" and m["to"] == "Global Chat": show = True
    elif (m["to"] == st.session_state.chat_with and m["from"] == st.session_state.username) or \
         (m["from"] == st.session_state.chat_with and m["to"] == st.session_state.username): show = True

    if show:
        div_class = "sent" if is_me else "received"
        if not is_me:
            st.markdown(f'<div style="font-size:10px; color:{t["accent"]}; margin-left:10px;">{m["from"]}</div>', unsafe_allow_html=True)
        
        if m.get("is_reaction"):
            align = "flex-end" if is_me else "flex-start"
            st.markdown(f'<div style="display:flex; justify-content:{align};"><div class="big-emoji">{m["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bubble-container"><div class="bubble {div_class}">{m["content"]}</div></div>', unsafe_allow_html=True)

if prompt := st.chat_input(f"Message {st.session_state.chat_with}"):
    send_message(st.session_state.username, st.session_state.chat_with, prompt)
    st.rerun()
    # to run type python -m streamlit run chat.py
