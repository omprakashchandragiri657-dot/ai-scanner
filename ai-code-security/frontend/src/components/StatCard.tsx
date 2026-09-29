export default function StatCard({
  label,
  value,
  hint,
  accent = "text-[#0F172A]",
}: {
  label: string;
  value: string | number;
  hint?: string;
  accent?: string;
}) {
  return (
    <div className="rounded-lg border border-[#E2E8F0] bg-white px-5 py-4">
      <p className="text-xs font-medium uppercase tracking-wider text-[#64748B]">
        {label}
      </p>
      <p className={`mt-1 text-[30px] font-bold leading-tight tabular-nums ${accent}`}>
        {value}
      </p>
      {hint && <p className="mt-0.5 text-xs text-[#94A3B8]">{hint}</p>}
    </div>
  );
}
