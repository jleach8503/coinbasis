from coinbasis.models import Transaction
from coinbasis.price_provider import get_usd_price_at_time


INCOME_TYPES = {
    'STAKING_REWARD',
    'MULTI_TOKEN_TRADE',
    'INTEREST_PAYMENT',
}

def compute_income_cost_basis(tx: Transaction) -> Transaction:
    if tx.received_qty is None or tx.received_currency is None:
        return tx

    price = get_usd_price_at_time(tx.received_currency, tx.timestamp)
    usd_value = tx.received_qty * price

    tx.received_usd_cost_basis = usd_value
    tx.realized_return = usd_value

    return tx

def compute_cost_basis(transactions: list[Transaction]) -> list[Transaction]:
    for tx in transactions:
        if tx.type in INCOME_TYPES:
            compute_income_cost_basis(tx)

    return transactions