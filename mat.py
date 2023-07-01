import argparse
from meteor_reasoner.utils.loader import load_program, load_dataset
from meteor_reasoner.materialization.materialize import coalescing_d, naive_immediate_consequence_operator
from meteor_reasoner.materialization.materialize import build_index
from meteor_reasoner.utils.parser import parse_rule

import time


def timeit(func):
    """
    Decorator for measuring function's running time.
    """

    def measure_time(*args, **kw):
        start_time = time.time()
        result = func(*args, **kw)
        print("Processing time of %s(): %.2f seconds."
              % (func.__qualname__, time.time() - start_time))
        return result

    return measure_time


def check_head_body_variables(rule):
    head = rule.head
    body = rule.body
    body_variables = []
    for atom in body:
        for ent in atom.get_entity():
            body_variables.append(ent.name)

    for ent in head.get_entity():
        if ent.type == "variable" and ent.name not in body_variables:
            return False
    return True


class DatalogMTLReasoner:
    def __init__(self, data_path, data_type="datalogmtl"):
        # with open(rulepath) as file:
        #     raw_program = file.readlines()
        #     self.program = load_program(raw_program)
        with open(data_path) as file:
            lines = file.readlines()
            if data_type == "quadruple":
                raw_data = []
                for line in lines: # convert quadruple to triple
                    items = line.strip().split("\t")
                    raw_data.append("{}({},{})@{}".format(items[1], items[0], items[2], items[3]))
            else:
                raw_data = lines[:]
            self.data = [item.strip() for item in raw_data]
            atemporal_data = set([item.split("@")[0] + "@1" for item in raw_data])
            atemporal_data = list(atemporal_data)
            self.D = load_dataset(raw_data)
            self.Datalog = load_dataset(atemporal_data)
            coalescing_d(self.Datalog)
            coalescing_d(self.D)
            self.D_index = build_index(self.D)
            self.Datalog_index = build_index(self.Datalog)
        self.predicate_arity = {}
        for predicate in self.D:
            for entity in self.D[predicate]:
                self.predicate_arity[predicate] = len(entity)

    def get_training_data(self, target_predicate, datalogmtl=True):
        target = []
        if datalogmtl:
            for line in self.data:
                if line.startswith(target_predicate):
                    target.append(line.strip())
            return target
        else:
            for line in self.data:
                if line.startswith(target_predicate):
                    target.append(line.strip().split("@")[0] + "@1")
            return target

    def check_predicate_arity(self, rule):
        # print(rule.head.get_predicate(), self.predicate_arity)  # DEBUG
        # print(rule.head.get_predicate() not in self.predicate_arity)
        # print(self.predicate_arity.keys())
        # print(rule.head.get_predicate() not in self.predicate_arity.keys())
        # print(type(rule.head.get_predicate()))
        if rule.head.get_predicate() not in self.predicate_arity:
            return False
        if len(rule.head.get_entity()) != self.predicate_arity[rule.head.get_predicate()]:
            return False
        for atom in rule.body:
            if atom.get_predicate() not in self.predicate_arity:
                return False
            if len(atom.get_entity()) != self.predicate_arity[atom.get_predicate()]:
                return False
        return True

    def calculate_standard_confidence(self, derived_facts, target_predicate, datalogmtl=True):
        matched = 0
        target = self.get_training_data(target_predicate, datalogmtl)
        for fact in derived_facts:
            if fact in target:
                matched += 1
        if len(derived_facts) > 0:
            return matched / len(derived_facts)
        else:
            return 0

    def calculate_head_coverage(self, derived_facts, target_predicate, datalogmtl=True):
        matched = 0
        target = self.get_training_data(target_predicate, datalogmtl)
        for fact in derived_facts:
            if fact in target:
                matched += 1
        if len(derived_facts) > 0:
            return matched / len(target)
        else:
            return 0

    # partial_completeness_assumption
    def calculate_pca_confidence(self, derived_facts, target_predicate, datalogmtl=True):
        matched = 0
        target = self.get_training_data(target_predicate, datalogmtl)
        # pca target, remove the second entity
        pca_target = []
        for fact in target:
            pca_target.append(fact.split("(")[1].split(",")[0])

        for fact in derived_facts:
            if fact in target:
                matched += 1
            else:
                if fact.split("(")[1].split(",")[0] not in pca_target:
                    matched += 1
        # TODO: return pca_support
        if len(derived_facts) > 0:
            return matched / len(derived_facts)
        else:
            return 0

    def apply_rules(self, rule, target_predicate, mode="pca", datalogmtl=True, beta=0.5):
        scores = {"score": 0}

        if rule.strip()[-1] == ".":
            rule = rule.strip()[:-1]
        try:
            rule = parse_rule(rule.strip().replace(" ", ""))
        except:
            scores["error"] = "The format of {} is not correct".format(rule)
            return scores

        if not check_head_body_variables(rule):
            scores["error"] = "Variables of the head does not appear in the body"
            return scores

        if not self.check_predicate_arity(rule):
            scores["error"] = "Some predicate does not exist or some predicate's arity is not correct!"
            return scores

        try:
            derived_facts_dict = naive_immediate_consequence_operator([rule], self.D, self.D_index) if datalogmtl \
                else naive_immediate_consequence_operator([rule], self.Datalog, self.Datalog_index)
            scores["count_prediction"] = len(derived_facts_dict)
            template = "{}({})@{}"
            derived_facts = []
            if target_predicate in derived_facts_dict:
                for entity in derived_facts_dict[target_predicate]:
                    for interval in derived_facts_dict[target_predicate][entity]:
                        fact = template.format(target_predicate, ",".join([item.name for item in entity]),
                                               interval.left_value)
                        derived_facts.append(fact)
            scores["pca_confidence"] = self.calculate_pca_confidence(derived_facts, target_predicate, datalogmtl)
            scores["confidence"] = self.calculate_standard_confidence(derived_facts, target_predicate, datalogmtl)
            scores["head_coverage"] = self.calculate_head_coverage(derived_facts, target_predicate, datalogmtl)

            scores["score"] = beta * scores["confidence"] + (1 - beta) * scores["head_coverage"]
            # if mode == "pca":
            #     scores["score"] = scores["pca_confidence"]
            # elif mode == "standard":
            #     scores["score"] = scores["confidence"]
            # else:
            #     scores["score"] = scores["head_coverage"]
        except Exception as inst:
            scores["error"] = "MeTeoR's reasoner's error! " + str(type(inst)) + " " + str(inst)
        return scores

@timeit
def lubm_tests():
    reasoner = DatalogMTLReasoner("LUBM/train.txt")

    # score = reasoner.apply_rules("C(X1, X2) :- A(X1, X2), B(X1, X2).", "C")
    # print(score)

    # score = reasoner.apply_rules(" C(X1, X2) :- A(X1, X2).", "C")
    # print(score)  # score =

    score = reasoner.apply_rules("C(X,Z):-Diamondminus[1,1]A(X,Y),B(Y,Z)", "C", mode="pca")
    print(score)  # score = 0.6666 std  0.61 pca

    score = reasoner.apply_rules("C(X,Z):-Diamondminus[2,2]A(X,Y),B(Y,Z)", "C")
    print(score)  # score =

    score = reasoner.apply_rules("C(X,Z):-Diamondminus[1,1]A(X,Y),A(X,Y),B(Y,Z)", "C")
    print(score)  # score =

    score = reasoner.apply_rules("C(X,Z):-Diamondminus[0,0]A(X,Y),B(Y,Z)", "C")
    print(score)  # score = 0.66666666

    score = reasoner.apply_rules("C(X):-Diamondminus[1,1]A(X,Y), A(X,Y),B(Y,Z)", "C")
    print(score)  # {'score': 0, 'error': "Some predicate does not exist or some predicate's arity is not correct!"}


@timeit
def employee_test():
    reasoner = DatalogMTLReasoner("LUBM/train_vada_Employee.txt")

    score = reasoner.apply_rules(
        "Employee(X1, X2) :- memberOf(X1, X3), memberOf(X2, X3)", "Employee", datalogmtl=False)
    print(score)  # score

    # exit()



if __name__ == "__main__":
    lubm_tests()