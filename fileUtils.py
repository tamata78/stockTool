# -*- coding: utf-8 -*-
import json
import os
import pandas as pd


class FileUtils:

    @staticmethod
    def open_file(exec_file, openfileName):
        exec_file_path = os.path.dirname(os.path.abspath(exec_file))
        with open(exec_file_path + openfileName, 'r') as f:
            config = json.load(f)

        return config

    @staticmethod
    def readCsv(file):
        csv_dframe = pd.read_csv(file)
        return csv_dframe

    @staticmethod
    def writeFile(file, data):
        with open(file, 'wb') as f:
            f.write(data)
