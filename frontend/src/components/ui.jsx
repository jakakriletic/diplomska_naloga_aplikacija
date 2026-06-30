// Skupne, ponovno uporabljene UI komponente.
import React from "react";
import { Loader2 } from "lucide-react";

export function Card({ className = "", children }) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function Button({
  children,
  onClick,
  disabled,
  variant = "primary",
  className = "",
  type = "button",
}) {
  const variants = {
    primary:
      "bg-gradient-to-r from-indigo-500 to-violet-500 text-white hover:from-indigo-600 hover:to-violet-600 shadow-sm",
    ghost: "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50",
    subtle: "bg-slate-100 text-slate-700 hover:bg-slate-200",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Badge({ children, color = "slate" }) {
  const colors = {
    slate: "bg-slate-100 text-slate-600",
    green: "bg-emerald-100 text-emerald-700",
    emerald: "bg-emerald-100 text-emerald-700",
    blue: "bg-blue-100 text-blue-700",
    amber: "bg-amber-100 text-amber-700",
    red: "bg-red-100 text-red-700",
    violet: "bg-violet-100 text-violet-700",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${colors[color]}`}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }) {
  const map = {
    completed: ["green", "Zaključeno"],
    running: ["blue", "V teku"],
    pending: ["amber", "Čaka"],
    failed: ["red", "Napaka"],
  };
  const [color, label] = map[status] || ["slate", status || "—"];
  return <Badge color={color}>{label}</Badge>;
}

export function Spinner({ className = "" }) {
  return <Loader2 className={`animate-spin ${className}`} />;
}

export function Empty({ icon: Icon, title, hint }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      {Icon && (
        <div className="rounded-2xl bg-slate-100 p-4 text-slate-400">
          <Icon className="h-7 w-7" />
        </div>
      )}
      <p className="font-semibold text-slate-600">{title}</p>
      {hint && <p className="max-w-md text-sm text-slate-400">{hint}</p>}
    </div>
  );
}

export function Field({ label, children }) {
  return (
    <div className="space-y-1">
      <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </label>
      <div className="text-sm text-slate-700">{children || "—"}</div>
    </div>
  );
}
