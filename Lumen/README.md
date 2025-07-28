# Lumen: A Persona-Driven Discord Chatbot

## Introduction

Lumen is a persona-driven chatbot for Discord, powered by the DeepSeek language model API. Its core design principle is to simulate natural, human-like conversation through a detailed and configurable system prompt.

The system is architected to be modular and persistent, saving user settings and conversation histories to local JSON files, ensuring data continuity across restarts.

## Demonstration

<img width="586" height="756" alt="image" src="https://github.com/user-attachments/assets/cf3a010d-ad4b-47e7-89cf-d07e6c8d345f" />

## System Architecture

The project is organized into several key components:

```
/
├── README.md                 # Project documentation
├── config.py                 # All configuration, API keys, and persona definitions
├── main.py                   # Main application logic, event handlers, and commands
├── requirements.txt          # Python package dependencies
│
├── providers/
│   ├── __init__.py
│   ├── base_provider.py      # ABC for providers
│   └── deepseek_provider.py  # A client for the DeepSeek API
│
├── conversations.json        # (Generated) Stores user conversation histories
└── user_settings.json        # (Generated) Stores user settings
```

## Installation Guide

### 1. Prerequisites

*   Python 3.8 or higher
*   A valid DeepSeek API Key
*   A Discord Application and Bot Token

*Why DeepSeek? Of course, it's much more affordable for me.*

### 2. Discord Application Setup

1.  Navigate to the [Discord Developer Portal](https://discord.com/developers/applications) and create a **New Application**.
2.  Go to the **"Bot"** tab and click **"Add Bot"**.
3.  Click **"Reset Token"** to generate a bot token. This token is sensitive and should not be shared publicly.
4.  Under the **Privileged Gateway Intents** section, enable the `MESSAGE CONTENT INTENT`.
5.  Navigate to the **OAuth2 > URL Generator** page. Select the `bot` scope.
6.  In the "Bot Permissions" section that appears, grant `Send Messages` and `Read Message History`.
7.  Copy the generated URL and use it to invite the bot to your Discord server.

### 3. Project Installation

1.  Clone the repository to your local machine.
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```
    *Or, manually download it.*

2.  Install the required Python packages using pip.
    ```bash
    pip install -r requirements.txt
    ```

### 4. Configuration

1.  Open the `config.py` file in a text editor.
2.  Insert your credentials into the following variables:
    ```python
    DISCORD_TOKEN = "your_discord_bot_token_here"
    DEEPSEEK_API_KEY = "your_deepseek_api_key_here"
    ```
3.  Review and modify other settings in `config.py` as needed, including the `SYSTEM_PROMPT` which defines the bot's core behavior.

### 5. Execution

Run the bot from the project's root directory:
```bash
python main.py
```
The console will print a confirmation message once the bot is successfully connected to Discord.

## Usage

Interaction with Lumen is performed via Direct Messages and slash commands.

*   **Standard Chat:** Simply send messages in your DM channel with the bot. The bot will wait for you to stop typing before generating a response.
*   **/settings `[model]`**: Configures the AI model used for your user profile.
*   **/clear**: Deletes your personal conversation history from the bot's memory and persistent storage.

## Core Concept: Prompt Engineering

Lumen's behavior is not dictated by complex logic but by a detailed set of instructions provided to the language model. This is managed in the `SYSTEM_PROMPT` variable within `config.py`. This prompt is composed of several key sections:

*   **Core Directives:** Non-negotiable rules the AI must follow, such as using the message-splitting delimiter and maintaining character integrity.
*   **Behavioral Heuristics:** A set of guidelines that humanize the AI's responses, such as avoiding lists of questions and using less formal punctuation.
*   **Contextual Knowledge Base:** A section that provides specific, contextual information to the AI, such as the nuanced meanings of certain emojis in internet culture.
*   **Persona Definition:** A detailed description of the AI's character, including its name, background, personality traits, and speech style.

Modifying these sections is the primary method of altering and refining the bot's behavior.
