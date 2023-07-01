from meteor_reasoner.utils.ruler_interval import *
from meteor_reasoner.materialization.coalesce import *
from meteor_reasoner.materialization.index_build import *
from meteor_reasoner.classes.literal import Literal, BinaryLiteral
import decimal, copy
from meteor_reasoner.canonical.calculate_w import get_w


class CanonicalRepresentation:
    def __init__(self, D, Program):
        self.D = D
        self.D_index = defaultdict(lambda : defaultdict(list))
        self.Program = Program

    def is_bounded_program(self):
        for rule in self.Program:
            for literal in rule.body:
                if isinstance(literal, Literal):
                    for op in literal.operators:
                        if op.right_value in [decimal.Decimal("+inf")]:
                            return False
                elif isinstance(literal, BinaryLiteral):
                    if literal.operator.right_value in [decimal.Decimal("+inf")]:
                        return False
        return True

    def initilization(self):
        t_program = copy.deepcopy(self.Program)
        self.w = 2 * get_w(t_program)
        coalescing_d(self.D)
        build_index(self.D,  self.D_index)
        self.points, self.min_x, self.max_x = get_dataset_points_x(self.D, min_x_flag=True)

        print("The w is:{}".format(self.w))
        print("The maximum number in the database:{}".format(self.max_x))
        print("The minimum number in the database:{}".format(self.min_x))
        self.base_interval = Interval(self.min_x, self.max_x, False, False)
        self.z, self.gcd = get_gcd(self.Program)
        self.left_initial_ruler_intervals, self.right_initial_ruler_intervals, self.pattern_num, self.pattern_len = get_initial_ruler_intervals(self.points[:], left_border= self.min_x-self.w, right_border=self.max_x+self.w, gcd=self.gcd)

        self.left_dict, self.right_dict = construct_left_right_pattern(self.points, self.gcd)