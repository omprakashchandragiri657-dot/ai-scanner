"""Domain models for FairShare."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class User:
    id: int
    email: str
    name: str
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "name": self.name}


@dataclass
class Expense:
    id: int
    group_id: int
    paid_by: int
    amount_cents: int
    description: str
    created_at: str = field(default_factory=utcnow)

    def split(self, members: int) -> int:
        if members <= 0:
            raise ValueError("members must be positive")
        return self.amount_cents // members


@dataclass
class Group:
    id: int
    name: str
    owner_id: int
    members: list[int] = field(default_factory=list)

    def add_member(self, user_id: int) -> None:
        if user_id not in self.members:
            self.members.append(user_id)
