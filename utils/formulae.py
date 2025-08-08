import numpy as np
from utils.constants import MU_0

def calculate_gap(turns, core_area, lm):
    return ((turns **2) * MU_0 * core_area) / lm

def calculate_minimum_turns(core_area,
                           lm = None,
                           ipk = None,
                           delta_i = None,
                           b_sat = None,
                           delta_b = None,
                           voltage = None,
                           f_sw = None,
                           duty = None
                           ):
    # --- Case 1: Use peak current and peak flux density ---
    if lm is not None and ipk is not None and b_sat is not None:
        return (lm * ipk) / (b_sat * core_area)

    # --- Case 2: Use ripple current and flux swing ---
    elif lm is not None and delta_i is not None and delta_b is not None:
        return (lm * delta_i) / (delta_b * core_area)

    # --- Case 3: Use volt-second product and flux swing ---
    elif voltage is not None and f_sw is not None and duty is not None and delta_b is not None:
        return (voltage * duty) / (delta_b * core_area * f_sw)

    else:
        raise ValueError("Insufficient or inconsistent inputs for any valid calculation path.")


# def calculate_minimum_tuns(lm, ilim, b_sat, core_area):
#     return (lm * ilim) / (b_sat * core_area)

def calculate_irms_with_ref(irms_0, kl, turns_ratio, d_max, topology):
    if topology == "flyback":
        return irms_0 * np.sqrt((1 - d_max) / d_max) * kl / turns_ratio
    elif topology == "forward":
        return irms_0 * kl / turns_ratio

def calculate_turns_with_ratio(turns_ratio, ref_turns):
    return turns_ratio * ref_turns

def calculate_wire_area(irms, j):
    return irms / j

def calculate_b(inductance, current, turns, core_area):
    return (inductance * current) / (turns * core_area)

def calculate_b(turns, core_area, inductance = None, current = None, voltage = None, freq = None, duty = None):
    """
    Calculates flux density B using either:
    - inductance & current, or
    - volt-second method: voltage * time

    Parameters:
        turns (int): Number of turns (N)
        core_area (float): Core cross-sectional area (A_core)
        inductance (float, optional): Inductance (L)
        current (float, optional): Current (I)
        voltage (float, optional): Voltage (V)
        freq (float, optional): Frequency (Hz)
        duty (float, optional): Duty (dimensionless)

    Returns:
        float: Calculated B in Tesla

    Raises:
        ValueError: If required parameters are missing or inconsistent
    """
    if inductance is not None and current is not None:
        return (inductance * current) / (turns * core_area)
    elif voltage is not None and freq is not None:
        return (voltage * duty) / (turns * core_area * freq)
    else:
        raise ValueError("Insufficient parameters: need (inductance and current) or (voltage and time)")


def calculate_d(vpri, vsec, primary_turns, secondary_turns, topology):
    if topology == "flyback":
        return (vsec * primary_turns) / ((vpri * secondary_turns) + (vsec * primary_turns))
    elif topology == "forward":
        return (vsec * primary_turns) / (vpri * secondary_turns)
    else:
        raise ValueError(f"{topology} topology not implemented")

def calculate_iedc(pin, vin, d):
    return pin / (vin * d)

def calculate_deltai(vin, d, lm, fs):
    return (vin * d) / (lm * fs)

def calculate_ippk(iedc, deltai):
    return 0.5 * deltai + iedc

def calculate_irms(iedc, deltai, d):
    return np.sqrt((iedc ** 2 + ((deltai ** 2) / 12)) * d)

def convert_area_diameter(area=None, diameter=None):
    if area is None and diameter is not None:
        diameter = np.asarray(diameter)
        return np.pi * (diameter / 2) ** 2
    elif diameter is None and area is not None:
        area = np.asarray(area)
        return 2 * np.sqrt(area / np.pi)
    else:
        raise ValueError("Provide exactly one of 'area' or 'diameter', not both or neither.")
    
def d_n_vro(topology: str, vs: float, vp: float, d: float = None, n: float = 0, vro: float = None):
    if topology == "flyback":
        if d is not None:
            vro = vp * (d / (1 - d))
            n = vs / (d * vp) - vs / vp
            return d, n, vro
        elif n != 0:
            d = vs / (vs + n * vp)
            vro = vp * (d / (1 - d))
            return d, n, vro
        elif vro is not None:
            n = vs / vro
            d = vs / (vs + n * vp)
            return d, n, vro
        else:
            raise ValueError("At least one of d, n, vro should be specified.")
    if topology == "forward":
        if d is not None:
            n = vs / (vp * d)
            vro = vs / n
            return d, n, vro
        elif n != 0:
            d = vs / (vp * n)
            vro = vs / n
            return d, n, vro
        elif vro is not None:
            n = vs / vro
            d = vs / (vp * n)
            return d, n, vro
        else:
            raise ValueError("At least one of d, n, vro should be specified.")        
        
def voltage_compiler(vdc_min: float = None, vdc_max: float = None, vac_min: float = None, vac_max: float = None, cap_discharge_ratio: float = 0.8):
    vmin_cand = []
    vmax_cand = []
    if vdc_min is not None:
        vmin_cand.append(vdc_min)
    if vac_min is not None:
        vmin_cand.append(vac_min * np.sqrt(2) * cap_discharge_ratio)
    if vdc_max is not None:
        vmax_cand.append(vdc_max)
    if vac_max is not None:
        vmax_cand.append(vac_max * np.sqrt(2))
    return min(vmin_cand) if vmin_cand else None, max(vmax_cand) if vmax_cand else None

def forward_d_n(vs: float, vp: float, d: float = None, n: float = None):
    if d is not None:
        n = vs / (vp * d)
        return d, n
    elif n is not None:
        d = vs / (vp * n)
        return d, n
    else:
        raise ValueError("At least one of d, n should be specified.")