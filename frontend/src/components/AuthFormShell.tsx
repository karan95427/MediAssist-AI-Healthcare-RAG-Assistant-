import type { ReactNode } from "react";

type AuthFormShellProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
};

function AuthFormShell({ title, subtitle, children }: AuthFormShellProps) {
  return (
    <div className="w-full max-w-md rounded-[2rem] bg-white p-8 shadow-panel">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-600">MediAssist AI</p>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900">{title}</h1>
      <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
      <div className="mt-8">{children}</div>
    </div>
  );
}

export default AuthFormShell;
