from core import Level

class LevelFactory:
    @staticmethod
    def get_all_levels():
        return [
            LevelFactory._make_level_1(),
            LevelFactory._make_level_2(),
            LevelFactory._make_level_3(),
            LevelFactory._make_level_4(),
            LevelFactory._make_level_5(),
            LevelFactory._make_level_6(),
            LevelFactory._make_level_7(),
            LevelFactory._make_level_8(),
            LevelFactory._make_level_9(),
            LevelFactory._make_level_10(),
            LevelFactory._make_level_freeplay()
        ]

    @staticmethod
    def _make_level_1():
        truth_table = {
            (0, 0): (0,),
            (0, 1): (0,),
            (1, 0): (0,),
            (1, 1): (1,)
        }
        input_names = ["A", "B"]
        output_names = ["F"]
        name = "Уровень 1: И (AND)"
        return Level(truth_table, input_names, output_names, name, unlocked=True)

    @staticmethod
    def _make_level_2():
        truth_table = {
            (0, 0): (0,),
            (0, 1): (1,),
            (1, 0): (1,),
            (1, 1): (1,)
        }
        input_names = ["A", "B"]
        output_names = ["F"]
        name = "Уровень 2: ИЛИ (OR)"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_3():
        truth_table = {
            (0,): (1,),
            (1,): (0,)
        }
        input_names = ["A"]
        output_names = ["F"]
        name = "Уровень 3: НЕ (NOT)"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_4():
        truth_table = {
            (0, 0): (0,),
            (0, 1): (1,),
            (1, 0): (1,),
            (1, 1): (0,)
        }
        input_names = ["A", "B"]
        output_names = ["F"]
        name = "Уровень 4: XOR из базовых"
        return Level(truth_table, input_names, output_names, name, unlocked=True)

    @staticmethod
    def _make_level_5():
        truth_table = {
            (0, 0): (0, 0),
            (0, 1): (1, 0),
            (1, 0): (1, 0),
            (1, 1): (0, 1)
        }
        input_names = ["A", "B"]
        output_names = ["S", "C"]
        name = "Уровень 5: Полусумматор"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_6():
        truth_table = {
            (0, 0, 0): (0, 0),
            (0, 0, 1): (1, 0),
            (0, 1, 0): (1, 0),
            (0, 1, 1): (0, 1),
            (1, 0, 0): (1, 0),
            (1, 0, 1): (0, 1),
            (1, 1, 0): (0, 1),
            (1, 1, 1): (1, 1)
        }
        input_names = ["A", "B", "Cin"]
        output_names = ["S", "Cout"]
        name = "Уровень 6: Полный сумматор"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_7():
        truth_table = {
            (0, 0, 0): (0,),
            (0, 1, 0): (0,),
            (1, 0, 0): (1,),
            (1, 1, 0): (1,),
            (0, 0, 1): (0,),
            (0, 1, 1): (1,),
            (1, 0, 1): (0,),
            (1, 1, 1): (1,)
        }
        input_names = ["A", "B", "SEL"]
        output_names = ["F"]
        name = "Уровень 7: 2-входовый мультиплексор"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_8():
        truth_table = {
            (0, 0, 0, 0, 0, 0): (0,),
            (0, 1, 0, 0, 0, 1): (1,),
            (1, 0, 0, 0, 0, 0): (1,),
            (0, 0, 1, 0, 1, 0): (1,),
            (0, 0, 0, 1, 1, 1): (1,),
            (1, 1, 1, 1, 0, 0): (1,),
            (0, 1, 1, 0, 1, 1): (0,)
            # Добавь ещё кейсы, если хочешь полную проверку
        }
        input_names = ["A", "B", "C", "D", "SEL1", "SEL0"]
        output_names = ["F"]
        name = "Уровень 8: 4-входовый мультиплексор из подсхем"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_9():
        truth_table = {
            (0, 0, 0, 0): (0, 0),
            (0, 0, 0, 1): (0, 0),
            (0, 0, 1, 0): (0, 1),
            (0, 0, 1, 1): (0, 1),
            (0, 1, 0, 0): (1, 0),
            (0, 1, 0, 1): (1, 0),
            (0, 1, 1, 0): (1, 0),
            (0, 1, 1, 1): (1, 0),
            (1, 0, 0, 0): (1, 1),
            (1, 0, 0, 1): (1, 1),
            (1, 0, 1, 0): (1, 1),
            (1, 0, 1, 1): (1, 1),
            (1, 1, 0, 0): (1, 1),
            (1, 1, 0, 1): (1, 1),
            (1, 1, 1, 0): (1, 1),
            (1, 1, 1, 1): (1, 1),
        }
        input_names = ["D3", "D2", "D1", "D0"]
        output_names = ["F1", "F0"]
        name = "Уровень 9: Приоритетный шифратор (4 бита)"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_10():
        truth_table = {
            (0, 0): ("Q",),
            (0, 1): (0,),
            (1, 0): (1,),
            (1, 1): ("invalid",)
        }
        input_names = ["S", "R"]
        output_names = ["Q"]
        name = "Уровень 10: Триггер SR"
        return Level(truth_table, input_names, output_names, name)

    @staticmethod
    def _make_level_freeplay():
        truth_table = {}
        input_names = []
        output_names = []
        name = "Игровое поле"
        return Level(truth_table, input_names, output_names, name, unlocked=True)