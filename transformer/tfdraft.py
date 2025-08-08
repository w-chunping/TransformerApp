import numpy as np
from transformer.core import Core, Material
from transformer.tfspec import TransformerSpec, TransformerOption
from transformer.winding import Winding
from utils.formulae import calculate_gap, calculate_minimum_turns, calculate_irms_with_ref, calculate_turns_with_ratio, calculate_b, calculate_d, calculate_deltai, calculate_iedc, calculate_ippk, calculate_irms
import copy

class TransformerDraft:
    def __init__(
            self,
            spec: TransformerSpec = None,
            core: Core = None,
            material: Material = None,
            winding_list: list[Winding] = None,
            n0_min: float = None,
            lg: float = None,
            options: TransformerOption = None,
            hr: float = None,        
            iedc: float = None,
            delta_i: float = None,
            dmax_cal: float = None
    ):
        self.spec = spec
        self.core = core
        self.material = material
        self.winding_list = winding_list
        self.n0_min = n0_min
        self.lg = lg
        self.options = options
        self.hr = hr
        self.iedc = iedc
        self.delta_i = delta_i
        self.dmax_cal = dmax_cal

        self._init_validate()

    def _init_validate(self):
        pass

    def get_material(self, material: Material):
        # self.material.get_material(how_to_choose)
        self.material = copy.deepcopy(material) # test
        # self.material = Material(delta_b = 0.25)
        pass

    def get_core(self, core: Core):
        # self.core.get_core(how_to_choose)
        # self.core = Core(core_area = 58e-6,
        #                  window_area = 68e-6)   # test
        self.core = copy.deepcopy(core)
        pass

    def create_draft(self, spec: TransformerSpec, options: TransformerOption):
        # Create draft based on spec. Initialize spec and options, create empty windings and fill role, kl. Initialize the primary turn's rms current.
        self.spec = spec
        self.options = options
        self.winding_list = []
        for i in range(len(self.spec.turns_ratio_list)):
            new_winding = Winding(role = "secondary", load_occupying_factor = spec.kl_list[i])
            self.winding_list.append(new_winding)
        # self.winding_list[0].i_rms = self.spec.ip_rms
        self.winding_list[0].role = "primary"

    def update_draft_n0_min(self):
        # TODO: calculate minimum primary turns
        n0_min_cand = []
        b_limit = (self.material.b_sat * ((1 + self.options.turn_check_tolerance_b) if self.options.turn_use_tolerance else 1.0)) if self.material.b_sat is not None else None

        # method 1: saturation bound
        try:
            n = calculate_minimum_turns(lm = self.spec.lm, ipk = self.spec.ip_pk, b_sat = b_limit, core_area = self.core.core_area)
            n0_min_cand.append(n)
            print("Calculated by peak current and bsat: n0_min = ", n)
        except ValueError:
            print("Cannot calculate n0_min by peak current and bsat. Are lm, ipk, bsat specified?")
            pass

        # method 2: delta b bound (core loss)
        try:
            n = calculate_minimum_turns(lm = self.spec.lm, delta_i = self.spec.delta_i, delta_b = self.material.delta_b, core_area = self.core.core_area)
            n0_min_cand.append(n)
            print("Calculated by deltai and deltab: n0_min = ", n)
        except ValueError:
            print("Cannot calculate n0_min by delta_i and delta_b. Are lm, delta_i, delta_b specified?")
            pass

        # method 3: voltage second (similar to delta b bound)
        try:
            n = calculate_minimum_turns(voltage = self.spec.vp, f_sw = self.spec.fs, duty = self.spec.d_max, delta_b = self.material.delta_b, core_area = self.core.core_area)
            n0_min_cand.append(n)
            print("Calculated by volt-second: n0_min = ", n)
        except ValueError:
            print("Cannot calculate n0_min by volt-second. Is delta_b specified?")
            pass
        
        if n0_min_cand:
            self.n0_min = max(n0_min_cand)
            print("n0_min is calculated as ", self.n0_min)
        else:
            raise ValueError("Unable to calculate n0_min: all calculation methods failed due to missing inputs.")
        # self.n0_min = calculate_minimum_turns(lm = self.spec.lm,
        #                                      ipk = self.spec.ip_pk,
        #                                     #  b_sat = self.material.b_sat,
        #                                      b_sat = b_limit,
        #                                      core_area = self.core.core_area)
        
    def determine_draft_turns(self) -> list["TransformerDraft"]:
        # TODO: choose the number of turns of each winding and update turns ratio in winding objects
        tolerant_solutions = []
        strict_solution = None
        print("\n======== Start finding turns solution ========\n")
        self.winding_list[0].turns = np.ceil(self.n0_min)
        print(f"Starting with: np = {self.winding_list[0].turns}")
        for i in range(10): # prevent infinite loop
            print(f"\n--- Iteration {i}: Trying np = {self.winding_list[0].turns} ---")
            self.winding_list[1].turns = round(self.winding_list[0].turns * self.spec.turns_ratio_list[1])
            self.update_draft_gap()
            self.dmax_cal = -1
            while True:
                print(f"Trying ns = {self.winding_list[1].turns}")
                self.dmax_cal = calculate_d(vpri = self.spec.vp, primary_turns = self.winding_list[0].turns, vsec = self.spec.vsec_main, secondary_turns = self.winding_list[1].turns, topology = self.spec.topology)
                # print(f"Calculated dmax_cal = {self.dmax_cal}")
                d_limit = self.spec.d_max * ((1 + self.options.turn_check_tolerance_d) if self.options.turn_use_tolerance else 1.0)
                # d_limit = self.spec.d_max # changed here
                if self.dmax_cal > d_limit:
                    print(f"Violation: Calculated dmax = {self.dmax_cal} > required dmax = {d_limit}. Increase ns by 1.\n")
                    self.winding_list[1].turns += 1
                    continue
                print(f"Calculated dmax = {self.dmax_cal} < required dmax = {d_limit}. Proceed to check bmax.")
                self.iedc = calculate_iedc(pin = self.spec.pin, vin = self.spec.vp, d = self.dmax_cal)
                ippk_cal = None
                bmax_cal = None
                if self.spec.lm is not None:
                    self.delta_i = calculate_deltai(vin = self.spec.vp, d = self.dmax_cal, lm = self.spec.lm, fs = self.spec.fs)
                    ippk_cal = calculate_ippk(iedc = self.iedc, deltai = self.delta_i)
                    bmax_cal = calculate_b(inductance = self.spec.lm, current = ippk_cal, core_area = self.core.core_area, turns = self.winding_list[0].turns)
                delta_b_cal = calculate_b(voltage = self.spec.vp, duty = self.dmax_cal, freq = self.spec.fs, core_area = self.core.core_area, turns = self.winding_list[0].turns) # for deltab check
                print(f"calculated iedc = {self.iedc}, delta_i = {self.delta_i}, ippk = {ippk_cal}")
                b_limit = (self.material.b_sat * ((1 + self.options.turn_check_tolerance_b) if self.options.turn_use_tolerance else 1.0)) if self.material.b_sat is not None else None
                print(f"b_max_limit = {b_limit}, bmax_cal = {bmax_cal}; delta_b_max = {self.material.delta_b}, delta_b_cal = {delta_b_cal}")
                bsat_ok = (bmax_cal <= b_limit) if self.material.b_sat is not None else None
                # print(f"The result of bsat check is: {bsat_ok}")
                deltab_ok = (delta_b_cal <= self.material.delta_b) if self.material.delta_b is not None else None
                # print(f"The result of delta_b check is: {deltab_ok}")
                if all(x is None for x in [bsat_ok, deltab_ok]):
                    raise ValueError("Neither Bsat nor delta B is defined — cannot validate flux swing.")
                elif not any(x == False for x in [bsat_ok, deltab_ok]):
                # if bmax_cal <= b_limit:
                    print(f"Calculated bmax = {bmax_cal} < required bmax = {b_limit}.") if b_limit is not None else print("Did not set an upper bound for bsat. (material.bsat == None)")
                    print(f"Calculated delta_b = {delta_b_cal} < required deltab = {self.material.delta_b}.") if self.material.delta_b is not None else print("Did not set an upper bound for delta_b. (material.delta_b == None)")
                    is_strict = ((self.dmax_cal <= self.spec.d_max) and (self.material.b_sat is None or bmax_cal < self.material.b_sat))
                    print(f"[DEBUG] self.damx_cal = {self.dmax_cal}, self.spec.d_max = {self.spec.d_max}; bmax_cal = {bmax_cal}, self.material.b_sat = {self.material.b_sat}")
                    print(f"[DEBUG] is_strict = {is_strict}")
                    if is_strict:
                        print(f"Calculated bmax_cal = {bmax_cal} < strict bsat = {self.material.b_sat}.") if b_limit is not None else print("Did not set an upper bound for bsat. (material.bsat == None)")
                        print(f"Calculated delta_b = {delta_b_cal} < required deltab = {self.material.delta_b}.") if self.material.delta_b is not None else print("Did not set an upper bound for delta_b. (material.delta_b == None)")
                        print(f"Strict solution found: np = {self.winding_list[0].turns}, ns = {self.winding_list[1].turns}.")
                        strict_solution = copy.deepcopy(self)
                        break
                    elif self.options.turn_use_tolerance:
                        print(f"Tolerant solution recorded: np = {self.winding_list[0].turns}, ns = {self.winding_list[1].turns}. Warning: bsat slightly exceeds bsat of the material but within a ratio of {self.options.turn_check_tolerance_b}.\n")
                        tolerant_solutions.append(copy.deepcopy(self))
                        self.winding_list[1].turns += 1
                        continue
                else:
                    print(f"Violation: Calculated bmax_cal = {bmax_cal} > required bmax = {b_limit}.") if b_limit is not None else print("Did not set an upper bound for bsat. (material.bsat == None)")
                    print(f"Violation: Calculated delta_b_cal = {delta_b_cal} > required delta_b_max = {self.material.delta_b}.") if self.material.delta_b is not None else print("Did not set an upper bound for delta_b. (material.delta_b == None)")
                    print("Increase np by 1.")
                    break
            if strict_solution:
                break
            self.winding_list[0].turns += 1
        all_solutions = []
        if strict_solution:
            all_solutions.append(strict_solution)
        all_solutions.extend(tolerant_solutions)
        print("\n======== End of finding turns solution ========\n")
        return all_solutions

    def update_draft_gap(self):    
        self.lg = calculate_gap(turns = self.winding_list[0].turns,
                                core_area = self.core.core_area,
                                lm = self.spec.lm)
        print(f"The air gap in current configuration is: {self.lg}\n")
        
    # def determine_primary_turns(self):
    #     self.winding_list[0].turns = np.ceil(self.n0_min)
        

    def update_draft_windings(self):
        # calculate irms, turns (except for pri and sec main)
        for i in range(len(self.winding_list)):
            if i == 0:
                self.winding_list[0].i_rms = calculate_irms(iedc = self.iedc, deltai = self.delta_i, d = self.dmax_cal)
            elif i == 1:    # main output
                self.winding_list[1].turns_ratio = self.winding_list[1].turns / self.winding_list[0].turns
                self.winding_list[1].i_rms = calculate_irms_with_ref(irms_0 = self.winding_list[0].i_rms, kl = self.spec.kl_list[1], turns_ratio = self.winding_list[1].turns_ratio, d_max = self.dmax_cal, topology = self.spec.topology)
            elif i > 1: # other outputs
                self.winding_list[i].turns = np.round(calculate_turns_with_ratio(turns_ratio = self.spec.turns_ratio_list[i],
                                                                                ref_turns = self.winding_list[0].turns)
                )
                self.winding_list[i].turns_ratio = self.winding_list[i].turns / self.winding_list[0].turns
                self.winding_list[i].i_rms = calculate_irms_with_ref(irms_0 = self.winding_list[0].i_rms,
                                                                     kl = self.winding_list[i].load_occupying_factor,
                                                                     turns_ratio = self.winding_list[i].turns_ratio,
                                                                     d_max = self.dmax_cal,
                                                                     topology = self.spec.topology)
            # self.winding_list[i].wire_area = calculate_wire_area(irms = self.winding_list[i].i_rms, j = self.options.ji_list[i])
        pass

    def check_draft_bmax(self):
        bmax_cal = calculate_b(inductance = self.spec.lm,
                               current = self.spec.ip_pk,
                               turns = self.winding_list[0].turns,
                               core_area = self.core.core_area)
        return (bmax_cal < self.material.b_sat)
    
    def check_draft_dmax(self):
        dmax_cal = calculate_d(vpri = self.spec.vp,
                               vsec = self.spec.vsec_main,
                               primary_turns = self.winding_list[0].turns,
                               secondary_turns = self.winding_list[1].turns)
        return (dmax_cal < self.spec.d_max)

    def apply_wire(self, result):
        for i, winding in enumerate(self.winding_list):
            if "di_list" in result and result["di_list"] is not None:
                winding.wire_diameter = result["di_list"][i]
            if "li_list" in result and result["li_list"] is not None:
                winding.layers = result["li_list"][i]
            # if "j_cal_list" in result and result["j_cal_list"] is not None:
            #     winding.current_density = result["j_cal_list"][i]
            if "wa_list" in result and result["wa_list"] is not None:
                winding.wire_area = result["wa_list"][i]


    def __str__(self):
        windings_str = ""
        if self.winding_list:
            windings_str += "----------------------------------------------\n"
            for i, winding in enumerate(self.winding_list):
                windings_str += f"Winding {i}:\n{str(winding)}\n"
        else:
            windings_str = "    None\n"

        return (
            "=====================================================\n"
            "TransformerDraft:\n"
            # f"  {self.spec or 'None'}\n"
            # f"  {self.options or 'None'}\n"
            # f"  {self.core or 'None'}\n"
            # f"  {self.material or 'None'}\n"
            f"  Windings: {len(self.winding_list) if self.winding_list else 0} windings\n"
            f"  {windings_str}"
            # f"  N0 min: {self.n0_min}\n"
            f"  Air gap (lg): {self.lg}\n"
            # f"  hr: {self.hr}\n"
            "=====================================================\n"
        )