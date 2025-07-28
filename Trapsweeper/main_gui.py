# main_gui.py
import tkinter as tk
from game import MinesweeperGame
from gui import MinesweeperGUI

def main():
    print("Running in GUI test mode.")
    root = tk.Tk()
    root.title("Minesweeper (GUI Test)")

    # Game settings
    width = 10
    height = 10
    num_mines = 10

    game = MinesweeperGame(width, height, num_mines)
    gui = MinesweeperGUI(root, game)

    root.mainloop()

if __name__ == "__main__":
    main()