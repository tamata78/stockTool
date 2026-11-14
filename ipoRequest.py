import os
import subprocess
import traceback
from urllib.parse import parse_qs, urljoin, urlsplit
from selenium.common.exceptions import WebDriverException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait, Select  # wait
from selenium.webdriver.support import expected_conditions as EC  # condition wait
from selenium.webdriver.common.action_chains import ActionChains
from slack_bot import Slack
from seleniumUtils import SeleniumUtils
from fileUtils import FileUtils
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class IpoRequest:

    IPO_APPLY_LINK_SELECTOR = ".button-group a[href*='oeapw011']"
    IPO_REQ_BUTTON_SELECTOR = ".fl01 a:has(img[alt='申込'])"
    LEGACY_TABLE_SELECTOR = "a[name]+table"
    LEGACY_ENTRY_XPATH = '//*[@id="MAINAREA02_780"]/div[1]/a[1]'
    WEB_WAITE_TIME = 180
    AUTH_WAIT_TIME = 600
    IPO_RETURN_LINK_SELECTOR = (
        "a[href='/oeliw011?type=21'], "
        "a[href='https://m.sbisec.co.jp/oeliw011?type=21']"
    )
    IPO_STOCK_TABLE_SELECTOR = "ul[role='table'][aria-label='switchTable']"
    IPO_QUANTITY_SELECTOR = "input#suryo:not([type='hidden']), input[name='suryo']:not([type='hidden'])"
    IPO_LIST_HEADING_XPATH = (
        "//*[self::h1 or self::h2 or self::h3 or self::h4 or self::div or self::span]"
        "[translate(normalize-space(.), ' 　', '')='IPO取扱銘柄一覧']"
    )
    IPO_APPLY_LABELS = (
        "申込", "申込み", "申し込み", "お申込み", "お申し込み",
        "ブックビルディング申込", "ブックビルディング申込み",
    )

    def __init__(self):
        self.driver = SeleniumUtils.getChromedriver(__file__, page_load_strategy="eager")
        self.driver.set_page_load_timeout(45)
        self.applyCount = 0
        self.login_info_list = FileUtils.open_file(__file__, "/config.json")["sbis_login_info"]

    def ipo_request(self):
        driver = self.driver
        slack = Slack()
        wait = WebDriverWait(driver, self.WEB_WAITE_TIME)
        try:
            start_person = self.choose_start_person(len(self.login_info_list))
            if start_person is None:
                return
            driver.get("https://login.sbisec.co.jp/login/entry?_ReturnPageInfo=WPLEThmR001Control%2FWPLEThmR001Tlst10%2FDefaultAID%2FDSWPLEThmR001Control&_ALLPARAM_JSON=&eventCode=")

            for login_info in self.login_info_list[start_person - 1:]:
                self.one_person_ipo_request(driver, wait, login_info, slack)

            message = "everyone's ipo applied num:" + str(self.applyCount)
            slack.post_message_to_channel("general", message)
        except WebDriverException:
            traceback.print_exc()
            message = "occurred system error!!\n" + traceback.format_exc()
            slack.post_message_to_channel("general", message)
        finally:
            driver.close()

    def one_person_ipo_request(self, driver, wait, login_info, slack):
        username_field = wait.until(EC.element_to_be_clickable((By.NAME, "username")))
        username_field.send_keys(login_info["uid"])
        driver.find_element(By.NAME, "password").send_keys(login_info["upa"])

        actions = ActionChains(driver)
        actions.move_to_element_with_offset(username_field, 10, 10).click().perform()

        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pw-btn"]'))).click()

        # Email authentication remains manual.
        print(f"[{login_info['uid']}] enter the email auth code and press 認証する (waiting up to {self.AUTH_WAIT_TIME}s)")
        try:
            WebDriverWait(driver, self.AUTH_WAIT_TIME).until(
                EC.presence_of_element_located((By.ID, "domestic-global-nav")))
        except TimeoutException:
            self.dump_page(driver, "after_login")
            raise

        nav = wait.until(EC.presence_of_element_located((By.ID, "domestic-global-nav")))
        driver.get(nav.get_attribute("href"))
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="domestic-local-nav"]/li[5]/a'))).click()
        if wait.until(self.ipo_list_page_type) == "legacy_entry":
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, self.LEGACY_ENTRY_XPATH))).click()
            wait.until(lambda d: self.ipo_list_page_type(d) in ("modern", "legacy"))

        stock_tables = driver.find_elements(By.CSS_SELECTOR, self.LEGACY_TABLE_SELECTOR)
        if stock_tables:
            messages = [f"================= IPO apply status {login_info['uid']} ================="]
            messages.extend(self.getIpoStockInfo(table.find_elements(By.CSS_SELECTOR, ".fl01"))
                            for table in stock_tables)
            slack.post_message_to_channel("general", '\n'.join(messages))

        self.apply_available_ipos(driver, wait, login_info)
        self.logout(driver, wait)
        return True

    def apply_available_ipos(self, driver, wait, login_info):
        while stock_reqbtns := self.find_ipo_request_buttons(driver):
            quantity_field = self.open_ipo_request_form(driver, wait, stock_reqbtns[0])
            quantity_field.clear()
            quantity_field.send_keys("6000", Keys.TAB)  # commit quantity via input/change/blur
            self.fill_ipo_terms(driver, wait)
            driver.find_element(By.NAME, "tr_pass").send_keys(login_info["uspa"])
            driver.find_element(By.NAME, "order_kakunin").click()

            driver.find_element(By.NAME, "order_btn").click()
            self.return_to_ipo_list(driver, wait)
            self.applyCount += 1

    @staticmethod
    def choose_start_person(account_count):
        if account_count < 1:
            raise ValueError("IPO申込用の口座が登録されていません。")
        # Native AppKit radio buttons; no Tkinter dependency is needed.
        script = r'''
function run(argv) {
    ObjC.import('AppKit');
    const app = $.NSApplication.sharedApplication;
    app.setActivationPolicy($.NSApplicationActivationPolicyAccessory);
    const alert = $.NSAlert.alloc.init;
    alert.messageText = 'IPO申込の開始位置';
    alert.informativeText = '何人目から開始しますか？\n選択した人から登録順に処理します。';
    alert.addButtonWithTitle('開始');
    alert.addButtonWithTitle('キャンセル');
    const cell = $.NSButtonCell.alloc.init;
    cell.setButtonType($.NSRadioButton);
    const radios = $.NSMatrix.alloc.initWithFrameModePrototypeNumberOfRowsNumberOfColumns(
        $.NSMakeRect(0, 0, 260, 112), $.NSRadioModeMatrix, cell, 4, 1);
    radios.setCellSize($.NSMakeSize(260, 26));
    for (let i = 0; i < 4; i++) {
        const option = radios.cellAtRowColumn(i, 0);
        option.title = String(i + 1) + '人目';
        option.enabled = i < Number(argv[0]);
    }
    radios.selectCellAtRowColumn(0, 0);
    alert.accessoryView = radios;
    app.activateIgnoringOtherApps(true);
    if (Number(alert.runModal) !== 1000) return '';
    return String(Number(radios.selectedRow) + 1);
}
'''
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script, str(account_count)],
            capture_output=True, text=True, check=True)
        selected = result.stdout.strip()
        if not selected:
            return None
        if selected not in {"1", "2", "3", "4"} or int(selected) > account_count:
            raise ValueError("開始位置の選択結果が不正です。")
        return int(selected)

    @staticmethod
    def logout(driver, wait):
        wait.until(EC.element_to_be_clickable((By.XPATH,
            "//*[contains(@class, 'slc-nav-item') and contains(@class, 'slc-logout')]"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH,
            "//*[@id='middleAreaM']/div/div[1]/a"))).click()

    @staticmethod
    def navigate_ipo_page(driver, url):
        try:
            driver.get(url)
        except TimeoutException:
            # A slow resource may keep navigation open after the form renders.
            # Do not navigate again: callers wait for the actual form/list.
            print("IPO画面の読み込み待ちが45秒を超えました。表示済みの画面を確認します。")
            driver.execute_script("window.stop();")

    def return_to_ipo_list(self, driver, wait):
        link = wait.until(lambda d: self.find_ready_input(
            d, self.IPO_RETURN_LINK_SELECTOR))
        self.navigate_ipo_page(driver, urljoin("https://m.sbisec.co.jp/", link.get_attribute("href")))
        wait.until(lambda d: self.ipo_list_page_type(d) in ("modern", "legacy"))

    def open_ipo_request_form(self, driver, wait, button):
        href = button.get_attribute("href")
        if self.is_ipo_request_url(href):
            self.navigate_ipo_page(driver, urljoin("https://m.sbisec.co.jp/", href))
        else:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", button)
            wait.until(EC.element_to_be_clickable(button)).click()
        try:
            return wait.until(lambda d: self.find_ready_input(
                d, self.IPO_QUANTITY_SELECTOR))
        except TimeoutException as exc:
            raise TimeoutException(
                "申込画面の表示された数量入力欄が見つかりません。"
                "画面の遷移先と数量欄のHTMLを確認してください。") from exc

    @staticmethod
    def find_ready_input(driver, selector):
        # Responsive forms may contain hidden copies before the visible field.
        for field in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                if (field.is_displayed() and field.is_enabled()
                        and not field.get_attribute("readonly")):
                    return field
            except StaleElementReferenceException:
                continue
        return False

    def fill_ipo_terms(self, driver, wait):
        price_selector = "select#kakaku, #strPriceRadio"
        price_field = wait.until(lambda d: self.find_ready_input(d, price_selector))
        if price_field.tag_name == "select":
            prices = Select(price_field)
            strike_options = [option for option in prices.options
                              if "ストライク" in "".join(option.text.split())
                              and option.is_enabled()]
            if len(strike_options) != 1:
                raise ValueError("価格欄のストライクプライスを一意に特定できません。選択肢を確認してください。")
            prices.select_by_visible_text(strike_options[0].text)

            label = wait.until(lambda d: self.find_ready_input(
                d, "label#ipo_type_0[for='ipoRadio1']"))
            label_text = "".join(label.text.split())
            if not any(text in label_text for text in (
                    "使用しない", "利用しない", "使用しません", "利用しません")):
                raise ValueError("ポイント欄の「使用しない」を確認できません。ラベルの文言を確認してください。")
            label.click()
            wait.until(EC.element_located_to_be_selected((By.ID, "ipoRadio1")))
        else:
            price_field.click()
            driver.find_element(By.NAME, "useKbn").send_keys(0)
            driver.find_element(By.NAME, "usePoint").send_keys("")

    def ipo_list_page_type(self, driver):
        if any(e.is_displayed() for e in driver.find_elements(
                By.CSS_SELECTOR, self.IPO_STOCK_TABLE_SELECTOR)):
            return "modern"
        if any(e.is_displayed() for e in driver.find_elements(By.XPATH, self.IPO_LIST_HEADING_XPATH)):
            return "modern"
        if driver.find_elements(By.CSS_SELECTOR, self.LEGACY_TABLE_SELECTOR):
            return "legacy"
        if driver.find_elements(By.XPATH, self.LEGACY_ENTRY_XPATH):
            return "legacy_entry"
        return False

    def find_ipo_request_buttons(self, driver):
        links = driver.find_elements(By.CSS_SELECTOR, self.IPO_APPLY_LINK_SELECTOR)
        candidates = self.enabled_ipo_buttons([
            link for link in links
            if self.is_ipo_request_url(link.get_attribute("href"))
        ])
        if candidates:
            return candidates
        if self.ipo_list_page_type(driver) == "modern":
            links = driver.find_elements(
                By.XPATH,
                f"({self.IPO_LIST_HEADING_XPATH})[1]/following::a[contains(@href, 'oeapw011')]",
            )
            candidates = [link for link in links
                          if self.is_ipo_request_url(link.get_attribute("href"))]
            if candidates:
                return self.enabled_ipo_buttons(candidates)
            # Exact labels avoid selecting 申込済, 申込取消, or purchase controls.
            labels = " or ".join(
                f"translate(normalize-space(.), ' 　', '')='{label}'"
                f" or @value='{label}' or @aria-label='{label}'"
                f" or .//img[@alt='{label}']"
                for label in self.IPO_APPLY_LABELS
            )
            xpath = (f"({self.IPO_LIST_HEADING_XPATH})[1]/following::*"
                     f"[self::a or self::button or self::input[@type='button' or @type='submit']]"
                     f"[{labels}]")
            candidates = driver.find_elements(By.XPATH, xpath)
        else:
            candidates = []
            for table in driver.find_elements(By.CSS_SELECTOR, self.LEGACY_TABLE_SELECTOR):
                candidates.extend(table.find_elements(By.CSS_SELECTOR, self.IPO_REQ_BUTTON_SELECTOR))
        return self.enabled_ipo_buttons(candidates)

    @staticmethod
    def is_ipo_request_url(href):
        if not href:
            return False
        url = urlsplit(urljoin("https://m.sbisec.co.jp/", href))
        query = parse_qs(url.query, keep_blank_values=True)
        return (url.scheme == "https" and url.netloc == "m.sbisec.co.jp"
                and url.path == "/oeapw011" and query.get("type") == ["21"]
                and len(query.get("p_cd", [])) == 1
                and bool(query["p_cd"][0].strip()))

    @staticmethod
    def enabled_ipo_buttons(candidates):
        return [button for button in candidates
                if button.is_displayed() and button.is_enabled()
                and button.get_attribute("aria-disabled") != "true"]

    def dump_page(self, driver, name):
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_" + name)
        driver.save_screenshot(base + ".png")
        with open(base + ".html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("dumped: " + base + ".png / .html  url=" + driver.current_url)

    def getIpoStockInfo(self, stockInfoTds):
        return  f""" {stockInfoTds[0].text}        
        BB:{stockInfoTds[3].text} status:{stockInfoTds[5].text} LotteryRet:{stockInfoTds[15].text}
        """

if __name__ == "__main__":
    ipoRequest = IpoRequest()
    ipoRequest.ipo_request()
