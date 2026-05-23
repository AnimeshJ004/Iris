[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit-00C7B7?style=for-the-badge&logo=vercel)](https://iris-lyart-pi.vercel.app/)
<div align="center">
  <h1>✨ Iris AI Assistant ✨</h1>
  <p><strong>A modern, serverless-ready conversational AI featuring a stunning UI and powerful local command routing.</strong></p>
  
  <p>
    <a href="https://iris-lyart-pi.vercel.app/"><strong>View Live Demo »</strong></a>
  </p>
</div>

<br />

## 📖 About
**Iris** is a highly polished, intelligent web-based AI assistant powered by advanced language models (via Groq). It features an "Ultimate AI UI" that blends the best aesthetic concepts from ChatGPT, Claude, and Gemini into a single, cohesive, and premium experience. 

Designed for both speed and aesthetics, Iris intercepts local commands instantly and streams AI responses dynamically, all while backing up your conversation history to a MySQL database.

---

## 📸 Screenshots
<img width="1362" height="604" alt="Screenshot 2026-05-23 224051" src="https://github.com/user-attachments/assets/45a2f016-4718-42f4-a43d-801e8b21fa99" />

<img width="1365" height="593" alt="Screenshot 2026-05-23 224044" src="https://github.com/user-attachments/assets/6d92c358-5049-474c-b4e8-dddab4a0b15c" />

<img width="1363" height="601" alt="Screenshot 2026-05-23 224032" src="https://github.com/user-attachments/assets/725206a2-b4f2-4a2e-89f5-c16a0b660243" />


---

## ⚡ Features & Functionality

*   **🗣️ Intelligent Conversations:** Powered by Llama 3 via Groq for lightning-fast, high-quality responses.
*   **🎙️ Voice Interaction:** Built-in Speech Recognition for voice input and Speech Synthesis for reading responses aloud.
*   **⚡ Instant Local Commands:** Commands like *Date, Time, Wikipedia searches, and Math calculations* bypass the AI and execute instantly via local python routing.
*   **💾 Persistent Sessions:** Chat histories are automatically saved and organized into sessions via a MySQL backend.
*   **🎨 Premium "Ultimate UI":** 
    *   Clean, constrained-width layout for optimized readability.
    *   Subtle, flowing animated mesh gradient background.
    *   Server-Sent Events (SSE) streaming with a highly optimized, throttle-rendered markdown interface that prevents browser lag.
*   **🚀 Serverless Ready:** Specifically optimized with connection pooling tailored for Vercel deployment and cold starts.

---

## 🛠️ Tech Stack

**Frontend:**
*   Vanilla JavaScript, HTML5
*   Custom CSS3 (Flexbox, CSS Variables, Animations)
*   Marked.js (Markdown Rendering)

**Backend:**
*   Python 3 & Flask
*   Groq API (Llama-3-70b-versatile)
*   MySQL (mysql-connector-python)

**Deployment:**
*   Ready for **Vercel** (`vercel.json` included)

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.8+
*   MySQL Server running locally or remotely
*   A free API key from [Groq Console](https://console.groq.com/keys)

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AnimeshJ004/Iris.git
   cd Iris
   ```

2. **Set up a Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate  # Windows
   # source .venv/bin/activate     # macOS/Linux
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the `src/` directory with the following configuration:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=iris_assistant
   ```

5. **Run the Server:**
   ```bash
   python api/index.py
   ```
   *The app will automatically initialize the database on startup. Open `http://localhost:5000` to chat with Iris.*

---

## 🌐 Deployment (Vercel)

Iris is structured to run as a serverless function on Vercel. 
Simply import the project to Vercel and ensure you add the environment variables from your `.env` file into the Vercel project settings.

---

<div align="center">
  <i>Designed with ❤️</i>
</div>
