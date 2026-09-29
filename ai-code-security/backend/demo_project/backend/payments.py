"""Payment and settlement calculations."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_cents(amount: Decimal) -> int:
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_cents(cents: int) -> Decimal:
    return (Decimal(cents) / 100).quantize(CENT)


def split_equally(amount_cents: int, members: int) -> list[int]:
    if members <= 0:
        raise ValueError("members must be positive")
    base = amount_cents // members
    remainder = amount_cents % members
    shares = [base] * members
    for index in range(remainder):
        shares[index] += 1
    return shares


def balances(transactions: list[dict]) -> dict[int, int]:
    net: dict[int, int] = {}
    for entry in transactions:
        payer = entry["paid_by"]
        participants = entry["participants"]
        share = entry["amount_cents"] // max(len(participants), 1)
        net[payer] = net.get(payer, 0) + entry["amount_cents"]
        for participant in participants:
            net[participant] = net.get(participant, 0) - share
    return net


def settle(net: dict[int, int]) -> list[dict]:
    debtors = sorted(
        ((uid, -amount) for uid, amount in net.items() if amount < 0),
        key=lambda item: item[1],
        reverse=True,
    )
    creditors = [(uid, amount) for uid, amount in sorted(net.items()) if amount > 0]
    transfers: list[dict] = []
    while debtors and creditors:
        debtor_id, owed = debtors[0]
        creditor_id, due = creditors[0]
        amount = min(owed, due)
        transfers.append(
            {"from": debtor_id, "to": creditor_id, "amount_cents": amount}
        )
        debtors[0] = (debtor_id, owed - amount)
        creditors[0] = (creditor_id, due - amount)
        if debtors[0][1] == 0:
            debtors.pop(0)
        if creditors[0][1] == 0:
            creditors.pop(0)
    return transfers
