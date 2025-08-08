import tkinter as tk
from tkinter import filedialog, messagebox
from app.workspace_io import (
    export_workspace_to_yaml,
    import_workspace_from_yaml,
)
from app.notebook import TransformerApp


class AppMenu:
    def __init__(self, master, app: TransformerApp):
        self.master = master
        self.app = app
        self.menu_bar = tk.Menu(master)
        self._create_file_menu()
        # Add more menus here later if needed

        master.config(menu=self.menu_bar)

    def _create_file_menu(self):
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Import Workspace", command=self.import_workspace)
        file_menu.add_command(label="Export Workspace", command=self.export_workspace)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

    def export_workspace(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".yaml", filetypes=[("YAML Files", "*.yaml")])
        if not filepath:
            return

        try:
            circuit_data = self.app.circuit_tab.to_export() if self.app.circuit_tab else None
            transformer_data = self.app.design_tab.to_export() if self.app.design_tab else None
            wire_data = self.app.wire_tab.to_export() if self.app.wire_tab else None


            export_workspace_to_yaml(filepath, transformer_data, wire_data, circuit_data)
            messagebox.showinfo("Export Success", f"Workspace exported to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def import_workspace(self):
        filepath = filedialog.askopenfilename(filetypes=[("YAML Files", "*.yaml")])
        if not filepath:
            return

        try:
            data = import_workspace_from_yaml(filepath)

            self.app.circuit_tab.from_import(data.get("circuit", {}))
            self.app.design_tab.from_import(data.get("transformer", {}))
            self.app.wire_tab.from_import(data.get("wire", {}))

            messagebox.showinfo("Import Success", f"Workspace loaded from:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Import Failed", str(e))
