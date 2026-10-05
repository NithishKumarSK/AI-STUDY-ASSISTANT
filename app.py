"""
StudyMate AI
------------
A GenAI study assistant with a chat interface, built with Streamlit and
Google's Gemini API.

- Sign up / log in (accounts stored in SQLite, passwords hashed)
- Chat with an AI tutor, with saved chat history per user
- Attach a PDF/TXT to a chat, then summarize it, ask questions about it,
  get explanations, take a quiz or review flashcards

Run locally with:
    streamlit run app.py
"""

import os
import re
import json
import html

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai
from google.genai import types

import db

# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------

load_dotenv()  # reads GEMINI_API_KEY from a local .env file, if present

st.set_page_config(page_title="StudyMate AI", page_icon="✦", layout="centered",
                   initial_sidebar_state="collapsed")

# Tried in order; the next one is used if a model is overloaded or unavailable.
MODELS = ["gemini-3.1-flash-lite", "gemini-3.5-flash"]
MAX_CHARS = 30000  # keep prompts reasonably sized for the free tier
MODES = ["Chat", "Summarize", "Explain", "Quiz", "Flashcards"]

db.init_db()

# --------------------------------------------------------------------------
# Styling (ChatGPT-style dark theme)
# --------------------------------------------------------------------------

st.markdown(
    """
<style>
html, body, [class*="css"], .stMarkdown, button, input, textarea, p, li, h1, h2, h3 {
  font-family: ui-sans-serif, -apple-system, system-ui, "Segoe UI", Helvetica, Arial, sans-serif !important;
}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppViewContainer"] { background: #212121; }
.block-container { max-width: 800px; padding-top: 1.2rem; padding-bottom: 7rem; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes blink { 50% { opacity: .35; } }

/* Top bar */
.brand { display:flex; align-items:center; gap:8px; font-size:1.12rem; font-weight:600; color:#ECECEC; padding-top:6px; }
.brand .logo { width:26px; height:26px; border-radius:50%; background:#ECECEC; color:#212121;
  display:grid; place-items:center; font-size:14px; font-weight:700; }

/* Buttons: ChatGPT-style ghost buttons, white pill for primary */
.stButton > button, [data-testid="stPopover"] button, .stDownloadButton > button {
  background: transparent !important; border: 1px solid #424242 !important; color: #ECECEC !important;
  border-radius: 999px !important; font-weight: 500 !important; transition: background .15s ease !important;
}
.stButton > button:hover, [data-testid="stPopover"] button:hover, .stDownloadButton > button:hover { background: #2F2F2F !important; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button {
  background: #ECECEC !important; color: #0D0D0D !important; border: none !important;
  border-radius: 999px !important; font-weight: 600 !important; min-height: 46px;
}
.stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover { background: #FFFFFF !important; }
.stButton > button[kind="tertiary"] { border: none !important; color: #ECECEC !important; text-decoration: underline; }

/* Inputs */
[data-testid="stTextInput"] input {
  background: #212121 !important; border-radius: 999px !important; padding: 12px 18px !important;
}
[data-testid="stTextInput"] > div > div { border-radius: 999px !important; border-color: #424242 !important; }

/* Auth */
.auth-head { text-align:center; margin: 9vh 0 22px; animation: fadeUp .5s ease both; }
.auth-head .logo { width:44px; height:44px; border-radius:50%; background:#ECECEC; color:#212121;
  display:inline-grid; place-items:center; font-size:22px; font-weight:700; margin-bottom:18px; }
.auth-head h1 { font-size: 2rem !important; font-weight: 600 !important; margin: 0 !important; padding: 0 !important; color:#ECECEC; }
.auth-head p { color:#B4B4B4; margin-top:8px; }
[data-testid="stForm"] { border: none !important; padding: 0 !important; max-width: 380px; margin: 0 auto; }
.legal { text-align:center; color:#8E8E8E; font-size:.8rem; margin-top: 18px; }

/* Empty state */
.hello { text-align:center; margin: 16vh 0 26px; animation: fadeUp .6s ease both; }
.hello h2 { font-size: 1.9rem !important; font-weight: 600 !important; color:#ECECEC; padding:0 !important; }
.hello p { color:#B4B4B4; }

/* Messages */
.msg-user { display:flex; justify-content:flex-end; margin: 18px 0; animation: fadeUp .3s ease both; }
.msg-user > div { background:#303030; color:#ECECEC; padding: 10px 18px; border-radius: 22px;
  max-width: 75%; line-height: 1.55; white-space: pre-wrap; }
.material { display:inline-flex; align-items:center; gap:8px; background:#2F2F2F; border:1px solid #424242;
  border-radius: 12px; padding: 8px 12px; font-size:.86rem; color:#ECECEC; margin: 4px 0 8px; }
.material .ficon { width:28px; height:28px; border-radius:7px; background:#FF5588; display:grid; place-items:center; font-size:12px; font-weight:700; color:white; }
[data-testid="stChatMessage"] { background: transparent !important; padding: 0 !important; animation: fadeUp .35s ease both; }
.thinking { color:#B4B4B4; animation: blink 1.2s ease-in-out infinite; }

/* Flashcards: click to flip */
.cards { display:grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin: 8px 0; }
.cards details { background:#2F2F2F; border:1px solid #424242; border-radius: 16px; padding: 18px; cursor: pointer;
  min-height: 120px; transition: border-color .2s ease, transform .2s ease; }
.cards details:hover { border-color:#6B6B6B; transform: translateY(-2px); }
.cards summary { list-style: none; font-weight: 600; color:#ECECEC; }
.cards summary::-webkit-details-marker { display: none; }
.cards details[open] { background:#1E3A32; border-color:#10A37F; }
.cards details[open] summary { color:#9FE3CC; font-size: .8rem; margin-bottom: 8px; }
.cards .back { color:#ECECEC; animation: fadeUp .3s ease both; }
.hint { color:#8E8E8E; font-size:.8rem; }

/* Mode pills + chat input */
/* Mode selector styled as pills */
[data-testid="stRadio"] [role="radiogroup"] { gap: 8px; flex-wrap: wrap; }
[data-testid="stRadio"] [role="radiogroup"] > label { border: 1px solid #424242; border-radius: 999px;
  padding: 5px 14px !important; margin: 0 !important; transition: background .15s ease; }
[data-testid="stRadio"] [role="radiogroup"] > label:hover { background: #2F2F2F; }
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) { background: #ECECEC; border-color: #ECECEC; }
[data-testid="stRadio"] [role="radiogroup"] > label:has(input:checked) p { color: #0D0D0D !important; font-weight: 600; }
[data-testid="stRadio"] [role="radiogroup"] > label > div:first-child { display: none; }
[data-testid="stChatInput"] { border-radius: 28px !important; background:#303030 !important; border: 1px solid #424242 !important; }
[data-testid="stChatInput"] textarea { color:#ECECEC !important; }
[data-testid="stBottom"] > div { background: #212121 !important; }
.disclaimer { text-align:center; color:#8E8E8E; font-size:.75rem; }
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Gemini helpers
# --------------------------------------------------------------------------


@st.cache_resource
def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def call_gemini(prompt: str, json_output: bool = False) -> str:
    """Call Gemini, falling back to the next model if one is overloaded."""
    client = get_client(os.getenv("GEMINI_API_KEY", ""))
    config = types.GenerateContentConfig(response_mime_type="application/json") if json_output else None
    last_error = None
    for model in MODELS:
        try:
            response = client.models.generate_content(model=model, contents=prompt, config=config)
            return response.text or ""
        except Exception as e:  # try the next model
            last_error = e
    raise last_error


def extract_text(uploaded_file) -> str:
    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    return uploaded_file.read().decode("utf-8", errors="ignore").strip()


def extract_json(text: str):
    """Pull a JSON array/object out of a model response that may include
    stray markdown fences or commentary."""
    cleaned = re.sub(r"^```(json)?|```$", "", text.strip()).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("["), cleaned.rfind("]")
        if start == -1 or end <= start:
            raise
        return json.loads(cleaned[start:end + 1])


def validate_quiz(data) -> list:
    """Keep only well-formed questions: 4 string options and a valid correct_index."""
    if isinstance(data, dict):
        data = data.get("questions") or data.get("quiz") or []
    quiz = [
        q for q in (data if isinstance(data, list) else [])
        if isinstance(q, dict) and isinstance(q.get("question"), str)
        and isinstance(q.get("options"), list) and len(q["options"]) == 4
        and all(isinstance(o, str) for o in q["options"])
        and isinstance(q.get("correct_index"), int) and 0 <= q["correct_index"] < 4
    ]
    if not quiz:
        raise ValueError("the model returned no valid questions")
    return quiz


def validate_cards(data) -> list:
    """Keep only cards with a non-empty front and back."""
    if isinstance(data, dict):
        data = data.get("flashcards") or data.get("cards") or []
    cards = [
        c for c in (data if isinstance(data, list) else [])
        if isinstance(c, dict) and str(c.get("front", "")).strip() and str(c.get("back", "")).strip()
    ]
    if not cards:
        raise ValueError("the model returned no valid flashcards")
    return cards


def source_block(chat: dict, text: str) -> str:
    """The material the AI should work from: the attached file, else the typed text."""
    if chat["material"]:
        return f"STUDY MATERIAL:\n{chat['material'][:MAX_CHARS]}"
    return f"TOPIC / MATERIAL PROVIDED BY THE STUDENT:\n{text[:MAX_CHARS]}"


def answer(chat: dict, mode: str, text: str, history: list):
    """Build the prompt for the chosen mode and return (kind, content)."""
    src = source_block(chat, text)
    if mode == "Summarize":
        prompt = ("You are a helpful study assistant. Summarize the material below with clear "
                  "headings and bullet points, and highlight key terms in bold."
                  + (f" Extra instruction from the student: {text}" if chat["material"] and text else "")
                  + f"\n\n{src}")
        return "text", call_gemini(prompt)
    if mode == "Explain":
        prompt = (f"You are a patient teacher. Explain '{text or 'the main ideas'}' using the material "
                  "below as the main source. Structure: a one-line definition, a clear explanation, "
                  "a simple real-world example or analogy, and 3 key takeaways as bullet points.\n\n"
                  + (src if chat["material"] else ""))
        return "text", call_gemini(prompt)
    if mode == "Quiz":
        n = int(m.group(1)) if (m := re.search(r"\b(\d{1,2})\b", text or "")) else 5
        prompt = (f"Create {max(3, min(n, 15))} multiple-choice quiz questions based on the material "
                  "below. Return ONLY valid JSON as a list of objects with keys: 'question' (string), "
                  "'options' (list of 4 strings), 'correct_index' (integer 0-3), and 'explanation' "
                  f"(short string explaining the right answer).\n\n{src}")
        return "quiz", validate_quiz(extract_json(call_gemini(prompt, json_output=True)))
    if mode == "Flashcards":
        prompt = ("Create 10 flashcards based on the material below. Return ONLY valid JSON as a list "
                  "of objects with keys 'front' (a term or question) and 'back' (the answer or "
                  f"definition).\n\n{src}")
        return "cards", validate_cards(extract_json(call_gemini(prompt, json_output=True)))
    # Chat: grounded in the attached material when there is one, with recent conversation context.
    convo = "\n".join(
        f"{'Student' if h['role'] == 'user' else 'Assistant'}: {h['content']}"
        for h in history[-8:] if h["kind"] == "text"
    )
    prompt = ("You are StudyMate AI, a friendly, accurate study tutor. Answer clearly using markdown. "
              + ("Use the study material below as your main source; if the answer isn't in it, say so "
                 "and answer from general knowledge.\n\n" + src[:MAX_CHARS] + "\n\n" if chat["material"] else "\n\n")
              + (f"CONVERSATION SO FAR:\n{convo}\n\n" if convo else "")
              + f"Student: {text}\nAssistant:")
    return "text", call_gemini(prompt)


# --------------------------------------------------------------------------
# Auth pages
# --------------------------------------------------------------------------


def auth_page():
    page = st.session_state.get("auth_page", "login")
    title, sub = ("Welcome back", "Log in to continue studying with StudyMate AI") if page == "login" \
        else ("Create an account", "Sign up to save your chats and study material")
    st.markdown(f'<div class="auth-head"><div class="logo">✦</div><h1>{title}</h1><p>{sub}</p></div>',
                unsafe_allow_html=True)

    with st.form(f"{page}_form", border=False):
        name = st.text_input("Name", placeholder="Full name", label_visibility="collapsed") if page == "signup" else ""
        email = st.text_input("Email", placeholder="Email address", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
        confirm = st.text_input("Confirm", type="password", placeholder="Confirm password",
                                label_visibility="collapsed") if page == "signup" else ""
        submitted = st.form_submit_button("Continue", use_container_width=True)

    if submitted:
        if page == "signup":
            if password != confirm:
                st.error("Passwords don't match.")
            else:
                try:
                    st.session_state.user = db.create_user(name, email, password)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        else:
            user = db.authenticate(email, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Incorrect email or password.")

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        label = "Don't have an account? Sign up" if page == "login" else "Already have an account? Log in"
        if st.button(label, type="tertiary", use_container_width=True, key="auth_switch"):
            st.session_state.auth_page = "signup" if page == "login" else "login"
            st.rerun()
    st.markdown('<div class="legal">Your password is stored securely as a salted hash.</div>',
                unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Chat page
# --------------------------------------------------------------------------


def render_quiz(msg_id: int, quiz: list):
    with st.form(f"quiz_{msg_id}", border=True):
        st.markdown(f"**Quiz · {len(quiz)} questions**")
        for i, q in enumerate(quiz):
            st.markdown(f"**{i + 1}. {q['question']}**")
            st.radio("Choose one:", range(4), format_func=lambda j, opts=q["options"]: opts[j],
                     key=f"q_{msg_id}_{i}", label_visibility="collapsed", index=None)
        submitted = st.form_submit_button("Submit answers")
    if submitted:
        score = 0
        for i, q in enumerate(quiz):
            chosen = st.session_state.get(f"q_{msg_id}_{i}")
            if chosen == q["correct_index"]:
                score += 1
                st.success(f"{i + 1}. Correct — {q.get('explanation', '')}")
            else:
                st.error(f"{i + 1}. Correct answer: {q['options'][q['correct_index']]} — {q.get('explanation', '')}")
        st.info(f"Score: {score} / {len(quiz)} ({round(score / len(quiz) * 100)}%)")


def render_cards(cards: list):
    items = "".join(
        f'<details><summary>{html.escape(str(c["front"]))}</summary>'
        f'<div class="back">{html.escape(str(c["back"]))}</div></details>'
        for c in cards
    )
    st.markdown(f'<div class="hint">{len(cards)} flashcards · click a card to flip it</div>'
                f'<div class="cards">{items}</div>', unsafe_allow_html=True)


def chat_page():
    user = st.session_state.user
    chats = db.list_chats(user["id"])
    if "chat_id" not in st.session_state or not db.get_chat(st.session_state.chat_id, user["id"]):
        st.session_state.chat_id = chats[0]["id"] if chats else db.create_chat(user["id"])
    chat = db.get_chat(st.session_state.chat_id, user["id"])

    # Top bar: brand · history · new chat · account
    c1, c2, c3, c4 = st.columns([4, 1.4, 1.4, 1.2], vertical_alignment="center")
    c1.markdown('<div class="brand"><span class="logo">✦</span>StudyMate AI</div>', unsafe_allow_html=True)
    with c2.popover("History", use_container_width=True):
        chats = db.list_chats(user["id"])
        for ch in chats:
            label = ("● " if ch["id"] == chat["id"] else "") + ch["title"]
            if st.button(label, key=f"open_{ch['id']}", use_container_width=True):
                st.session_state.chat_id = ch["id"]
                st.rerun()
        if len(chats) > 1 and st.button("Delete this chat", key="del_chat", use_container_width=True):
            db.delete_chat(chat["id"], user["id"])
            st.session_state.pop("chat_id")
            st.rerun()
    if c3.button("New chat", key="new_chat", use_container_width=True):
        st.session_state.chat_id = db.create_chat(user["id"])
        st.rerun()
    with c4.popover(user["name"].split()[0][:10], use_container_width=True):
        st.markdown(f"**{html.escape(user['name'])}**  \n{html.escape(user['email'])}")
        if st.button("Log out", key="logout", use_container_width=True):
            for k in ["user", "chat_id"]:
                st.session_state.pop(k, None)
            st.rerun()

    messages = db.get_messages(chat["id"])
    if not messages:
        first = html.escape(user["name"].split()[0])
        st.markdown(f'<div class="hello"><h2>What are we studying today, {first}?</h2>'
                    '<p>Attach a PDF or TXT with the 📎 button, or just ask a question.</p></div>',
                    unsafe_allow_html=True)

    if chat["material_name"]:
        st.markdown(f'<div class="material"><span class="ficon">DOC</span>{html.escape(chat["material_name"])}'
                    f' · {len(chat["material"].split()):,} words loaded</div>', unsafe_allow_html=True)

    for m in messages:
        if m["role"] == "user":
            st.markdown(f'<div class="msg-user"><div>{html.escape(m["content"])}</div></div>',
                        unsafe_allow_html=True)
        else:
            with st.chat_message("assistant", avatar=":material/auto_awesome:"):
                if m["kind"] == "quiz":
                    render_quiz(m["id"], m["content"])
                elif m["kind"] == "cards":
                    render_cards(m["content"])
                else:
                    st.markdown(m["content"])
                    st.download_button("Download", m["content"], file_name=f"studymate_{m['id']}.md",
                                       key=f"dl_{m['id']}", icon=":material/download:")

    mode = st.radio("Mode", MODES, key="mode", horizontal=True, label_visibility="collapsed")
    placeholders = {
        "Chat": "Ask anything",
        "Summarize": "Summarize the attached file (or paste notes here)",
        "Explain": "Which topic should I explain?",
        "Quiz": "Quiz me (e.g. '10 questions') or type a topic",
        "Flashcards": "Make flashcards (or type a topic)",
    }
    prompt = st.chat_input(placeholders[mode], accept_file=True, file_type=["pdf", "txt"])
    st.markdown('<div class="disclaimer">StudyMate AI can make mistakes. Check important info.</div>',
                unsafe_allow_html=True)

    if prompt:
        text = (prompt.text or "").strip()
        files = prompt.files or []
        if files:
            f = files[0]
            try:
                material = extract_text(f)
            except Exception as e:
                st.error(f"Couldn't read {f.name}: {e}")
                return
            if not material:
                st.error(f"No text could be extracted from {f.name}. Scanned/image-only PDFs aren't supported.")
                return
            db.set_material(chat["id"], f.name, material)
            chat = db.get_chat(chat["id"], user["id"])
            if len(material) > MAX_CHARS:
                st.warning(f"{f.name} is long — only the first {MAX_CHARS:,} characters are used by the AI.")
        if not text and not files:
            return
        if chat["title"] == "New chat":
            db.rename_chat(chat["id"], text[:40] if text else (files[0].name if files else "New chat"))
        user_line = (f"📎 {files[0].name}\n" if files else "") + (f"[{mode}] " if mode != "Chat" else "") + text
        db.add_message(chat["id"], "user", "text", user_line.strip())
        if files and not text and mode == "Chat":
            db.add_message(chat["id"], "assistant", "text",
                           f"I've read **{files[0].name}** ({len(chat['material'].split()):,} words). "
                           "Ask me anything about it, or pick **Summarize**, **Explain**, **Quiz** or "
                           "**Flashcards** above.")
            st.rerun()
        if mode != "Chat" and not text and not chat["material"]:
            db.add_message(chat["id"], "assistant", "text",
                           "Attach a PDF/TXT with 📎 or type a topic, and I'll get started.")
            st.rerun()
        st.markdown(f'<div class="msg-user"><div>{html.escape(user_line.strip())}</div></div>',
                    unsafe_allow_html=True)
        with st.chat_message("assistant", avatar=":material/auto_awesome:"):
            st.markdown('<span class="thinking">Thinking…</span>', unsafe_allow_html=True)
            try:
                kind, content = answer(chat, mode, text, messages)
                db.add_message(chat["id"], "assistant", kind, content)
            except Exception as e:
                msg = str(e)
                if "API key" in msg or "API_KEY" in msg:
                    msg = "The Gemini API key is missing or invalid. Set GEMINI_API_KEY in the .env file."
                elif "503" in msg or "UNAVAILABLE" in msg:
                    msg = "Gemini is busy right now. Please try again in a moment."
                db.add_message(chat["id"], "assistant", "text", f"⚠️ Something went wrong: {msg}")
        st.rerun()


# --------------------------------------------------------------------------
# Router
# --------------------------------------------------------------------------

if not os.getenv("GEMINI_API_KEY"):
    st.error("Server is not configured: set GEMINI_API_KEY in the .env file and restart the app.")
    st.stop()

if "user" in st.session_state:
    chat_page()
else:
    auth_page()
