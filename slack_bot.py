# _*_ coding: utf-8 _*_
from slacker import Slacker
import json
import os


class Slack(object):
    __slacker = None

    def __init__(self):
        exec_file_path = os.path.dirname(os.path.abspath(__file__))
        f = open(exec_file_path + "/config.json", 'r')
        json_data = json.load(f)
        token = json_data["slack_token"]
        self.__slacker = Slacker(token["token"])

    def get_channel_list(self):
        """
        get list(channel_id, channel_name) slack team
        """

        raw_data = self.__slacker.channels.list().body

        result = []
        for data in raw_data["channels"]:
            result.append(dict(channel_id=data["id"], channel_name=data["name"]))

        return result

    def post_message_to_channel(self, channel, message):

        channel_name = "#" + channel
        self.__slacker.chat.post_message(channel_name, message)
