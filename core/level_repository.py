from core import Level, Grid

def get_all_levels():
    levels = []

    # Уровень 1
    level1_grid = Grid()
    truth_table = {
        (0, 0): (0,),
        (0, 1): (0,),
        (1, 0): (0,),
        (1, 1): (1,)
    }
    levels.append(Level(level1_grid, truth_table))

    # Уровень 2
    level2_grid = Grid()
    truth_table = {
        (0, 0): (0,),
        (0, 1): (1,),
        (1, 0): (1,),
        (1, 1): (1,)
    }
    levels.append(Level(level2_grid, truth_table))

    return levels