"""Offline regression tests: no credentials, browser, dialog, or network access.

Run: .venv/bin/python -m unittest discover -s tests -v
"""
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from selenium.common.exceptions import (
    StaleElementReferenceException, TimeoutException, WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from ipoRequest import IpoRequest
from seleniumUtils import SeleniumUtils


def element(*, text="", tag="input", visible=True, enabled=True, **attrs):
    field = Mock(spec=WebElement)
    field.text, field.tag_name = text, tag
    field.get_attribute.side_effect = attrs.get
    field.get_dom_attribute.side_effect = attrs.get
    field.is_displayed.return_value = visible
    field.is_enabled.return_value = enabled
    field.is_selected.return_value = False
    field.value_of_css_property.return_value = "visible"
    return field


class ImmediateWait:
    """Use Selenium's real conditions without spending time polling."""
    def __init__(self, driver, timeout=None):
        self.driver = driver

    def until(self, condition):
        result = condition(self.driver)
        if not result:
            raise TimeoutException("Test condition was not satisfied")
        return result


class IpoTests(unittest.TestCase):
    def setUp(self):
        # Patch every external entry point before constructing the real class.
        self.driver = Mock()
        self.driver.find_elements.return_value = []
        self.accounts = [dict(uid=f"test-{i}", upa="test-login", uspa="test-trade")
                         for i in range(1, 5)]
        patches = {
            "factory": patch("ipoRequest.SeleniumUtils.getChromedriver", return_value=self.driver),
            "config": patch("ipoRequest.FileUtils.open_file", return_value={"sbis_login_info": self.accounts}),
            "slack": patch("ipoRequest.Slack"),
            "dialog": patch("ipoRequest.subprocess.run"),
            "wait": patch("ipoRequest.WebDriverWait", ImmediateWait),
        }
        self.mocks = {name: self.enterContext(patcher) for name, patcher in patches.items()}
        self.app = IpoRequest()
        self.wait = ImmediateWait(self.driver)

    def test_ipo_browser_uses_eager_and_shorter_page_timeout(self):
        self.assertEqual(self.mocks["factory"].call_args.kwargs, {"page_load_strategy": "eager"})
        self.driver.set_page_load_timeout.assert_called_once_with(45)

    def test_each_start_position_processes_only_remaining_accounts(self):
        for start in range(1, 5):
            with self.subTest(start=start), patch.object(self.app, "one_person_ipo_request") as run:
                self.mocks["dialog"].return_value = SimpleNamespace(stdout=str(start))
                self.app.ipo_request()
                self.assertEqual([args.args[2] for args in run.call_args_list], self.accounts[start - 1:])

    def test_cancel_never_logs_in_or_notifies(self):
        self.mocks["dialog"].return_value = SimpleNamespace(stdout="\n")
        self.app.ipo_request()
        self.driver.get.assert_not_called()
        self.driver.close.assert_called_once()
        self.mocks["slack"].return_value.post_message_to_channel.assert_not_called()

    def test_dialog_rejects_invalid_and_unregistered_positions(self):
        for output, count in [("0", 4), ("5", 4), ("bad", 4), ("3", 2)]:
            with self.subTest(output=output, count=count), self.assertRaises(ValueError):
                self.mocks["dialog"].return_value = SimpleNamespace(stdout=output)
                self.app.choose_start_person(count)
        with self.assertRaises(ValueError):
            self.app.choose_start_person(0)

    def test_dialog_failure_propagates_and_closes_browser(self):
        self.mocks["dialog"].side_effect = subprocess.CalledProcessError(1, "osascript")
        with self.assertRaises(subprocess.CalledProcessError):
            self.app.ipo_request()
        self.driver.get.assert_not_called()
        self.driver.close.assert_called_once()

    def test_webdriver_failure_reports_error_and_closes_browser(self):
        self.mocks["dialog"].return_value = SimpleNamespace(stdout="3")
        with patch.object(self.app, "one_person_ipo_request", side_effect=WebDriverException("test failure")), \
                patch("ipoRequest.traceback.print_exc"):
            self.app.ipo_request()
        message = self.mocks["slack"].return_value.post_message_to_channel.call_args.args[1]
        self.assertIn("test failure", message)
        self.driver.close.assert_called_once()

    def test_request_url_validation(self):
        for href in ["/oeapw011?type=21&p_cd=667A",
                     "https://m.sbisec.co.jp/oeapw011?p_cd=664A&type=21"]:
            with self.subTest(href=href):
                self.assertTrue(self.app.is_ipo_request_url(href))
        for href in [None, "", "/oeapw011?type=22&p_cd=667A", "/oeapw011?type=21",
                     "/oeapw011?type=21&p_cd=", "/oeapw011?type=21&p_cd=667A&p_cd=664A",
                     "https://example.com/oeapw011?type=21&p_cd=667A",
                     "http://m.sbisec.co.jp/oeapw011?type=21&p_cd=667A",
                     "/other?type=21&p_cd=667A"]:
            with self.subTest(href=href):
                self.assertFalse(self.app.is_ipo_request_url(href))

    def test_modern_link_detection_without_heading_filters_unusable_links(self):
        good = element(href="/oeapw011?type=21&p_cd=667A")
        links = [good, element(visible=False, href="/oeapw011?type=21&p_cd=664A"),
                 element(enabled=False, href="/oeapw011?type=21&p_cd=664A"),
                 element(**{"aria-disabled": "true", "href": "/oeapw011?type=21&p_cd=664A"}),
                 element(href="/oeapw011?type=22&p_cd=664A")]
        self.driver.find_elements.side_effect = lambda by, query: links if query == ".button-group a[href*='oeapw011']" else []
        self.assertEqual(self.app.find_ipo_request_buttons(self.driver), [good])

    def test_page_types(self):
        cases = [(By.CSS_SELECTOR, "ul[role='table'][aria-label='switchTable']", "modern"),
                 (By.XPATH, self.app.IPO_LIST_HEADING_XPATH, "modern"),
                 (By.CSS_SELECTOR, "a[name]+table", "legacy"),
                 (By.XPATH, '//*[@id="MAINAREA02_780"]/div[1]/a[1]', "legacy_entry")]
        for by, query, expected in cases:
            with self.subTest(expected=expected, query=query):
                self.driver.find_elements.side_effect = lambda b, q: [element()] if (b, q) == (by, query) else []
                self.assertEqual(self.app.ipo_list_page_type(self.driver), expected)
        self.driver.find_elements.side_effect = None
        self.assertFalse(self.app.ipo_list_page_type(self.driver))

    def test_legacy_button_detection(self):
        button, table = element(), element(tag="table")
        table.find_elements.return_value = [button]
        self.driver.find_elements.side_effect = lambda by, query: [table] if query == "a[name]+table" else []
        self.assertEqual(self.app.find_ipo_request_buttons(self.driver), [button])
        table.find_elements.assert_called_once_with(By.CSS_SELECTOR, ".fl01 a:has(img[alt='申込'])")

    def test_modern_heading_url_and_label_fallbacks(self):
        button = element(href="/oeapw011?type=21&p_cd=667A")
        for fallback in ("url", "label"):
            with self.subTest(fallback=fallback):
                def lookup(by, query):
                    if query == "ul[role='table'][aria-label='switchTable']":
                        return [element()]
                    if by == By.XPATH and "following::a[" in query:
                        return [button] if fallback == "url" else []
                    if by == By.XPATH and "following::*" in query:
                        # Exact matching prevents 申込取消 / 申込済 from being selected.
                        self.assertIn("='申込'", query)
                        self.assertNotIn("contains(normalize-space(.)", query)
                        return [button]
                    return []
                self.driver.find_elements.side_effect = lookup
                self.assertEqual(self.app.find_ipo_request_buttons(self.driver), [button])

    def test_ready_input_skips_hidden_disabled_readonly_and_stale_copies(self):
        stale = element()
        stale.is_displayed.side_effect = StaleElementReferenceException()
        visible = element()
        self.driver.find_elements.return_value = [stale, element(visible=False), element(enabled=False),
                                                  element(readonly="true"), visible]
        self.assertIs(self.app.find_ready_input(self.driver, "input#suryo"), visible)

    def test_form_navigation_uses_link_and_visible_quantity_instead_of_hidden_name(self):
        visible = element()
        self.driver.find_elements.return_value = [element(visible=False), visible]
        button = element(href="/oeapw011?type=21&p_cd=667A")
        self.assertIs(self.app.open_ipo_request_form(self.driver, self.wait, button), visible)
        self.driver.get.assert_called_once_with("https://m.sbisec.co.jp/oeapw011?type=21&p_cd=667A")
        query = self.driver.find_elements.call_args.args[1]
        self.assertIn("input#suryo:not([type='hidden'])", query)
        button.click.assert_not_called()

    def test_slow_navigation_stops_loading_then_uses_form_without_reload(self):
        self.driver.get.side_effect = TimeoutException("slow resource")
        visible = element()
        self.driver.find_elements.return_value = [visible]
        with patch("builtins.print"):
            result = self.app.open_ipo_request_form(
                self.driver, self.wait, element(href="/oeapw011?type=21&p_cd=667A"))
        self.assertIs(result, visible)
        self.driver.get.assert_called_once()
        self.driver.execute_script.assert_called_once_with("window.stop();")

    def test_missing_quantity_fails_instead_of_continuing_to_submit(self):
        with self.assertRaisesRegex(TimeoutException, "数量入力欄"):
            self.app.open_ipo_request_form(
                self.driver, self.wait, element(href="/oeapw011?type=21&p_cd=667A"))

    def test_legacy_form_uses_click(self):
        button, quantity = element(), element()
        self.driver.find_elements.return_value = [quantity]
        self.assertIs(self.app.open_ipo_request_form(self.driver, self.wait, button), quantity)
        button.click.assert_called_once()
        self.driver.get.assert_not_called()

    def modern_terms(self, options, label_text="ポイントを使用しない"):
        price, label, radio = element(tag="select"), element(tag="label", text=label_text), element()
        price.find_elements.side_effect = lambda by, query: options if by == By.TAG_NAME else [o for o in options if f'"{o.text}"' in query]
        label.click.side_effect = lambda: setattr(radio.is_selected, "return_value", True)
        fields = {"select#kakaku, #strPriceRadio": [price],
                  "label#ipo_type_0[for='ipoRadio1']": [label]}
        self.driver.find_elements.side_effect = lambda by, query: fields.get(query, [])
        self.driver.find_element.return_value = radio
        return label, radio

    def test_modern_price_and_no_points_use_real_selenium_select(self):
        strike = element(tag="option", text="ストライクプライス（成行）")
        label, radio = self.modern_terms([element(tag="option", text="1,240円"), strike])
        self.app.fill_ipo_terms(self.driver, self.wait)
        strike.click.assert_called_once()
        label.click.assert_called_once()
        self.assertTrue(radio.is_selected())

    def test_missing_ambiguous_or_disabled_strike_options_stop(self):
        for options in [[], [element(text="1,240円")], [element(text="ストライク", enabled=False)],
                        [element(text="ストライク1"), element(text="ストライク2")]]:
            with self.subTest(options=len(options)), self.assertRaisesRegex(ValueError, "価格欄"):
                label, _ = self.modern_terms(options)
                self.app.fill_ipo_terms(self.driver, self.wait)
            label.click.assert_not_called()

    def test_unverified_points_option_is_not_selected(self):
        label, _ = self.modern_terms([element(tag="option", text="ストライク")], "ポイントを使用する")
        with self.assertRaisesRegex(ValueError, "ポイント欄"):
            self.app.fill_ipo_terms(self.driver, self.wait)
        label.click.assert_not_called()

    def test_legacy_terms(self):
        price = element()
        self.driver.find_elements.return_value = [price]
        self.app.fill_ipo_terms(self.driver, self.wait)
        price.click.assert_called_once()
        self.assertEqual(self.driver.find_element.call_args_list,
                         [call(By.NAME, "useKbn"), call(By.NAME, "usePoint")])
        self.assertEqual(self.driver.find_element.return_value.send_keys.call_args_list,
                         [call(0), call("")])

    def test_returns_without_old_wrapper_and_waits_for_list(self):
        for href in ["/oeliw011?type=21", "https://m.sbisec.co.jp/oeliw011?type=21"]:
            with self.subTest(href=href):
                link = element(href=href)
                self.driver.find_elements.side_effect = lambda by, query: [link] if "oeliw011" in query else [element()]
                self.driver.reset_mock()
                self.app.return_to_ipo_list(self.driver, self.wait)
                self.driver.get.assert_called_once_with("https://m.sbisec.co.jp/oeliw011?type=21")
                self.assertNotIn(".mtext", self.driver.find_elements.call_args_list[0].args[1])

    def test_no_targets_skips_all_input_and_submission(self):
        with patch.object(self.app, "open_ipo_request_form") as open_form:
            self.app.apply_available_ipos(self.driver, self.wait, self.accounts[0])
        open_form.assert_not_called()
        self.driver.find_element.assert_not_called()
        self.assertEqual(self.app.applyCount, 0)

    def test_empty_third_and_fourth_accounts_log_out_and_continue(self):
        """Run the actual account loop, login/list handling and logout offline."""
        self.mocks["dialog"].return_value = SimpleNamespace(stdout="3")
        username, logout, logout_confirm = element(), element(), element()
        fields = {
            (By.NAME, "username"): username,
            (By.NAME, "password"): element(),
            (By.XPATH, '//*[@id="pw-btn"]'): element(),
            (By.ID, "domestic-global-nav"): element(href="https://m.sbisec.co.jp/test-nav"),
            (By.XPATH, '//*[@id="domestic-local-nav"]/li[5]/a'): element(),
            (By.XPATH, "//*[contains(@class, 'slc-nav-item') and contains(@class, 'slc-logout')]"): logout,
            (By.XPATH, "//*[@id='middleAreaM']/div/div[1]/a"): logout_confirm,
        }
        self.driver.find_element.side_effect = lambda by, query: fields[(by, query)]
        self.driver.find_elements.side_effect = lambda by, query: (
            [element()] if query == "ul[role='table'][aria-label='switchTable']" else [])
        with patch("ipoRequest.ActionChains"), patch("builtins.print"):
            self.app.ipo_request()
        self.assertEqual(username.send_keys.call_args_list, [call("test-3"), call("test-4")])
        self.assertEqual(logout.click.call_count, 2)
        self.assertEqual(logout_confirm.click.call_count, 2)
        self.assertEqual(self.app.applyCount, 0)
        self.assertFalse(any(c.args == (By.NAME, "order_btn")
                             for c in self.driver.find_element.call_args_list))

    def test_two_applications_return_to_list_before_finding_next_target(self):
        first, second, quantity = element(), element(), element()
        events = []
        targets = iter([[first, second], [second], []])
        def find(driver):
            events.append("find")
            return next(targets)
        with patch.object(self.app, "find_ipo_request_buttons", side_effect=find), \
                patch.object(self.app, "open_ipo_request_form", return_value=quantity) as open_form, \
                patch.object(self.app, "fill_ipo_terms"), \
                patch.object(self.app, "return_to_ipo_list", side_effect=lambda d,w: events.append("return")):
            self.app.apply_available_ipos(self.driver, self.wait, self.accounts[0])
        self.assertEqual(events, ["find", "return", "find", "return", "find"])
        self.assertEqual([c.args[2] for c in open_form.call_args_list], [first, second])
        self.assertEqual(quantity.clear.call_count, 2)
        self.assertEqual(quantity.send_keys.call_args_list, [call("6000", Keys.TAB)] * 2)
        self.assertEqual(self.app.applyCount, 2)
        names = [c.args[1] for c in self.driver.find_element.call_args_list]
        self.assertEqual(names, ["tr_pass", "order_kakunin", "order_btn"] * 2)

    def test_input_error_never_reaches_confirmation_or_submission(self):
        with patch.object(self.app, "find_ipo_request_buttons", return_value=[element()]), \
                patch.object(self.app, "open_ipo_request_form", return_value=element()), \
                patch.object(self.app, "fill_ipo_terms", side_effect=ValueError("unknown option")):
            with self.assertRaises(ValueError):
                self.app.apply_available_ipos(self.driver, self.wait, self.accounts[0])
        self.driver.find_element.assert_not_called()
        self.assertEqual(self.app.applyCount, 0)

    def test_failed_list_return_does_not_start_another_application(self):
        link = element(href="/oeliw011?type=21")
        self.driver.find_elements.side_effect = lambda by, query: [link] if "oeliw011" in query else []
        with patch.object(self.app, "find_ipo_request_buttons", return_value=[element()]) as find, \
                patch.object(self.app, "open_ipo_request_form", return_value=element()), \
                patch.object(self.app, "fill_ipo_terms"):
            with self.assertRaises(TimeoutException):
                self.app.apply_available_ipos(self.driver, self.wait, self.accounts[0])
        find.assert_called_once()
        self.assertEqual(sum(c.args == (By.NAME, "order_btn")
                             for c in self.driver.find_element.call_args_list), 1)


class DriverFactoryTests(unittest.TestCase):
    def test_defaults_and_ipo_strategy_without_launch_or_download(self):
        with patch("seleniumUtils.ChromeDriverManager") as manager, \
                patch("seleniumUtils.ChromeService"), patch("seleniumUtils.webdriver.Chrome") as chrome:
            manager.return_value.install.return_value = "/fake/chromedriver"
            for kwargs, strategy in [({}, "normal"), ({"page_load_strategy": "eager"}, "eager"),
                                     ({"isHeadless": True, "page_load_strategy": "eager"}, "eager")]:
                with self.subTest(kwargs=kwargs):
                    result = SeleniumUtils.getChromedriver(__file__, **kwargs)
                    self.assertIs(result, chrome.return_value)
                    options = chrome.call_args.kwargs["options"]
                    self.assertEqual(options.page_load_strategy, strategy)
                    self.assertEqual("--no-sandbox" in options.arguments, kwargs.get("isHeadless", False))


if __name__ == "__main__":
    unittest.main()
