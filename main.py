import tkinter as tk
from app.notebook import TransformerApp
from app.menu import AppMenu

root = tk.Tk()
root.title("Transformer Design App")
app = TransformerApp(root)
AppMenu(root, app)
root.mainloop()