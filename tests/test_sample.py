import datetime
from decimal import Decimal
import os

from ofxstatement.ui import UI

from ofxstatement_lloyds.plugin import LloydsPlugin


def test_sample() -> None:
    plugin = LloydsPlugin(UI(), {"currency": "EUR"})
    here = os.path.dirname(__file__)
    sample_filename = os.path.join(here, "sample-statement.csv")

    parser = plugin.get_parser(sample_filename)

    statement = parser.parse()

    assert statement is not None
    assert len(statement.lines) == 6

    assert statement.lines[0].amount == Decimal('-8.99')
    assert statement.lines[3].amount == Decimal('2000')
    assert statement.lines[5].date == datetime.datetime(2023, 12, 1)
    assert statement.lines[2].memo == 'ADAGIO EUROS       202.40 VISAXR     1.16168 CD 1417 '

    assert statement.start_balance == Decimal("6043.70")
    assert statement.end_balance == Decimal("2040.59")
    assert statement.start_date == datetime.datetime(2023, 12, 1)
    assert statement.end_date == datetime.datetime(2024, 1, 15)

    assert statement.currency ==  'EUR'
    assert statement.account_id == '38530568'

def sum2num(x, y):
    return x+y

def test_iop():
    h=2-5
    h=h+5*19+8
    assert h==100

    assert sum2num(5, 9) == 14
