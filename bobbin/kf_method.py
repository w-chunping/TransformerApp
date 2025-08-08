from transformer.tfdraft import TransformerDraft
from bobbin.option import WireOption
from utils.formulae import calculate_wire_area, convert_area_diameter

def fit_wire_kf(draft: TransformerDraft, option: WireOption):
    window_area_required = 0
    for i in range(len(draft.winding_list)):
        draft.winding_list[i].wire_area = calculate_wire_area(irms = draft.winding_list[i].i_rms, j = option.ji_list[i])
        window_area_required += draft.winding_list[i].wire_area * draft.winding_list[i].turns
    window_area_required = window_area_required / option.kf
    
    result = {
        "status": (window_area_required <= draft.core.window_area),
        "di_list": None,
        "j_cal_list": None,
        "required_window_area": None,
        "wa_list": None,
        "method": "kf"
    }
    if (window_area_required <= draft.core.window_area):
        wa_list = []
        for i in range(len(draft.winding_list)):
            wa_list.append(draft.winding_list[i].wire_area)
        di_list = convert_area_diameter(area = wa_list)
        j_cal_list = option.ji_list
        result.update({
            "di_list": di_list,
            "wa_list": wa_list,
            "j_cal_list": j_cal_list,
            "required_window_area": window_area_required
        })
    return result
