from dataclasses import dataclass

@dataclass
class Transaction:
    timestamp: str
    type: str
    transaction_id: str

    received_qty: float | None
    received_currency: str | None
    received_usd_cost_basis: float | None
    received_wallet: str | None
    received_address: str | None
    received_comment: str | None

    sent_qty: float | None
    sent_currency: str | None
    sent_usd_cost_basis: float | None
    sent_wallet: str | None
    sent_address: str | None
    sent_comment: str | None

    fee_qty: float | None
    fee_currency: str | None
    fee_usd_cost_basis: float | None

    realized_return: float | None
    fee_realized_return: float | None
    transaction_hash: str | None


COLUMN_MAP = {
    'Date': 'timestamp',
    'Type': 'type',
    'Transaction ID': 'transaction_id',
    'Received Quantity': 'received_qty',
    'Received Currency': 'received_currency',
    'Received Cost Basis (USD)': 'received_usd_cost_basis',
    'Received Wallet': 'received_wallet',
    'Received Address': 'received_address',
    'Received Comment': 'received_comment',
    'Sent Quantity': 'sent_qty',
    'Sent Currency': 'sent_currency',
    'Sent Cost Basis (USD)': 'sent_usd_cost_basis',
    'Sent Wallet': 'sent_wallet',
    'Sent Address': 'sent_address',
    'Sent Comment': 'sent_comment',
    'Fee Amount': 'fee_qty',
    'Fee Currency': 'fee_currency',
    'Fee Cost Basis (USD)': 'fee_usd_cost_basis',
    'Realized Return (USD)': 'realized_return',
    'Fee Realized Return (USD)': 'fee_realized_return',
    'Transaction Hash': 'transaction_hash',
}