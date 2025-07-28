# image_generator.py
from PIL import Image, ImageDraw, ImageFont
from game import MinesweeperGame
import os
import config


class BoardImageGenerator:
    def __init__(self, cell_size=30, margin=25):
        self.cell_size = cell_size
        self.margin = margin

        self.colors = {
            'bg': '#c0c0c0', 'border_light': '#ffffff', 'border_dark': '#7b7b7b',
            'revealed': '#bdbdbd', 'mine_bg_fail': '#ff0000', '1': '#0000ff',
            '2': '#008200', '3': '#ff0000', '4': '#000084', '5': '#840000',
            '6': '#008284', '7': '#840084', '8': '#757575'
        }

        try:
            # Use font from config file
            font_path = os.path.join('assets', config.FONT_FILENAME)
            self.font = ImageFont.truetype(font_path, size=int(self.cell_size * 0.7))
            self.header_font = ImageFont.truetype(font_path, size=int(self.margin * 0.6))
        except IOError:
            print(f"Warning: {config.FONT_FILENAME} not found. Using default font.")
            self.font = ImageFont.load_default()
            self.header_font = ImageFont.load_default()

        try:
            icon_size = int(self.cell_size * 0.7)
            self.flag_img = Image.open(os.path.join('assets', 'flag.png')).convert("RGBA").resize(
                (icon_size, icon_size))
            self.mine_img = Image.open(os.path.join('assets', 'mine.png')).convert("RGBA").resize(
                (icon_size, icon_size))
            # Load the new question mark image
            self.question_img = Image.open(os.path.join('assets', 'question.png')).convert("RGBA").resize(
                (icon_size, icon_size))
        except FileNotFoundError as e:
            raise SystemExit(
                f"Error: Asset file not found: {e.filename}. Ensure 'flag.png', 'mine.png', and 'question.png' are in the 'assets' directory.")

    def generate_image(self, game: MinesweeperGame) -> Image:
        board_width_px = game.width * self.cell_size
        board_height_px = game.height * self.cell_size
        img_width = board_width_px + self.margin
        img_height = board_height_px + self.margin

        image = Image.new('RGB', (img_width, img_height), self.colors['bg'])
        draw = ImageDraw.Draw(image, 'RGBA')

        self._draw_headers(draw, game, board_width_px, board_height_px)

        for y in range(game.height):
            for x in range(game.width):
                self._draw_cell(draw, image, game, x, y)

        return image

    def _draw_headers(self, draw: ImageDraw, game: MinesweeperGame, board_w: int, board_h: int):
        for i in range(game.width):
            letter = chr(ord('A') + i)
            bbox = draw.textbbox((0, 0), letter, font=self.header_font)
            text_width = bbox[2] - bbox[0]
            pos_x = self.margin + (i * self.cell_size) + (self.cell_size - text_width) / 2
            pos_y = (self.margin - bbox[3] - bbox[1]) / 2
            draw.text((pos_x, pos_y), letter, fill='black', font=self.header_font)

        for i in range(game.height):
            num = str(i + 1)
            bbox = draw.textbbox((0, 0), num, font=self.header_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            pos_x = (self.margin - text_width) / 2
            pos_y = self.margin + (i * self.cell_size) + (self.cell_size - text_height) / 2 - 2
            draw.text((pos_x, pos_y), num, fill='black', font=self.header_font)

    def _draw_cell(self, draw: ImageDraw, image: Image, game: MinesweeperGame, x: int, y: int):
        px, py = self.margin + x * self.cell_size, self.margin + y * self.cell_size
        pos = (x, y)

        is_revealed = pos in game.revealed
        is_flagged = pos in game.flags
        is_questioned = pos in game.questioned  # Check if questioned
        is_mine = pos in game.mines

        if not is_revealed:
            draw.rectangle([px, py, px + self.cell_size, py + self.cell_size], fill=self.colors['bg'])
            draw.line([(px, py), (px + self.cell_size - 1, py)], fill=self.colors['border_light'])
            draw.line([(px, py), (px, py + self.cell_size - 1)], fill=self.colors['border_light'])
            draw.line([(px + self.cell_size - 1, py), (px + self.cell_size - 1, py + self.cell_size - 1)],
                      fill=self.colors['border_dark'])
            draw.line([(px, py + self.cell_size - 1), (px + self.cell_size - 1, py + self.cell_size - 1)],
                      fill=self.colors['border_dark'])
        else:
            bg_color = self.colors['mine_bg_fail'] if is_mine else self.colors['revealed']
            draw.rectangle([px, py, px + self.cell_size, py + self.cell_size], fill=bg_color)
            draw.line([(px, py), (px + self.cell_size - 1, py)], fill=self.colors['border_dark'])
            draw.line([(px, py), (px, py + self.cell_size - 1)], fill=self.colors['border_dark'])

        content_pos = (px + (self.cell_size - self.flag_img.width) // 2,
                       py + (self.cell_size - self.flag_img.height) // 2)

        if not is_revealed:
            if is_flagged:
                image.paste(self.flag_img, content_pos, self.flag_img)
            elif is_questioned:  # Draw question mark
                image.paste(self.question_img, content_pos, self.question_img)
        elif is_revealed:
            if is_mine:
                image.paste(self.mine_img, content_pos, self.mine_img)
            else:
                cell_value = game.board[y][x]
                if cell_value != ' ':
                    text_color = self.colors.get(cell_value, 'black')
                    bbox = draw.textbbox((0, 0), cell_value, font=self.font)
                    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    text_pos = (px + (self.cell_size - text_width) / 2,
                                py + (self.cell_size - text_height) / 2 - 2)
                    draw.text(text_pos, cell_value, fill=text_color, font=self.font)
        elif game.game_over and is_mine and not is_flagged:
            image.paste(self.mine_img, content_pos, self.mine_img)