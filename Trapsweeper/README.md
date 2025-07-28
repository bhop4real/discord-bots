# Trapsweeper

This project is a fully functional Minesweeper game that can be played via a Discord bot in Direct Messages or run as a standalone desktop application with a GUI.

## Features

- **Multiple Difficulties:** Choose between Easy, Medium, and Hard settings.
- **Safe First Click:** The first cell you reveal is guaranteed to be safe; mines are generated after the first move.
- **Advanced Input:**
    - **Combined Actions:** Reveal, flag, and question tiles in a single message (e.g., `r a1 m b1 q c1`).
    - **Range Parsing:** Reveal or mark entire rows/columns at once (e.g., `a1-e1`).

## Project Structure

The codebase is organized to separate concerns, making it easy to maintain and extend.

```
minesweeper/
├── bot.py                # Main Discord bot application
├── main_gui.py           # Entry point for the local GUI mode
├── game.py               # Core Minesweeper game logic
├── image_generator.py    # Generates board images from game state
├── gui.py                # Tkinter GUI implementation
├── config.py             # Bot token and font configuration
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── assets/
    ├── flag.png
    ├── mine.png
    ├── question.png
    └── FiraCode-Regular.ttf  # Or your chosen font file
```

## Setup and Installation

Follow these steps to get the bot running.

### 1. Prerequisites
- Python 3.8 or newer.
- A Discord account and a bot account.
- A Discord server where you can invite the bot.

### 2. Download/clone the Repository
Clone this project to your local machine:
```bash
git clone <your-repository-url>
cd minesweeper
```

Or download manually to a directory of your choice.

### 3. Install Dependencies
Install the required Python libraries using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### 4. Create a Discord Bot
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click "New Application" and give it a name (e.g., "Trapsweeper").
3. Go to the "Bot" tab and click "Add Bot".
4. Under the bot's username, click "Reset Token" to reveal and copy your bot's token. **Treat this token like a password.**
5. Enable the **Message Content Intent** under the "Privileged Gateway Intents" section.

### 5. Configure the Bot
1. Rename `config.py.example` to `config.py` if you have a template, or create `config.py`.
2. Open `config.py` and paste your bot token:
   ```python
   # config.py
   DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"
   FONT_FILENAME = "FiraCode-Regular.ttf"
   ```
3. Ensure the font specified in `FONT_FILENAME` exists in the `assets` directory.

### 6. Set Up Assets
- Place your `flag.png`, `mine.png`, `question.png`, and a `.ttf` font file inside the `assets/` directory.
- The icons should ideally be square (e.g., 20x20 pixels).

*There are default icons, but it's not suggested to use them.*

### 7. Invite the Bot to Your Server
1. In the Discord Developer Portal, go to the "OAuth2" -> "URL Generator" tab.
2. Select the scopes `bot` and `applications.commands`.
3. Under "Bot Permissions", grant it `Send Messages` and `Attach Files`.
4. Copy the generated URL, paste it into your browser, and invite the bot to a server where you have administrator permissions.

## Usage

### Running the Discord Bot
To start the bot, run the `bot.py` file:
```bash
python bot.py
```
The bot will print a confirmation message to your console once it's logged in and ready. You can then interact with it by sending it a Direct Message.

### Running the GUI Version
For testing or local play, you can run the GUI version:
```bash
python main_gui.py
```

## Bot Commands & Actions

Interact with the bot in its DMs. The recommended way is to use quick actions.

#### Quick Actions (Message Parsing)
- **Reveal:** `a1` or `r a1 b2`
- **Flag/Mark:** `m c3`
- **Question:** `q d4`
- **Ranges:** `a1-e1` or `f2-f7` (must be a straight horizontal or vertical line)
- **Combined:** You can mix and match in one message: `r a1-e1 m f1 q g1`

#### Slash Commands
- `/help`: Shows a detailed help message.
- `/start`: Starts a fresh game.
- `/reset`: Resets your current game board.
- `/difficulty <level>`: Sets the difficulty for your *next* game (`easy`, `medium`, `hard`).
- `/reveal <locations>`: A slash command for revealing tiles.
- `/mark <locations>`: A slash command for flagging tiles.
- `/question <locations>`: A slash command for questioning tiles.