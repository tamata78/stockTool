# -*- coding: utf-8 -*-
import json
import os

class FileUtils:
    @staticmethod
    def open_file(exec_file, openfileName):
        exec_file_path = os.path.dirname(os.path.abspath(exec_file))
        f = open(exec_file_path + openfileName, 'r')
        config = json.load(f)
        f.close()

        return config

