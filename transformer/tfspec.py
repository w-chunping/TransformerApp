import numpy as np

class TransformerSpec:
    def __init__(
            self,
            lm: float = None,
            turns_ratio_list: list[float] = None,
            kl_list: list[float] = None,
            ip_pk: float = None,
            # ip_rms: float = None,
            vp: float = None,
            fs: float = None,
            d_max: float = None,
            topology: str = None,
            vsec_main: float = None,
            pin: float = None,
            delta_i: float = None
    ):
        self.lm = lm
        self.turns_ratio_list = turns_ratio_list
        self.kl_list = kl_list
        self.ip_pk = ip_pk
        # self.ip_rms = ip_rms
        self.vp = vp
        self.fs = fs
        self.d_max = d_max
        self.topology = topology
        self.vsec_main = vsec_main
        self.pin = pin
        self.delta_i = delta_i
        
        self._validate()

    def _validate(self):
        # TODO validate if the input to the transformer designer is valid
        if self.lm == None:
            raise ValueError("Failed to create transformer spec. Must specify Lm value.")
        if self.vp == None:
            raise ValueError("Failed to create transformer spec. Must specify primary voltage value.")
        if self.fs == None:
            raise ValueError("Failed to create transformer spec. Must specify switching frequency.")
        if self.d_max == None:
            raise ValueError("Failed to create transformer spec. Must specify maximum duty ratio.")
        if self.pin == None:
            raise ValueError("Failed to create transformer spec. Must specify input power.")
        if self.vsec_main == None:
            raise ValueError("Failed to create transformer spec. Must specify main output voltage.")
        if (self.ip_pk == None) and (self.delta_i == None):
            raise ValueError("Failed to create transformer spec. Must specify at least one of primary current value or current ripple value.")
        if self.turns_ratio_list[0] != 1:
            raise ValueError("The first entry of the turns ratio list is for the primary. It must be 1.")
        if self.kl_list[0] != 1:
            raise ValueError("The first entry of load occupying factor list must be 1.")

    def __str__(self):
        return (
            "========= TransformerSpec =========\n"
            f"  Lm = {self.lm}\n"
            f"  Turns Ratio = {self.turns_ratio_list}\n"
            f"  Load occupying factor (Kl) = {self.kl_list}\n"
            f"  Ip Limit = {self.ip_pk}\n"
            # f"  Ip RMS = {self.ip_rms}\n"
            f"  Vp = {self.vp}\n"
            f"  Fs = {self.fs}\n"
            f"  Max Duty = {self.d_max}\n"
            f"  Topology = {self.topology}\n"
            f"  Vsec (main) = {self.vsec_main}\n"
            f"  Pin = {self.pin}\n"
            f"  delta_i = {self.delta_i}\n"
            f"========= End of TransformerSpec =========\n"
        )

    def to_dict(self):
        def convert(val):
            if isinstance(val, (np.float32, np.float64)):
                return float(val)
            elif isinstance(val, (np.int32, np.int64)):
                return int(val)
            elif isinstance(val, np.ndarray):
                return val.tolist()
            elif isinstance(val, list):
                return [convert(v) for v in val]
            return val

        return {k: convert(v) for k, v in self.__dict__.items()}

class TransformerOption:
    def __init__(self,
                #  ji_list: list[float] = None,
                #  kf: float = None,
                #  delta_l: float = None,
                #  delta_u: float = None,
                 turn_check_tolerance_b = 0.05,
                 turn_check_tolerance_d = 0,
                 turn_use_tolerance = True
    ):
        # self.ji_list = ji_list
        # self.kf = kf
        # self.delta_l = delta_l
        # self.delta_u = delta_u
        self.turn_check_tolerance_b = turn_check_tolerance_b
        self.turn_check_tolerance_d = turn_check_tolerance_d
        self.turn_use_tolerance = turn_use_tolerance
    

    def __str__(self):
        return (
            "========= TransformerOption =========\n"
            # f"  Ji list = {self.ji_list}\n"
            # f"  Kf = {self.kf}\n"
            # f"  Delta L = {self.delta_l}\n"
            # f"  Delta U = {self.delta_u}\n"
            f"========= End of TransformerOption =========\n"
        )    