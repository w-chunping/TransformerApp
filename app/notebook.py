from tkinter import ttk
from app.design_state import DesignState
from app.transformer import TransformerDesignTab
from app.wire import WireDesignTab
from app.circuit import CircuitCompilerTab

class TransformerApp:
    def __init__(self, master):
        self.master = master
        self.state = DesignState()

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(fill="both", expand=True)

        self.circuit_tab = CircuitCompilerTab(self.notebook, self.state)
        self.notebook.add(self.circuit_tab, text="Circuit Compiler")

        # Tab 1: Transformer Design
        self.design_tab = TransformerDesignTab(self.notebook, self.state, self)
        self.notebook.add(self.design_tab, text="Transformer Design")

        # Tab 2: Wire Design (will implement later)
        self.wire_tab = WireDesignTab(self.notebook, self.state, self)
        self.notebook.add(self.wire_tab, text="Wire Design")

        # print("[DEBUG] DesignState.catalog at app start:", self.state.catalog)
