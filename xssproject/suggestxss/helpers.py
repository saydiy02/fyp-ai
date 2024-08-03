import numpy as np

def prepare_input_data(goal, attackT, skill, automation, platform):
    input_data = np.array([[goal, attackT, skill, automation, platform]])
    return input_data
