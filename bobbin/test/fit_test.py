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

di_min_list = 2 * np.sqrt(irms_list / (ji_list * np.pi * spi_list * pi_list))

li_list = np.ceil(ni_list * spi_list * (di_min_list + insulator_thickness) / (wb * kwb))
print(li_list)

di_max_list = wb * kwb / (spi_list * np.ceil(ni_list / li_list)) - 0.03

sum_upper_bound = hb * khb - ht * lt

di = cp.Variable(len(irms_list))

objective = cp.Maximize(di[0])

constraints = [di >= di_min_list,
               di <= di_max_list,
               (di + 0.03) @ (li_list * pi_list) <= sum_upper_bound]

# Solve the problem
problem = cp.Problem(objective, constraints)
problem.solve()

# Output
print("Optimal value:", problem.value)
print("Optimal d:", di.value)

fill_rate = (0.03 + di.value) * (ni_list / li_list) * spi_list / wb
print("Width usage rate: ", fill_rate)

j_cal = 4 * irms_list / (pi_list * spi_list * np.pi * (di.value ** 2))
print("The current density for each winding:", j_cal)

hr = np.sum((di.value + insulator_thickness) * li_list * pi_list) + ht * lt
print("The required height is:", hr)