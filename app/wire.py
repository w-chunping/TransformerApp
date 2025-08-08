import tkinter as tk
from tkinter import ttk, messagebox
import json, os
import numpy as np
from bobbin.ector import fit_wire_ector
from bobbin.kf_method import fit_wire_kf
from bobbin.option import WireOption
from app.design_state import DesignState
from transformer.tfdraft import TransformerDraft
from transformer.winding import Winding
from transformer.core import Core
from app.tooltips import Tooltip
from utils.tooltips_text import TOOLTIPS_WIRE

class WireDesignTab(tk.Frame):
    def __init__(self, master, state: DesignState, app):
        super().__init__(master)
        self.state = state
        self.app = app
        self.tab = self

        # Reuse your existing frames
        self.wire_design_frame = WireDesignFrame(master = self, state = self.state)

    def to_export(self):
        wire_spec = self.wire_design_frame.capture_fields()
        wire_result = self.wire_design_frame.capture_result()
        wire_advanced = self.wire_design_frame.config["advanced"]
        return {
            "wire_spec": wire_spec,
            "wire_result": wire_result,
            "wire_advanced": wire_advanced
        }
    
    def from_import(self, data: dict):
        if not data:
            return
        data_to_populate = {**data.get("wire_spec", {}), **data.get("wire_advanced", {})}
        self.wire_design_frame.populate_fields(data_to_populate)
        if "wire_result" in data:
            print("[DEBUG] Attempting to get wire_result.")
            self.wire_design_frame.result = data.get("wire_result", {})
            if self.wire_design_frame.result:
                self.wire_design_frame._display_wire_result(self.wire_design_frame.result, self.wire_design_frame.capture_fields())
        else:
            self.wire_design_frame.result = None

class WireDesignFrame(tk.LabelFrame):
    def __init__(self, master, state):
        super().__init__(master, text="Wire Design")
        self.pack(fill="both", expand=True)
        self.state = state
        self.config = {
            "basic": {},
            "advanced": {},
            "use_advanced": False
        }
        self.config["basic"] = self.get_basic_config()
        print(self.config)
        self.scalar_field = ["lt", "wb", "hb"]
        self.advanced_field = ["insulator_thickness", "khb", "kwb", "ht", "kf", "Aw"]
        self.list_field = []
        self.max_channels = 5  # maximum windings assumed
        self.build_ui()
        self.load_wire_cache()
    
    def get_basic_config(self):
        return {
            "khb": 0.8,
            "kwb": 0.9,
            "insulator_thickness": 3e-5,
            "ht": 5e-5,
            "kf": -1,
            "Aw": -1,
            "method": "ector_discrete"
        }

    def get_effective_config(self):
        return self.config["advanced"] if self.config["use_advanced"] else self.config["basic"]

    def build_ui(self):
        self.entries = {}
        row = 0
        tk.Label(self, text = "Primary").grid(row = row, column = 1, sticky = 'w')
        for i in range(1, 5):
            tk.Label(self, text = f"Output Channel {i}").grid(row = row, column = i + 1, sticky = 'w')
        row += 1

        # List fields: irms_list, ji_list, pi_list, spi_list, ni_list
        list_fields_labels = {
            "irms_list": "RMS Current (A)",
            "ji_list": "Current Density (A/mm²)",
            "pi_list": "Number of Windings",
            "spi_list": "Strands per Winding",
            "ni_list": "Number of Turns"
        }
        for field, label in list_fields_labels.items():
            tk.Label(self, text=label).grid(row=row, column=0, sticky="w")
            self.entries[field] = []
            for i in range(self.max_channels):
                entry = tk.Entry(self)
                entry.grid(row=row, column=i+1, sticky = 'w')
                Tooltip(widget = entry, text = TOOLTIPS_WIRE[field])
                self.entries[field].append(entry)
            row += 1

        # Scalar fields
        scalar_fields_labels = {
            "lt": "Number of Layers of Tapes",
            "wb": "Width of Winding Area of Bobbin (mm)",
            "hb": "Height of Winding Area of Bobbin (mm)",
        }

        for field, label in scalar_fields_labels.items():
            tk.Label(self, text=label).grid(row=row, column=0, sticky="w")
            entry = tk.Entry(self)
            entry.grid(row=row, column=1, columnspan=self.max_channels, sticky = 'w')
            Tooltip(widget = entry, text = TOOLTIPS_WIRE[field])
            self.entries[field] = entry
            row += 1



        # Buttons
        import_btn = tk.Button(self, text="Import from Turn Design", command=self.import_from_turn_solution)
        import_btn.grid(row=row, column=0, pady=5, sticky = 'w')

        run_btn = tk.Button(self, text="Run Optimization", command=self.run_wire_optimization)
        run_btn.grid(row=row, column=1, pady=5, sticky = 'w')

        adv_btn = tk.Button(self, text="Advanced Settings", command=self.open_advanced_settings)
        adv_btn.grid(row=row, column=2, pady=5, sticky="w")
        
        tk.Button(self, text = "Clear all", command = self.clear_all_entries).grid(row = row, column = 3, pady = 5)

        # Output
        self.output_tree = ttk.Treeview(self, columns=("irms", "layer", "diameter", "j_cal", "wire_area", "width_rate"), show="tree headings", height = 20)
        self.output_tree.grid(row=row+2, column=0, columnspan=6, sticky="nsew", pady=10)
        self.output_tree.heading("#0", text = "Info/Winding")
        self.output_tree.column("#0", width = 360, stretch = False)

        # These two buttons are deprecated.
        # export_btn = tk.Button(self, text = "Export to yaml", command = self.export_yaml)
        # export_btn.grid(row = row + 3, column = 0, pady = 5)
        # import_btn = tk.Button(self, text = "Import from yaml", command = self.import_from_yaml)
        # import_btn.grid(row = row + 3, column = 1, pady = 5)

    def clear_all_entries(self):
        for field in self.entries:
            if isinstance(self.entries[field], list):
                for i in range(len(self.entries[field])):
                    self.entries[field][i].delete(0, tk.END)
            else:
                self.entries[field].delete(0, tk.END)
    

    def open_advanced_settings(self):
        WireAdvancedOptionsWindow(self, self.state)

    def import_from_turn_solution(self):
        draft = self.state.selected_solution
        if draft is None:
            messagebox.showwarning("Missing", "No selected solution to import.")
            return

        try:
            # Fill list fields
            for field in ["irms_list", "ni_list"]:
                values = []
                for w in draft.winding_list:
                    if field == "irms_list":
                        val = w.i_rms
                        val = f"{val:.4g}" if isinstance(val, float) else str(val) # Format to 4 significant figures if it's a float
                        # values.append(w.i_rms)
                        values.append(val)
                    else:
                        values.append(w.turns)
                self._fill_list_entries(field, values)

            # Fill scalar values
            self._set_scalar("wb", draft.core.winding_width * 1e3) # unit conversion: m -> mm for displaying bobbin width
            self._set_scalar("hb", draft.core.winding_height * 1e3) # unit conversion: m -> mm for displaying bobbin height
            # self._set_scalar("Aw", draft.core.window_area)

            print("[INFO] Turn design data imported successfully.")
            messagebox.showinfo("Imported", "Turn design data imported successfully.")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))

    def _fill_list_entries(self, field, values):
        for i, val in enumerate(values):
            if i < self.max_channels:
                self.entries[field][i].delete(0, tk.END)
                self.entries[field][i].insert(0, str(val))

    def _set_scalar(self, field, value):
        self.entries[field].delete(0, tk.END)
        self.entries[field].insert(0, str(value))

    def _parse_list(self, field):
        return [float(e.get()) for e in self.entries[field] if e.get().strip()]

    def _parse_scalar(self, field):
        val = self.entries[field].get().strip()
        return float(val) if val else None

    def run_wire_optimization(self):
        try:
            fundamental = self.capture_fields()
            config_to_use = self.get_effective_config()
        except Exception as e:
            messagebox.showerror("Input Error", f"Failed to parse inputs: {e}")
            return

        compiled = {**fundamental, **config_to_use}

        print("[DEBUG] Below is compiled")
        print(compiled)

    # if self.state.selected_solution is None:
        winding_list = []
        for i in range(len(compiled["irms_list"])):
            winding = Winding(turns = compiled["ni_list"][i], i_rms = compiled["irms_list"][i])
            winding_list.append(winding)
        core = Core(window_area = compiled["Aw"], winding_width = compiled["wb"], winding_height = compiled["hb"])
        self.state.selected_solution = TransformerDraft(winding_list = winding_list, core = core)

        wire_option = WireOption(
            ji_list=compiled["ji_list"],
            pi_list=compiled["pi_list"],
            spi_list=compiled["spi_list"],
            lt=compiled["lt"],
            insulator_thickness=compiled["insulator_thickness"],
            kwb=compiled["kwb"],
            khb=compiled["khb"],
            ht=compiled["ht"],
            kf = compiled["kf"],
        )

        method = compiled["method"]
        try:
            if self.state.selected_solution is None:
                raise Exception("No transformer draft available for optimization.")
            
            print(f"[INFO] Attempting to optimize wire diameter using method: {method}")
            if method == "ector_continuous":
                self.result = fit_wire_ector(self.state.selected_solution, wire_option, discrete=False)
            elif method == "ector_discrete":
                self.result = fit_wire_ector(self.state.selected_solution, wire_option, discrete=True, catalog = self.state.catalog)
            elif method == "kf":
                self.result = fit_wire_kf(self.state.selected_solution, wire_option)
            else:
                raise ValueError("Invalid optimization method")
            
            print(f"[INFO] Optimization finished with status: {self.result["status"]}.")
            self._display_wire_result(self.result, compiled)


            self.save_wire_cache()
        except Exception as e:
            messagebox.showerror("Optimization Failed", str(e))

    def _display_wire_result(self, result_dict, compiled):
        self.output_tree.delete(*self.output_tree.get_children())

        columns = ["Irms (A)"]
        all_fields = {"di_list": "Diameter (mm)",
                      "li_list": "Layer",
                      "j_cal_list": "Calculated Current Density (A/mm²)",
                      "wa_list": "Cross Sectional Area of a Wire (mm²)",
                      "fill_rate_list": "Bobbin Width Usage Rate"}
        for key, label in all_fields.items():
            if key in result_dict:
                columns.append(label)
        self.output_tree["columns"] = columns
        

        for col in columns:
            # label = col.replace("_", " ").capitalize()
            self.output_tree.heading(col, text = col)
            self.output_tree.column(col, width = 120, anchor = "center")


        # Top-level info
        summary_fields_labels = {
            "status": "Optimization Status/Feasibility",
            "method": "Winding Method",
            "height_required": "Required Bobbin Winding Height (mm)",
            "required_window_area": "Required Window Area (cm²)"
        }
        # print("[DEBUG] Summary fields labels dict constructed.")

        for field, label in summary_fields_labels.items():
            if field in result_dict:
                val = result_dict.get(field)
                if field == "height_required":
                    val *= 1e3 # unit conversion: m -> mm for displaying height required
                elif field == "required_window_area":
                    val *= 1e4 # unit conversion: m² -> cm² for displaying required window area
                self.output_tree.insert("", "end", text=f"{label}: {val:.4g}" if isinstance(val, float) else f"{label}: {val}")

        # Handle per-winding data
        for idx in range(len(compiled["irms_list"])):
            for j in range(int(compiled["pi_list"][idx])):
                node_id = self.output_tree.insert("", "end", text = f"Output Channel {idx}" if idx > 0 else "Primary")
                values = [f"{compiled["irms_list"][idx]:.4g}"]
                try:
                    if "di_list" in result_dict:
                        values.append(f"{result_dict["di_list"][idx] * 1e3:.4g}") # unit conversion: m -> mm for displaying diameter
                    if "li_list" in result_dict:
                        values.append(f"{result_dict["li_list"][idx]:.4g}")
                    if "j_cal_list" in result_dict:
                        values.append(f"{result_dict["j_cal_list"][idx] * 1e-6:.4g}") # unit conversion: A/m² -> A/mm² for displaying current density
                    if "wa_list" in result_dict:
                        values.append(f"{result_dict["wa_list"][idx] * 1e6:.4g}")
                    if "fill_rate_list" in result_dict:
                        values.append(f"{result_dict["fill_rate_list"][idx]:.4g}")
                except Exception as e:
                    pass
                self.output_tree.insert(node_id, "end", text = "", values = values)
                self.output_tree.item(node_id, open = True)
                j += 1

    def save_wire_cache(self, filename = "./app_cache/last_wire_spec.json"):

        data = {}

        for field in ["irms_list", "ji_list", "pi_list", "spi_list", "ni_list"]:
            data[field] = [e.get() for e in self.entries[field]]
            if field == "ji_list":
                # data[field] /= 1e-6 # unit conversion: A/mm² -> A/m² for capturing current density
                data[field] = [float(val) / 1e-6 if val != '' else '' for val in data[field]] # unit conversion: A/mm² -> A/m² for capturing current density

        for field in self.scalar_field:
            data[field] = float(self.entries[field].get())
            if field == "wb":
                data[field] /= 1e3 # unit conversion: mm -> m for capturing bobbin width
            elif field == "hb":
                data[field] /= 1e3 # unit conversion: mm -> m for capturing bobbin height
        print("[DEBUG] Successfully retrieved scalar fields")
        for field in self.advanced_field:
            if self.config["advanced"]:
                # print(f"[DEBUG] field = {field}")
                # print(f"[DEBUG] self.config[advanced]: {self.config["advanced"]}")
                # print(f"[DEBUG] self.config[advanced][field]: {self.config["advanced"][field]}")
                data[field] = self.config["advanced"][field]
        if self.config["advanced"]:
            data["method"] = self.config["advanced"]["method"]
        try:
            os.makedirs(os.path.dirname(filename), exist_ok = True) if os.path.dirname(filename) else None
            with open(filename, 'w') as f:
                json.dump(data, f)
            print(f"[INFO] Successfully cached input wire spec into {filename}.")
        except Exception as e:
            print(f"[ERROR] Failed to save cache: {e}")


    def load_wire_cache(self, filename = "./app_cache/last_wire_spec.json"):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
            self.populate_fields(data)
            print(f"[INFO] Loaded wire spec cache from {filename}")

    def populate_fields(self, data: dict):
        # Populate list-based entries
        # print("[DEBUG] Populating wire spec field")
        for field in ["irms_list", "ji_list", "pi_list", "spi_list", "ni_list"]:
            values = data.get(field, [])
            if field == "irms_list":
                values = [f"{float(val):.4g}" if val != '' else '' for val in values] # round to 4 significant figures
            if field == "ji_list":
                values = [float(val) * 1e-6 if val != '' else '' for val in values] # unit conversion: A/m² -> A/mm² for displaying current density
            for i in range(min(len(values), self.max_channels)):
                self.entries[field][i].delete(0, tk.END)
                self.entries[field][i].insert(0, str(values[i]))

        # Populate scalar fields
        for field in self.scalar_field:
            val = float(data.get(field))
            if field == "wb":
                val *= 1e3 # unit conversion: m -> mm for displaying bobbin width
            elif field == "hb":
                val *= 1e3 # unit conversion: m -> mm for displaying bobbin height
            if val is not None:
                self.entries[field].delete(0, tk.END)
                self.entries[field].insert(0, str(val))

        for field in self.advanced_field:
            val = data.get(field)
            if val is not None:
                self.config["advanced"][field] = val

        if "method" in data:
            self.config["advanced"]["method"] = data.get("method", "ector_discrete")

    def capture_fields(self):
        wire_data = {}
        for field in ["irms_list", "ji_list", "pi_list", "spi_list", "ni_list"]:
            values = []
            for e in self.entries[field]:
                v = e.get().strip()
                if v:
                    try:
                        values.append(float(v))
                    except ValueError:
                        pass
                else:
                    pass
            if values:
                if field == "ji_list":
                    values = [float(val) / 1e-6 if val != '' else '' for val in values] # unit conversion: A/mm² -> A/m² for capturing current density
                    # values /= 1e-6 # unit conversion: A/mm² -> A/m² for capturing current density
                wire_data[field] = values

        for field in ["lt", "wb", "hb"]:
            val = float(self.entries[field].get().strip())
            if field == "wb":
                val /= 1e3 # unit conversion: mm -> m for capturing bobbin width
            elif field == "hb":
                val /= 1e3 # unit conversion: mm -> m for capturing bobbin height
            wire_data[field] = float(val) if val else None

        # wire_data["method"] = self.method_var.get()
        return wire_data
    
    def capture_result(self):
        if not hasattr(self, "result"):
            return None
        return make_yaml_serializable(self.result)
    
    """
        The section of the class below is deprecated.
    """
    """
    
    def export_yaml(self):
        try:
            wire_data = {}

            # Extract list-based values
            for field in ["irms_list", "ji_list", "pi_list", "spi_list", "ni_list"]:
                raw_list = [
                    float(entry.get().strip()) if entry.get().strip() else None
                    for entry in self.entries[field]
                ]
                wire_data[field] = trim_none_tail(raw_list)

            # Extract scalar values
            for field in ["insulator_thickness", "kwb", "ht", "lt", "khb", "wb", "hb", "kf", "Aw"]:
                val = self.entries[field].get().strip()
                if val:
                    wire_data[field] = float(val)

            # Ask where to save
            file_path = filedialog.asksaveasfilename(defaultextension=".yaml",
                                                     filetypes=[("YAML Files", "*.yaml")],
                                                     title="Export Wire Spec")
         
            wire_data["result"] = make_yaml_serializable(self.result)
            # wire_data["result"] = processed_result

            if not file_path:
                return  # user canceled
            

            with open(file_path, "w") as f:
                yaml.dump(wire_data, f)

            messagebox.showinfo("Export Complete", f"Wire spec exported to {file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export wire spec:\n{e}")

    def import_from_yaml(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("YAML Files", "*.yaml")],
                                                   title="Import Wire Spec")
            if not file_path:
                return

            with open(file_path, "r") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise ValueError("Invalid wire spec format in YAML.")

            self.populate_fields(data)
            messagebox.showinfo("Import Complete", f"Wire spec loaded from {file_path}")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import wire spec:\n{e}")

    """


class WireAdvancedOptionsWindow(tk.Toplevel):
    def __init__(self, master, state):
        super().__init__(master)
        self.title("Advanced Settings for Wire Design")
        self.state = state
        self.master = master

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.general_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.general_frame, text = "General")

        self.catalog_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.catalog_frame, text = "Wire Catalogue")

        self.build_general_frame()
        self.build_catalog_frame()

    def build_general_frame(self):
        advanced_fields_labels = {
            "insulator_thickness": "Insulator Thickness (m)",
            "kwb": "Maximum Bobbin Width Usage Rate",
            "ht": "Tape Thickness (m)",
            "khb": "Maximum Bobbin Height Usage Rate",
            "kf": "Fill Factor",
            "Aw": "Window Area (m²)"
        }
        row = 0
        self.advanced_entries = {}
        for field, label in advanced_fields_labels.items():
            tk.Label(self.general_frame, text=label).grid(row=row, column=0, sticky="w")
            entry = tk.Entry(self.general_frame)
            Tooltip(widget = entry, text = TOOLTIPS_WIRE[field])
            if field in self.master.config["advanced"]:
                entry.delete(0, tk.END)
                entry.insert(0, self.master.config["advanced"][field])
            entry.grid(row=row, column=1, sticky = 'w')
            self.advanced_entries[field] = entry
            row += 1        

        # Optimization method dropdown
        tk.Label(self.general_frame, text="Optimization Method").grid(row=row, column=0, sticky="w")
        self.method_var = tk.StringVar(value=self.master.config["advanced"]["method"] if "method" in self.master.config["advanced"] else "ector_discrete")
        self.method_combo = ttk.Combobox(self.general_frame, textvariable=self.method_var, values=["ector_continuous", "ector_discrete", "kf"], state="readonly")
        self.method_combo.grid(row=row, column=1, sticky='w')
        row += 1

        self.use_advanced_var = tk.BooleanVar(value=self.master.config.get("use_advanced", False))
        tk.Checkbutton(self.general_frame, text = "Use advanced config", variable = self.use_advanced_var).grid(row = 0, column = 3)

        apply_btn = tk.Button(self.general_frame, text="Apply", command=self.apply_general)
        apply_btn.grid(row=row, columnspan = 6, sticky="ew", padx=5, pady=10)

    def apply_general(self):
        try:
            for field in ["insulator_thickness", "kwb", "khb", "ht", "kf", "Aw"]:
                val = float(self.advanced_entries[field].get().strip())
                self.master.config["advanced"][field] = val
            self.master.config["advanced"]["method"] = self.method_var.get()
            self.master.config["use_advanced"] = self.use_advanced_var.get()
            # print(f"[DEBUG] self.master.config[useadvanced] {self.master.config["use_advanced"]}")
            # print("[INFO] Applied advanced options for wire design.")
            tk.messagebox.showinfo("Success", "Successfully applied advanced options.")
            # print(f"[INFO] Using advanced: {self.use_advanced_var}")
            # print(self.master.get_effective_config())
            self.destroy()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to apply advanced options:\n{e}")

    def build_catalog_frame(self):

        row = 0

        self.caption = tk.Label(self.catalog_frame, text = "The available wire diameter catalog for optimizing option ector discrete. Please enter them in mm.")
        self.caption.grid(row = row, column = 0)
        # row += 1

        self.entry = tk.Entry(self.catalog_frame)
        self.entry.grid(row = row, column = 1, padx = 5, sticky = 'ew')
        row += 1

        self.catalog_listbox = tk.Listbox(self.catalog_frame, height=30, width=20)
        self.catalog_listbox.grid(row=row, column=0, rowspan=20, padx=(10, 5), pady=10, sticky="w")
        row += 1

        add_btn = tk.Button(self.catalog_frame, text="Add", command=self.add_diameter)
        add_btn.grid(row=row, column=1, sticky="ew", padx=5, pady=(0, 2))
        row += 1

        remove_btn = tk.Button(self.catalog_frame, text="Remove Selected", command=self.remove_selected)
        remove_btn.grid(row=row, column=1, sticky="ew", padx=5, pady=(0, 2))
        row += 1

        apply_btn = tk.Button(self.catalog_frame, text="Apply", command=self.apply_catalog)
        apply_btn.grid(row=row, column=1, sticky="ew", padx=5, pady=10)

        self.populate_from_state()

    def populate_from_state(self):
        self.catalog_listbox.delete(0, tk.END)
        catalog = getattr(self.state, "catalog", [])
        for val in catalog:
            self.catalog_listbox.insert(tk.END, f"{(val * 1e3):.2f}") # unit conversion: m -> mm
        # print("[DEBUG] Populating listbox with catalog:", catalog)

    def add_diameter(self):
        try:
            val = float(self.entry.get())
            if val <= 0:
                raise ValueError("Value must be positive.")
            existing = [float(v) for v in self.catalog_listbox.get(0, tk.END)]
            if any(np.isclose(val, e) for e in existing):
                tk.messagebox.showwarning("Duplicate", f"{val:.2f} is already in the catalog.")
                return
            self.catalog_listbox.insert(tk.END, f"{val:.2f}")
            self.entry.delete(0, tk.END)
        except ValueError as e:
            tk.messagebox.showerror("Invalid Input", str(e))

    def remove_selected(self):
        selected = self.catalog_listbox.curselection()
        for i in reversed(selected):
            self.catalog_listbox.delete(i)

    def apply_catalog(self):
        try:
            values = self.catalog_listbox.get(0, tk.END)
            self.state.catalog = np.array([float(v) * 1e-3 for v in values]) # unit conversion: mm -> m
            print("[INFO] Wire catalog updated:", self.state.catalog)
            tk.messagebox.showinfo("Success", "Wire catalogue applied successfully.")
            self.destroy()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to apply catalogue:\n{e}")

def make_yaml_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.float32, np.float64, np.int32, np.int64)):
        return obj.item()
    elif isinstance(obj, dict):
        return {k: make_yaml_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_yaml_serializable(v) for v in obj]
    else:
        return obj
def trim_none_tail(lst):
    """Trim trailing None values from a list."""
    while lst and lst[-1] is None:
        lst.pop()
    return lst