# -*- coding: UTF-8 -*-
from JackFramework.SysBasic.switch import Switch
from JackFramework.SysBasic.loghander import LogHandler as log

from .build_training_graph import BuildTrainingGraph
from .build_testing_graph import BuildTestingGraph


def graph_selection(args: object, jf_model: object, rank: object) -> object:
    graph = None
    for case in Switch(args.mode):
        if case('train'):
            log.info("Enter training graph")
            graph = BuildTrainingGraph(args, jf_model, rank)
            break
        if case('test'):
            log.info("Enter testing graph")
            graph = BuildTestingGraph(args, jf_model, rank)
            break
        if case('background'):
            log.info("Enter background graph")
            graph = BuildTestingGraph(args, jf_model, rank)
            break
        if case('online'):
            log.info("Enter online graph")
            break
        if case('reinforcement_learning'):
            log.info("Enter reinforcement learning graph")
            break
        if case(''):
            log.error("The mode's name is error!!!")
    return graph
