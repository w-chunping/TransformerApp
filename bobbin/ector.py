import numpy as np
import cvxpy as cp
from transformer.tfdraft import TransformerDraft
from bobbin.option import WireOption

def compile_opt_prob(draft: TransformerDraft, option: WireOption):

    channel_number = len(draft.winding_list)
    irms_list = np.zeros(channel_number)
    ji_list = np.zeros(channel_number)
    pi_list = np.zeros(channel_number)
    spi_list = np.zeros(channel_number)
    ni_list = np.zeros(channel_number)

    for i, winding in enumerate(draft.winding_list):
        irms_list[i] = winding.i_rms
        ni_list[i] = winding.turns
        ji_list[i] = option.ji_list[i]
        pi_list[i] = option.pi_list[i]
        spi_list[i] = option.spi_list[i]

    compiled = {
        'irms_list': irms_list,
        'ji_list': ji_list,
        'pi_list': pi_list,
        'spi_list': spi_list,
        'ni_list': ni_list,
        'insulator_thickness': option.insulator_thickness,
        'kwb': option.kwb,
        'ht': option.ht,
        'lt': option.lt,
        'khb': option.khb,
        'wb': draft.core.winding_width,
        'hb': draft.core.winding_height
    }
    # print(compiled)
    return compiled

def optimize_diameter(compiled):
    # print(compiled)

    irms_list = compiled['irms_list']
    ji_list = compiled['ji_list']
    pi_list = compiled['pi_list']
    spi_list = compiled['spi_list']
    ni_list = compiled['ni_list']
    insulator_thickness = compiled['insulator_thickness']
    wb = compiled['wb']
    kwb = compiled['kwb']
    hb = compiled['hb']
    khb = compiled['khb']
    ht = compiled['ht']
    lt = compiled['lt']

    di_min_list = cal_di_min_list(irms_list = irms_list, ji_list = ji_list, spi_list = spi_list, pi_list = pi_list)
    li_list = cal_li_list(ni_list = ni_list, spi_list = spi_list, di_min_list = di_min_list, insulator_thickness = insulator_thickness, wb = wb, kwb = kwb)
    di_max_list = cal_di_max_list(wb = wb, kwb = kwb, spi_list = spi_list, ni_list = ni_list, li_list = li_list, insulator_thickness = insulator_thickness)
    sum_upper_bound = cal_sum_upper_bound(hb = hb, khb = khb, ht = ht, lt = lt)

    di_list = cp.Variable(len(irms_list))
    objective = cp.Maximize(di_list[0])
    
    constraints = [di_list >= di_min_list,
                  di_list <= di_max_list,
                  (di_list + insulator_thickness) @ (li_list * pi_list) <= sum_upper_bound]
    
    problem = cp.Problem(objective, constraints)
    problem.solve()

    # Output
    # print("Optimal value:", problem.value)
    # print("Optimal diameter (m):", di_list.value)


    # print("The required height is:", hr)

    result = {
        "status": problem.status,
        "di_list": None,
        "li_list": li_list,
        "j_cal_list": None,
        "fill_rate_list": None,
        "height_required": None,
        "method": "ector_continuous"
    }

    if problem.status == "optimal":

        fill_rate = (insulator_thickness + di_list.value) * (ni_list / li_list) * spi_list / wb
        j_cal = 4 * irms_list / (pi_list * spi_list * np.pi * (di_list.value ** 2))
        hr = np.sum((di_list.value + insulator_thickness) * li_list * pi_list) + ht * lt

        result.update({
            "di_list": di_list.value,
            "fill_rate_list": fill_rate,
            "j_cal_list": j_cal,
            "height_required": hr
        })

    return result

def fit_wire_ector(draft: TransformerDraft, option: WireOption, discrete: bool = False, catalog = None):
    compiled = compile_opt_prob(draft = draft, option = option)
    result = None
    if discrete:
        result = optimize_diameter_discrete(compiled = compiled, catalog = catalog)
    else:
        result = optimize_diameter(compiled = compiled)
    # result = optimize_diameter(compiled = compiled)
    # result = optimize_diameter_discrete(compiled = compiled, catalog = None)
    return result
    
def optimize_diameter_discrete(compiled, catalog=None):

    if catalog is None:
        omit_values = [0.26e-3, 0.29e-3, 0.31e-3, 0.33e-3, 0.34e-3, 0.36e-3] # diameters that are not used
        full_range = np.arange(0.1e-3, 0.37e-3, 0.01e-3)
        catalog = full_range[~np.isin(full_range, omit_values)]
        print("[WARNING] No wire diameter catalog passed in discrete method. Using default setting...")

    irms_list = compiled['irms_list']
    ji_list = compiled['ji_list']
    pi_list = compiled['pi_list']
    spi_list = compiled['spi_list']
    ni_list = compiled['ni_list']
    insulator_thickness = compiled['insulator_thickness']
    wb = compiled['wb']
    kwb = compiled['kwb']
    hb = compiled['hb']
    khb = compiled['khb']
    ht = compiled['ht']
    lt = compiled['lt']

    di_min_list = cal_di_min_list(irms_list, ji_list, spi_list, pi_list)
    li_list = cal_li_list(ni_list, spi_list, di_min_list, insulator_thickness, wb, kwb)

    # sum_upper_bound = cal_sum_upper_bound(hb, khb, ht, lt)
    height_bound = hb * khb

    # Discrete variable approach: choose from catalog
    k = len(irms_list)
    m = len(catalog)

    # Binary matrix: x[i][j] = 1 if winding i uses diameter catalog[j]
    x = cp.Variable((k, m), boolean=True)

    # Objective: maximize diameter for primary winding (i = 0)
    objective = cp.Maximize(catalog @ x[0])

    # Each winding chooses exactly one diameter
    constraints = [cp.sum(x[i]) == 1 for i in range(k)]

    # Compute effective di values (vector of shape (k,))
    di_list_expr = cp.sum(cp.multiply(x, catalog), axis=1)

    # Width usage constraint (total winding height)
    height_expr = cp.sum(cp.multiply((di_list_expr + insulator_thickness), (li_list * pi_list))) + ht * lt
    constraints.append(height_expr <= height_bound)

    # Optional: diameter bounds (enforced by catalog choice anyway)
    di_max_list = cal_di_max_list(wb, kwb, spi_list, ni_list, li_list, insulator_thickness)
    constraints.append(di_list_expr >= di_min_list)
    constraints.append(di_list_expr <= di_max_list)

    problem = cp.Problem(objective, constraints)
    problem.solve()

    result = {
        "status": problem.status,
        "di_list": None,
        "li_list": li_list,
        "j_cal_list": None,
        "fill_rate_list": None,
        "height_required": None,
        "method": "ector_discrete"
    }

    if problem.status == "optimal":
        di_values = di_list_expr.value
        fill_rate = (insulator_thickness + di_values) * (ni_list / li_list) * spi_list / wb
        j_cal = 4 * irms_list / (pi_list * spi_list * np.pi * di_values ** 2)
        hr = np.sum((di_values + insulator_thickness) * li_list * pi_list) + ht * lt

        result.update({
            "di_list": di_values,
            "fill_rate_list": fill_rate,
            "j_cal_list": j_cal,
            "height_required": hr
        })

    return result

# function for calculating the minimum diameter
def cal_di_min_list(irms_list, ji_list, spi_list, pi_list):
    return 2 * np.sqrt(irms_list / (ji_list * np.pi * spi_list * pi_list))

# function for calculating the maximum diameter
def cal_di_max_list(wb, kwb, spi_list, ni_list, li_list, insulator_thickness):
    return wb * kwb / (spi_list * np.ceil(ni_list / li_list)) - insulator_thickness

# function for calculating the layers needed
def cal_li_list(ni_list, spi_list, di_min_list, insulator_thickness, wb, kwb):
    return np.ceil(ni_list * spi_list * (di_min_list + insulator_thickness) / (wb * kwb))

def cal_sum_upper_bound(hb, khb, ht, lt):
    return hb * khb - ht * lt
