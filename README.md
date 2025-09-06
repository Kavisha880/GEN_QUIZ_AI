# 🤖 GEN QUIZ AI

An **AI-powered quiz generator** built with [Streamlit](https://streamlit.io/) and [LangChain](https://www.langchain.com/) using the **Groq API**.  
Generate multiple-choice questions (MCQs) on any topic, answer interactively, and maintain a saved history of quizzes.

---

## ✨ Features

- 🔑 **Groq LLM integration** — supports models like `llama-3.1-8b-instant` and `llama-3.3-70b-versatile`.
- 📝 **Custom MCQ generation** — enter a topic & number of questions.
- 🎮 **Interactive answering**
  - Each option (`a)`, `b)`, `c)`, `d)`) is a button.
  - Selected option turns **green (correct)** or **red (wrong)**.
  - **Show Answer** button reveals the correct one.
- 📜 **Persistent history**
  - Saved in `quiz_history.json`.
  - View/search/reload/delete/download past quizzes in the **History tab**.
- 📂 **Export quizzes** to `.txt` files.
- ⚡ Built with **Streamlit + LangChain (LCEL)**.

---

## 🚀 Getting Started with uv

```bash
# 1. Clone the repo
git clone https://github.com/Kavisha880/GEN_QUIZ_AI.git
cd GEN_QUIZ_AI

# 2. Create a virtual environment
uv venv .venv

# 3. Activate it
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate

# 4. Install dependencies
uv add streamlit langchain langchain-groq

# 5. (Optional) Save your Groq API key in .env
echo "GROQ_API_KEY=your_api_key_here" > .env

# 6. Run the app
streamlit run qachatbot.py
```
📂 Project Structure
```bash
.
├── qachatbot.py          # Main Streamlit app
├── quiz_history.json     # Auto-created history file
├── pyproject.toml        # uv project manifest
├── uv.lock               # uv lockfile
└── README.md
```
**🛠️ Tech Stack**
```bash
Streamlit
 — Web app framework
```
**LangChain**
 — LLM orchestration

**Groq API**
 — Fast inference backend

**uv**
 — Ultra-fast Python package manager

Python 3.10+

**🙌 Future Enhancements**

Export to CSV/Excel with answer keys

Difficulty level selection

Deploy on Streamlit Cloud / HuggingFace Spaces

**📬 Contact**

Author: Kavisha Gupta

GitHub: Kavisha880

Email: kavishagupta8806@gmail.com
