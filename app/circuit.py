import tkinter as tk
from tkinter import ttk
import json, os
import numpy as np
from utils.style import get_pretty_mono_font, format_channelized_decimal_aligned
from app.tooltips import Tooltip
from utils.tooltips_text import TOOLTIPS_CIRCUIT, ordinal
# circuit.flyback and circuit.forward are imported conditionally in the middle of this file.

class CircuitCompilerTab(tk.Frame):
    def __init__(self, master, state):
        super().__init__(master)
        self.state = state

        self.entries = {}
        self.list_entries = {}

        # Scrollable canvas setup (optional if many fields)
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0,0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.input_frame = ttk.LabelFrame(self.scrollable_frame, text="Circuit Input")
        self.input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.output_frame = ttk.LabelFrame(self.scrollable_frame, text="Compiled Output")
        self.output_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        row = 0

        self.topology_var = tk.StringVar(value="flyback")
        ttk.Label(self.input_frame, text="Converter Type").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        topology_menu = ttk.OptionMenu(self.input_frame, self.topology_var, "flyback", "flyback", "forward")
        topology_menu.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        self.converter_mode_var = tk.StringVar(value = "CCM")
        ttk.Label(self.input_frame, text = "Converter Mode").grid(row = row, column = 0, sticky = 'w', padx = 5, pady = 2)
        converter_mode_menu = ttk.OptionMenu(self.input_frame, self.converter_mode_var, "CCM", "CCM", "BCM")
        converter_mode_menu.grid(row = row, column = 1, sticky = 'w', padx = 5, pady = 2)
        row += 1

        # Scalar float/string fields (user inputs)
        scalar_fields = [
            ("vin_dc_min", "Min DC Input Voltage (V)"),
            ("vin_dc_max", "Max DC Input Voltage (V)"),
            ("vin_ac_min", "Min AC Input Voltage (V)"),
            ("vin_ac_max", "Max AC Input Voltage (V)"),
            ("efficiency", "Efficiency"),
            ("lm", "Magnetizing Inductance (H)"),
            ("fs", "Switching Frequency (Hz)"),
            ("d_max", "Duty Ratio"),
            ("vro", "Reflected Voltage (V)"),
        ]

        for key, label_text in scalar_fields:
            tk.Label(self.input_frame, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry = tk.Entry(self.input_frame)
            entry.grid(row=row, column=1, padx=5, pady=2)
            Tooltip(entry, TOOLTIPS_CIRCUIT[key])
            self.entries[key] = entry
            row += 1

        # List inputs — for vo_list, vf_list, io_list, turns_ratio_list
        # Provide 4 input fields each for these lists
        list_fields = [
            ("vo_list", "Output Voltages (V)"),
            ("vf_list", "Diode Forward Voltages (V)"),
            ("io_list", "Output Currents (A)"),
            ("turns_ratio_list", "Turns Ratio List")
        ]
        
        for i in range(4):
            tk.Label(self.input_frame, text = f"Output Channel {i + 1}").grid(row = row, column = i + 1)
        row += 1

        for key, label_text in list_fields:
            tk.Label(self.input_frame, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            entry_list = []
            for i in range(4):
                e = tk.Entry(self.input_frame) #, width=10)
                e.grid(row=row, column=1 + i, padx=3, pady=2)
                Tooltip(widget = e, text = (TOOLTIPS_CIRCUIT[key][0] + ordinal(i + 1) + TOOLTIPS_CIRCUIT[key][1]))
                entry_list.append(e)
            self.list_entries[key] = entry_list
            row += 1

        # Compile button
        compile_btn = tk.Button(self.input_frame, text="Compile Circuit", command=self.compile_circuit)
        compile_btn.grid(row=row, column=0, pady=10)

        tk.Button(self.input_frame, text = "Clear all", command = self.clear_all_entries).grid(row = row, column = 2, pady = 5, padx = 10)

        # Treeview for structured output
        style = ttk.Style()
        pretty_font = get_pretty_mono_font()
        style.configure("Treeview", font = pretty_font)
        self.output_tree = ttk.Treeview(self.output_frame, columns=("value",), show="tree", height=23)
        self.output_tree.heading("#0", text="Parameter")
        self.output_tree.heading("value", text="Value")
        self.output_tree.column("#0", width=300, anchor="w")
        self.output_tree.column("value", width=800, anchor="w")
        self.output_tree.grid(row = 0, column = 0)# (fill="both", padx=10, pady=10, expand=True)
        # self.output_tree.configure(font = ("Courier New", 10))

        tk.Button(self.output_frame, text = "Record to Proceed", command = self.record_circuit).grid(row = 1, column = 0, pady = 5, columnspan = 6)
        self.record_status = tk.Label(self.output_frame, text = "❌ Circuit not recorded", fg = "red")
        self.record_status.grid(row = 2, columnspan = 6)

        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())


        # Optionally load cached data here
        self.load_cache()
        # These two buttons are deprecated
        # row += 2
        # tk.Button(self.input_frame, text="Import YAML", command=self.import_yaml).grid(row=row, column=0, pady=5)
        # tk.Button(self.input_frame, text="Export YAML", command=self.export_yaml).grid(row=row, column=1, pady=5)

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

    def compile_circuit(self):
        try:
            # kwargs = {}

            # # Read scalar fields
            # for key, entry in self.entries.items():
            #     val = entry.get().strip()
            #     if val == "":
            #         kwargs[key] = None
            #     # elif key == "mode":
            #         # kwargs[key] = val
            #     else:
            #         kwargs[key] = float(val)

            # kwargs["mode"] = self.converter_mode_var.get()

            # # Read list fields, convert to float, ignore blanks
            # for key, entry_list in self.list_entries.items():
            #     vals = []
            #     for e in entry_list:
            #         v = e.get().strip()
            #         if v != "":
            #             vals.append(float(v))
            #     kwargs[key] = vals if vals else None
            kwargs = self.capture_fields()
            topology = kwargs.pop("topology")

            topology = self.topology_var.get()
            if topology == "flyback":
                from circuit.flyback import Flyback
                flyback = Flyback(**kwargs)
                flyback.compile_params()
                compiled = flyback
            elif topology == "forward":
                from circuit.forward import Forward
                forward = Forward(**kwargs)
                forward.compile_params()
                compiled = forward
            else:
                raise ValueError(f"Unknown converter type: {topology}")


            self.state.circuit = compiled  # Store in state for other tabs if needed

            self._insert_treeview_output(compiled)
            print("[INFO] Successfully compiled input circuit.")

            tk.messagebox.showinfo("Success", f"{topology} converter compiled successfully!")

            # Cache inputs (also save topology)
            data = kwargs.copy()
            data["topology"] = topology
            self.cache_inputs(data)

        except Exception as e:
            print(f"[ERROR] Failed to compile circuit. {e}")
            tk.messagebox.showerror("Error", f"Failed to compile circuit:\n{e}")

    def cache_inputs(self, data, filename="./app_cache/cache_circuit.json"):
        try:
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w") as f:
                json.dump(data, f)
            print(f"[INFO] Cached circuit inputs to {filename}")
        except Exception as e:
            print(f"[ERROR] Could not cache circuit inputs: {e}")

    def load_cache(self, filename="./app_cache/cache_circuit.json"):
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    data = json.load(f)
                    self.populate_fields(data)

                print(f"[INFO] Loaded cached circuit inputs from {filename}")
            except Exception as e:
                print(f"[ERROR] Could not load cached circuit inputs: {e}")

    def populate_fields(self, data: dict):
        # Set converter type and mode first
        if "topology" in data:
            self.topology_var.set(data["topology"])
        if "mode" in data:
            self.converter_mode_var.set(data["mode"])

        for key, val in data.items():
            if key in ["topology", "mode"]:
                continue
            if key in self.entries:
                self.entries[key].delete(0, tk.END)
                if val is not None:
                    self.entries[key].insert(0, str(val))
            elif key in self.list_entries and val is not None:
                for i, v in enumerate(val):
                    if i < len(self.list_entries[key]):
                        self.list_entries[key][i].delete(0, tk.END)
                        self.list_entries[key][i].insert(0, str(v))

    def capture_fields(self):
        data = {}
        for key, entry in self.entries.items():
            val = entry.get().strip()
            if val:
                data[key] = float(val)
            else:
                data[key] = None

        for key, entry_list in self.list_entries.items():
            vals = []
            for e in entry_list:
                v = e.get().strip()
                if v:
                    vals.append(float(v))
            data[key] = vals if vals else None

        data["topology"] = self.topology_var.get()
        data["mode"] = self.converter_mode_var.get()

        return data

    def record_circuit(self):
        if not hasattr(self.state, "circuit") or self.state.circuit is None:
            tk.messagebox.showwarning("Nothing to Record", "Please compile a circuit first.")
            return
        self.state.circuit_dict = self.state.circuit.to_dict()
        self.state.circuit_dict["kl_list"].insert(0, 1)
        self.state.circuit_dict["turns_ratio_list"].insert(0, 1)
        self.state.circuit_dict["topology"] = self.state.circuit.__class__.__name__.lower()
        self.record_status.config(text="✅ Circuit recorded", fg="green")
        # print(self.state.circuit_dict)
        print("[INFO] The compiled circuit is recorded and ready to use in transformer tab.")
        print("[WARNING] A '1' is explicitly prepended to the kl_list and turns_ratio_list for compatibility in populating transformer tab.")
        tk.messagebox.showinfo("Success", "Successfully recorded your circuit.")




    def _insert_treeview_output(self, compiled):
        self.output_tree.delete(*self.output_tree.get_children())

        def format_channelized(values):
            if not isinstance(values, (list, np.ndarray)):
                return f"{values:.4g}"
            return format_channelized_decimal_aligned(values, precision=4, total_int_len=8)

        def insert_section(title, param_dict):
            parent = self.output_tree.insert("", "end", text=title, open=True)
            for param, val in param_dict.items():
                if val is not None:
                    formatted_val = format_channelized(val)
                    self.output_tree.insert(parent, "end", text=param, values=(formatted_val,))

        # Grouped fields
        input_params = {
            "Minimum Input DC Voltage (V)": compiled.vin_dc_min,
            "Maximum Input DC Voltage (V)": compiled.vin_dc_max,
            "Minimum Input AC Voltage (V)": compiled.vin_ac_min,
            "Maximum Input AC Voltage (V)": compiled.vin_ac_max,
            "Efficiency": compiled.efficiency,
            "Switching Frequency (Hz)": compiled.fs,
            "Output Voltage (V)": compiled.vo_list,
            "Forward Voltage of Diodes (V)": compiled.vf_list,
            "Output Current (A)": compiled.io_list,
        }

        interdependent_params = {
            "Duty": compiled.d_max,
            "Reflected Voltage (V)": getattr(compiled, "vro", None),
            "Minimum Turns Ratio": compiled.turns_ratio_list, # changed here
            "Magnetizing Inductance (H)": compiled.lm
        }

        output_params = {
            "Output Power (W)": compiled.po_list,
            "Load Occupying Factor": compiled.kl_list,
            "Total Output Power": compiled.po,
            "Input Power": compiled.pin,
            "Maximum Current at Primary (A)": compiled.ip_pk,
            "Delta I at Primary (A)": compiled.delta_i,
        }
        if hasattr(compiled, "lo_crit"):
            output_params["Critical Output Inductance (H)"] = compiled.lo_crit

        self.output_tree.insert("", "end", text = "Converter Topology", values = compiled.__class__.__name__)
        self.output_tree.insert("", "end", text = "Operation Mode", values = compiled.mode)
        insert_section("Specified Parameters", input_params)
        insert_section("Specified or Derived Parameters", interdependent_params)
        insert_section("Derived Parameters", output_params)

    def prepare_circuit_export_dict(self, data: dict) -> dict:
        data = data.copy()

        # Prepend 1.0 for compatibility with transformer tab
        if "turns_ratio_list" in data and data["turns_ratio_list"]:
            data["turns_ratio_list"] = [1.0] + data["turns_ratio_list"]
        if "kl_list" in data and data["kl_list"]:
            data["kl_list"] = [1.0] + data["kl_list"]

        return data
    
    def to_export(self):
        return {
            "spec": self.capture_fields()
        }
    
    def from_import(self, data: dict):
        if "spec" in data:
            self.populate_fields(data["spec"])
            print("[INFO] Successfully imported circuit data.")

    def clear_all_entries(self):

        for key in self.entries:
            if key in ["topology", "mode"]:
                continue
            self.entries[key].delete(0, tk.END)
        
        for key in self.list_entries:
            for i in range(len(self.list_entries[key])):
                self.list_entries[key][i].delete(0, tk.END)

    """

    The section of the class below is deprecated.

    """
    """

    def export_yaml(self):
        if not hasattr(self.state, "circuit") or self.state.circuit is None:
            messagebox.showwarning("Nothing to Export", "Please compile a circuit first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".yaml",
                                                 filetypes=[("YAML files", "*.yaml")])
        if not file_path:
            return

        data = self.state.circuit.to_dict()
        data["topology"] = self.topology_var.get()
        # data["mode"] = self.converter_mode_var.get()
        export_data = self.prepare_circuit_export_dict(data) # IMPORTANT: insert 1 at the beginning of kl and turns ratio to work with transformer
        try:
            with open(file_path, 'w') as f:
                yaml.safe_dump(export_data, f)
            messagebox.showinfo("Export Successful", f"Saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def import_yaml(self):
        file_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            import_data = self.sanitize_imported_data_for_circuit(data)
            self.populate_fields(import_data)

            # Optional: auto-compile after import
            # self.compile_circuit()

            messagebox.showinfo("Import Successful", f"Loaded from {file_path}")
        except Exception as e:
            messagebox.showerror("Import Failed", str(e))

    def sanitize_imported_data_for_circuit(self, data: dict) -> dict:
        data = data.copy()
        required_len = len(data.get("vo_list", []))

        for key in ("turns_ratio_list", "kl_list"):
            values = data.get(key)

            if values is None:
                continue  # key may not be required for circuit input

            if not isinstance(values, list):
                raise ValueError(f"{key} must be a list.")

            if len(values) != (required_len + 1):
                raise ValueError(
                    f"{key} must include a primary entry (1.0) followed by one value for each output (expected {required_len + 1}, got {len(values)})."
                )

            if abs(values[0] - 1.0) < 1e-6:
                data[key] = values[1:]  # remove the primary
            else:
                raise ValueError(f"The first entry of {key} should be 1.0 for the primary.")

        return data

    """
