import streamlit as st

# 1. Setup Session State (The App's Brain)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_with" not in st.session_state:
    st.session_state.chat_with = "Global Chat"
if "theme" not in st.session_state:
    st.session_state.theme = "Midnight"

# 2. Themes
THEMES = {
    "Midnight": {"bg": "#000000", "text": "#ffffff", "side": "#1c1c1e", "acc": "#0b84ff", "rec": "#262629"},
    "Emerald": {"bg": "#0a1f1a", "text": "#e0f2f1", "side": "#122e28", "acc": "#2dcf8e", "rec": "#1b4332"},
    "Classic": {"bg": "#ffffff", "text": "#000000", "side": "#f2f2f7", "acc": "#007aff", "rec": "#e9e9eb"}
}
t = THEMES[st.session_state.theme]

# 3. CSS (Fixed for Visibility)
st.markdown(f"""
<style>
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    [data-testid="stSidebar"] {{ background-color: {t['side']} !important; }}
    
    .bubble {{ 
        padding: 12px 16px; border-radius: 20px; margin: 5px 0; 
        max-width: 70%; font-family: sans-serif; display: inline-block;
    }}
    .sent {{ background-color: {t['acc']}; color: white; float: right; clear: both; }}
    .received {{ background-color: {t['rec']}; color: {t['text']}; float: left; clear: both; }}
    
    .big-emoji {{ font-size: 50px; cursor: pointer; }}
    
    /* Fix Input Box */
    .stChatInput textarea {{
        background-color: {t['rec']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['acc']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# 4. Login Screen
if st.session_state.username is None:
    st.title("GChat")
    user_input = st.text_input("Enter Username:")
    if st.button("Start Chatting"):
        if user_input:
            st.session_state.username = user_input
            st.rerun()
    st.stop()

# 5. Sidebar
with st.sidebar:
    st.header(f"👤 {st.session_state.username}")
    
    # Theme Switcher
    new_theme = st.selectbox("Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme))
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.write("---")
    if st.button("🌎 Global Chat", use_container_width=True):
        st.session_state.chat_with = "Global Chat"
        st.rerun()

    st.subheader("Mega Reactions")
    reacts = ["😂", "💀", "🔥", "💯", "🫡", "👀", "❤️", "✅", "❌"]
    cols = st.columns(3)
    for i, emoji in enumerate(reacts):
        if cols[i % 3].button(emoji):
            st.session_state.messages.append({
                "from": st.session_state.username,
                "to": st.session_state.chat_with,
                "content": emoji,
                "is_react": True
            })
            st.rerun()

# 6. Chat Area
st.subheader(f"To: {st.session_state.chat_with}")

# Display Messages
for m in st.session_state.messages:
    # DM Logic: Show if Global OR if it's between current users
    is_me = m["from"] == st.session_state.username
    show = False
    if st.session_state.chat_with == "Global Chat" and m["to"] == "Global Chat":
        show = True
    elif (m["to"] == st.session_state.chat_with and m["from"] == st.session_state.username) or \
         (m["from"] == st.session_state.chat_with and m["to"] == st.session_state.username):
        show = True

    if show:
        style = "sent" if is_me else "received"
        if m.get("is_react"):
            align = "right" if is_me else "left"
            st.markdown(f'<div style="text-align:{align};" class="big-emoji">{m["content"]}</div>', unsafe_allow_html=True)
        else:
            # Show name for received messages
            if not is_me:
                st.markdown(f'<div style="font-size:10px; margin-left:10px;">{m["from"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="bubble {style}">{m["content"]}</div><div style="clear:both;"></div>', unsafe_allow_html=True)

# 7. Input
if prompt := st.chat_input(f"Message {st.session_state.chat_with}..."):
    st.session_state.messages.append({
        "from": st.session_state.username,
        "to": st.session_state.chat_with,
        "content": prompt,
        "is_react": False
    })
    st.rerun()
    # to run type python -m streamlit run chat.py
