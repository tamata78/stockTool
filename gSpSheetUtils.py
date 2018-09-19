# -*- coding: utf-8 -*-
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os


class GSpSheetUtils():

    @staticmethod
    def getGoogleCred(exec_file, secfile):
        # authority setting(can read and write)
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        exec_file_path = os.path.dirname(os.path.abspath(exec_file))

        credentials = ServiceAccountCredentials.from_json_keyfile_name(exec_file_path + "/" + secfile, scope)
        return gspread.authorize(credentials)

