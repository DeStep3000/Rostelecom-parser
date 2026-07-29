import argparse
import sys
from pathlib import Path
from typing import Final

from rialcom_parser.client import DEFAULT_URL, RialcomClient
from rialcom_parser.exceptions import RialcomParserError
from rialcom_parser.exporter import ExcelTariffExporter
from rialcom_parser.parser import RialcomTariffParser
from rialcom_parser.service import TariffExportService

DEFAULT_OUTPUT: Final = Path("output") / "rialcom_tariffs.xlsx"


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
        help="тайм-аут HTTP-запроса в секундах",
    )
    return parser


def main() -> int:
    """Точка входа приложения."""
    args = build_parser().parse_args()
    service = TariffExportService(
        client=RialcomClient(url=args.url, timeout=args.timeout),
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
