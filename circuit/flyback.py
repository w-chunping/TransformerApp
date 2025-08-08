import numpy as np
from utils.formulae import calculate_iedc, calculate_deltai, calculate_ippk, d_n_vro, voltage_compiler

class Flyback:
    def __init__(self,
                 vin_dc_min: float = None,
                 vin_dc_max: float = None,
                 vin_ac_min: float = None,
                 vin_ac_max: float = None,
                 vp: float = None,
                 vo_list: list[float] = None,
                 vf_list: list[float] = None,
                 io_list: list[float] = None,
                 po_list:list[float] = None,
                 efficiency: float = None,
                 po: float = None,
                 pin: float = None,
                 lm: float = None,
                 turns_ratio_list: list[float] = None,
                 kl_list: list[float] = None,
                 ip_pk: float = None,
                 fs: float = None,
                 d_max: float = None,
                 vro: float = None,
                 mode: str = None,
                 delta_i: float = None
                 ):
        self.vp = vp
        self.vin_dc_min = vin_dc_min
        self.vin_dc_max = vin_dc_max
        self.vin_ac_min = vin_ac_min
        self.vin_ac_max = vin_ac_max
        self.vo_list = vo_list
        self.vf_list = vf_list
        self.io_list = io_list
        self.po_list = po_list
        self.efficiency = efficiency
        self.po = po
        self.pin = pin
        self.lm = lm
        self.turns_ratio_list = turns_ratio_list
        self.kl_list = kl_list
        self.ip_pk = ip_pk
        self.fs = fs
        self.d_max = d_max
        self.vro = vro
        self.mode = mode
        self.delta_i = delta_i
        self._validate()

    def compile_params(self):

        self.vp, _ = voltage_compiler(vdc_min = self.vin_dc_min, vdc_max = self.vin_dc_max, vac_min = self.vin_ac_min, vac_max = self.vin_ac_max)

        self.po_list = list((np.array(self.vo_list) + np.array(self.vf_list))* np.array(self.io_list))
        self.po = np.sum(self.po_list)
        self.pin = self.po / self.efficiency
        self.kl_list = self.po_list / self.po
        # self.kl_list = np.insert(self.kl_list, 0, 1)

        self.turns_ratio_list = np.zeros(len(self.vo_list)) if self.turns_ratio_list is None else self.turns_ratio_list
        self.d_max, self.turns_ratio_list[0], self.vro = d_n_vro(topology = "flyback", vs = (self.vf_list[0] + self.vo_list[0]), vp = self.vp, d = self.d_max, n = self.turns_ratio_list[0], vro = self.vro)

        self.turns_ratio_list = (np.array(self.vo_list) + np.array(self.vf_list)) / self.vro
        # self.turns_ratio_list = np.insert(self.turns_ratio_list, 0, 1)
        if self.mode == "BCM":
            lcrit = (self.vp * (self.d_max ** 2) / (2 * (self.pin / self.vp) * self.fs))
            self.lm = lcrit
        iedc = calculate_iedc(pin = self.pin, vin = self.vp, d = self.d_max)
        self.delta_i = calculate_deltai(vin = self.vp, d = self.d_max, lm = self.lm, fs = self.fs)
        self.ip_pk = calculate_ippk(iedc = iedc, deltai = self.delta_i)
        # print(f"iedc = {iedc}, deltai = {self.delta_i}, ip_pk = {self.ip_pk}")


    def __str__(self):
        return (
            "========= Flyback Converter =========\n"
            f"  Vin_dc_min                  = {self.vin_dc_min}\n"
            f"  Vin_dc_max                  = {self.vin_dc_max}\n"
            f"  Vin_ac_min                  = {self.vin_ac_min}\n"
            f"  Vin_ac_max                  = {self.vin_ac_max}\n"
            f"  vp                     = {self.vp}\n"
            f"  VO List                     = {self.vo_list}\n"
            f"  VF List                     = {self.vf_list}\n"
            f"  IO List                     = {self.io_list}\n"
            f"  Switching Frequency (Fs)    = {self.fs}\n"
            f"  Mode                        = {self.mode}\n"
            f"------------------------------------------------------------\n"
            f"  Duty Cycle (D)              = {self.d_max}\n"
            f"  Reflected voltage (Vro)     = {self.vro}\n"
            f"  Turns Ratio                 = {self.turns_ratio_list}\n"
            f"  Lm                          = {self.lm}\n"
            f"------------------------------------------------------------\n"
            f"  Total PO                    = {self.po}\n"
            f"  PO List                     = {self.po_list}\n"
            f"  Load Occupying Factor (Kl)  = {self.kl_list}\n"
            f"  Efficiency                  = {self.efficiency}\n"
            f"  PIN                         = {self.pin}\n"
            f"  Ip Peak                     = {self.ip_pk}\n"
            f"  Delta I                     = {self.delta_i}\n"
            "========= End of Flyback Converter =========\n"
        )

    # @classmethod
    # def from_yaml(cls, filepath):
    #     with open(filepath, "r") as f:
    #         data = yaml.safe_load(f)
    #     return cls(**data)

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

    def _validate(self):
        if self.mode == "CCM":
            if not self.lm:
                raise ValueError("Must specify magnetizing inductance for CCM operation.")
        elif self.mode == "BCM":
            if self.lm:
                print("[WARNING] The magnetizing inductance is a derived parameter for BCM design. The value filled in magnetizing inductance entry will not be used.")
        if not self.efficiency:
            raise ValueError("You must specify a value between 0 and 1 for efficiency.")
        if self.efficiency < 0 or self.efficiency > 1:
            raise ValueError("Efficiency must be a value between 0 and 1.")
        if self.d_max:
            if self.d_max > 1 or self.d_max < 0:
                raise ValueError("Your duty ratio must be a value between 0 and 1.")