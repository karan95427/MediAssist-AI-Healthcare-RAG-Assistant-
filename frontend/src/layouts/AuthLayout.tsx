import { Outlet } from "react-router-dom";

function AuthLayout() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-10">
      <div className="absolute inset-0 bg-[linear-gradient(140deg,rgba(255,255,255,0.95),rgba(219,234,254,0.8))]" />
      <div className="relative z-10 w-full">
        <Outlet />
      </div>
    </div>
  );
}

export default AuthLayout;
