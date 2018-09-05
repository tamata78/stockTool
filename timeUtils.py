# -*- coding: utf-8 -*-
import time


class TimeUtils:
    start_time = 0
    end_time = 0

    @staticmethod
    def start():
        TimeUtils.start_time = time.time()

    @staticmethod
    def end():
        TimeUtils.end_time = time.time()

    @staticmethod
    def elapse_time():
        elapse_time = TimeUtils.end_time - TimeUtils.start_time
        return print(f"経過時間：{elapse_time}")
