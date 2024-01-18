from typing import Iterable

from ofxstatement.plugin import Plugin
from ofxstatement.parser import StatementParser
from ofxstatement.statement import Statement, StatementLine

from ofxstatement.parser import CsvStatementParser

__import__("pkg_resources").declare_namespace(__name__)


class LloydsPlugin(Plugin):
    """Lloyds plugin (for developers only)"""

    def get_parser(self, filename: str) -> "LloydsParser":
        return LloydsParser(filename)



class LloydsParser(CsvStatementParser):
    mappings = {"date": 0, "memo": 4, "bank_account_to": 3}
    date_format = "%d/%m/%Y"
