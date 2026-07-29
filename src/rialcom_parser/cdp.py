import json
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class CdpConnection:
    """Параметры подключения Playwright к удаленному Chromium."""

    endpoint: str
    headers: dict[str, str]


def resolve_cdp_connection(endpoint: str, timeout_ms: int) -> CdpConnection:
    """Подготавливает WebSocket-адрес и Host для Chromium в Docker-сети."""
    parsed_endpoint = urlparse(endpoint)
    if parsed_endpoint.scheme not in {"http", "https"}:
        return CdpConnection(endpoint=endpoint, headers={})

    version_url = urlunparse(
        (
            parsed_endpoint.scheme,
            parsed_endpoint.netloc,
            "/json/version",
            "",
            parsed_endpoint.query,
            "",
        )
    )
    host_header = "127.0.0.1"
    if parsed_endpoint.port is not None:
        host_header = f"{host_header}:{parsed_endpoint.port}"

    request = Request(
        version_url,
        headers={
            "Accept": "application/json",
            "Host": host_header,
        },
    )
    with urlopen(request, timeout=max(timeout_ms / 1000, 1)) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not isinstance(payload, dict):
        return CdpConnection(endpoint=endpoint, headers={"Host": host_header})

    websocket_url = payload.get("webSocketDebuggerUrl")
    if not isinstance(websocket_url, str) or not websocket_url:
        return CdpConnection(endpoint=endpoint, headers={"Host": host_header})

    parsed_websocket = urlparse(websocket_url)
    websocket_scheme = "wss" if parsed_endpoint.scheme == "https" else "ws"
    resolved_endpoint = urlunparse(
        (
            websocket_scheme,
            parsed_endpoint.netloc,
            parsed_websocket.path,
            parsed_websocket.params,
            parsed_websocket.query,
            parsed_websocket.fragment,
        )
    )
    return CdpConnection(
        endpoint=resolved_endpoint,
        headers={"Host": host_header},
    )
