import cvxpy as cp
import numpy as np

# Example problem setup
n = 6 # pin number

irms = np.array([3.25887, 3.25887, 3.9366, 3.9366, 3.9366, 0.029344])
p = np.array([2, 2, 3, 3, 3, 1])
sp = np.array([4, 4, 4, 4, 4, 2])
j = np.array([12, 12, 12, 12, 12, 12])
lower_bounds = 2 * np.sqrt(irms / (np.pi * p * sp * j))
print(lower_bounds)

wb = 16.7
wb_factor = 0.9
turns = np.array([12, 12, 10, 10, 10, 4])
upper_bounds = wb * wb_factor / (turns * sp) - 0.03
print(upper_bounds)

objective_constant = 12 * 4 / 16.7

hb = 2.5
hb_factor = 0.8
tape_layer = 8
h_tape = 0.05
sum_upper_bound = hb * hb_factor - h_tape * tape_layer - 0.03 * n
print(sum_upper_bound)

# lower_bounds = np.array([1, 2, 1, 0, 3]) # J constrained
# upper_bounds = np.array([10, 9, 7, 8, 6])
# sum_upper_bound = 20

# Define variable
d = cp.Variable(n)

# Define objective (example: sum of sqrt(di), which is concave)
objective = cp.Maximize(objective_constant * d[0])
# objective = cp.Maximize(d[0] + d[1])

# Constraints
constraints = [
    d >= lower_bounds,
    d <= upper_bounds,
    cp.sum(d) <= sum_upper_bound,
    d[0] == d[1]
]

# Solve the problem
problem = cp.Problem(objective, constraints)
problem.solve()

# Output
print("Optimal value:", problem.value)
print("Optimal d:", d.value)

fill_rate = (0.03 + d.value) * turns * sp / wb
print("Width usage rate: ", fill_rate)

j_cal = 4 * irms / (p * sp * np.pi * (d.value ** 2))
print("The current density for each winding:", j_cal)

hr = np.sum(d.value) + 0.03 * len(d.value) + 0.05 * 2 * 4
print("The required height is:", hr)