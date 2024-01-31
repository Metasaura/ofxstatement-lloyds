from datetime import date
from decimal import Decimal
from typing import Iterable, Optional, TextIO

from ofxstatement.plugin import Plugin
from ofxstatement.parser import StatementParser
from ofxstatement.statement import Statement, StatementLine, generate_unique_transaction_id

from ofxstatement.parser import CsvStatementParser


class LloydsPlugin(Plugin):
    """Lloyds plugin (for developers only)"""

    def get_parser(self, filename: str) -> "LloydsParser":
        f = open(filename, "r")
        return LloydsParser(f)



class LloydsParser(CsvStatementParser):
    mappings = {"date": 0, "memo": 4}
    date_format = "%d/%m/%Y"
    start_balance = None
    end_balance = None
    start_date = None
    end_date = None

    def __init__(self, fin: TextIO) -> None:
        super().__init__(fin)
        self.uids = set()

    def parse(self) -> Statement:
        stmt = super().parse()
        stmt.start_date = self.start_date
        stmt.start_balance = Decimal(self.start_balance)
        stmt.end_date = self.end_date
        stmt.end_balance = Decimal(self.end_balance)
        return stmt

    def parse_record(self, line: list[str]) -> Optional[StatementLine]:
        sline = super().parse_record(line)
        sline.id = generate_unique_transaction_id(sline, self.uids)
        debit = line[5]
        credit = line[6]
        balance = line[7]
        self.start_balance = balance
        self.start_date = sline.date
        if debit == '':
            debit = 0
        else:
            debit = self.parse_decimal(debit)
        if credit == '':
            credit = 0
        else:
            credit = self.parse_decimal(credit)
        sline.amount = (-debit + credit)
        
        if self.end_balance == None:
            self.end_balance = balance
        
        if self.end_date == None:
            self.end_date = sline.date


        return sline

    def split_records(self) -> Iterable[list[str]]:
        reader = super().split_records()
        next(reader)  #Skip first line
        return reader
