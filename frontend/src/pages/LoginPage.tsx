import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthFormShell from "../components/AuthFormShell";
import { useAuth } from "../hooks/useAuth";

function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("doctor@mediassist.ai");
  const [password, setPassword] = useState("Password123");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await login({ email, password });
    navigate("/dashboard");
  };

  return (
    <AuthFormShell title="Sign in" subtitle="Access the clinical knowledge workspace.">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Email</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-brand-500"
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-brand-500"
          />
        </label>

        <button type="submit" className="w-full rounded-2xl bg-brand-600 px-4 py-3 font-semibold text-white">
          Sign in
        </button>
      </form>

      <p className="mt-6 text-sm text-slate-500">
        No account?{" "}
        <Link className="font-semibold text-brand-600" to="/register">
          Create one
        </Link>
      </p>
    </AuthFormShell>
  );
}

export default LoginPage;
