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
    levels.append(Level(truth_table1))

    # Уровень 2
    truth_table2 = {
        (0, 0): (0,),
        (0, 1): (1,),
        (1, 0): (1,),
        (1, 1): (1,)
    }
    levels.append(Level(truth_table2))

    return levels