import tkinter as tk
from tkinter import messagebox, font
from PIL import Image, ImageTk, ImageGrab


class MinesweeperGUI:
    def __init__(self, master, game):
        self.master = master
        self.game = game
        self.buttons = {}

        # --- Visual Configuration ---
        self.CELL_SIZE = 30
        self.font = font.Font(family='Helvetica', size=int(self.CELL_SIZE / 2), weight='bold')

        icon_size = int(self.CELL_SIZE * 0.75)
        self.flag_image = ImageTk.PhotoImage(Image.open("assets/flag.png").resize((icon_size, icon_size)))
        self.mine_image = ImageTk.PhotoImage(Image.open("assets/mine.png").resize((icon_size, icon_size)))

        self.pixel = tk.PhotoImage(width=1, height=1)

        self.frame = tk.Frame(self.master)
        self.frame.pack()

        self.create_widgets()

    def create_widgets(self):
        for y in range(self.game.height):
            for x in range(self.game.width):
                button = tk.Button(
                    self.frame,
                    image=self.pixel,
                    width=self.CELL_SIZE,
                    height=self.CELL_SIZE,
                    compound='c',
                    relief=tk.RAISED,
                    font=self.font
                )
                button.grid(row=y, column=x)
                button.bind('<Button-1>', lambda e, x=x, y=y: self.on_left_click(x, y))
                button.bind('<Button-3>', lambda e, x=x, y=y: self.on_right_click(x, y))
                self.buttons[(x, y)] = button

    def on_left_click(self, x, y):
        if self.game.game_over or (x, y) in self.game.revealed:
            return

        self.game.reveal(x, y)
        self.update_buttons()

        if self.game.game_over:
            if self.game.win:
                messagebox.showinfo("Minesweeper", "Congratulations! You won!")
            else:
                messagebox.showerror("Minesweeper", "Game Over! You hit a mine.")
            self.reveal_all()

    def on_right_click(self, x, y):
        if not self.game.game_over:
            self.game.flag(x, y)
            self.update_buttons()

    def update_buttons(self):
        color_map = {
            '1': 'blue', '2': 'green', '3': 'red', '4': 'darkblue',
            '5': 'maroon', '6': 'cyan', '7': 'black', '8': 'gray'
        }

        for y in range(self.game.height):
            for x in range(self.game.width):
                button = self.buttons[(x, y)]
                if (x, y) in self.game.revealed:
                    if (x, y) in self.game.mines:
                        button.config(image=self.mine_image, bg='red', relief=tk.SUNKEN, state=tk.DISABLED)
                    else:
                        cell_value = self.game.board[y][x]
                        button.config(
                            text=cell_value if cell_value != ' ' else '',
                            fg=color_map.get(cell_value, 'black'),
                            relief=tk.SUNKEN,
                            state=tk.DISABLED,
                            disabledforeground=color_map.get(cell_value, 'black')
                        )
                elif (x, y) in self.game.flags:
                    # A flagged button must remain active to be unflagged.
                    button.config(image=self.flag_image, text='', state=tk.NORMAL)
                else:
                    # This is a standard hidden tile. It needs to be active.
                    button.config(image=self.pixel, text='', relief=tk.RAISED, state=tk.NORMAL)

    def reveal_all(self):
        for y in range(self.game.height):
            for x in range(self.game.width):
                if (x, y) in self.game.mines and (x, y) not in self.game.flags:
                    self.buttons[(x, y)].config(image=self.mine_image, relief=tk.SUNKEN)

    def get_gui_as_image(self, filename="minesweeper.png"):
        self.master.update_idletasks()
        x = self.master.winfo_rootx() + self.frame.winfo_x()
        y = self.master.winfo_rooty() + self.frame.winfo_y()
        x1 = x + self.frame.winfo_width()
        y1 = y + self.frame.winfo_height()
        ImageGrab.grab().crop((x, y, x1, y1)).save(filename)