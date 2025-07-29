import discord
from discord import app_commands
from typing import Literal
import asyncio

import config
import database as db
from providers.deepseek_provider import DeepSeekProvider
from openai import APIError, RateLimitError, AuthenticationError

# --- Initialization and State Management ---
try:
    ai_provider = DeepSeekProvider(api_key=config.DEEPSEEK_API_KEY)
except ValueError as e:
    print(f"Configuration Error: {e}")
    exit(1)

# Initialize the database
db.init_db()

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
        print('Ready to receive DMs!')
        print('-' * 20)

client = LumenClient(intents=intents)

# In-memory state for handling real-time user input buffering.
# This does not need to be persisted in the database.
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

    # 1. Get settings and conversation history from the database
    settings = db.get_user_settings(user_id)
    model = settings.get('model', config.DEFAULT_MODEL)
    conversation_history = db.get_conversation_history(user_id)
    conversation_history.append({"role": "user", "content": prompt})

    # 2. Make API Call and handle errors
    try:
        api_response = await asyncio.to_thread(
            ai_provider.get_response, conversation_history, model, config.MAX_REPLY_TOKENS
        )
    except AuthenticationError:
        await channel.send("`**Authentication Error (401)**, API key is invalid. Contant the host to fix this problem.`")
        return
    except RateLimitError:
        await channel.send("`**Rate Limit Reached (429)**. You're sending requests too quickly. Please wait.`")
        return
    except APIError as e:
        if e.code == "insufficient_balance":
            await channel.send("`**Insufficient Balance (402)**. Tell the host to get some balance.`")
        elif e.status_code >= 500:
            await channel.send(f"`The service is currently down. **Server Error ({e.status_code})**.`")
        else:
            await channel.send(f"`An unexpected API error occurred (Code: {e.status_code}).`")
        return
    except Exception as e:
        print(f"A general error occurred for user {user_id}: {e}")
        await channel.send("An unexpected internal error occurred.")
        return

    # 3. Process and send the successful response
    final_answer = api_response.choices[0].message.content

    await send_reply_with_delay(channel, final_answer)

    # 4. Save the user and assistant messages to the database
    db.add_message_to_history(user_id, 'user', prompt)
    db.add_message_to_history(user_id, 'assistant', final_answer)
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

    # Clear in-memory buffer for this user, if it exists
    if user_id in user_message_buffers:
        del user_message_buffers[user_id]
    if user_id in user_input_tasks:
        user_input_tasks[user_id].cancel()
        del user_input_tasks[user_id]

    if db.clear_conversation_history(user_id):
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
    db.update_user_settings(user_id, model)
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