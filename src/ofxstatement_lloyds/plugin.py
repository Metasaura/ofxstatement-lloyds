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

    def __init__(self, fin: TextIO) -> None:
        super().__init__(fin)
        self.uids = set()

    def parse_record(self, line: list[str]) -> Optional[StatementLine]:
        sline = super().parse_record(line)
        sline.id = generate_unique_transaction_id(sline, self.uids)
        return sline

    def split_records(self) -> Iterable[list[str]]:
        reader = super().split_records()
        next(reader)  #Skip first line
        return reader
