class Core:
    """
    Represents a magnetic core used in transformer design.
    Warning: the creation of a Core object does not handle unit conversion.

    Attributes:
        core_area (float): Effective core area A_e [m²]. (doc: Ae)
        al_value (float): Inductance per N², A_L [H / turn²]. (doc: AL)
        window_area (float): Core window area A_w [m²]. (doc: Aw)
        winding_width (float): Bobbin winding width W_b [m]. (doc: Wb)
        winding_height (float): Bobbin winding height h_b [m]. (doc: hb)
    """

    def __init__(
        self,
        core_area = None,
        al_value = None,
        window_area = None,
        winding_width = None,
        winding_height = None,
        name = None,
        core_type = None
    ):
        self.core_area = core_area
        self.al_value = al_value
        self.window_area = window_area
        self.winding_width = winding_width
        self.winding_height = winding_height
        self.name = name
        self.core_type = core_type

        self._validate()

    def get_core(self, how_to_choose):
        # TODO: get core based on how to choose
        pass

    def _validate(self):
        pass
    
    def unit_conv(self):
        self.al_value = self.al_value * 1e-9
        self.core_area = self.core_area * 1e-6
        self.window_area = self.window_area * 1e-6
        self.winding_height = self.winding_height * 1e-3
        self.winding_width = self.winding_width * 1e-3

    def __str__(self):
        return (
            "Core:\n"
            f"  Core Name              = {self.name}\n"
            f"  Core Type              = {self.core_type}\n"
            f"  Core Area (Ae)         = {self.core_area} m²\n"
            f"  AL Value (AL)          = {self.al_value} H/turn²\n"
            f"  Window Area (Aw)       = {self.window_area} m²\n"
            f"  Winding Width (Wb)     = {self.winding_width} m\n"
            f"  Winding Height (hb)    = {self.winding_height} m\n"
        )
    
    def to_dict(self) -> dict:
        return {
            "core_area": self.core_area,
            "al_value": self.al_value,
            "window_area": self.window_area,
            "winding_width": self.winding_width,
            "winding_height": self.winding_height,
            "name": self.name,
            "core_type": self.core_type
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            core_area=data.get("core_area"),
            al_value=data.get("al_value"),
            window_area=data.get("window_area"),
            winding_width=data.get("winding_width"),
            winding_height=data.get("winding_height"),
            name=data.get("name"),
            core_type=data.get("core_type")
        )


class Material:
    """
    Represents a magnetic core used in transformer design.

    Attributes:        
        b_sat (float): Core saturation flux density B_sat [T]. (doc: Bsat)
    """

    def __init__(
        self,
        b_sat = None,
        delta_b = None
    ):
        self.b_sat = b_sat
        self.delta_b = delta_b
        self._validate()
        # print(self)

    def get_material(self, how_to_choose):
        # TODO: get material based on how_to_choose
        pass

    def _validate(self):
        if not (self.b_sat or self.delta_b):
            raise ValueError("At least one of b_sat or delta_b should be specified.")

    def __str__(self):
        return (
            "Material:\n"
            f"  Saturation Flux Density (Bsat) = {self.b_sat} T\n"
            f"  Maximum Flux Density Swing (delta_B) = {self.delta_b} T\n"
        )