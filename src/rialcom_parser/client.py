from typing import Final

from playwright.sync_api import Page
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from rialcom_parser.cdp import resolve_cdp_connection
from rialcom_parser.exceptions import SourceFetchError

DEFAULT_URL: Final = "https://www.rialcom.ru/internet_tariffs/"
DEFAULT_USER_AGENT: Final = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/138.0.0.0 Safari/537.36"
)


class RialcomBrowserClient:
    """Открывает страницу RialCom через управляемый браузер."""

    def __init__(
        self,
        url: str = DEFAULT_URL,
        timeout: float = 20.0,
        browser_cdp_url: str | None = None,
        headless: bool = True,
        ignore_https_errors: bool = False,
    ) -> None:
        self.url = url
        self.timeout_ms = int(timeout * 1000)
        self.browser_cdp_url = browser_cdp_url
        self.headless = headless
        self.ignore_https_errors = ignore_https_errors

    def fetch_html(self) -> str:
        """Имитирует действия пользователя и возвращает итоговый HTML."""
        try:
            with sync_playwright() as playwright:
                if self.browser_cdp_url:
                    connection = resolve_cdp_connection(
                        self.browser_cdp_url,
                        self.timeout_ms,
                    )
                    browser = playwright.chromium.connect_over_cdp(
                        connection.endpoint,
                        headers=connection.headers,
                        timeout=self.timeout_ms,
                    )
                else:
                    browser = playwright.chromium.launch(headless=self.headless)

                try:
                    context = browser.new_context(
                        user_agent=DEFAULT_USER_AGENT,
                        locale="ru-RU",
                        viewport={"width": 1440, "height": 1000},
                        ignore_https_errors=self.ignore_https_errors,
                    )
                    try:
                        page = context.new_page()
                        return self._load_tariffs_page(page)
                    finally:
                        context.close()
                finally:
                    browser.close()
        except PlaywrightTimeoutError as error:
            raise SourceFetchError(
                f"Страница {self.url} не загрузилась за {self.timeout_ms / 1000:g} секунд"
            ) from error
        except PlaywrightError as error:
            raise SourceFetchError(
                f"Не удалось загрузить страницу {self.url} через браузер: {error}"
            ) from error
        except OSError as error:
            raise SourceFetchError(f"Не удалось подключиться к браузеру: {error}") from error

    def _load_tariffs_page(self, page: Page) -> str:
        page.set_default_timeout(self.timeout_ms)
        page.set_extra_http_headers({"Accept-Language": "ru-RU,ru;q=0.9"})

        response = page.goto(
            self.url,
            wait_until="domcontentloaded",
            timeout=self.timeout_ms,
        )
        if response is None:
            raise SourceFetchError("Браузер не получил ответ от страницы с тарифами")
        if not response.ok:
            raise SourceFetchError(
                f"Страница с тарифами вернула HTTP-статус {response.status}"
            )

        page.locator("#accordionTariff").wait_for(state="attached")
        self._open_tariff_section(page, "Многоквартирные дома")
        self._open_tariff_section(page, "Частные дома и коттеджи")
        return page.content()

    @staticmethod
    def _open_tariff_section(page: Page, heading: str) -> None:
        button = page.get_by_role("button", name=heading, exact=True)
        button.wait_for(state="visible")
        button.click()

        target_selector = button.get_attribute("data-target")
        if target_selector:
            page.locator(target_selector).wait_for(state="visible")
