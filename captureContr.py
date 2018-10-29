from selenium.common.exceptions import WebDriverException
from slack_bot import Slack
from seleniumUtils import SeleniumUtils
from fileUtils import FileUtils


class capureContr():

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__, True)

        capTgtList = FileUtils.readCsv("cap_tgt_list.csv")

        self.capTgtList = capTgtList

    def execute(self):
        driver = self.driver
        slack = Slack()
        try:

            for url in self.capTgtList['url']:
                img_path = SeleniumUtils.capureRange(driver, url)

                # post img to slack
                #slack.post_img_to_channel("general", img_path)

        except WebDriverException:
            import traceback
            message = "occurred system error!!\n" + str(traceback.print_exc())
            slack.post_message_to_channel("general", message)
        finally:
            driver.close()


if __name__ == "__main__":
    capureContr = capureContr()
    capureContr.execute()
