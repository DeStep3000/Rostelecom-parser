import json
from unittest.mock import MagicMock, patch

from rialcom_parser.cdp import resolve_cdp_connection


def test_websocket_endpoint_is_rewritten_for_docker_network() -> None:
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(
        {"webSocketDebuggerUrl": ("ws://127.0.0.1:9222/devtools/browser/407f8e4a-5b0a-4226")}
    ).encode()

    with patch("rialcom_parser.cdp.urlopen", return_value=response) as mocked_urlopen:
        result = resolve_cdp_connection("http://browserless:9222", timeout_ms=20000)

    assert result.endpoint == "ws://browserless:9222/devtools/browser/407f8e4a-5b0a-4226"
    assert result.headers == {"Host": "127.0.0.1:9222"}
    request = mocked_urlopen.call_args.args[0]
    assert request.full_url == "http://browserless:9222/json/version"
    assert request.get_header("Host") == "127.0.0.1:9222"


def test_websocket_endpoint_does_not_require_resolution() -> None:
    endpoint = "ws://browserless:9222/devtools/browser/test"

    result = resolve_cdp_connection(endpoint, timeout_ms=20000)

    assert result.endpoint == endpoint
    assert result.headers == {}
