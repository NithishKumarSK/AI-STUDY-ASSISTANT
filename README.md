<div align="center">

# ✦ StudyMate AI

### A GenAI-Based Personalized Study Assistant

Turn your notes, chapters and PDFs into **summaries, answers, explanations, quizzes and flashcards** through a simple chat interface, powered by **Google Gemini**.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Google_Gemini-GenAI-4285F4?style=for-the-badge&logo=google&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

<img src="screenshots/06_pdf_analysis.png" width="85%" alt="StudyMate AI analysing a PDF"/>

</div>

---

## 📌 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#️-system-architecture)
- [Workflow](#-workflow)
- [Screenshots](#-screenshots)
- [Tech Stack](#️-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Limitations](#️-limitations)
- [Future Scope](#-future-scope)

---

## 🎯 Overview

Students spend a lot of time reading long notes and textbooks, writing summaries and preparing self-tests by hand. **StudyMate AI** uses Generative AI to automate this. A student signs in, attaches a PDF or TXT file (or just types a question), and chats with an AI tutor that can summarize the material, answer questions about it, explain topics, generate multiple-choice quizzes with scoring, and create flashcards.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Sign up / Login** | User accounts stored in SQLite; passwords hashed with PBKDF2-SHA256 and a per-user salt |
| 💬 **AI Chat** | Conversational tutor that remembers the recent conversation |
| 📎 **PDF / TXT upload** | Attach study material from the chat box; text is extracted automatically |
| 📝 **Summarize** | Structured summary with headings, bullet points and key terms |
| 💡 **Explain** | Definition, explanation, real-world analogy and key takeaways for any topic |
| 🧠 **Quiz** | Auto-generated MCQs (structured JSON output) with instant scoring and explanations |
| 🗂️ **Flashcards** | Click-to-flip cards for active recall |
| 🕘 **Chat History** | Every chat and its material is saved per user and can be reopened or deleted |
| ⬇️ **Download** | Save any AI answer as a Markdown file |
| 🛡️ **Robust AI handling** | JSON validation, automatic fallback to a second model when one is busy, clear error messages |

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    U([👤 Student]) --> UI

    subgraph UI["🖥️ Presentation Layer — Streamlit"]
        A[Login / Sign-up Page]
        C[Chat Interface<br/>Chat · Summarize · Explain · Quiz · Flashcards]
    end

    subgraph PROC["⚙️ Processing Layer — Python"]
        E[PDF / TXT Text Extraction<br/>pypdf]
        P[Prompt Construction<br/>task-specific prompts]
        V[Response Parsing<br/>JSON validation]
    end

    subgraph AI["🤖 Generative AI Layer"]
        G[Google Gemini API<br/>gemini-3.1-flash-lite, fallback gemini-3.5-flash]
    end

    subgraph DATA["🗄️ Data Layer — SQLite"]
        D1[(users)]
        D2[(chats)]
        D3[(messages)]
    end

    A <--> D1
    C --> E --> P
    C --> P
    P --> G --> V --> C
    C <--> D2
    C <--> D3
```

---

## 🔄 Workflow

```mermaid
sequenceDiagram
    actor S as Student
    participant UI as StudyMate UI
    participant PY as Python Backend
    participant GM as Gemini API
    participant DB as SQLite

    S->>UI: Log in / Sign up
    UI->>DB: Verify hashed password
    S->>UI: Attach PDF + choose mode (e.g. Quiz)
    UI->>PY: Extract text from PDF
    PY->>DB: Save material to chat
    PY->>GM: Send task-specific prompt + material
    GM-->>PY: Generated response (text / JSON)
    PY->>PY: Validate and format output
    PY->>DB: Save message to history
    PY-->>UI: Render summary / quiz / flashcards
    UI-->>S: Interactive result
```

### Feature pipeline

```mermaid
flowchart LR
    M[📄 Study Material] --> X[Text Extraction] --> PR[Prompt Engineering] --> GE[Gemini]
    GE --> S1[📝 Summary]
    GE --> S2[💬 Answer]
    GE --> S3[💡 Explanation]
    GE --> S4[🧠 Quiz JSON → Score]
    GE --> S5[🗂️ Flashcards JSON]
```

---

## 📸 Screenshots

| Sign up | Login |
|---|---|
| <img src="screenshots/01_signup.png" width="100%"/> | <img src="screenshots/02_login.png" width="100%"/> |

| Home | AI Chat |
|---|---|
| <img src="screenshots/03_home.png" width="100%"/> | <img src="screenshots/04_chat.png" width="100%"/> |

| PDF Upload | PDF Analysis |
|---|---|
| <img src="screenshots/05_pdf_upload.png" width="100%"/> | <img src="screenshots/06_pdf_analysis.png" width="100%"/> |

| Summary | Explain |
|---|---|
| <img src="screenshots/07_summary.png" width="100%"/> | <img src="screenshots/08_explain.png" width="100%"/> |

| Quiz | Flashcards |
|---|---|
| <img src="screenshots/09_quiz.png" width="100%"/> | <img src="screenshots/10_flashcards.png" width="100%"/> |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.10+ | Core application logic |
| Frontend | Streamlit | Web UI, chat interface, custom CSS theme |
| Generative AI | Google Gemini API (`google-genai`) | Summaries, answers, explanations, quizzes, flashcards |
| PDF processing | pypdf | Text extraction from PDFs |
| Database | SQLite | Users, chats and messages |
| Security | PBKDF2-HMAC-SHA256 | Password hashing |
| Config | python-dotenv | Loads the API key from `.env` |

---

## 📁 Project Structure

```
StudyMate_AI/
├── app.py                 # Streamlit app: auth pages, chat UI, prompts, Gemini calls
├── db.py                  # SQLite storage: users, chats, messages, password hashing
├── requirements.txt       # Python dependencies
├── .env.example           # Template for the Gemini API key
├── .gitignore
├── .streamlit/
│   └── config.toml        # Dark theme
└── screenshots/           # Application screenshots
```

---

## 🚀 Getting Started

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Add your Gemini API key** (free at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey))
```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```
Then edit `.env`:
```
GEMINI_API_KEY=your_key_here
```

**3. Run**
```bash
streamlit run app.py
```
Open the URL shown in the terminal (default `http://localhost:8501`), create an account and start studying.

---

## ⚠️ Limitations

- Scanned / image-only PDFs are not supported (no OCR).
- Only the first 30,000 characters of a document are sent to the AI.
- Requires an internet connection and a valid Gemini API key.
- AI output can occasionally be inaccurate — important facts should be verified.
- Refreshing the browser logs the user out; there is no password reset yet.

---

## 🔮 Future Scope

- OCR support for scanned notes and handwritten material
- RAG with chunking and vector search for very large documents
- Voice input and multilingual support
- Progress tracking dashboard with quiz score history
- Persistent sessions, password reset and email verification
- Cloud deployment

---

## 📚 References

1. Google Gemini API Documentation — https://ai.google.dev/gemini-api/docs
2. Streamlit Documentation — https://docs.streamlit.io
3. pypdf Documentation — https://pypdf.readthedocs.io
4. SQLite Documentation — https://www.sqlite.org/docs.html
5. Python `hashlib` (PBKDF2) — https://docs.python.org/3/library/hashlib.html
6. Base project: AI Study Assistant (open-source Streamlit + Gemini app), extended and redesigned for this project

<div align="center">

**StudyMate AI** · Built with Python, Streamlit and Google Gemini

</div>
