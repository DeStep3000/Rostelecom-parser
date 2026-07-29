from typing import Final

import requests

from rialcom_parser.exceptions import SourceFetchError

DEFAULT_URL: Final = "https://www.rialcom.ru/internet_tariffs/"
DEFAULT_USER_AGENT: Final = "RialcomTariffParser/1.0"


class RialcomClient:
    """Загружает страницу с тарифами RialCom."""

    def __init__(
        self,
        url: str = DEFAULT_URL,
        timeout: float = 20.0,
        session: requests.Session | None = None,
    ) -> None:
        self.url = url
        self.timeout = timeout
        self._session = session or requests.Session()

    def fetch_html(self) -> str:
        """Возвращает HTML страницы или понятную ошибку загрузки."""
        try:
            response = self._session.get(
                self.url,
                timeout=self.timeout,
                headers={"User-Agent": DEFAULT_USER_AGENT},
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise SourceFetchError(f"Не удалось загрузить страницу {self.url}: {error}") from error

        if not response.encoding:
            response.encoding = "utf-8"
        return response.text
