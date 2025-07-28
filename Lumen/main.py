import discord
from discord import app_commands
from typing import Literal
import asyncio

import json
import os
import config
from providers.deepseek_provider import DeepSeekProvider
from openai import APIError, RateLimitError, AuthenticationError

# --- File Paths for Persistence ---
SETTINGS_FILE = 'user_settings.json'
CONVERSATIONS_FILE = 'conversations.json'

# --- 1. Helper Functions for Saving and Loading ---

def save_data(file_path, data):
    """Saves a dictionary to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")

def load_data(file_path):
    """Loads data from a JSON file."""
    if not os.path.exists(file_path):
        return {} # Return an empty dict if the file doesn't exist yet
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # JSON saves all keys as strings, so we must convert user IDs back to integers
            return {int(k): v for k, v in data.items()}
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading or parsing {file_path}. Starting with empty data. Error: {e}")
        return {} # Return empty dict if file is corrupted or empty

# --- Initialization and State Management ---
try:
    ai_provider = DeepSeekProvider(api_key=config.DEEPSEEK_API_KEY)
except ValueError as e:
    print(f"Configuration Error: {e}")
    exit(1)

intents = discord.Intents.default()
intents.messages = True
intents.dm_messages = True
intents.message_content = True

class LumenClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f'Lumen is logged in as {self.user}')
        print(f"Loaded data for {len(user_settings)} users and {len(user_conversations)} conversations.")
        print('Ready to receive DMs!')
        print('-' * 20)

client = LumenClient(intents=intents)

# --- 2. Load Existing Data on Startup ---
user_conversations = load_data(CONVERSATIONS_FILE)
user_settings = load_data(SETTINGS_FILE)
user_input_tasks = {}
user_message_buffers = {}


# --- Core Logic and Helper Functions ---

async def send_reply_with_delay(channel: discord.abc.Messageable, text: str):
    """Splits a message and sends each part with a realistic typing delay."""
    if not text:
        return
    chars_per_second = (config.TYPING_SPEED_WPM * 5) / 60
    for part in text.split(config.MESSAGE_BREAKER):
        part = part.strip()
        if part:
            delay = len(part) / chars_per_second
            async with channel.typing():
                await asyncio.sleep(min(delay, 10.0))
            await channel.send(part)


async def get_and_process_ai_response(channel: discord.abc.Messageable, user: discord.User, prompt: str):
    """The central function to get and process the AI response."""
    user_id = user.id

    settings = user_settings.get(user_id, {})
    model = settings.get('model', config.DEFAULT_MODEL)
    show_cot = settings.get('show_cot', False)

    if user_id not in user_conversations:
        user_conversations[user_id] = [{"role": "system", "content": config.SYSTEM_PROMPT}]
    user_conversations[user_id].append({"role": "user", "content": prompt})

    # 2. Make API Call and handle errors
    try:
        api_response = await asyncio.to_thread(
            ai_provider.get_response, user_conversations[user_id], model, config.MAX_REPLY_TOKENS
        )
    except AuthenticationError:
        await channel.send("`**Authentication Error (401)**, API key is invalid. Contant the host to fix this problem.`")
        # We failed, so remove the user message we just added
        user_conversations[user_id].pop()
        return
    except RateLimitError:
        await channel.send("`**Rate Limit Reached (429)**. You're sending requests too quickly. Please wait.`")
        user_conversations[user_id].pop()
        return
    except APIError as e:
        if e.code == "insufficient_balance":
            await channel.send("`**Insufficient Balance (402)**. Tell the host to get some balance.`")
            user_conversations[user_id].pop()
        elif e.status_code >= 500:
            await channel.send(f"`The service is currently down. **Server Error ({e.status_code})**.`")
            user_conversations[user_id].pop()
        else:
            await channel.send(f"`An unexpected API error occurred (Code: {e.status_code}).`")
            user_conversations[user_id].pop()
        return
    except Exception as e:
        print(f"A general error occurred for user {user_id}: {e}")
        await channel.send("An unexpected internal error occurred.")
        return

    # 3. Process and send the successful response
    final_answer = api_response.choices[0].message.content
    response_dict = api_response.model_dump()

    await send_reply_with_delay(channel, final_answer)
    user_conversations[user_id].append({"role": "assistant", "content": final_answer})
    save_data(CONVERSATIONS_FILE, user_conversations)
    print(f"Saved conversation for user {user_id}")


# --- Bot Event Handler for Messages ---

async def delayed_task_runner(message: discord.Message):
    """Waits for the delay then runs the AI processing."""
    await asyncio.sleep(config.USER_INPUT_DELAY)
    user_id = message.author.id

    # Combine all messages buffered for this user
    prompt = "\n".join(user_message_buffers.pop(user_id, [])).strip()
    if not prompt:
        return

    print(f"Processing buffered prompt from {message.author}: '{prompt}'")
    await get_and_process_ai_response(message.channel, message.author, prompt)


@client.event
async def on_message(message: discord.Message):
    """Buffers user input and schedules it for processing."""
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = message.author.id

    if user_id in user_input_tasks:
        user_input_tasks[user_id].cancel()

    if user_id not in user_message_buffers:
        user_message_buffers[user_id] = []
    user_message_buffers[user_id].append(message.content)

    # Schedule the new task
    user_input_tasks[user_id] = asyncio.create_task(delayed_task_runner(message))


# --- Slash Commands ---

@client.tree.command(name="chat", description="Send a single, direct message to Lumen.")
@app_commands.describe(prompt="Your message to the AI.")
async def chat(interaction: discord.Interaction, prompt: str):
    # Acknowledge the command immediately
    await interaction.response.defer(thinking=True, ephemeral=True)
    print(f"Processing /chat command from {interaction.user}: '{prompt}'")
    # Because we deferred, subsequent messages must use followup.send
    # The helper functions need to be aware of this. A direct channel.send will fail.
    # The easiest way is to treat the interaction's channel as the destination.
    await get_and_process_ai_response(interaction.channel, interaction.user, prompt)
    # Edit the original "thinking" message to show it's done.
    await interaction.edit_original_response(content="Response sent!")


@client.tree.command(name="clear", description="Clears your conversation history with Lumen.")
async def clear(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in user_conversations:
        del user_conversations[user_id]
        if user_id in user_message_buffers:
            del user_message_buffers[user_id]

        save_data(CONVERSATIONS_FILE, user_conversations)
        await interaction.response.send_message("Your conversation history has been cleared.", ephemeral=True)
    else:
        await interaction.response.send_message("You have no history to clear.", ephemeral=True)


@client.tree.command(name="settings", description="Change the AI model Lumen uses.")
@app_commands.describe(model="The AI model you want to use for responses.")
async def settings(
        interaction: discord.Interaction,
        model: Literal[tuple(config.ALLOWED_MODELS)]
):
    user_id = interaction.user.id
    if user_id not in user_settings:
        user_settings[user_id] = {}

    user_settings[user_id]['model'] = model

    save_data(SETTINGS_FILE, user_settings)

    await interaction.response.send_message(
        f"`The model has been changed to **{model}**`",
        ephemeral=True
    )


# --- Run the Bot ---
if __name__ == "__main__":
    if not all([config.DISCORD_TOKEN,
                config.DEEPSEEK_API_KEY]) or 'your' in config.DISCORD_TOKEN or 'your' in config.DEEPSEEK_API_KEY:
        print("ERROR: Bot token or API key is missing or is a placeholder in config.py.")
    else:
        client.run(config.DISCORD_TOKEN)