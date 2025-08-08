TOOLTIPS_CIRCUIT = {
    "vin_dc_min" : "*Optional* The minimum DC input voltage of your circuit. Please note that at least one of minimum DC or AC input voltage should be specified.",
    "vin_dc_max" : "*Optional* The maximum DC input voltage of your circuit.",
    "vin_ac_min" : "*Optional* The minimum AC input voltage of your circuit *in RMS.*  Please note that at least one of minimum DC or AC input voltage should be specified.",
    "vin_ac_max" : "*Optional* The maximum AC input voltage of your circuit *in RMS.* ",
    "efficiency" : "*Required* The efficiency of your circuit. Accept only value from 0 to 1.",
    "lm" : "*Required* if CCM in flyback converter is selected.\n*Leave blank* if BCM and Flyback is selected.\n*Required* if forward converter is selected.",
    "fs" : "*Required* The switching frequency of your circuit.",
    "d_max" : "*Optional* The maximum duty ratio of your circuit. Accept only value from 0 to 1.",
    "vro"  : "*Optional* The reflected voltage to primary side.",
    "vo_list": ["The output voltage of the ", " channel. You should also fill your auxiliary output in one of these entries if exists."],
    "vf_list": ["The forward voltage of the diode on the ", " channel. You should also fill your auxiliary output in one of these entries if exists."],
    "io_list": ["The output current of the ", " channel. You should also fill your auxiliary output in one of these entries if exists."],
    "turns_ratio_list": ["*Optional* The turns ratio of the ", " channel. You should also fill your auxiliary output in one of these entries if exists.\n*IMPORTANT* The primary winding is set as 1. (Enter Ns/Np for this entry)\nFor example, you should enter 1.5 for an output channel with 15 turns if your primary winding has 10 turns."],
}

TOOLTIPS_TRANSFORMER = {
    'lm': "*Required* Magnetizing inductance of the transformer.",
    'ip_pk': "*Optional* Maximum current flowing through primary winding. Only considered if B sat is specified. At least one of maximum current or delta i should be specified.",
    "vp": "*Required* The voltage across primary side.",
    "fs": "*Required* Switching frequency.",
    "d_max": "*Required* Maximum duty ratio allowed.",
    "vsec_main": "*Required* The output voltage of the first channel. It should also include the diode forward voltage.",
    "pin": "*Required* The input power of the transformer.",
    "delta_i": "*Optional* Delta I of the primary side. Only considered if Delta B is specified. At least one of maximum current or delta i should be specified.",
    "b_sat": "*Optional* Saturation flux density of the material. Only considered if maximum current flowing through primary side is specified. At least one of saturation flux density or delta b should be specified.\nInstruction:\nSet 0.3 for 95材\nSet 0.27 for 40材",
    "delta_b": "*Optional* Maximum flux density swing allowed for the material. Only considered if delta i is specified. At least one of saturation flux density or delta b should be specified.",
    "turns_ratio_list": ["The turns ratio of the ", " channel. You should also fill your auxiliary output in one of these entries if exists.\n*IMPORTANT* The primary winding is defined as 1. (Enter Ns/Np for this entry)\nFor example, you should enter 1.5 for an output channel with 15 turns if your primary winding has 10 turns."],
    "kl_list": ["The load occupying ratio of the ", " channel. You should also fill your auxiliary output in one of these entries if exists."]
}

TOOLTIPS_WIRE = {
    "irms_list": "The RMS current of the corresponding channel (including primary).",
    "ji_list": "The current density of the corresponding channel (including primary).",
    "pi_list": "The number of windings for the corresponding channel (including primary).",
    "spi_list": "The number of strands of the wire for the corresponding channel (including primary)",
    "ni_list": "The number of turns for the corresponding channel (including primary).",
    "lt": "The number of layers of tape.",
    "wb": "The winding width of your chosen bobbin.",
    "hb": "The winding height of your chosen bobbin.",
    "insulator_thickness": "The thickness of the insulator around the wire. Default: 3e-5",
    "kwb": "The maximum allowed ratio of width that is used for winding for a layer in the bobbin. Default: 0.9",
    "ht": "The thickness of a single layer of tape. Default: 5e-5",
    "khb": "The maximum allowed ratio of height for all windings in the bobbin. Default: 0.8",
    "kf": "The fill factor for all of your windings. Only relevant in kf method.",
    "Aw": "The window area of the core. Only relevant in kf method.",
}

def ordinal(n):
    """Converts 1 → 1st, 2 → 2nd, etc."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n} {suffix}"
