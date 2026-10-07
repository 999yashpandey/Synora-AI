
# Synora AI

> A local-first personal AI assistant built with Python, Ollama, Qwen2.5, local speech recognition, web search, persistent memory, and a futuristic voice-first interface.

## Overview

**Synora AI** is a local personal AI assistant designed to combine natural-language interaction with practical computer automation.

The project focuses on keeping the core AI processing local while providing useful capabilities such as:

- Natural-language conversations
- Computer and application control
- File and document operations
- Code generation
- Web search and article summarization
- Persistent local memory
- Voice input using local Whisper
- Voice output using Windows SAPI
- A browser-based futuristic assistant interface
- Safety checks for potentially dangerous actions

Synora uses **Ollama with Qwen2.5 3B Instruct** as its local language model, allowing the core conversational AI to run without sending normal conversations to a cloud LLM API.

---

## Features

### Local AI

- Powered by **Qwen2.5 3B Instruct**
- Runs through **Ollama**
- Local conversational processing
- Configurable generation settings
- Designed for relatively lightweight local hardware

### Voice Interaction

Synora supports a complete local voice pipeline:


text
Microphone
    ↓
Speech Recognition
    ↓
Local Faster-Whisper
    ↓
Synora AI
    ↓
Response
    ↓
Windows SAPI
    ↓
Speaker


Speech-to-text

* Faster-Whisper

* CPU-based inference

* Local transcription

* Voice activity detection

Text-to-speech

* Windows SAPI

* Local speech synthesis

* No external TTS API required

### Web Search

Synora can search the web when a request requires current external information.

The web pipeline is:


User Query
    ↓
Web Search
    ↓
Relevant Page
    ↓
Content Extraction
    ↓
Local Qwen Summarization
    ↓
Answer


The project uses DuckDuckGo-based search, BeautifulSoup, and local Qwen processing.

### Persistent Memory

Synora includes a local SQLite-based memory system.

It can store information explicitly requested by the user and retrieve previous conversation information.

Memory is stored locally in:

```
data/synora.db
```

The database is intentionally excluded from Git using `.gitignore`.

### Computer Control

Synora can interpret natural-language commands and route supported requests to deterministic computer actions.

Examples include:

```
Open Chrome
Open Brave
Open a website
Search Google
Take a screenshot
Play music
```

Application commands are handled through deterministic routing instead of relying entirely on the language model.

### File and Document Operations

The project includes tools for working with:

* Files

* Code files

* Word documents

* Application operations

Document generation uses `python-docx`.

### Code Generation

Synora can generate code files through its tool layer.

Supported development workflows can include languages such as:

* Python

* Java

* JavaScript

* TypeScript

The project separates code generation from ordinary conversational responses.

### Safety

Potentially dangerous actions can require explicit confirmation.

Configuration:

```
REQUIRE_CONFIRMATION_FOR_DANGEROUS_ACTIONS=true
```

This provides an additional layer between natural-language requests and potentially destructive operations.

# Architecture

Synora follows a layered architecture instead of allowing the language model to directly control every operation.

```
                    ┌─────────────────────┐
                    │      User Input     │
                    │   Text / Voice      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Input Processing  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Core Identity     │
                    │   & Deterministic   │
                    │      Commands       │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
             ┌─────────────┐       ┌─────────────┐
             │    Tools    │       │  Web Search │
             │ Files / App │       │ & Research  │
             │ Code / Docs │       └──────┬──────┘
             └──────┬──────┘              │
                    │                     │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Long-Term Memory  │
                    │       SQLite        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Local LLM       │
                    │ Qwen2.5 3B Instruct │
                    │       Ollama        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Final Response   │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
              ┌───────────┐        ┌────────────┐
              │   Text    │        │ Windows    │
              │ Interface │        │ SAPI TTS   │
              └───────────┘        └────────────┘
```

A key design principle is:

```
Core Identity
      ↓
Deterministic Commands
      ↓
Tools / Web / Files
      ↓
Long-Term Memory
      ↓
Local LLM
```

This reduces unnecessary reliance on the LLM for deterministic operations.

# Voice State Flow

The assistant UI is designed around a voice-first interaction flow:

```
IDLE
 ↓
LISTENING
 ↓
THINKING
 ↓
EXECUTING
 ↓
SPEAKING
 ↓
IDLE
```

This provides a clearer visual representation of what Synora is doing during voice interaction.

# Technology Stack

| Component            | Technology                  |
| -------------------- | --------------------------- |
| Programming Language | Python                      |
| Local LLM            | Qwen2.5 3B Instruct         |
| LLM Runtime          | Ollama                      |
| Web Interface        | Flask                       |
| Frontend             | HTML, CSS, JavaScript       |
| Speech-to-Text       | Faster-Whisper              |
| Audio Input          | SpeechRecognition + PyAudio |
| Text-to-Speech       | Windows SAPI                |
| TTS Integration      | pywin32                     |
| Memory               | SQLite                      |
| Web Search           | DuckDuckGo Search           |
| Web Extraction       | BeautifulSoup               |
| Document Generation  | python-docx                 |
| System Utilities     | psutil                      |
| Version Control      | Git                         |
| Repository           | GitHub                      |

# Project Structure

```
Synora-AI/
│
├── app/
│   │
│   ├── agent/
│   │   ├── executor.py
│   │   ├── planner.py
│   │   └── router.py
│   │
│   ├── ai/
│   │   ├── llm.py
│   │   └── prompts.py
│   │
│   ├── core/
│   │   └── identity.py
│   │
│   ├── memory/
│   │   └── conversation.py
│   │
│   ├── security/
│   │   └── permissions.py
│   │
│   ├── tools/
│   │   ├── app_tools.py
│   │   ├── code_tools.py
│   │   ├── document_tools.py
│   │   └── file_tools.py
│   │
│   ├── ui/
│   │   ├── server.py
│   │   ├── static/
│   │   │   ├── app.js
│   │   │   └── style.css
│   │   └── templates/
│   │       └── index.html
│   │
│   ├── voice/
│   │   ├── speech_to_text.py
│   │   └── text_to_speech.py
│   │
│   ├── web/
│   │   └── search.py
│   │
│   └── main.py
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── run.py
```

# Hardware Used

The current development environment is:

* CPU: AMD Ryzen 5 6600H

* RAM: 16 GB

* GPU: NVIDIA RTX 3050 Laptop GPU, 4 GB

* Storage: 512 GB SSD

* Operating System: Windows

The current Whisper implementation uses CPU inference rather than CUDA.

# Installation

## 1. Clone the repository

Bash

```
git clone https://github.com/999yashpandey/Synora-AI.git
cd Synora-AI
```

## 2. Create a virtual environment

On Windows:

PowerShell

```
python -m venv .venv
```

Activate it:

PowerShell

```
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

PowerShell

```
python -m pip install -r requirements.txt
```

## 4. Install Ollama

Install Ollama from:

[https://ollama.com/](https://ollama.com/)

Then download the configured model:

PowerShell

```
ollama pull qwen2.5:3b-instruct
```

Make sure Ollama is running.

You can verify the model with:

PowerShell

```
ollama list
```

# Configuration

Create a local `.env` file if configuration needs to be customized.

Example:

```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b-instruct

REQUIRE_CONFIRMATION_FOR_DANGEROUS_ACTIONS=true
```

A template is provided as:

```
.env.example
```

Do not commit personal `.env` files or local databases to GitHub.

# Running Synora

## Terminal Assistant

Activate the virtual environment:

PowerShell

```
.\.venv\Scripts\Activate.ps1
```

Run:

PowerShell

```
python -m app.main
```

## Web Interface

Run:

PowerShell

```
python -m app.ui.server
```

Then open the local address shown by Flask in your browser.

# Example Commands

Synora can handle requests such as:

```
Who are you?

Who created you?

Open Chrome

Open Brave

Search the web for the latest AI news

Search the web for NVIDIA RTX 3050 specifications

Take a screenshot

Open YouTube

Create a Python file

Create a Word document

Remember this forever that Synora AI was created by Yash Pandey.
```

The exact set of supported commands can evolve as the project develops.

# Privacy

Synora is designed around a local-first architecture.

The core language model runs through local Ollama rather than requiring a hosted LLM API.

Local data such as conversation memory is stored in the project's local `data/` directory.

However, when the user explicitly requests a web search, Synora must access external websites to retrieve current information.

Therefore:

* Normal LLM processing can remain local.

* Conversation memory is stored locally.

* Voice transcription is performed locally.

* Text-to-speech is performed locally.

* Web-search requests require internet access.

* Retrieved web content is processed by the local LLM.

# Design Goals

Synora is being developed with the following principles:

### Local-first

Prefer local models and local processing whenever practical.

### Deterministic where possible

Use conventional program logic for operations that should not depend on an LLM's interpretation.

### Useful over flashy

The assistant should perform practical tasks rather than simply simulate an AI assistant.

### Privacy-conscious

Keep personal memory, local conversations, and local processing on the user's machine whenever possible.

### Modular

AI, memory, tools, web search, voice, security, and UI are separated into different modules so individual components can evolve independently.

# Current Limitations

Synora is an active development project and is not intended to be presented as a production-grade commercial assistant.

Current limitations include:

* Local 3B-class models have limited reasoning capability compared with larger cloud models.

* Voice transcription accuracy depends on microphone quality and background noise.

* CPU-based Whisper inference is slower than optimized GPU inference.

* Web search depends on internet availability and external websites.

* Computer-control capabilities are limited to implemented deterministic actions.

* Long-term memory is currently based on explicit local storage rather than human-like memory.

* The system is designed primarily for Windows.

* The project does not attempt to provide perfect autonomous planning or unrestricted computer control.

# Future Scope

Potential future improvements include:

* Better local models

* More robust agent planning

* Improved voice activity detection

* Wake-word support

* More application integrations

* Better memory retrieval

* Semantic/vector memory

* More advanced computer-use capabilities

* Improved UI animations

* Offline web-cache capabilities

* More extensive safety and permission controls

* Cross-platform support

* Optional GPU-accelerated speech processing

* More advanced task automation

These are future directions rather than guaranteed current capabilities.

# Project Philosophy

Synora is an exploration of how far a useful personal AI assistant can be developed using:

* Local open-weight language models

* Python

* Deterministic automation

* Local memory

* Local speech processing

* Web research

* A lightweight web interface

The goal is not simply to build another chatbot.

The goal is to build a practical personal AI system that can understand requests, use tools, remember useful information, interact with the computer, research the web when necessary, and communicate through both text and voice while keeping the core system local.

# Author

Yash Pandey

B.Tech Computer Science & Engineering

GitHub:

[https://github.com/999yashpandey](https://github.com/999yashpandey)

# License

This project is licensed under the terms specified in the repository's `LICENSE` file.

````
After saving the file, run:

```powershell
git diff -- README.md
````

