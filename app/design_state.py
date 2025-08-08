from transformer.tfspec import TransformerSpec, TransformerOption
from transformer.tfdraft import TransformerDraft
from transformer.core import Core, Material
from data.core_repo import CoreRepository
import numpy as np

class DesignState:
    def __init__(self):
        self.spec: TransformerSpec = None
        self.repo: CoreRepository = None
        self.core: Core = None
        self.tf_draft: TransformerDraft = None
        self.solutions = []
        self.selected_solution: TransformerDraft = None
        self.tf_option: TransformerOption = None
        self.material: Material = None
        self.catalog = None
        omit_values = [0.26e-3, 0.29e-3, 0.31e-3, 0.33e-3, 0.34e-3, 0.36e-3] # diameters that are not used
        full_range = np.arange(0.1e-3, 0.38e-3, 0.01e-3)
        mask = ~np.any(np.isclose(full_range[:, None], omit_values, rtol=0, atol=1e-10), axis=1)
        self.catalog = full_range[mask]
        # print("[DEBUG] Initial catalog:", self.catalog)