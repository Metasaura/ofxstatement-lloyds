ofxstatement-lloyds
===================

Plugin for `ofxstatement <https://github.com/kedder/ofxstatement>`_ to convert
CSV statements exported from Lloyds Bank (UK) into OFX format for import into
accounting software such as Odoo, GnuCash, and others.

Features
--------

Payee extraction
    Parses Lloyds transaction descriptions to produce a clean payee name in the
    OFX ``<NAME>`` field. Downstream importers use this as the primary
    transaction label for display and auto-reconciliation.

Transaction type preservation
    Prefixes the OFX ``<MEMO>`` field with the original Lloyds transaction type
    code (DD, FPI, FPO, DEB, BGC etc.), preserving detail that is lost in the
    standard OFX TRNTYPE mapping.

Structured memo
    Splits the description into payee and remainder, so importers that display
    ``NAME : MEMO`` show useful detail rather than duplication.

Balance tracking
    Calculates opening and closing balances from the reverse-chronological CSV,
    included in the OFX output for statement validation.

Supported transaction patterns
------------------------------

Card purchases
    ``MERCHANT CD nnnn [ddMMMYY]`` extracts the merchant name.

FX purchases
    ``MERCHANT [ref] [CURRENCY] amount VISAXR rate CD nnnn`` extracts the
    merchant, with FX details in the memo.

FX fees
    ``NON-GBP TRANS FEE n.nn% CD nnnn`` normalised to
    ``Non-GBP Transaction Fee``.

Faster payments (FPI/FPO/BGC)
    ``PAYEE reference sortcode ddMMMYY HH:MM`` extracts the payer or payee
    name.

Direct debits and standing orders (DD/SO)
    ``PAYEE mandate-reference`` extracts the payee name.

Service charges (PAY)
    ``SERVICE CHARGES REF : number`` extracts the charge description.

Unrecognised formats fall back to the full description as payee with the
transaction type code as memo.

Installation
------------

.. code-block:: bash

    pip install ofxstatement-lloyds

Or with pipx:

.. code-block:: bash

    pipx inject ofxstatement ofxstatement-lloyds

Configuration
-------------

Edit the ofxstatement configuration:

.. code-block:: bash

    ofxstatement edit-config

Add a section for your Lloyds account:

.. code-block:: ini

    [lloyds]
    plugin = lloyds
    currency = GBP

Usage
-----

Export a CSV statement from Lloyds online banking, then convert:

.. code-block:: bash

    ofxstatement convert -t lloyds statement.csv statement.ofx

The CSV is expected in the format provided by Lloyds online banking with
columns: date, type, sort code, account number, description, debit, credit,
balance.

Odoo reconciliation
-------------------

The payee and memo split is designed to work with Odoo's reconciliation models
and the OCA ``account_statement_completion_label_simple`` module.

The ``Label`` field in Odoo matches against the OFX ``<NAME>`` (clean payee).
The ``Note`` field matches against ``<MEMO>`` (prefixed with the Lloyds
transaction type code).

Example reconciliation model rules:

=================  ==============  =========================================
Label Contains     Note Contains   Action
=================  ==============  =========================================
``Non-GBP``                        Counterpart: bank charges expense account
``DIRECT LINE``    ``DD``          Partner: Direct Line Insurance
\                  ``FPI``         Filter: incoming faster payments only
``HMRC``           ``FPO``         Partner: HMRC
=================  ==============  =========================================
