from unittest.mock import MagicMock, patch

from rialcom_parser.cdp import CdpConnection
from rialcom_parser.client import RialcomBrowserClient


@patch("rialcom_parser.client.sync_playwright")
def test_client_opens_both_tariff_sections(mocked_sync_playwright: MagicMock) -> None:
    manager = MagicMock()
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()
    response = MagicMock(ok=True, status=200)
    apartment_button = MagicMock()
    private_button = MagicMock()

    mocked_sync_playwright.return_value = manager
    manager.__enter__.return_value = playwright
    playwright.chromium.launch.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page
    page.goto.return_value = response
    page.content.return_value = "<html>tariffs</html>"
    page.get_by_role.side_effect = [apartment_button, private_button]
    apartment_button.get_attribute.return_value = "#collapse1"
    private_button.get_attribute.return_value = "#collapse2"

    html = RialcomBrowserClient().fetch_html()

    assert html == "<html>tariffs</html>"
    playwright.chromium.launch.assert_called_once_with(headless=True)
    page.goto.assert_called_once()
    apartment_button.click.assert_called_once_with()
    private_button.click.assert_called_once_with()
    context.close.assert_called_once_with()
    browser.close.assert_called_once_with()


@patch("rialcom_parser.client.resolve_cdp_connection")
@patch("rialcom_parser.client.sync_playwright")
def test_client_connects_to_remote_browser(
    mocked_sync_playwright: MagicMock,
    mocked_resolve_cdp_connection: MagicMock,
) -> None:
    manager = MagicMock()
    playwright = MagicMock()
    browser = MagicMock()
    context = MagicMock()
    page = MagicMock()
    response = MagicMock(ok=True, status=200)

    mocked_sync_playwright.return_value = manager
    manager.__enter__.return_value = playwright
    mocked_resolve_cdp_connection.return_value = CdpConnection(
        endpoint="ws://browserless:9222/devtools/browser/test",
        headers={"Host": "127.0.0.1:9222"},
    )
    playwright.chromium.connect_over_cdp.return_value = browser
    browser.new_context.return_value = context
    context.new_page.return_value = page
    page.goto.return_value = response
    page.content.return_value = "<html>tariffs</html>"
    page.get_by_role.return_value.get_attribute.return_value = None

    client = RialcomBrowserClient(browser_cdp_url="http://browserless:9222")

    assert client.fetch_html() == "<html>tariffs</html>"
    playwright.chromium.connect_over_cdp.assert_called_once_with(
        "ws://browserless:9222/devtools/browser/test",
        headers={"Host": "127.0.0.1:9222"},
        timeout=20000,
    )
    playwright.chromium.launch.assert_not_called()
