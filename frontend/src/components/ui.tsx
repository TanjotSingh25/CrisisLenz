import type { ButtonHTMLAttributes, ReactNode } from "react";
import { ChevronDown, Loader2 } from "lucide-react";

export function Card({
  title,
  icon,
  actions,
  children,
  className = "",
  collapsible = false,
  collapsed = false,
  onToggleCollapse,
}: {
  title?: ReactNode;
  icon?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  collapsible?: boolean;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}) {
  return (
    <section className={`rounded-xl border-2 border-ink-600 bg-ink-800 shadow-lg ${className}`}>
      {(title || actions) && (
        <header className={`flex items-center justify-between gap-2 px-4 py-3 ${collapsed ? "" : "border-b-2 border-ink-600"}`}>
          <button
            type="button"
            onClick={collapsible ? onToggleCollapse : undefined}
            className={`flex items-center gap-2 text-sm font-semibold tracking-wide text-slate-100 ${
              collapsible ? "cursor-pointer hover:text-cyan-300" : "cursor-default"
            }`}
          >
            {collapsible && (
              <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${collapsed ? "-rotate-90" : ""}`} />
            )}
            {icon}
            {title}
          </button>
          {actions}
        </header>
      )}
      {!collapsed && <div className="p-4">{children}</div>}
    </section>
  );
}

type Variant = "primary" | "ghost" | "subtle" | "danger";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-cyan-600 hover:bg-cyan-500 text-white disabled:bg-cyan-800/60 disabled:text-cyan-100/60",
  ghost: "bg-transparent hover:bg-ink-600 text-slate-200 ring-1 ring-inset ring-ink-500 disabled:opacity-60",
  subtle: "bg-ink-600 hover:bg-ink-500 text-slate-100 disabled:opacity-60",
  danger: "bg-red-600/90 hover:bg-red-500 text-white disabled:opacity-60",
};

export function Button({
  variant = "subtle",
  loading,
  icon,
  children,
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; loading?: boolean; icon?: ReactNode }) {
  return (
    <button
      {...props}
      disabled={props.disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}

export function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="space-y-0.5">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-cyan-400/80">{label}</div>
      <div className="text-sm text-slate-100">{value ?? <span className="text-slate-500">—</span>}</div>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border-2 border-dashed border-ink-600 px-4 py-6 text-center text-sm text-slate-400">{children}</div>;
}
