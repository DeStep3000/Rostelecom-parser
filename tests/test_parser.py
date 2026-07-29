from pathlib import Path

import pytest

from rialcom_parser.exceptions import SourceStructureError
from rialcom_parser.models import Tariff
from rialcom_parser.parser import RialcomTariffParser

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "rialcom_tariffs.html"


@pytest.fixture
def tariffs_html() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parse_all_tariff_groups(tariffs_html: str) -> None:
    tariffs = RialcomTariffParser().parse(tariffs_html)

    assert len(tariffs) == 11
    assert tariffs[0] == Tariff(
        name="РиалКомий-15+",
        channels=None,
        speed_mbps=200,
        monthly_fee=1000,
    )
    assert tariffs[1].name == "Социальный"
    assert tariffs[1].speed_mbps == 2
    assert tariffs[2] == Tariff(
        name="Комбо Лайт + РиалКом Интернет 50 + ТВ",
        channels=165,
        speed_mbps=50,
        monthly_fee=529,
    )
    assert tariffs[7] == Tariff(
        name="Комбо Лайт + РиалКом Интернет 50 + ТВ_ч",
        channels=165,
        speed_mbps=50,
        monthly_fee=1579,
    )


def test_private_tariffs_receive_channels_from_apartment_table(tariffs_html: str) -> None:
    tariffs = RialcomTariffParser().parse(tariffs_html)

    private_combo = [
        tariff for tariff in tariffs if tariff.name.endswith("_ч")
    ]

    assert {tariff.channels for tariff in private_combo if tariff.name.startswith("Комбо Лайт")} == {
        165
    }
    assert {tariff.channels for tariff in private_combo if tariff.name.startswith("Комбо Макс")} == {
        298
    }


def test_unknown_private_plan_causes_structure_error(tariffs_html: str) -> None:
    changed_html = tariffs_html.replace(
        "<td>Комбо Лайт</td>",
        "<td>Неизвестный пакет</td>",
        1,
    )

    with pytest.raises(SourceStructureError, match="не найдено количество каналов"):
        RialcomTariffParser().parse(changed_html)


def test_price_columns_must_match_speed_columns(tariffs_html: str) -> None:
    changed_html = tariffs_html.replace(
        "<td>1579</td>\n                    <td>2079</td>",
        "<td>1579</td>",
        1,
    )

    with pytest.raises(SourceStructureError, match="Количество цен"):
        RialcomTariffParser().parse(changed_html)
