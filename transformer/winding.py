class Winding:
    """
    Represents a winding (primary or secondary) in a transformer.

    Attributes:
        role (str): 'primary' or 'secondary'. Used for identification.
        voltage (float): The voltage accross this winding [V]. (doc: Vin,min for primary; Vo,i for secondary)
        current (float): The current flowing through this winding [A]. Kept None for primary. (doc: Io,i)
        power (float): Power for this winding [W]. Calculated as Vo,i * Io,i (doc: Pin for primary; Po,i for secondary)
        turns_ratio (float): Turns ratio relative to the primary (doc: Ni/N0)
        turns (int): Actual number of turns (doc: Ni)
        i_rms (float): RMS current through this winding [A]. (doc: Irms,i)
        wire_diameter (float): Wire diameter [m]. (doc: Di)
        load_occupying_factor (float): Contribution to the total output. Kept None for primary. (doc: KL,i)
        wire_area (float): Cross-sectional area of the wire [m²]. (doc: WAi)
        layers (float): Number of wire layers in bobbin window. (doc: mi)
    """
    def __init__(
        self,
        role: str = None,
        # voltage = None,
        # current = None,
        # power = None,
        turns_ratio: float = None,
        turns: int = None,
        i_rms: float = None,
        wire_diameter: float = None,
        load_occupying_factor: float = None,
        wire_area: float = None,
        layers: float = None,
    ):
        self.role = role
        # self.voltage = voltage
        # self.current = current
        # self.power = power
        self.turns_ratio = turns_ratio
        self.turns = turns
        self.i_rms = i_rms
        self.wire_diameter = wire_diameter
        self.load_occupying_factor = load_occupying_factor
        self.wire_area = wire_area
        self.layers = layers

        self._validate()

    def _validate(self):
        # TODO: validate if the winding is reasonable
        if self.role == "primary" and self.current != None:
            raise ValueError("The current attribute for primary winding must be None.")
        if self.role == "primary" and self.turns_ratio != 1:
            raise ValueError("The turns ratio of the primary to itself must be 1")
        if self.role == "primary" and self.load_occupying_factor != None:
            raise ValueError("The primary winding do not own a load occupying factor.")
        
    def __str__(self):
        return (
            "----------------------------------------------\n"
            f"  Role                          = {self.role}\n"
            f"  Turns Ratio (Ni/N0)           = {self.turns_ratio}\n"
            f"  Turns (Ni)                    = {self.turns}\n"
            f"  RMS Current (Irms,i)          = {self.i_rms} A\n"
            f"  Wire Diameter (Di)            = {self.wire_diameter} m\n"
            f"  Load Occupying Factor (KL,i)  = {self.load_occupying_factor}\n"
            f"  Wire Area (WAi)               = {self.wire_area} m²\n"
            f"  Layers (mi)                   = {self.layers}\n"
            f"---------------------------------------------"
        )
