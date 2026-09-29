export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export interface User {
  id: number;
  email: string;
  name: string;
}

export interface Expense {
  id: number;
  group_id: number;
  paid_by: number;
  amount_cents: number;
  description: string;
  created_at: string;
}

export interface Group {
  id: number;
  name: string;
  owner_id: number;
  members: number[];
}

export interface ApiError {
  error: string;
}

export interface Settlement {
  from: number;
  to: number;
  amount_cents: number;
}

export function isExpense(value: unknown): value is Expense {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<Expense>;
  return (
    typeof candidate.id === "number" &&
    typeof candidate.amount_cents === "number" &&
    typeof candidate.description === "string"
  );
}
