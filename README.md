#AI accoutability partner

This is an attempt to create a LLM based rubber duck that speaks to you and listens to your problems.


# AI-Partner: Your Personal Rubber Duck (LLM-Based Thought Partner)

-Talk out loud. Get clarity. Make better decisions.

**AI-Partner** is a voice-activated personal assistant built with an LLM (via Ollama) that helps you **plan your day, clarify thoughts, or debug ideas** — just like a smart version of the classic *rubber duck* technique.

This project is designed to be:
- **Conversational** – Talk to it like you would to a teammate.
- **Introspective** – Get feedback, reflection, and better clarity.
- **Modular & Hackable** – Build your own features on top of it.

---

##  Features

-  **Voice-to-LLM pipeline** using [Whisper](https://github.com/openai/whisper) for speech-to-text.
-   **Local LLM via Ollama** – fast, private, and customizable.
-  **Looping conversations** for deep reflection.
-  **Dockerized** for easy local setup.

---
---

##  Installation

### 1. Clone the repo
```bash
git clone https://github.com/Umanagendra-M/AI-Partner.git
cd AI-Partner

inside the root directory

docker-compose up --build ### builds the containers

you need to run the container seperately

move inside the "client" directory
create a virtual env
python -m venv venv

activate the venv environment

pip install -r requirements.txt

run below command

python record_and_trigger_new copy.py ## this should turn on the voice bot which you can converse 
