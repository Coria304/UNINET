import { useState } from "react";
import { isAxiosError } from "axios";

import { useLogin } from "@/hooks/useAuth";

function getErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    const status = error.response?.status;
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail;
    if (status === 423) return detail ?? "Cuenta bloqueada temporalmente.";
    if (status === 401) return detail ?? "Correo o contraseña incorrectos.";
    if (status === 403) return detail ?? "Cuenta inactiva. Contacta al administrador.";
    return detail ?? "No fue posible iniciar sesión. Intenta de nuevo.";
  }
  return "Error inesperado.";
}

function Login() {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const mutation = useLogin();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // trim para neutralizar whitespace que se cuela en pastes (chats, PDFs).
    mutation.mutate({ correo: correo.trim(), password: password.trim() });
  };

  return (
    <div className="min-h-screen grid place-items-center bg-slate-100 px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-white rounded-lg shadow p-6 space-y-4"
      >
        <h1 className="text-xl font-semibold text-center">UniNet Connect</h1>
        <p className="text-sm text-slate-500 text-center">
          Inicia sesión con tu cuenta institucional
        </p>

        <div>
          <label htmlFor="correo" className="block text-sm font-medium mb-1">
            Correo institucional
          </label>
          <input
            id="correo"
            type="email"
            className="input-base"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            placeholder="usuario@escom.ipn.mx"
            autoComplete="username"
            required
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-1">
            Contraseña
          </label>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              className="input-base pr-10"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              aria-pressed={showPassword}
              className="absolute inset-y-0 right-0 flex items-center px-2 text-slate-500 hover:text-slate-700 focus:outline-none focus:text-slate-700"
              tabIndex={-1}
            >
              {showPassword ? (
                // Eye-off
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
                  <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a21.83 21.83 0 0 1 5.06-5.94" />
                  <path d="M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 8 11 8a21.77 21.77 0 0 1-3.17 4.19" />
                  <path d="M14.12 14.12A3 3 0 1 1 9.88 9.88" />
                  <line x1="1" y1="1" x2="23" y2="23" />
                </svg>
              ) : (
                // Eye
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden="true">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {mutation.isError && (
          <p role="alert" className="text-sm text-red-600">
            {getErrorMessage(mutation.error)}
          </p>
        )}

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Validando…" : "Iniciar sesión"}
        </button>

        <p className="text-xs text-slate-400 text-center">
          Tras 5 intentos fallidos la cuenta se bloquea por 15 minutos.
        </p>
      </form>
    </div>
  );
}

export default Login;
