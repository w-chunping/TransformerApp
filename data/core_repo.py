from collections import defaultdict
from transformer.core import Core
from data.fileloader import load_excel_file
from data.dataloader import extract_sections


class CoreRepository:
    def __init__(self, filepath: str, sheet_name: str):
        self.all: list[Core] = []
        self.by_type: dict[str, list[Core]] = defaultdict(list)
        self.by_model: dict[str, Core] = {}
        self.sheet_name = sheet_name
        self.filepath = filepath

        self._load(filepath, sheet_name)

    def _load(self, filepath: str, sheet_name: str):
        df_raw = load_excel_file(filepath, sheet_name)
        df_clean = extract_sections(df_raw)
        # print(df_clean)

        for _, row in df_clean.iterrows():
            section = str(row.get("Section", "")).strip()
            name = str(row.get("TYPE", "")).strip()

            try:
                core = Core(
                    name = name,
                    # material=row.get('MATERIAL'),
                    # dimensions=row.get('Dimensions (mm)'),
                    # ap=row.get('Ap'),
                    core_area = row.get('Ae'),
                    window_area = row.get('Aw'),
                    al_value = row.get('AL'),
                    # le=row.get('Le'),
                    # ve=row.get('Ve'),
                    # wt=row.get('Wt'),
                    # pcl=row.get('PCL 100kHz 200mT'),
                    # pt=row.get('Pt  (100kHz)'),
                    winding_width = row.get('width'),
                    winding_height = row.get('height'),
                    # pin=row.get('PIN'),
                    # shape=row.get('形狀'),
                    core_type = section
                )
                core.unit_conv() # convert unit to mks

                self.all.append(core)
                self.by_type[section].append(core)
                self.by_model[name] = core

            except Exception as e:
                print(f"Skipping core '{name}' due to error: {e}")

    def get_by_type(self, section: str) -> list[Core]:
        return self.by_type.get(section, [])

    def get_by_model(self, model: str) -> Core | None:
        return self.by_model.get(model)

    def filter(self, predicate) -> list[Core]:
        return [core for core in self.all if predicate(core)]

'''
Example Usage:

from core_repo import CoreRepository

repo = CoreRepository("core_data.xls")

# All cores
for core in repo.all:
    print(core)

# All EC cores
for core in repo.get_by_type("EC"):
    print(core)

# One specific core
core = repo.get_by_model("EC35")
if core:
    print(core)

# Filter: all cores with Ap > 5
filtered = repo.filter(lambda c: c.ap and c.ap > 5)

'''