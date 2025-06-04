from .LogicElements import *

class Level:
    def __init__(self,
                 truth_table: Dict[Tuple[int, ...], Tuple[int, ...]],
                 input_names: List[str],
                 output_names: List[str],
                 name = "Уровень",
                 unlocked = False
                 ):
        self.truth_table = truth_table
        self.input_names = input_names
        self.output_names = output_names
        self.name = name
        self.unlocked = unlocked

    def get_truth_table(self) -> Dict[Tuple[int, ...], Tuple[int, ...]]:
        return self.truth_table