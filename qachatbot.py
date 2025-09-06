# qachatbot.py — uses your server-side key only (no user input)
import os, re, json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import streamlit as st

from dotenv import load_dotenv              # for local .env fallback
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

# ---------------- CONFIG ----------------
load_dotenv()  # reads .env locally; on Streamlit Cloud you'll use Secrets
st.set_page_config(page_title="GEN QUIZ AI", page_icon="🤖", layout="wide")
HISTORY_FILE = Path("quiz_history.json")

# CSS for colored tiles
st.markdown("""
<style>
.option-tile { border: 2px solid var(--border, #ddd); border-radius: 12px; padding: 10px 12px; margin: 8px 0; }
.option-correct { --border: #31a24c; }  /* green */
.option-wrong   { --border: #e64848; }  /* red   */
.option-neutral { --border: #ddd;    }  /* gray  */
</style>
""", unsafe_allow_html=True)

st.title("GEN QUIZ AI")
st.caption("Generate MCQs with Groq. Click an option to check; use 'Show answer' at the end.")

# ---------------- PERSISTENCE ----------------
def load_history() -> List[Dict]:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_history(items: List[Dict]):
    HISTORY_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------------- SESSION DEFAULTS ----------------
st.session_state.setdefault("history", load_history())
st.session_state.setdefault("messages", [])
st.session_state.setdefault("current_blocks", [])
st.session_state.setdefault("current_raw", "")
st.session_state.setdefault("current_topic", "")
st.session_state.setdefault("current_num", 0)

# ---------------- API KEY (Secrets → env/.env) ----------------
def get_api_key() -> str | None:
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        key = None
    return key or os.getenv("GROQ_API_KEY")

# ---------------- SIDEBAR (no key prompt) ----------------
with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox("Model", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"])
    st.caption(f"📜 Saved runs: **{len(st.session_state.history)}**")
    if st.button("Clear All History 🧹"):
        st.session_state.history = []
        save_history([])
        st.success("History cleared.")
        st.rerun()

# ---------------- LLM ----------------
@st.cache_resource(show_spinner=False)
def get_llm(model_name: str):
    api_key = get_api_key()
    if not api_key:
        return None
    return ChatGroq(groq_api_key=api_key, model_name=model_name, temperature=0.7)

llm = get_llm(model_name)

# ---------------- PROMPT / CHAIN ----------------
mcq_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert exam question setter. Generate multiple-choice questions (MCQs) on the given topic."),
    ("user", """Topic: {topic}
Number of Questions: {num_questions}

Instructions:
1. Each question must be clear and concise.
2. Provide 4 options (a, b, c, d).
3. Only one option should be correct.
4. After each question, include: Answer: <a|b|c|d>
5. Number questions like: 1., 2., 3., ...
""")
])
chain = (mcq_prompt | llm | StrOutputParser()) if llm else None

# ---------------- HELPERS ----------------
def parse_mcqs(text: str) -> List[Dict]:
    """Return list of dicts: {question, options(['a) ...']), answer('a'|'b'|'c'|'d')}"""
    parts = re.split(r'(?m)^(?=\d+\.\s)', text.strip())
    out = []
    for block in parts:
        block = block.strip()
        if not block:
            continue
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue

        q_line = re.sub(r'^\d+\.\s*', '', lines[0])

        opt_pat = re.compile(r'^([a-dA-D])[\.\)]\s+(.*)$')
        options_raw = []
        for l in lines[1:]:
            m = opt_pat.match(l)
            if m:
                letter = m.group(1).lower()
                text_only = m.group(2).strip()
                options_raw.append(f"{letter}) {text_only}")  # keep a) style

        ans = ""
        for l in lines:
            m = re.search(r'answer:\s*([a-dA-D])\b', l, re.IGNORECASE)
            if m:
                ans = m.group(1).lower()
                break

        if q_line and options_raw:
            out.append({"question": q_line, "options": options_raw[:4], "answer": ans})
    return out

def add_to_history(topic: str, num: int, response: str):
    items = st.session_state.history
    new_id = (items[-1]["id"] + 1) if items else 1
    items.append({
        "id": new_id,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "topic": topic,
        "num": int(num),
        "response": response
    })
    save_history(items)

def clear_selection_state(_max_q: int):
    to_delete = []
    for k in list(st.session_state.keys()):
        if k.startswith("sel_") or k.startswith("rev_"):
            to_delete.append(k)
    for k in to_delete:
        st.session_state.pop(k, None)

# ---------- INTERACTIVE MCQ ----------
def render_mcq_interactive(qid: int, question: str, options: List[str], correct_letter: str):
    sel_key = f"sel_{qid}"
    rev_key = f"rev_{qid}"

    st.markdown(f"**Q{qid+1}. {question}**")

    chosen = st.session_state.get(sel_key)
    revealed = st.session_state.get(rev_key, False)

    # initial state → buttons
    if not chosen and not revealed:
        for opt in options:
            letter = opt.split(')')[0].strip().lower()
            label = opt
            if st.button(label, key=f"optbtn-{qid}-{letter}", use_container_width=True):
                st.session_state[sel_key] = letter
                st.rerun()

        if st.button("Show answer", key=f"reveal-{qid}", type="secondary"):
            st.session_state[rev_key] = True
            st.rerun()
        return

    # colored tiles after selection/reveal
    for opt in options:
        letter = opt.split(')')[0].strip().lower()
        if revealed:
            if letter == correct_letter:
                css = "option-correct"
            elif chosen and letter == chosen and chosen != correct_letter:
                css = "option-wrong"
            else:
                css = "option-neutral"
        else:
            if chosen == letter:
                css = "option-correct" if letter == correct_letter else "option-wrong"
            else:
                css = "option-neutral"
        st.markdown(f'<div class="option-tile {css}">{opt}</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([1,1])
    with c1:
        if not revealed and st.button("Change selection", key=f"reset-{qid}"):
            st.session_state.pop(sel_key, None)
            st.rerun()
    with c2:
        if not revealed and st.button("Show answer", key=f"reveal2-{qid}", type="secondary"):
            st.session_state[rev_key] = True
            st.rerun()

    if revealed:
        st.info(f"Answer: **{correct_letter})**")

# ---------------- UI TABS ----------------
tab_generate, tab_history = st.tabs(["🧠 Generate MCQs", "📜 History"])

with tab_generate:
    c1, c2 = st.columns([2,1])
    with c1:
        topic = st.text_input("Topic", placeholder="e.g., Binary Search Trees",
                              value=st.session_state.current_topic or "")
    with c2:
        num_questions = st.number_input("Number of questions", min_value=1, max_value=20,
                                        value=int(st.session_state.current_num or 5), step=1)

    run = st.button("Generate MCQs 🚀", use_container_width=True, type="primary")

    # If key not configured, show a developer-only message (no textbox anywhere)
    if llm is None:
        st.warning("Server key missing. Set GROQ_API_KEY in Streamlit Secrets (Cloud) or in your local .env.", icon="🔑")

    if run:
        if not llm:
            st.error("Service not ready: missing API key (developer setup).")
        elif not topic.strip():
            st.warning("Enter a topic.")
        else:
            with st.spinner("Generating…"):
                raw = (mcq_prompt | llm | StrOutputParser()).invoke(
                    {"topic": topic.strip(), "num_questions": int(num_questions)}
                )
            blocks = parse_mcqs(raw)

            # persist for reruns
            st.session_state.current_blocks = blocks
            st.session_state.current_raw = raw
            st.session_state.current_topic = topic
            st.session_state.current_num = int(num_questions)

            clear_selection_state(len(blocks))

            # Save to history
            st.session_state.messages.append(HumanMessage(content=f"Topic: {topic}, Questions: {num_questions}"))
            st.session_state.messages.append(AIMessage(content=raw))
            add_to_history(topic, num_questions, raw)

            st.rerun()

    # render current set (keeps state on reruns)
    blocks = st.session_state.current_blocks
    if blocks:
        for i, b in enumerate(blocks):
            render_mcq_interactive(
                qid=i,
                question=b["question"],
                options=b["options"],
                correct_letter=b["answer"]
            )
            st.divider()
        if st.session_state.current_raw:
            st.download_button(
                "Download MCQs (.txt)",
                st.session_state.current_raw.encode("utf-8"),
                file_name=f"mcqs_{st.session_state.current_topic.replace(' ','_')}.txt"
            )

with tab_history:
    q = st.text_input("Search in history", placeholder="e.g., tree, dbms, numpy")
    newest_first = st.toggle("Newest first", value=True)
    items = st.session_state.history
    if q:
        qlow = q.lower()
        items = [h for h in items if (qlow in h["topic"].lower() or qlow in h["response"].lower())]
    if newest_first:
        items = list(reversed(items))

    if not items:
        st.info("No history yet. Generate in the first tab.")
    else:
        for h in items:
            with st.container(border=True):
                st.markdown(f"#{h['id']} • {h['ts']} • **{h['topic']}** ({h['num']} Qs)")
                with st.expander("Preview MCQs", expanded=False):
                    prev_blocks = parse_mcqs(h["response"])
                    if prev_blocks:
                        for i, b in enumerate(prev_blocks):
                            st.markdown(f"**Q{i+1}. {b['question']}**")
                            for opt in b["options"]:
                                st.markdown(f"- {opt}")
                            if b["answer"]:
                                st.markdown(f"**Answer: {b['answer']})**")
                            st.write("---")
                    else:
                        st.code(h["response"])

                cA, cB, cC = st.columns([1,1,1])
                with cA:
                    st.download_button(
                        "Download .txt",
                        h["response"].encode("utf-8"),
                        file_name=f"mcqs_{h['topic'].replace(' ','_')}_{h['id']}.txt",
                        key=f"dl-{h['id']}"
                    )
                with cB:
                    if st.button("Load this set", key=f"load-{h['id']}"):
                        st.session_state.current_blocks = parse_mcqs(h["response"])
                        st.session_state.current_raw = h["response"]
                        st.session_state.current_topic = h["topic"]
                        st.session_state.current_num = h["num"]
                        clear_selection_state(len(st.session_state.current_blocks))
                        st.toast("Loaded into Generate tab.")
                        st.rerun()
                with cC:
                    if st.button("Delete", key=f"del-{h['id']}"):
                        st.session_state.history = [x for x in st.session_state.history if x["id"] != h["id"]]
                        save_history(st.session_state.history)
                        st.rerun()
