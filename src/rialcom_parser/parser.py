import re
from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag

from rialcom_parser.exceptions import SourceStructureError
from rialcom_parser.models import Tariff

_SPACE_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"\d[\d\s\u00a0]*")
_CHANNELS_RE = re.compile(r"\((\d+)\s+канал[а-я]*\)", re.IGNORECASE)


class RialcomTariffParser:
    """Преобразует таблицы RialCom в единый список тарифов."""

    APARTMENT_HEADING = "Многоквартирные дома"
    PRIVATE_HEADING = "Частные дома и коттеджи"

    def parse(self, html: str) -> list[Tariff]:
        """Разбирает четыре требуемые группы тарифов."""
        soup = BeautifulSoup(html, "html.parser")
        apartment_card = self._find_card(soup, self.APARTMENT_HEADING)
        private_card = self._find_card(soup, self.PRIVATE_HEADING)

        apartment_tables = self._get_tariff_tables(apartment_card, self.APARTMENT_HEADING)
        private_tables = self._get_tariff_tables(private_card, self.PRIVATE_HEADING)

        apartment_internet = self._parse_internet_table(apartment_tables[0])
        apartment_combo, channels_by_plan = self._parse_apartment_combo(apartment_tables[1])
        private_internet = self._parse_internet_table(private_tables[0])
        private_combo = self._parse_private_combo(private_tables[1], channels_by_plan)

        tariffs = apartment_internet + apartment_combo + private_internet + private_combo
        self._validate_result(tariffs)
        return tariffs

    def _find_card(self, soup: BeautifulSoup, heading: str) -> Tag:
        accordion = soup.select_one("#accordionTariff")
        if accordion is None:
            raise SourceStructureError("На странице не найден блок с тарифами")

        for card in accordion.find_all("div", class_="card", recursive=False):
            button = card.select_one("button")
            if button is not None and self._text(button) == heading:
                return card

        raise SourceStructureError(f'На странице не найден раздел "{heading}"')

    @staticmethod
    def _get_tariff_tables(card: Tag, heading: str) -> tuple[Tag, Tag]:
        tables = card.find_all("table")
        if len(tables) < 2:
            raise SourceStructureError(f'В разделе "{heading}" должно быть две таблицы')
        return tables[0], tables[1]

    def _parse_internet_table(self, table: Tag) -> list[Tariff]:
        tariffs: list[Tariff] = []
        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            if len(cells) < 4:
                raise SourceStructureError("В таблице интернет-тарифов не хватает столбцов")

            tariffs.append(
                Tariff(
                    name=self._remove_footnotes(self._text(cells[0])),
                    channels=None,
                    speed_mbps=self._kbps_to_mbps(self._parse_number(self._text(cells[3]))),
                    monthly_fee=self._parse_number(self._text(cells[1])),
                )
            )

        if not tariffs:
            raise SourceStructureError("Таблица интернет-тарифов пуста")
        return tariffs

    def _parse_apartment_combo(self, table: Tag) -> tuple[list[Tariff], dict[str, int]]:
        headers = self._combo_headers(table)
        tariffs: list[Tariff] = []
        channels_by_plan: dict[str, int] = {}

        for cells in self._combo_rows(table, len(headers)):
            row_label = self._text(cells[0])
            channels_match = _CHANNELS_RE.search(row_label)
            if channels_match is None:
                raise SourceStructureError(
                    f'Не найдено количество каналов для тарифа "{row_label}"'
                )

            channels = int(channels_match.group(1))
            plan_name = self._normalize_text(_CHANNELS_RE.sub("", row_label))
            channels_by_plan[self._plan_key(plan_name)] = channels

            for header, fee_cell in zip(headers[1:], cells[1:], strict=True):
                clean_header = self._remove_footnotes(self._text(header))
                tariffs.append(
                    Tariff(
                        name=f"{plan_name} + {clean_header}",
                        channels=channels,
                        speed_mbps=self._parse_number(clean_header),
                        monthly_fee=self._parse_number(self._text(fee_cell)),
                    )
                )

        if not tariffs:
            raise SourceStructureError("Таблица квартирных тарифов с ТВ пуста")
        return tariffs, channels_by_plan

    def _parse_private_combo(
        self,
        table: Tag,
        channels_by_plan: dict[str, int],
    ) -> list[Tariff]:
        headers = self._combo_headers(table)
        tariffs: list[Tariff] = []

        for cells in self._combo_rows(table, len(headers)):
            plan_name = self._remove_footnotes(self._text(cells[0]))
            channels = channels_by_plan.get(self._plan_key(plan_name))
            if channels is None:
                raise SourceStructureError(
                    f'Для частного тарифа "{plan_name}" не найдено количество каналов '
                    "в таблице многоквартирных домов"
                )

            for header, fee_cell in zip(headers[1:], cells[1:], strict=True):
                speed = self._parse_number(self._remove_footnotes(self._text(header)))
                # Названия столбцов двух таблиц отличаются, поэтому приводим их
                # к формату из задания и добавляем признак частного дома.
                tariff_name = f"{plan_name} + РиалКом Интернет {speed} + ТВ_ч"
                tariffs.append(
                    Tariff(
                        name=tariff_name,
                        channels=channels,
                        speed_mbps=speed,
                        monthly_fee=self._parse_number(self._text(fee_cell)),
                    )
                )

        if not tariffs:
            raise SourceStructureError("Таблица частных тарифов с ТВ пуста")
        return tariffs

    @staticmethod
    def _combo_headers(table: Tag) -> list[Tag]:
        header_row = table.select_one("thead tr")
        if header_row is None:
            raise SourceStructureError("В таблице тарифов с ТВ не найдена строка заголовков")

        headers = header_row.find_all("th")
        if len(headers) < 2:
            raise SourceStructureError("В таблице тарифов с ТВ не найдены варианты скорости")
        return headers

    @staticmethod
    def _combo_rows(table: Tag, expected_cells: int) -> list[Sequence[Tag]]:
        rows: list[Sequence[Tag]] = []
        for row in table.select("tbody tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            if len(cells) != expected_cells:
                raise SourceStructureError(
                    "Количество цен в строке тарифа не совпадает с количеством скоростей"
                )
            rows.append(cells)
        return rows

    @staticmethod
    def _parse_number(value: str) -> int:
        match = _NUMBER_RE.search(value)
        if match is None:
            raise SourceStructureError(f'В значении "{value}" не найдено число')
        return int(re.sub(r"\s+", "", match.group(0)))

    @staticmethod
    def _kbps_to_mbps(speed_kbps: int) -> int | float:
        speed_mbps = speed_kbps / 1000
        return int(speed_mbps) if speed_mbps.is_integer() else speed_mbps

    @classmethod
    def _text(cls, tag: Tag) -> str:
        return cls._normalize_text(tag.get_text(" ", strip=True))

    @staticmethod
    def _normalize_text(value: str) -> str:
        return _SPACE_RE.sub(" ", value).strip()

    @classmethod
    def _remove_footnotes(cls, value: str) -> str:
        return cls._normalize_text(value.replace("*", ""))

    @classmethod
    def _plan_key(cls, value: str) -> str:
        return re.sub(r"\s+", "", cls._remove_footnotes(value)).casefold()

    @staticmethod
    def _validate_result(tariffs: list[Tariff]) -> None:
        if not tariffs:
            raise SourceStructureError("На странице не найдено ни одного тарифа")

        names = [tariff.name for tariff in tariffs]
        if len(names) != len(set(names)):
            raise SourceStructureError("После разбора страницы обнаружены повторяющиеся тарифы")
