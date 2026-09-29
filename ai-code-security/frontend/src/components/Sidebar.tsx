import { NavLink } from "react-router-dom";
import { useScan } from "../context/ScanContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "▤" },
  { to: "/scanner", label: "Project Scanner", icon: "⌕" },
  { to: "/findings", label: "Findings", icon: "⚠" },
  { to: "/research", label: "Research", icon: "◈" },
  { to: "/about", label: "About", icon: "ⓘ" },
];

export default function Sidebar() {
  const { result } = useScan();
  const openFindings = result?.summary.total ?? 0;

  return (
    <aside className="w-60 shrink-0 border-r border-[#E2E8F0] bg-white flex flex-col">
      <div className="px-5 py-6 border-b border-[#E2E8F0]">
        <div className="flex items-center gap-2.5">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-[#2563EB] text-sm font-bold text-white">
            AS
          </span>
          <div>
            <p className="text-[13px] font-bold tracking-wide text-[#0F172A]">
              AI CODE SECURITY
            </p>
            <p className="text-[11px] text-[#64748B]">Research Platform</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              [
                "flex items-center gap-3 border-l-2 px-3 py-2 text-[13px] font-medium transition-colors duration-150",
                isActive
                  ? "border-[#2563EB] bg-[#EFF6FF] text-[#1D4ED8]"
                  : "border-transparent text-[#475569] hover:bg-[#F8FAFC] hover:text-[#0F172A]",
              ].join(" ")
            }
          >
            <span className="w-4 text-center opacity-60">{item.icon}</span>
            <span className="flex-1">{item.label}</span>
            {item.to === "/findings" && openFindings > 0 && (
              <span className="rounded-md bg-[#FEF2F2] px-1.5 py-0.5 text-[11px] font-semibold text-[#B91C1C]">
                {openFindings}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-[#E2E8F0] px-5 py-4 text-[11px] leading-relaxed text-[#94A3B8]">
        Research build · v0.1.0
        <br />
        Static analysis only — uploaded code is never executed.
      </div>
    </aside>
  );
}
