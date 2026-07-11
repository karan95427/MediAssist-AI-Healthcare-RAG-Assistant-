import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthFormShell from "../components/AuthFormShell";
import { useAuth } from "../hooks/useAuth";

function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [fullName, setFullName] = useState("Dr. Jane Smith");
  const [email, setEmail] = useState("doctor@mediassist.ai");
  const [password, setPassword] = useState("Password123");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await register({ full_name: fullName, email, password });
    navigate("/login");
  };

  return (
    <AuthFormShell title="Create account" subtitle="Provision a new healthcare workspace user.">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-700">Full name</span>
          <input
            type="text"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            className="w-full rounded-2xl border border-slate-200 px-4 py-3 outline-none focus:border-brand-500"
          />
        </label>

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
          Create account
        </button>
      </form>

      <p className="mt-6 text-sm text-slate-500">
        Already registered?{" "}
        <Link className="font-semibold text-brand-600" to="/login">
          Sign in
        </Link>
      </p>
    </AuthFormShell>
  );
}

export default RegisterPage;
