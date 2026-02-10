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
    assert len(statement.lines) == 12

    # Statement-level fields
    assert statement.currency == "EUR"
    assert statement.account_id == "1515152252"
    assert statement.start_balance == Decimal("5926.70")
    assert statement.end_balance == Decimal("2040.59")
    assert statement.start_date == datetime.datetime(2023, 12, 1)
    assert statement.end_date == datetime.datetime(2024, 1, 15)

    # [0] Card payment: ACME STORE CD 1417    14JAN24
    assert statement.lines[0].amount == Decimal("-8.99")
    assert statement.lines[0].trntype == "DEBIT"
    assert statement.lines[0].payee == "ACME STORE"
    assert statement.lines[0].memo == "DEB CD 1417    14JAN24"

    # [1] FX fee: NON-GBP TRANS FEE 2.75% CD 1417
    assert statement.lines[1].amount == Decimal("-4.79")
    assert statement.lines[1].trntype == "DEBIT"
    assert statement.lines[1].payee == "Non-GBP Transaction Fee"
    assert statement.lines[1].memo == "DEB 2.75% CD 1417"

    # [2] FX purchase: OUiog dollaros 202.40 VISAXR 1.16168 CD 1417
    assert statement.lines[2].amount == Decimal("-5975.12")
    assert statement.lines[2].trntype == "DEBIT"
    assert statement.lines[2].payee == "OUiog dollaros"
    assert statement.lines[2].memo == "DEB 202.40 VISAXR     1.16168 CD 1417"

    # [3] Faster payment in: HHHHH LTD RP... 01DEC23 16:05
    assert statement.lines[3].amount == Decimal("2000")
    assert statement.lines[3].trntype == "CREDIT"
    assert statement.lines[3].payee == "HHHHH LTD"
    assert (
        statement.lines[3].memo == "FPI RP555000111222333 207348     10 01DEC23 16:05"
    )

    # [4] Direct debit: INS2 01000011/010011110010
    assert statement.lines[4].amount == Decimal("-5.97")
    assert statement.lines[4].trntype == "DIRECTDEBIT"
    assert statement.lines[4].payee == "INS2"
    assert statement.lines[4].memo == "DD 01000011/010011110010"

    # [5] Direct debit: INS1 1010100110101-10101010
    assert statement.lines[5].amount == Decimal("-4.12")
    assert statement.lines[5].trntype == "DIRECTDEBIT"
    assert statement.lines[5].payee == "INS1"
    assert statement.lines[5].memo == "DD 1010100110101-10101010"

    # [6] Faster payment out: HMRC - TAXES 700... 01DEC23 14:49
    assert statement.lines[6].amount == Decimal("-250.00")
    assert statement.lines[6].trntype == "DEBIT"
    assert statement.lines[6].payee == "HMRC - TAXES"
    assert (
        statement.lines[6].memo
        == "FPO 700000009988776655 8833445566B 083210     10 01DEC23 14:49"
    )

    # [7] FX purchase with country code: HOTEL MARAIS EUROS 78.80 VISAXR...
    assert statement.lines[7].amount == Decimal("-73.48")
    assert statement.lines[7].trntype == "DEBIT"
    assert statement.lines[7].payee == "HOTEL MARAIS"
    assert statement.lines[7].memo == "DEB 78.80 VISAXR     1.0724 CD 1425"

    # [8] Service charge: SERVICE CHARGES REF : 998877
    assert statement.lines[8].amount == Decimal("-12.50")
    assert statement.lines[8].trntype == "PAYMENT"
    assert statement.lines[8].payee == "SERVICE CHARGES"
    assert statement.lines[8].memo == "PAY REF : 998877"

    # [9] FX fee with date: NON-GBP TRANS FEE 2.75% CD 1425    30NOV23
    assert statement.lines[9].amount == Decimal("-2.02")
    assert statement.lines[9].trntype == "DEBIT"
    assert statement.lines[9].payee == "Non-GBP Transaction Fee"
    assert statement.lines[9].memo == "DEB 2.75% CD 1425    30NOV23"

    # [10] Direct debit with alphanumeric ref: ACME PENSIONS 112233...
    assert statement.lines[10].amount == Decimal("-45.00")
    assert statement.lines[10].trntype == "DIRECTDEBIT"
    assert statement.lines[10].payee == "ACME PENSIONS"
    assert statement.lines[10].memo == "DD 112233A44556677889"

    # [11] Bank giro credit: CLIENT CO LTD 400... 01DEC23 09:15
    assert statement.lines[11].amount == Decimal("500")
    assert statement.lines[11].trntype == "CREDIT"
    assert statement.lines[11].payee == "CLIENT CO LTD"
    assert (
        statement.lines[11].memo == "BGC 400000005566778899 306364     10 01DEC23 09:15"
    )
