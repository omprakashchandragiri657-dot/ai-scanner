const CURRENCY_SYMBOLS = { USD: "$", EUR: "€", GBP: "£", INR: "₹", NGN: "₦" };

export function formatCurrency(amountCents, currency = "USD") {
  const symbol = CURRENCY_SYMBOLS[currency] || "$";
  const value = (amountCents / 100).toFixed(2);
  return `${symbol}${value}`;
}

export function formatDate(isoString) {
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function initials(name = "") {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join("");
}

export function sortByDateDesc(items, key = "created_at") {
  return [...items].sort((a, b) => (a[key] < b[key] ? 1 : -1));
}
