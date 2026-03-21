import type { ReactNode } from "react";

export function Field({ label, children, className = "" }: { label: string; children: ReactNode; className?: string }) {
  return (
    <div className={`form-field ${className}`}>
      <span className="field-label">{label}</span>
      <div className="field-control">
        {children}
      </div>
    </div>
  );
}
