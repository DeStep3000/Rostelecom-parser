from pathlib import Path

from rialcom_parser.client import RialcomClient
from rialcom_parser.exporter import ExcelTariffExporter
from rialcom_parser.parser import RialcomTariffParser


class TariffExportService:
    """Выполняет полный сценарий от загрузки страницы до Excel."""

    def __init__(
        self,
        client: RialcomClient,
        parser: RialcomTariffParser,
        exporter: ExcelTariffExporter,
    ) -> None:
        self._client = client
        self._parser = parser
        self._exporter = exporter

    def export(self, output_path: Path) -> int:
        """Выгружает тарифы и возвращает количество записанных строк."""
        html = self._client.fetch_html()
        tariffs = self._parser.parse(html)
        self._exporter.export(tariffs, output_path)
        return len(tariffs)
