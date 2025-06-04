from core import Level

class LevelFactory:
    @staticmethod
    def get_all_levels():
        return [
            LevelFactory._make_level_1(),
            LevelFactory._make_level_2(),
            LevelFactory._make_level_plain()
        ]

    @staticmethod
    def _make_level_1():
        truth_table = {
            (0, 0): (0,),
            (0, 1): (0,),
            (1, 0): (0,),
            (1, 1): (1,)
        }
        input_names = ["Input_1", "Input_2"]
        output_names = ["Output_1"]
        name = "Уровень №1: И (AND)"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_2():
        truth_table = {
            (0, 0): (0,),
            (0, 1): (1,),
            (1, 0): (1,),
            (1, 1): (1,)
        }
        input_names = ["Input_1", "Input_2"]
        output_names = ["Output_1"]
        name = "Уровень №2: ИЛИ (OR)"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_plain():
        truth_table = {}
        input_names = []
        output_names = []
        name = "Игровое поле"
        return Level(truth_table, input_names, output_names, name)