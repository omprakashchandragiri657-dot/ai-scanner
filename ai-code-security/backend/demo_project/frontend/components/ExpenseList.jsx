import { formatCurrency } from "../utils";

export default function ExpenseList({ expenses, onSelect }) {
  if (!expenses || expenses.length === 0) {
    return <p className="empty">No expenses yet.</p>;
  }

  return (
    <table className="expense-table">
      <thead>
        <tr>
          <th>Description</th>
          <th>Paid by</th>
          <th>Amount</th>
        </tr>
      </thead>
      <tbody>
        {expenses.map((expense) => (
          <tr key={expense.id} onClick={() => onSelect(expense)}>
            <td>{expense.description}</td>
            <td>{expense.paid_by}</td>
            <td>{formatCurrency(expense.amount_cents)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
