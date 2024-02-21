from datetime import date
from decimal import Decimal
from typing import Iterable, Iterator, Optional, TextIO, cast

from ofxstatement.plugin import Plugin
from ofxstatement.parser import StatementParser
from ofxstatement.statement import Statement, StatementLine, generate_unique_transaction_id

from ofxstatement.parser import CsvStatementParser


class LloydsPlugin(Plugin):
    """Lloyds plugin (for developers only)"""

    def get_parser(self, filename: str) -> "LloydsParser":
        f = open(filename, "r")
        abc = LloydsParser(f) # create an instanse of lloyds parser
        if 'currency' not in self.settings:
            self.ui.warning("Currency is not set")
            self.ui.status("")
            self.ui.status("Edit your configuration and set the currency:")
            self.ui.status("$ ofxstatement edit-config")
            self.ui.status("[lloyds]")
            self.ui.status("plugin = lloyds")
            self.ui.status("currency = GBP")
        abc.statement.currency = self.settings.get("currency")
        return abc



class LloydsParser(CsvStatementParser):
    mappings = {"date": 0, "memo": 4}
    date_format = "%d/%m/%Y"
    start_balance: Decimal | None = None
    end_balance: str | None = None
    start_date = None
    end_date = None

    def __init__(self, fin: TextIO) -> None:
        super().__init__(fin)
        self.uids: set[str] = set()

    def parse(self) -> Statement:
        stmt = super().parse()
        stmt.start_date = self.start_date
        if self.start_balance is not None:
            stmt.start_balance = Decimal(self.start_balance)
        stmt.end_date = self.end_date
        if self.end_balance is not None:
            stmt.end_balance = Decimal(self.end_balance)
        stmt.account_id = self.account_id
        return stmt

    def parse_record(self, line: list[str]) -> Optional[StatementLine]:
        sline = super().parse_record(line)
        if sline is None:
            return None
        sline.id = generate_unique_transaction_id(sline, self.uids)
        account_id = line[3]
        debit_str = line[5]
        credit_str = line[6]
        balance_str = line[7]
        self.account_id = account_id
        self.start_date = sline.date

        if debit_str == '':
            debit = Decimal("0")
        else:
            debit = self.parse_decimal(debit_str)

        if credit_str == '':
            credit = Decimal("0")
        else:
            credit = self.parse_decimal(credit_str)

        sline.amount = (-debit + credit)
        
        if self.end_balance == None:
            self.end_balance = balance_str
        
        if self.end_date == None:
            self.end_date = sline.date
        
        if debit:
            sline.trntype = "DEBIT"
        
        if credit:
            sline.trntype = "CREDIT"
        
        typemap = dict(
            DD = 'DIRECTDEBIT', 
            FPI='CREDIT', 
            BGC='CREDIT', 
            FPO = 'DEBIT', 
            PAY = 'PAYMENT', 
            DEB = 'DEBIT', 
            SO = 'REPEATPMT', 
            COR = 'OTHER', 
            TFR = 'XFER'
        )
        trtype = line [1]
        if trtype in typemap:
            sline.trntype = typemap[trtype]
    
        balance = self.parse_decimal(balance_str)
        self.start_balance = balance + debit - credit

        return sline

    def split_records(self) -> Iterable[list[str]]:
        reader = cast(Iterator[list[str]], super().split_records())
        next(reader)  # Skip first line
        return reader
