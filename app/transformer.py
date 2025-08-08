import json, os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk
from transformer.tfspec import TransformerSpec, TransformerOption
from transformer.core import Core, Material
from transformer.tfdraft import TransformerDraft
from data.core_repo import CoreRepository
from app.design_state import DesignState
from app.tooltips import Tooltip
from utils.tooltips_text import TOOLTIPS_TRANSFORMER, ordinal

class TransformerDesignTab(tk.Frame):
    def __init__(self, master, state: DesignState, app):
        super().__init__(master)
        self.state = state
        self.app = app
        self.tab = self

        self.canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Now place your actual frames inside scrollable_frame, not self
        self.spec_frame = SpecInputFrame(self.scrollable_frame, self.state)
        self.repo_frame = RepoFrame(self.scrollable_frame, state=self.state, tab=self)
        self.core_select_frame = CoreSelectFrame(self.scrollable_frame, state=self.state, tab=self)
        self.solution_select_frame = SolutionSelectFrame(self.scrollable_frame, state=self.state)

        # self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())


    def _bind_mousewheel(self):
        if os.name == "nt":
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        else:
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        if os.name == "nt":
            self.canvas.unbind_all("<MouseWheel>")
        else:
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if os.name == "nt":
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")


    def design_turns(self):
        if self.state.spec is None:
            tk.messagebox.showwarning("Missing Data", "Please input spec and load core repo first.")
            return

        # Get the selected core model
        if self.state.core is None:
            tk.messagebox.showwarning("No Core Selected", "Please select a core from the list.")
            return

        # selected_core = self.repo.get_by_model(selected_model)

        # Draft creation and turn design
        self.state.tf_draft = TransformerDraft()
        if self.state.tf_option is None:
            self.state.tf_option = TransformerOption(turn_use_tolerance = False)
        # self.state.tf_option = TransformerOption(turn_use_tolerance = False)
        self.state.tf_draft.create_draft(spec=self.state.spec, options=self.state.tf_option)  # Assume tf_option is predefined or optional
        # self.tf_draft.get_core(selected_core)
        self.state.tf_draft.get_core(self.state.core)
        self.state.tf_draft.get_material(self.state.material)
        self.state.tf_draft.update_draft_n0_min()
        self.state.solutions = self.state.tf_draft.determine_draft_turns()

        for sol in self.state.solutions:
            sol.update_draft_windings()
        self.state.tf_draft.update_draft_windings()

        # Feedback
        tk.messagebox.showinfo("Success", f"Found {len(self.state.solutions)} design solution(s).")
        print(f"[INFO] Turns design complete. Found {len(self.state.solutions)} design solution(s)")

        self.solution_select_frame.update_solutions()
    
    def to_export(self):

        return {
            "spec": self.spec_frame.capture_fields(),
            "repo": self.repo_frame.capture_fields(),
            "core": self.core_select_frame.capture_fields()
        }
    
    def from_import(self, data: dict):
        """
        Populate fields from imported data.
        """
        self.spec_frame.populate_fields(data.get("spec", {}))
        self.repo_frame.populate_fields(data.get("repo", {}))
        self.core_select_frame.populate_fields(data.get("core", {}))

        # Rebuild core if present
        # if "core" in data:
        #     self.state.core = Core.from_dict(data["core"])
        #     print(f"[INFO] Core loaded: {self.state.core.name}")

class SpecInputFrame(tk.LabelFrame):
    def __init__(self, master: tk.Tk, state: DesignState):
        super().__init__(master = master, text = "Transformer Spec")
        self.state = state
        self.pack(padx=10, pady=5, fill="x")

        # prev_spec = self.load_spec_from_cache()

        self.spec_entries = {}
        row = 0

        # Float / str attributes
        scalar_fields_labels = {
            'lm': "Magnetizing Inducance (H)",
            'ip_pk': "Maximum Primary Current (A)",
            "vp": "Voltage Across Primary Side (V)",
            "fs": "Switching Frequency (Hz)",
            "d_max": "Maximum Duty Ratio",
            "vsec_main": "Voltage Across Main Secondary Channel (V)",
            "pin": "Input Power (W)",
            "delta_i": "Delta I at Primary Side (A)",
            "b_sat": "Saturation Flux Density of Material (T)",
            "delta_b": "Flux Density Swing Limit of Material (T)"
        }
        # scalar_fields = ["lm", "ip_pk", "vp", "fs", "d_max", "vsec_main", "pin", "delta_i"]
        for field, label in scalar_fields_labels.items():
        # for i, label in enumerate(scalar_fields):
            tk.Label(self, text=label).grid(row=row, column=0, sticky="w")
            entry = tk.Entry(self)
            entry.grid(row=row, column=1)
            Tooltip(widget = entry, text = TOOLTIPS_TRANSFORMER[field])
            # if field in prev_spec:
            #     entry.insert(0, prev_spec[field])
            self.spec_entries[field] = entry
            row += 1

        # List attributes (4 inputs each)
        self.list_fields = {}
        list_attrs = [("turns_ratio_list", "Minimum Turns Ratio"), ("kl_list", "Load Occupying Factor")]
        for idx, (key, label_text) in enumerate(list_attrs, start=len(scalar_fields_labels)):
            tk.Label(self, text=label_text).grid(row=idx, column=0, sticky="nw")
            entry_list = []
            primary = tk.Entry(self)
            primary.insert(0, 1.0)
            primary.config(state = "disabled")
            primary.grid(row = idx, column = 1)
            Tooltip(widget = primary, text = "The turn ratio and load occupying factor are both defined as 1 for primary winding.")
            entry_list.append(primary)
            for j in range(4):  # Up to 4 inputs
                e = tk.Entry(self)
                e.grid(row=idx, column=2 + j)
                Tooltip(widget = e, text = TOOLTIPS_TRANSFORMER[key][0] + ordinal(j + 1) + TOOLTIPS_TRANSFORMER[key][1])
                entry_list.append(e)
            self.list_fields[key] = entry_list

        row += 2

        topologies = ["flyback", "forward"]

        tk.Label(self, text="Topology").grid(row=row, column=0, sticky="w")
        self.topology_var = tk.StringVar()
        topo_combo = ttk.Combobox(self, textvariable=self.topology_var, values=topologies, state="readonly")
        topo_combo.grid(row=row, column=1)
        topo_combo.set(topologies[0])  # Default value
        self.spec_entries["topology"] = self.topology_var
        row += 1

        adv_btn = tk.Button(self, text="Advanced Settings", command=self.open_advanced_settings)
        adv_btn.grid(row=row, column=4, pady=5)


        tk.Button(self, text = "Clear all", command = self.clear_all_entries).grid(row = row, column = 1, pady = 5)
        tk.Button(self, text = "Load from Circuit Compiler", command = self.get_from_circuit).grid(row = row, column = 0, pady = 5)
        row += 1

        # Submit button and status
        submit_btn = tk.Button(self, text="Submit Spec", command=self.submit_spec)
        submit_btn.grid(row=row, columnspan = 6, pady=5)
        # row += 1

        self.spec_status = tk.Label(self, text="❌ Spec not loaded", fg="red")
        self.spec_status.grid(row=row + 1, columnspan=6)
        # row += 1

        cached_data = self.load_spec_from_cache()
        if cached_data:
            self.populate_fields(cached_data)
            print(f"[INFO] Loaded transformer spec cache from ./app_cache/cache_spec.json")

        # These two buttons are deprecated.
        # import_button = tk.Button(self, text="Import Spec from YAML", command=self.import_yaml)
        # import_button.grid(row=row + 2, column=1, pady=5, sticky="w")

        # export_button = tk.Button(self, text="Export Spec to YAML", command=self.export_yaml)
        # export_button.grid(row=row + 2, column=2, sticky="w", pady=5)

    def cache_spec_to_file(self, spec_dict, filename = "./app_cache/cache_spec.json"):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True) if os.path.dirname(filename) else None
            with open(filename, 'w') as f:
                json.dump(spec_dict, f)
            print(f"[INFO] Successfully cached input transformer spec into {filename}.")
        except Exception as e:
            print(f"[ERROR] Failed to save cache: {e}")

    def load_spec_from_cache(self, filename = "./app_cache/cache_spec.json"):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return {}  # fallback to empty if no file
    
    def clear_all_entries(self):
        for field in self.spec_entries:
            if field == "topology":
                continue
            self.spec_entries[field].delete(0, tk.END)
        for list_field in self.list_fields:
            for i in range(len(self.list_fields[list_field])):
                if self.list_fields[list_field][i].cget("state") == "disabled":
                    continue
                self.list_fields[list_field][i].delete(0, tk.END)
    
    def submit_spec(self):
        try:

            kwargs = self.capture_fields()
            material_keys = {"b_sat", "delta_b"} # The set of keys which material info is contained in kwargs
            material_kwargs = {}
            for key in material_keys:
                material_kwargs[key] = kwargs.pop(key, None)

            # kwargs = {}
            # material_kwargs = {}

            # # Parse scalar entries
            # for key, entry in self.spec_entries.items():
            #     val = entry.get().strip()
            #     if not val:
            #         continue
            #     if val:
            #         if key == "topology":
            #             kwargs[key] = entry.get()  # String field
            #         elif key in ["b_sat", "delta_b"]:
            #             material_kwargs[key] = float(val)
            #         else:
            #             kwargs[key] = float(val)

            # # Parse list fields
            # for key, entries in self.list_fields.items():
            #     values = []
            #     for e in entries:
            #         v = e.get().strip()
            #         if v:
            #             values.append(float(v))
            #     if values:
            #         kwargs[key] = values

            # Construct TransformerSpec
            self.state.spec = TransformerSpec(**kwargs)
            self.spec_status.config(text="✅ Spec loaded", fg="green")
            # print("TransformerSpec:", self.state.spec)
            print("[INFO] Successfully submitted transformer spec.")
            self.state.material = Material(**material_kwargs)
            # print("Material:\n", self.state.material)
            print("[INFO] Successfully created material.")
            self.cache_spec_to_file(spec_dict = {**kwargs, **material_kwargs})

        except Exception as e:
            self.spec_status.config(text=f"❌ Error: {str(e)}", fg="red")

    def populate_fields(self, data: dict):
        for key, entry in self.spec_entries.items():
            if key in data and key != "topology":
                to_insert = data[key]
                if key in ["lm", "ip_pk", "vp", "fs", "d_max", "vsec_main", "pin", "delta_i"]:
                    to_insert = f"{to_insert:.4g}" # round to 4 significant figures
                entry.delete(0, tk.END)
                entry.insert(0, str(to_insert))
                # entry.insert(0, str(data[key]))
            elif key == "topology" and key in data:
                self.topology_var.set(data[key])

        for key, entries in self.list_fields.items():
            if key in data and isinstance(data[key], list):
                for i, val in enumerate(data[key]):
                    if i + 1 < len(data[key]):  # skip index 0 (primary), fill Ch.1, Ch.2...
                        to_insert = f"{data[key][i + 1]:.4g}" # round to 4 significant figures
                        entries[i + 1].delete(0, tk.END)
                        entries[i + 1].insert(0, to_insert)
                        # entries[i + 1].insert(0, data[key][i + 1])
        # print("[DEBUG] Successfully populated transformer spec data.")

    def capture_fields(self):
        """
        Capture all fields from the spec input frame and return as a dictionary.
        """
        spec_data = {}
        for key, entry in self.spec_entries.items():
            value = entry.get().strip()
            if not value:
                continue
            if key == "topology":
                spec_data[key] = value  # keep as string
            else:
                try:
                    spec_data[key] = float(value)
                except ValueError:
                    pass

        for key, entries in self.list_fields.items():
            values = []
            for e in entries:
                v = e.get().strip()
                if v:
                    try:
                        values.append(float(v))
                    except ValueError:
                        continue
            if values:
                spec_data[key] = values

        return spec_data


    def open_advanced_settings(self):
        AdvancedOptionsWindow(self.master, self.state)

    def get_from_circuit(self):
        data = self.state.circuit_dict
        for key in ("turns_ratio_list", "kl_list"):
                if key in data and isinstance(data[key], list):
                    if abs(data[key][0] - 1.0) > 1e-6:
                        raise ValueError(f"The imported file does not have {key} with a beginning 1.0. Is the file correctly configured?")
        if "vsec_main" not in data:
            if "vo_list" in data and "vf_list" in data:
                data["vsec_main"] = data["vo_list"][0] + data["vf_list"][0]
        self.populate_fields(data)
        tk.messagebox.showinfo("Circuit loaded", f"Successfully imported transformer spec from circuit tab.")
        print(f"[INFO] Transformer info loaded from circuit tab.")

    """
        The section of the class below is deprecated.
    """
    """

    def import_yaml(self):
        filepath = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml *.yml")])
        # filepath = os.path.relpath(filepath, start = os.getcwd())
        if not filepath:
            return
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)

            for key in ("turns_ratio_list", "kl_list"):
                if key in data and isinstance(data[key], list):
                    if abs(data[key][0] - 1.0) > 1e-6:
                        raise ValueError(f"The imported file does not have {key} with a beginning 1.0. Is the file correctly configured?")
            if "vsec_main" not in data:
                if "vo_list" in data and "vf_list" in data:
                    data["vsec_main"] = data["vo_list"][0] + data["vf_list"][0]
            self.populate_fields(data)
            tk.messagebox.showinfo("File loaded", f"Successfully imported transformer yaml file from {filepath}")
            print(f"[INFO] Transformer info loaded from {filepath}")
            
        except Exception as e:
            tk.messagebox.showerror("Import Failed", f"Could not load YAML:\n{e}")
            print(f"[ERROR] Could not load file from {filepath}, {e}")          

    def export_yaml(self):
        
        # Ask user where to save
        filename = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml")],
            title="Export Transformer Spec"
        )

        if not filename:
            return  # User cancelled

        try:
            # Use same logic as cache — regenerate kwargs/material_kwargs
            kwargs = {}
            material_kwargs = {}

            for key, entry in self.spec_entries.items():
                val = entry.get().strip()
                if not val:
                    continue
                if key == "topology":
                    kwargs[key] = entry.get()
                elif key in ["b_sat", "delta_b"]:
                    material_kwargs[key] = float(val)
                else:
                    kwargs[key] = float(val)

            for key, entries in self.list_fields.items():
                values = []
                for e in entries:
                    v = e.get().strip()
                    if v:
                        values.append(float(v))
                if values:
                    kwargs[key] = values

            spec_dict = {**kwargs, **material_kwargs}

            # Optional comment before dump
            with open(filename, "w") as f:
                f.write("# Exported Transformer Spec\n")
                yaml.dump(spec_dict, f, sort_keys=False)

            print(f"[INFO] Successfully exported to YAML: {filename}")

        except Exception as e:
            print(f"[ERROR] Failed to export YAML: {e}")
    """

class RepoFrame(tk.LabelFrame):
    def __init__(self, master: tk.Tk, state: DesignState, tab: TransformerDesignTab):
        super().__init__(master = master, text = "Core Repository")
        self.state = state
        self.pack(padx=10, pady=5, fill="x")
        self.tab = tab

        load_btn = tk.Button(self, text="Load Core Repo", command=self.load_repo)
        load_btn.pack()

        self.repo_status = tk.Label(self, text="❌ Repo not loaded", fg="red")
        self.repo_status.pack()

    def access_repo(self, path: str, sheet: str):
        try:
            self.state.repo = CoreRepository(path, sheet)
            self.core_model_list = [core.name for core in self.state.repo.all]
            self.tab.core_select_frame.core_combobox["values"] = self.core_model_list
            self.tab.core_select_frame.core_combobox["state"] = "readonly"
            self.repo_status.config(text=f"✅ Repo loaded: {os.path.basename(path)} ({sheet})", fg="green")
            print(f"[INFO] Successfully loaded core repo and updated core list from {path}.")
        except Exception as e:
            # tk.messagebox.showerror("Load Error", f"Failed to access repository:\n{e}")
            print(f"[ERROR] Failed to access repository: {e}")


    def load_repo(self):
        filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls *.xlsx")])
        filepath = os.path.relpath(filepath, start = os.getcwd())
        if filepath:
            try:
                xls = pd.ExcelFile(filepath)
                sheet_names = xls.sheet_names

                sheet_selection_window = tk.Toplevel(self.master)
                sheet_selection_window.title("Select Sheet")

                tk.Label(sheet_selection_window, text="Choose a sheet:").pack(padx=10, pady=5)
                selected_sheet = tk.StringVar(sheet_selection_window)
                combo = ttk.Combobox(sheet_selection_window, textvariable=selected_sheet, values=sheet_names, state="readonly")
                combo.pack(padx=10, pady=5)
                combo.set(sheet_names[0])  # Default selection

                def confirm_selection():
                    sheet_name = selected_sheet.get()
                    self.access_repo(filepath, sheet_name)
                    sheet_selection_window.destroy()

                tk.Button(sheet_selection_window, text="OK", command=confirm_selection).pack(pady=10)

            except Exception as e:
                tk.messagebox.showerror("Load Error", f"Failed to load Excel file:\n{e}")
    
    def populate_fields(self, data):
        if data:
            print("[DEBUG] Populating repository fields with data:", data)
            if "filepath" in data and data["filepath"]:
                filepath = data["filepath"]
                if "sheet_name" in data and data["sheet_name"]:
                    sheet_name = data["sheet_name"]
                    try:
                        self.access_repo(filepath, sheet_name)
                    except Exception as e:
                        tk.messagebox.showerror("Load Error", f"Failed to access repository:\n{filepath}, sheet: {sheet_name}\n. Please load core repository manually.")    
        print("[INFO] Successfully imported core repository.")

    def capture_fields(self):
        """
        Capture the repository path and selected sheet.
        """
        repo_data = {}
        if self.state.repo and self.state.repo.filepath:
            repo_data["filepath"] = self.state.repo.filepath
        if self.state.repo and self.state.repo.sheet_name:
            repo_data["sheet_name"] = self.state.repo.sheet_name
        return repo_data if repo_data else None

class CoreSelectFrame(tk.LabelFrame):
    def __init__(self, master: tk.Tk, state: DesignState, tab: TransformerDesignTab):
        super().__init__(master = master, text = "Select Core")
        self.pack(padx=10, pady=5, fill="x")
        self.state = state
        self.tab = tab

        self.core_combobox = ttk.Combobox(self, state="disabled")
        self.core_combobox.pack()
        self.core_combobox.bind("<<ComboboxSelected>>", self.on_core_selected)

        self.core_label = tk.Label(self, text="No core selected")
        self.core_label.pack()

        self.start_design_button = tk.Button(self, text = "Start designing turns", command = self.tab.design_turns)
        self.start_design_button.pack(pady = 5)

    def on_core_selected(self, event):
        selected = self.core_combobox.get()
        self.state.core = self.state.repo.get_by_model(selected)
        self.core_label.config(text=f"Selected core: {selected}, Ae = {self.state.core.core_area * 1e6}mm²") # unit conversion at display
        print(f"[INFO] Core selected: {selected}")
        # print(self.state.core)

    def populate_fields(self, data):
        print(f"[DEBUG] Data passed in populate_field in core selection: {data}")
        if "core" in data and data["core"]:
            self.state.core = Core.from_dict(data["core"])
            self.core_label.config(text = f"From imported file loaded core: {self.state.core.name}, Ae = {self.state.core.core_area * 1e6}mm²") # unit conversion at display
        print("[INFO] Successfully imported core.")

    def capture_fields(self):
        """
        Capture the selected core model and return as a dictionary.
        """
        return {
            "core": self.state.core.to_dict() if self.state.core else None,
            # "filepath": self.state.repo.filepath if self.state.repo.filepath else None,
            # "sheet_name": self.state.repo.sheet_name if self.state.repo.sheet_name else None
        }


class SolutionSelectFrame(tk.LabelFrame):
    def __init__(self, master, state):
        super().__init__(master, text="Select Solution")
        self.pack(padx=10, pady=5, fill="both", expand=True)

        self.state = state

        columns = ("role", "turns", "turns_ratio", "irms")
        # self.tree = ttk.Treeview(self, columns=columns, show="tree headings", selectmode="browse")

        # Create a frame to hold the tree and scrollbar
        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True)

        # Create the Treeview
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", selectmode="browse")

        # Create and attach scrollbar
        scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Layout tree and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


        self.tree.heading("#0", text="Solution / Winding")
        self.tree.heading("role", text="Role")
        self.tree.heading("turns", text="Turns")
        self.tree.heading("turns_ratio", text="Turns Ratio")
        self.tree.heading("irms", text="I RMS (A)")

        self.tree.column("#0", width=150)
        self.tree.column("role", width=100, anchor="center")
        self.tree.column("turns", width=80, anchor="center")
        self.tree.column("turns_ratio", width=100, anchor="center")
        self.tree.column("irms", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)

        self.select_button = tk.Button(self, text="Use Selected Solution", command=self.select_solution)
        self.select_button.pack(pady=5)

        self.status_label = tk.Label(self, text="No solution selected", fg="red")
        self.status_label.pack()

    def update_solutions(self):
        self.tree.delete(*self.tree.get_children())

        for sol_idx, draft in enumerate(self.state.solutions):
            # Insert parent solution node
            sol_id = self.tree.insert("", "end", text=f"Solution {sol_idx+1}", values=("", "", "", ""))
            self.tree.insert(sol_id, "end", text = f"Gap length (mm): {draft.lg * 1e3:.3f}") # unit conversion: m -> mm for displaying gap length

            for w_idx, winding in enumerate(draft.winding_list):
                # Calculate turns ratio = winding turns / input winding turns (assumed index 0)
                turns_ratio = (winding.turns / draft.winding_list[0].turns) if draft.winding_list else 0
                self.tree.insert(
                    sol_id, "end",
                    text=f"Winding {w_idx}",
                    values=(
                        winding.role,
                        winding.turns,
                        f"{turns_ratio:.3f}",
                        f"{winding.i_rms:.3f}"
                    )
                )
            # Expand solution by default
            self.tree.item(sol_id, open=True)

    def select_solution(self):
        selected = self.tree.selection()
        if not selected:
            tk.messagebox.showwarning("No selection", "Please select a solution node.")
            return

        # Only allow selecting the solution parent node, not a winding node
        selected_id = selected[0]
        if self.tree.parent(selected_id):  # If it has a parent, it's a winding node
            # Get parent solution node instead
            selected_id = self.tree.parent(selected_id)

        # The index is order in treeview: map back to state.solutions
        children = self.tree.get_children()
        try:
            idx = children.index(selected_id)
        except ValueError:
            tk.messagebox.showerror("Selection error", "Could not find selected solution.")
            return

        self.state.selected_solution = self.state.solutions[idx]
        self.status_label.config(text=f"✅ Solution {idx+1} selected", fg="green")
        print(f"[INFO] Selected solution {idx+1}.")



class AdvancedOptionsWindow(tk.Toplevel):
    def __init__(self, master, state: DesignState):
        super().__init__(master)
        self.title("Advanced Transformer Options")
        self.state = state

        self.fields = {}

        # Options with default values from TransformerOption
        options = {
            "turn_check_tolerance_b": 0.05,
            "turn_check_tolerance_d": 0,
            "turn_use_tolerance": False,
        }

        loaded_cache_option = self.load_tf_option_from_file()
        if loaded_cache_option is not None:
            options = loaded_cache_option
            print("[INFO] Loaded transformer option cache from ./app_cache/cache_tf_option.json")

        for i, (key, default) in enumerate(options.items()):
            tk.Label(self, text=' '.join(word.capitalize() for word in key.split('_')[-2:])).grid(row=i, column=0, sticky="w")
            if isinstance(default, bool):
                var = tk.BooleanVar(value=default)
                checkbox = tk.Checkbutton(self, variable=var)
                checkbox.grid(row=i, column=1, sticky="w")
                self.fields[key] = var
            else:
                entry = tk.Entry(self)
                entry.insert(0, str(default))
                entry.grid(row=i, column=1)
                self.fields[key] = entry

        save_btn = tk.Button(self, text="Apply", command=self.save_options)
        save_btn.grid(row=len(options), columnspan=2, pady=10)

    def save_options(self):
        try:
            kwargs = {}
            for key, widget in self.fields.items():
                if isinstance(widget, tk.BooleanVar):
                    kwargs[key] = widget.get()
                else:
                    kwargs[key] = float(widget.get())

            self.state.tf_option = TransformerOption(**kwargs)
            print("[INFO] Applied TransformerOption:", self.state.tf_option.__dict__)
            self.cache_tf_option_to_file(option_dict = kwargs)
            self.destroy()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to apply options: {e}")

    def cache_tf_option_to_file(self, option_dict, filename = "./app_cache/cache_tf_option.json"):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True) if os.path.dirname(filename) else None
            with open(filename, 'w') as f:
                json.dump(option_dict, f)
            print(f"[INFO] Successfully cached input transformer option into {filename}.")
        except Exception as e:
            print(f"[ERROR] Failed to save cache: {e}")

    def load_tf_option_from_file(self, filename = "./app_cache/cache_tf_option.json"):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return None  # fallback to empty if no file


