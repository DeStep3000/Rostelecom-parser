import argparse
import os
import sys
from pathlib import Path
from typing import Final

from rialcom_parser.client import DEFAULT_URL, RialcomBrowserClient
from rialcom_parser.exceptions import RialcomParserError
from rialcom_parser.exporter import ExcelTariffExporter
from rialcom_parser.parser import RialcomTariffParser
from rialcom_parser.service import TariffExportService

DEFAULT_OUTPUT: Final = Path("output") / "rialcom_tariffs.xlsx"
DEFAULT_BROWSER_CDP_URL: Final = os.getenv("RIALCOM_BROWSER_CDP_URL", "").strip()


def build_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Собирает тарифы RialCom и сохраняет их в Excel.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="адрес страницы с тарифами",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"путь к итоговому файлу (по умолчанию: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--timeout",
        type=_positive_float,
        default=20.0,
        help="тайм-аут загрузки страницы в секундах",
    )
    parser.add_argument(
        "--browser-cdp-url",
        default=DEFAULT_BROWSER_CDP_URL,
        help="адрес удаленного Chromium по CDP",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="показывать окно браузера при локальном запуске",
    )
    parser.add_argument(
        "--ignore-https-errors",
        action="store_true",
        help="пропускать ошибки сертификата сайта",
    )
    return parser


def main() -> int:
    """Точка входа приложения."""
    args = build_parser().parse_args()
    service = TariffExportService(
        client=RialcomBrowserClient(
            url=args.url,
            timeout=args.timeout,
            browser_cdp_url=args.browser_cdp_url or None,
            headless=not args.headed,
            ignore_https_errors=args.ignore_https_errors,
        ),
        parser=RialcomTariffParser(),
        exporter=ExcelTariffExporter(),
    )

    try:
        tariff_count = service.export(args.output)
    except (RialcomParserError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1

    print(f"Готово: {tariff_count} тарифов сохранено в {args.output}")
    return 0


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("значение должно быть больше нуля")
    return number
