from core import Level, Grid

def get_all_levels():
    levels = []

    # Уровень 1
    truth_table1 = {
        (0, 0): (0,),
        (0, 1): (0,),
        (1, 0): (0,),
        (1, 1): (1,)
    }
    input_names1 = ["Input_1", "Input_2"]
    output_names1 = ["Output_1"]
    levels.append(Level(truth_table1, input_names1, output_names1))

    # Уровень 2
    truth_table2 = {
        (0, 0): (0,),
        (0, 1): (1,),
        (1, 0): (1,),
        (1, 1): (1,)
    }
    input_names2 = ["Input 1", "Input 2"]
    output_names2 = ["Output 1"]
    levels.append(Level(truth_table2, input_names2, output_names2))

    return levels