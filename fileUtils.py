# -*- coding: utf-8 -*-
import json
import os


class FileUtils:

    @staticmethod
    def open_file(exec_file, openfileName):
        exec_file_path = os.path.dirname(os.path.abspath(exec_file))
        with open(exec_file_path + openfileName, 'r') as f:
            config = json.load(f)

        return config
