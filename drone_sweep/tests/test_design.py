"""The report is a field sheet a new operator can read."""

from drone_sweep.assemble import Inputs, assemble
from drone_sweep.report import render_html
from drone_sweep.webapp import explain_page, form_page, home_page
from tests.test_ports import DUMP


def test_report_names_fields_in_russian_and_keeps_every_key():
    card = assemble(Inputs(dump_text=DUMP, nameplates={"vtx": "Skyzone VT7550"}))
    page = render_html(card, saved_path="/tmp/report.html")
    assert "Порт приёмника" in page
    assert "USART1" in page
    assert "Подтверждено" in page
    assert "Нет данных" in page
    assert "С шильдика" in page
    assert "Skyzone VT7550" in page
    assert "С чего начать" in page
    assert "strela" not in page.lower() or "Стрела" in page
    for name in card.fields:
        assert f">{name}<" in page or f">{name}</p>" in page
    assert 'class="key">' in page
    assert "--primary-500: #ff2b2b" in page
    assert "#e5f6e5" not in page


def test_menu_pages_use_the_same_sheet():
    home = home_page().decode("utf-8")
    form = form_page().decode("utf-8")
    explain = explain_page().decode("utf-8")
    for body in (home, form, explain):
        assert 'class="sheet"' in body
        assert "Liberation Sans" in body
    assert "Собрать карточку" in home
    assert "Подключение по USB" in home
    assert "Собрать карточку" in form
    assert "dump all" in form
    assert "парол" in explain.lower()
    assert "Файл отчёта" not in home
    assert "Пять видов карточки" in home


def test_five_looks_explain_the_screen_and_the_log_in_plain_russian():
    from drone_sweep.designs import design_page

    first = design_page(1).decode("utf-8")
    assert "Ночная лампа" in first
    assert "Экран в очках" in first
    assert "Точка взлёта" in first
    assert "не скорость радио" in first
    assert "prefers-reduced-motion" in first
    names = [design_page(number).decode("utf-8") for number in range(1, 6)]
    assert len({page.split("<title>", 1)[1].split("</title>", 1)[0] for page in names}) == 5
