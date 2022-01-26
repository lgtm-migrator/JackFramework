# -*- coding: utf-8 -*-
import math
import time
from abc import ABCMeta, abstractmethod

from JackFramework.SysBasic.loghander import LogHandler as log
from JackFramework.SysBasic.processbar import ShowProcess
from JackFramework.FileHandler.tensorboard_handler import TensorboardHandler

from ..Graph import graph_selection
from ..Graph.data_handler_manager import DataHandlerManager


class MetaMode(object):
    DEFAULT_RANK_ID = 0
    __metaclass__ = ABCMeta

    def __init__(self, args: object, user_inference_func: object,
                 is_training: bool = True) -> object:
        super().__init__()

        self.__args = args
        self.__is_training = is_training
        self.__user_inference_func = user_inference_func
        self.__graph, self.__data_manager, self.__tensorboard_handler = None, None, None
        self.__training_iteration, self.__val_iteration = self.__calculate_batch_size()

    @property
    def _graph(self):
        return self.__graph

    @property
    def _data_manager(self):
        return self.__data_manager

    @property
    def _is_training(self):
        return self.__is_training

    @property
    def _tensorboard_handler(self):
        return self.__tensorboard_handler

    @property
    def _training_iteration(self):
        return self.__training_iteration

    def set_training_iteration(self, iteration: int) -> None:
        self.__training_iteration = iteration

    @property
    def _val_iteration(self):
        return self.__val_iteration

    def set_val_iteration(self, iteration: int) -> None:
        self.__val_iteration = iteration

    @property
    def _get_graph_and_data_manager(self):
        return self.__graph, self.__data_manager

    def __calculate_batch_size(self):
        args = self.__args
        training_iteration, val_iteration = 0, 0
        if args.dist:
            training_iteration = math.ceil(
                args.imgNum * args.sampleNum / (args.batchSize * args.gpu))
            val_iteration = math.ceil(
                args.valImgNum * args.sampleNum / (args.batchSize * args.gpu))
        else:
            training_iteration = math.ceil(args.imgNum * args.sampleNum / args.batchSize)
            val_iteration = math.ceil(args.valImgNum * args.sampleNum / args.batchSize)
        return training_iteration, val_iteration

    def _init_datahandler_modelhandler(self, rank: object) -> object:
        args = self.__args

        if not args.dist:
            self.__tensorboard_handler = TensorboardHandler(args)
        elif rank == MetaMode.DEFAULT_RANK_ID:
            # dist reinit log
            log().init_log(args.outputDir, args.pretrain)
            log().info("LogHandler is reinitialized!")
            self.__tensorboard_handler = TensorboardHandler(args)

        model, dataloader = self.__user_inference_func(self.__args)
        assert model is not None and dataloader is not None
        self.__graph = graph_selection(self.__args, model, rank)
        self.__data_manager = DataHandlerManager(self.__args, dataloader)

    def _get_img_id(self, iteration: int, rank: object) -> int:
        args = self.__args
        if rank is None:
            return iteration
        return rank + iteration * (args.batchSize * args.gpu)

    def _save_model(self, epoch: int, rank: object) -> None:
        args = self.__args
        graph, _ = self._get_graph_and_data_manager
        off_set = 1

        if (epoch + off_set) % args.auto_save_num == 0 and (
                rank == MetaMode.DEFAULT_RANK_ID or rank is None):
            graph.save_model(epoch)

    def _save_result(self, iteration: int, rank: object,
                     outputs_data: list, supplement: list):
        _, data_manager = self._get_graph_and_data_manager
        img_id = self._get_img_id(iteration, rank)
        data_manager.save_result(outputs_data, supplement, img_id)

    @abstractmethod
    def exec(self, rank: object = None) -> None:
        # do something in this mode
        pass

    @staticmethod
    def _calculate_ave_runtime(start_time: object, end_time: object,
                               total_iteration: int, training_iteration: int) -> tuple:
        duration = (end_time - start_time) / (total_iteration)
        rest_time = (training_iteration - total_iteration) * duration
        return duration, rest_time

    @staticmethod
    def _init_show_setting(rank, training_iteration: int, bar_info: str) -> tuple:
        process_bar = None
        if rank == MetaMode.DEFAULT_RANK_ID or rank is None:
            process_bar = ShowProcess(training_iteration, bar_info)
        start_time = time.time()
        return process_bar, start_time

    @staticmethod
    def _stop_show_setting(rank: object, process_bar: object) -> None:
        if rank == MetaMode.DEFAULT_RANK_ID or rank is None:
            process_bar.close()
