import type { Severity } from "../types";

const STYLES: Record<Severity, string> = {
  CRITICAL: "bg-[#FEF2F2] text-[#B91C1C] ring-[#FECACA]",
  HIGH: "bg-[#FFF7ED] text-[#C2410C] ring-[#FED7AA]",
  MEDIUM: "bg-[#FEFCE8] text-[#A16207] ring-[#FEF08A]",
  LOW: "bg-[#F0FDF4] text-[#15803D] ring-[#BBF7D0]",
};

const DOT: Record<Severity, string> = {
  CRITICAL: "bg-[#DC2626]",
  HIGH: "bg-[#EA580C]",
  MEDIUM: "bg-[#CA8A04]",
  LOW: "bg-[#16A34A]",
};

export default function SeverityBadge({
  severity,
  compact = false,
}: {
  severity: Severity;
  compact?: boolean;
}) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-md ring-1 font-medium",
        STYLES[severity],
        compact ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-[11px]",
      ].join(" ")}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${DOT[severity]}`} />
      {severity}
    </span>
  );
}

export const SEVERITY_COLOR: Record<Severity, string> = {
  CRITICAL: "#DC2626",
  HIGH: "#EA580C",
  MEDIUM: "#CA8A04",
  LOW: "#16A34A",
};

