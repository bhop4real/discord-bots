# bot.py
import discord
from discord.ext import commands
from discord import app_commands
import io
import re

from game import MinesweeperGame
from image_generator import BoardImageGenerator
from config import DISCORD_TOKEN

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Globals
user_games = {}
user_difficulty = {}
image_gen = BoardImageGenerator()

DIFFICULTY_SETTINGS = {
    'easy': {'width': 9, 'height': 9, 'mines': 10},
    'medium': {'width': 16, 'height': 16, 'mines': 40},
    'hard': {'width': 30, 'height': 16, 'mines': 99}
}


# --- Helper Functions ---
def get_or_create_game(user_id: int) -> MinesweeperGame:
    if user_id not in user_games:
        difficulty = user_difficulty.get(user_id, 'easy')
        settings = DIFFICULTY_SETTINGS[difficulty]
        user_games[user_id] = MinesweeperGame(settings['width'], settings['height'], settings['mines'])
    return user_games[user_id]


def coords_to_str(x: int, y: int) -> str:
    return f"{chr(ord('A') + x)}{y + 1}"


def _parse_range(range_str: str, max_x: int, max_y: int) -> (list, str):
    range_pattern = re.compile(r'^([a-zA-Z])(\d+)-([a-zA-Z])(\d+)$')
    match = range_pattern.match(range_str)
    if not match: return [], ""

    c1, r1_str, c2, r2_str = match.groups()
    x1, x2 = ord(c1) - ord('a'), ord(c2) - ord('a')
    y1, y2 = int(r1_str) - 1, int(r2_str) - 1

    if not (0 <= x1 < max_x and 0 <= y1 < max_y and 0 <= x2 < max_x and 0 <= y2 < max_y):
        return [], f"Range `{range_str}` is out of board bounds."

    if x1 > x2: x1, x2 = x2, x1
    if y1 > y2: y1, y2 = y2, y1

    coords = []
    if y1 == y2 and x1 != x2:
        for x in range(x1, x2 + 1): coords.append((x, y1))
        return coords, ""
    elif x1 == x2 and y1 != y2:
        for y in range(y1, y2 + 1): coords.append((x1, y))
        return coords, ""
    elif x1 == x2 and y1 == y2:
        return [(x1, y1)], ""
    else:
        return [], f"Invalid range `{range_str}`. Ranges must be horizontal or vertical."


def parse_message_actions(text: str, max_x: int, max_y: int):
    actions = {'reveal': [], 'mark_flag': [], 'mark_question': []}
    warnings = []
    current_mode = 'reveal'

    words = text.lower().split()
    pos_pattern = re.compile(r'^([a-zA-Z])(\d+)$')

    for word in words:
        if word in ('r', 'reveal'): current_mode = 'reveal'; continue
        if word in ('m', 'mark'): current_mode = 'mark_flag'; continue
        if word in ('q', 'question'): current_mode = 'mark_question'; continue

        coords, error = _parse_range(word, max_x, max_y)
        if error: warnings.append(error); continue
        if coords: actions[current_mode].extend(coords); continue

        match = pos_pattern.match(word)
        if match:
            col_char, row_str = match.groups()
            x, y = ord(col_char) - ord('a'), int(row_str) - 1
            if 0 <= x < max_x and 0 <= y < max_y:
                actions[current_mode].append((x, y))
            else:
                warnings.append(f"Coordinate `{word}` is out of bounds.")

    return actions, warnings


async def execute_actions(source, game: MinesweeperGame, actions: dict, warnings: list):
    user_id = source.author.id if isinstance(source, discord.Message) else source.user.id
    all_warnings = warnings[:]

    if game.first_move and len(actions['reveal']) > 1:
        await source.channel.send("You can only reveal one cell on your first move.")
        return

    for x, y in actions['mark_question']: game.mark_question(x, y)
    for x, y in actions['mark_flag']:
        game.mark_flag(x, y)
        if game.game_over: break

    if not game.game_over:
        for x, y in actions['reveal']:
            pos = (x, y)
            if pos in game.revealed: continue
            if pos in game.flags: all_warnings.append(
                f"Cannot reveal **{coords_to_str(x, y)}**: it is flagged."); continue
            if pos in game.questioned: all_warnings.append(
                f"Cannot reveal **{coords_to_str(x, y)}**: it has a question mark."); continue
            game.reveal(x, y)
            if game.game_over: break

    status_message = "\n".join(all_warnings)
    if game.game_over:
        if game.win:
            status_message += "\n**Congratulations! You've cleared the board!** 🎉"
        else:
            status_message += f"\n**Game Over! You hit a mine.**"
        if user_id in user_games: del user_games[user_id]

    image = image_gen.generate_image(game)
    with io.BytesIO() as image_binary:
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        file = discord.File(fp=image_binary, filename='board.png')
        if isinstance(source, discord.Interaction):
            await source.followup.send(content=status_message.strip(), file=file)
        else:
            await source.channel.send(content=status_message.strip(), file=file)


# --- Bot Events & Commands ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user or not isinstance(message.channel, discord.DMChannel) or message.content.startswith(
            '/'):
        return
    game = get_or_create_game(message.author.id)
    actions, warnings = parse_message_actions(message.content, game.width, game.height)
    if not any(actions.values()) and not warnings: return
    await execute_actions(message, game, actions, warnings)


@bot.tree.command(name="help", description="Shows how to play the game and use commands.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Minesweeper Bot Help", color=discord.Color.blue())
    embed.add_field(name="How to Play",
                    value="Clear the board of mines. Numbers show adjacent mines. Your first click is always safe!",
                    inline=False)
    embed.add_field(name="Quick Actions (Recommended)",
                    value="Combine actions and ranges in one message! The prefixes `r`, `m`, and `q` set the mode for the coordinates that follow.\n\n• **To reveal:** `a1` or `r a1 b2-b5`\n• **To flag/un-flag:** `m c3`\n• **To question/un-question:** `q d4`\n\n**Example:** `r a1-e1 m f1 q g1` reveals A1 to E1, toggles a flag on F1, and toggles a question mark on G1.",
                    inline=False)
    embed.add_field(name="Slash Commands",
                    value="`/start` or `/reset`: Starts a new game.\n`/difficulty`: Sets difficulty for the next game.\n`/reveal`, `/mark`, `/question`: For single-action commands.",
                    inline=False)
    embed.set_footer(text="Win by revealing all safe cells or by flagging all mines correctly.")
    await interaction.response.send_message(embed=embed, ephemeral=True)


async def start_reset_command(interaction: discord.Interaction, is_reset: bool):
    await interaction.response.defer()
    user_id = interaction.user.id
    if is_reset and user_id in user_games:
        del user_games[user_id]
    game = get_or_create_game(user_id)
    with io.BytesIO() as image_binary:
        image_gen.generate_image(game).save(image_binary, 'PNG')
        image_binary.seek(0)
        await interaction.followup.send("Game reset!" if is_reset else "New game started!",
                                        file=discord.File(fp=image_binary, filename='board.png'))


@bot.tree.command(name="start", description="Starts a new Minesweeper game.")
async def start(interaction: discord.Interaction): await start_reset_command(interaction, is_reset=False)


@bot.tree.command(name="reset", description="Resets your current game.")
async def reset(interaction: discord.Interaction): await start_reset_command(interaction, is_reset=True)


@bot.tree.command(name="difficulty", description="Sets the difficulty for your next game.")
@app_commands.choices(level=[
    app_commands.Choice(name="Easy (9x9, 10 mines)", value="easy"),
    app_commands.Choice(name="Medium (16x16, 40 mines)", value="medium"),
    app_commands.Choice(name="Hard (30x16, 99 mines)", value="hard"),
])
async def difficulty(interaction: discord.Interaction, level: app_commands.Choice[str]):
    user_difficulty[interaction.user.id] = level.value
    await interaction.response.send_message(f"Difficulty set to **{level.name}**. It will apply on your next game.")


async def single_action_command(interaction: discord.Interaction, locations: str, action_type: str):
    await interaction.response.defer(thinking=True)
    game = get_or_create_game(interaction.user.id)
    prefix = {'reveal': 'r', 'mark_flag': 'm', 'mark_question': 'q'}.get(action_type, 'r')
    command_str = f"{prefix} {locations}"
    actions, warnings = parse_message_actions(command_str, game.width, game.height)
    await execute_actions(interaction, game, actions, warnings)


@bot.tree.command(name="reveal", description="Reveals one or more cells (e.g., a1 b2-b5).")
async def reveal(interaction: discord.Interaction, locations: str): await single_action_command(interaction, locations,
                                                                                                'reveal')


@bot.tree.command(name="mark", description="Toggles a flag on one or more cells (e.g., a1 b2-b5).")
async def mark(interaction: discord.Interaction, locations: str): await single_action_command(interaction, locations,
                                                                                              'mark_flag')


@bot.tree.command(name="question", description="Toggles a question mark on cells (e.g., a1 b2-b5).")
async def question(interaction: discord.Interaction, locations: str): await single_action_command(interaction,
                                                                                                  locations,
                                                                                                  'mark_question')


bot.run(DISCORD_TOKEN)