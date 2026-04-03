import streamlit as st

# 1. Page Configuration
st.set_page_config(page_title="GChat", layout="wide")

# 2. State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_with" not in st.session_state:
    st.session_state.chat_with = "Global Chat"
if "theme_name" not in st.session_state:
    st.session_state.theme_name = "Midnight"
if "online_players" not in st.session_state:
    st.session_state.online_players = set()

# 3. Theme Definitions
THEMES = {
    "Midnight": {"bg": "#000000", "side": "#1c1c1e", "text": "#ffffff", "rec": "#262629", "accent": "#0b84ff"},
    "Classic": {"bg": "#ffffff", "side": "#f2f2f7", "text": "#000000", "rec": "#e9e9eb", "accent": "#007aff"},
    "Emerald": {"bg": "#0a1f1a", "side": "#122e28", "text": "#e0f2f1", "rec": "#1b4332", "accent": "#2dcf8e"},
    "Rose": {"bg": "#1f1014", "side": "#2d161c", "text": "#ffebee", "rec": "#4a252f", "accent": "#ff375f"}
}

t = THEMES[st.session_state.theme_name]

# 4. CSS Injection
st.markdown(f"""
<style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    [data-testid="stSidebar"] {{ background-color: {t['side']} !important; border-right: 1px solid {t['rec']}; }}
    
    .gchat-header {{ text-align: center; font-size: 26px; font-weight: 800; color: {t['accent']}; margin-bottom: 20px; }}
    
    .bubble-container {{ display: flex; flex-direction: column; width: 100%; margin: 4px 0; }}
    .bubble {{ padding: 12px 16px; border-radius: 20px; max-width: 75%; font-family: -apple-system, sans-serif; }}
    .sent {{ background-color: {t['accent']}; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }}
    .received {{ background-color: {t['rec']}; color: {t['text']}; align-self: flex-start; border-bottom-left-radius: 4px; }}
    
    /* BIG EMOJI REACTION STYLE */
    .big-emoji {{ font-size: 50px; line-height: 1; margin: 10px 0; }}
    
    /* Sidebar Button Contrast */
    .stButton button {{
        background-color: {t['rec']} !important;
        color: {t['text']} !important;
        border: 1px solid transparent !important;
    }}
    .stButton button:hover {{
        border: 1px solid {t['accent']} !important;
    }}

    input[type="text"], .stChatInput textarea {{
        background-color: {t['rec']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['accent']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# 5. Login
if "username" not in st.session_state:
    st.markdown('<div class="gchat-header">GChat</div>', unsafe_allow_html=True)
    u_input = st.text_input("Username:", placeholder="Who are you?")
    if st.button("Sign In"):
        if u_input:
            st.session_state.username = u_input
            st.rerun()
    st.stop()

# 6. Sidebar
with st.sidebar:
    st.markdown('<div class="gchat-header">GChat</div>', unsafe_allow_html=True)
    
    # Theme Selection (Instant Update)
    choice = st.selectbox("Appearance", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme_name))
    if choice != st.session_state.theme_name:
        st.session_state.theme_name = choice
        st.rerun()
    
    st.write("---")
    if st.button("🌎 Global Chat", use_container_width=True):
        st.session_state.chat_with = "Global Chat"
        st.rerun()
        
    st.subheader("Mega Reactions")
    # expanded reaction list
    react_list = [
        "😂", "💀", "🔥", "💯", "🫡", "👀", 
        "✅", "❌", "🤔", "👎", "👍", "❤️",
        "🎉", "🚀", "🤡", "🤫", "😤", "🫠"
    ]
    
    cols = st.columns(3)
    for i, emoji in enumerate(react_list):
        if cols[i % 3].button(emoji, key=f"react_{i}"):
            st.session_state.messages.append({
                "from": st.session_state.username,
                "to": st.session_state.chat_with,
                "content": emoji,
                "is_reaction": True
            })
            st.rerun()

# 7. Main Chat UI
st.subheader(f"To: {st.session_state.chat_with}")

for m in st.session_state.messages:
    is_me = m["from"] == st.session_state.username
    # Filter logic
    show = False
    if st.session_state.chat_with == "Global Chat" and m["to"] == "Global Chat":
        show = True
    elif (m["to"] == st.session_state.chat_with and m["from"] == st.session_state.username) or \
         (m["from"] == st.session_state.chat_with and m["to"] == st.session_state.username):
        show = True

    if show:
        div_class = "sent" if is_me else "received"
        if not is_me:
            st.markdown(f'<div style="font-size:10px; color:{t["accent"]}; margin-left:10px;">{m["from"]}</div>', unsafe_allow_html=True)
        
        # Check if it's a reaction to show it BIG
        if m.get("is_reaction"):
            align = "flex-end" if is_me else "flex-start"
            st.markdown(f'<div style="display:flex; justify-content:{align};"><div class="big-emoji">{m["content"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bubble-container"><div class="bubble {div_class}">{m["content"]}</div></div>', unsafe_allow_html=True)

# 8. Send Message
if prompt := st.chat_input(f"Message {st.session_state.chat_with}"):
    st.session_state.messages.append({
        "from": st.session_state.username,
        "to": st.session_state.chat_with,
        "content": prompt,
        "is_reaction": False
    })
    st.rerun()
    # to run type python -m streamlit run chat.py