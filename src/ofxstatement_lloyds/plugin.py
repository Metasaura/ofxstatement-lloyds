import re
from decimal import Decimal
from typing import Iterable, Iterator, Optional, TextIO, cast

from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import (
    Statement,
    StatementLine,
    generate_unique_transaction_id,
)


# Lloyds transaction type to OFX TRNTYPE mapping
TRNTYPE_MAP = {
    "BGC": "CREDIT",       # Bank Giro Credit
    "BP":  "DEBIT",        # Bill Payment
    "CD":  "DEBIT",        # Card Payment
    "CHQ": "CHECK",        # Cheque
    "COR": "OTHER",        # Correction
    "CPT": "ATM",          # Cashpoint/ATM
    "CR":  "CREDIT",       # Credit
    "DD":  "DIRECTDEBIT",  # Direct Debit
    "DEB": "DEBIT",        # Debit
    "DEP": "DEP",          # Deposit
    "FEE": "SRVCHG",       # Fee
    "FPI": "CREDIT",       # Faster Payment In
    "FPO": "DEBIT",        # Faster Payment Out
    "PAY": "PAYMENT",      # Payment
    "SO":  "REPEATPMT",    # Standing Order
    "TFR": "XFER",         # Transfer
}

# Patterns for extracting payee from Lloyds description text.
# Each returns (payee, memo) where memo is the useful remainder.
# Order matters: more specific patterns must come first.

# FX fee: "NON-GBP TRANS FEE n.nn% CD nnnn [ddMMMYY]"
FX_FEE_RE = re.compile(
    r"^(NON-GBP TRANS FEE)\s+([\d.]+%\s+CD\s+\d{4}(?:\s+\d{2}[A-Z]{3}\d{2})?)\s*$"
)

# FX purchase: merchant then amount VISAXR rate CD nnnn [date]
# Anchors on VISAXR. Optional country/currency code before amount.
FX_PURCHASE_RE = re.compile(
    r"^(.+?)\s+(?:(?:[A-Z]{2,5})\s+)?"
    r"(\d[\d.]+\s+VISAXR\s+[\d.]+\s+CD\s+\d{4}"
    r"(?:\s+\d{2}[A-Z]{3}\d{2})?)\s*$"
)

# Card payment: "MERCHANT CD nnnn [ddMMMYY]"
CARD_PAYMENT_RE = re.compile(
    r"^(.+?)\s+(CD\s+\d{4}(?:\s+\d{2}[A-Z]{3}\d{2})?)\s*$"
)

# Faster payment (in/out): name then long numeric ref then ddMMMYY HH:MM
# Reference may have RP/FP prefix
FASTER_PAYMENT_RE = re.compile(
    r"^(.+?)\s+((?:RP|FP)?\d{9,}[\d\s/A-Z-]*\d{2}[A-Z]{3}\d{2}"
    r"\s+\d{2}:\d{2})\s*$"
)

# Service charge: "SERVICE CHARGES REF : number"
SERVICE_CHARGE_RE = re.compile(
    r"^(.+?)\s+(REF\s*:\s*\d+)\s*$"
)

# Direct debit / standing order: name then alphanumeric reference
DD_REF_RE = re.compile(
    r"^(.+?)\s+([\dA-Z][\dA-Z/-]{7,})\s*$"
)


def extract_payee(description: str, trtype: str) -> tuple[str, str]:
    """Extract a clean payee name from the Lloyds description.

    Returns (payee, memo) where payee is the cleaned name and
    memo is the useful remainder (reference numbers, FX details).
    When no pattern matches, memo is empty to avoid duplication.
    """
    desc = description.strip()

    # FX fee (before card payment - both have CD suffix)
    m = FX_FEE_RE.match(desc)
    if m:
        return ("Non-GBP Transaction Fee", m.group(2).strip())

    # FX purchase (before card payment - both have CD suffix)
    m = FX_PURCHASE_RE.match(desc)
    if m:
        return (m.group(1).strip(), m.group(2).strip())

    # Card payment
    m = CARD_PAYMENT_RE.match(desc)
    if m:
        return (m.group(1).strip(), m.group(2).strip())

    # Faster payment (in and out)
    if trtype in ("FPI", "FPO", "BGC"):
        m = FASTER_PAYMENT_RE.match(desc)
        if m:
            return (m.group(1).strip(), m.group(2).strip())

    # Service charge
    m = SERVICE_CHARGE_RE.match(desc)
    if m:
        return (m.group(1).strip(), m.group(2).strip())

    # Direct debit / standing order
    if trtype in ("DD", "SO"):
        m = DD_REF_RE.match(desc)
        if m:
            return (m.group(1).strip(), m.group(2).strip())

    # Fallback: full description as payee, empty memo
    return (desc, "")


def parse_amount(debit_str: str, credit_str: str) -> tuple[Decimal, Decimal, Decimal]:
    """Parse the separate debit/credit columns into amounts.

    Returns (amount, debit, credit) where amount is the signed
    transaction value (negative for debits).
    """
    debit = Decimal(debit_str) if debit_str else Decimal("0")
    credit = Decimal(credit_str) if credit_str else Decimal("0")
    amount = credit - debit
    return (amount, debit, credit)


def determine_trntype(trtype: str, debit: Decimal, credit: Decimal) -> str:
    """Map Lloyds transaction type code to OFX TRNTYPE.

    Falls back to generic DEBIT/CREDIT based on amount direction.
    """
    if trtype in TRNTYPE_MAP:
        return TRNTYPE_MAP[trtype]
    if credit:
        return "CREDIT"
    return "DEBIT"


def clean_sort_code(raw: str) -> str:
    """Strip the leading quote that Lloyds adds to prevent
    Excel formula interpretation.
    """
    return raw.lstrip("'").strip()


class LloydsPlugin(Plugin):
    """Lloyds UK bank CSV statement plugin"""

    def get_parser(self, filename: str) -> "LloydsParser":
        f = open(filename, "r")
        parser = LloydsParser(f)
        if "currency" not in self.settings:
            self.ui.warning("Currency is not set")
            self.ui.status("")
            self.ui.status("Edit your configuration and set the currency:")
            self.ui.status("$ ofxstatement edit-config")
            self.ui.status("[lloyds]")
            self.ui.status("plugin = lloyds")
            self.ui.status("currency = GBP")
        parser.statement.currency = self.settings.get("currency")
        return parser


class LloydsParser(CsvStatementParser):
    mappings = {"date": 0, "payee": 4, "memo": 4}
    date_format = "%d/%m/%Y"

    def __init__(self, fin: TextIO) -> None:
        super().__init__(fin)
        self.uids: set[str] = set()
        self.account_id: Optional[str] = None
        self.start_balance: Optional[Decimal] = None
        self.end_balance: Optional[Decimal] = None
        self.start_date = None
        self.end_date = None

    def parse(self) -> Statement:
        stmt = super().parse()
        stmt.start_date = self.start_date
        stmt.end_date = self.end_date
        if self.start_balance is not None:
            stmt.start_balance = self.start_balance
        if self.end_balance is not None:
            stmt.end_balance = self.end_balance
        if self.account_id is not None:
            stmt.account_id = self.account_id
        return stmt

    def parse_record(self, line: list[str]) -> Optional[StatementLine]:
        sline = super().parse_record(line)
        if sline is None:
            return None

        sline.id = generate_unique_transaction_id(sline, self.uids)

        # Set account_id once from first record
        if self.account_id is None:
            self.account_id = line[3].strip()

        # Parse amounts from separate debit/credit columns
        amount, debit, credit = parse_amount(line[5].strip(), line[6].strip())
        sline.amount = amount

        # Map transaction type
        trtype = line[1].strip()
        sline.trntype = determine_trntype(trtype, debit, credit)

        # Extract clean payee from description
        description = line[4].strip()
        payee, memo = extract_payee(description, trtype)
        sline.payee = payee
        # Prefix memo with Lloyds type code for reconciliation matching
        # via the Note field (e.g. "DD 701956574-33938726")
        sline.memo = f"{trtype} {memo}".strip() if memo else trtype

        # Track balance and dates.
        # Lloyds CSV is reverse chronological (newest first),
        # so first record has the end balance/date and last
        # record yields the start balance/date.
        balance_str = line[7].strip()
        balance = self.parse_decimal(balance_str)

        if self.end_balance is None:
            self.end_balance = balance
            self.end_date = sline.date

        # Overwritten each record; final value is the earliest
        self.start_balance = balance + debit - credit
        self.start_date = sline.date

        return sline

    def split_records(self) -> Iterable[list[str]]:
        reader = cast(Iterator[list[str]], super().split_records())
        next(reader)  # Skip CSV header row
        return reader
