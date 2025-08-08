import numpy as np
import cvxpy as cp

irms_list = np.array([3.25887, 3.9366, 0.029344])
ji_list = np.array([12, 12, 12])
pi_list = np.array([2, 3, 1])
spi_list = np.array([4, 4, 2])
ni_list = np.array([12, 10, 4])
insulator_thickness = 0.03
wb = 16.7
kwb = 0.9
hb = 2.5
khb = 0.8
ht = 0.05
lt = 8

# discrete try
# catalog = [0.25, 0.3, 0.35, 0.4]  # allowed diameters (mm)
# Generate values from 0.1 to 0.34 (inclusive) with 0.01 step
catalog = np.arange(0.1, 0.35, 0.01)

# Remove 0.26 and 0.29
catalog = catalog[(catalog != 0.26) & (catalog != 0.29)]
m = len(catalog)
catalog_arr = np.array(catalog)
n = len(irms_list)

di_min_list = 2 * np.sqrt(irms_list / (ji_list * np.pi * spi_list * pi_list))

# Binary selection matrix (n x m)
z = cp.Variable((n, m), boolean=True)

# Compute di as sum over catalog * z
di_expr = cp.sum(cp.multiply(z, catalog_arr), axis=1)

li_list = np.ceil(ni_list * spi_list * (di_min_list + insulator_thickness) / (wb * kwb))
print(li_list)

di_max_list = wb * kwb / (spi_list * np.ceil(ni_list / li_list)) - 0.03

# Height constraint
height_expr = cp.sum(cp.multiply((di_expr + insulator_thickness), (li_list * pi_list))) + ht * lt
height_limit = hb * khb


# Constraints
constraints = [
    cp.sum(z, axis=1) == 1,                         # one diameter per winding
    di_expr >= di_min_list,                         # current density
    di_expr <= di_max_list,
    height_expr <= height_limit                    # total winding height
]


# objective = cp.Maximize(di_expr[0] - cp.inv_prod(di_expr[0]))
objective = cp.Maximize(di_expr[0] + di_expr[1])

# Solve the problem
problem = cp.Problem(objective, constraints)
problem.solve()#solver = cp.GLPK_MI)

# # Output
# print("Optimal value:", problem.value)
# print("Optimal d:", di.value)
selected_diameters = None
# Output
if problem.status == "optimal":
    selected = np.argmax(z.value, axis=1)
    selected_diameters = catalog_arr[selected]
    print("Selected diameters:", selected_diameters)
else:
    print("No feasible solution")

fill_rate = (0.03 + selected_diameters) * (ni_list / li_list) * spi_list / wb
print("Width usage rate: ", fill_rate)

j_cal = 4 * irms_list / (pi_list * spi_list * np.pi * (selected_diameters ** 2))
print("The current density for each winding:", j_cal)

hr = np.sum((selected_diameters + insulator_thickness) * li_list * pi_list) + ht * lt
print("The required height is:", hr)

# fill_rate = (0.03 + di.value) * (ni_list / li_list) * spi_list / wb
# print("Width usage rate: ", fill_rate)

# j_cal = 4 * irms_list / (pi_list * spi_list * np.pi * (di.value ** 2))
# print("The current density for each winding:", j_cal)

# hr = np.sum((di.value + insulator_thickness) * li_list * pi_list) + ht * lt
# print("The required height is:", hr)