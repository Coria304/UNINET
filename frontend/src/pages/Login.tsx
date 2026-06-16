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
    mutation.mutate({ correo: correo.trim(), password: password.trim() });
  };

  return (
    <div className="min-h-screen flex bg-[#F5F8FF]">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-brand-900 flex-col justify-between p-12">
        <div>
          <img src="/logo-text.png" alt="UniNet Connect" className="w-full max-h-20 object-contain object-left brightness-0 invert" />
        </div>

        <div>
          <h1 className="text-4xl font-semibold text-white leading-tight">
            Monitoreo WiFi
            <br />
            del Campus ESCOM
          </h1>
        </div>

        <div className="flex gap-6 text-xs text-white/30">
          <span>ESCOM — IPN</span>
          <span>Sprint 3</span>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="lg:hidden flex flex-col items-center mb-10 gap-2">
            <img src="/logo-icon.png" alt="" className="h-10 w-auto" />
            <img src="/logo-text.png" alt="UniNet Connect" className="h-5 w-auto" />
            <p className="text-xs text-[#AAAAAA] mt-0.5">ESCOM — Campus WiFi</p>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-[#111111]">Iniciar sesión</h2>
            <p className="text-sm text-[#787774] mt-1">Usa tu cuenta institucional ESCOM.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label htmlFor="correo" className="block text-sm font-medium text-[#111111]">
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

            <div className="space-y-1.5">
              <label htmlFor="password" className="block text-sm font-medium text-[#111111]">
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
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-[#AAAAAA] hover:text-[#111111] transition-colors duration-150 focus:outline-none"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
                      <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a21.83 21.83 0 0 1 5.06-5.94" />
                      <path d="M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 8 11 8a21.77 21.77 0 0 1-3.17 4.19" />
                      <path d="M14.12 14.12A3 3 0 1 1 9.88 9.88" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {mutation.isError && (
              <div role="alert" className="flex items-start gap-2 rounded-lg bg-red-50 border border-red-100 px-3 py-2.5 text-sm text-red-700">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 shrink-0 mt-0.5">
                  <path fillRule="evenodd" d="M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Zm-8-5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-1.5 0v-4.5A.75.75 0 0 1 10 5Zm0 10a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
                </svg>
                {getErrorMessage(mutation.error)}
              </div>
            )}

            <button
              type="submit"
              className="btn-primary w-full py-2.5"
              disabled={mutation.isPending}
            >
              {mutation.isPending ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Validando…
                </span>
              ) : "Iniciar sesión"}
            </button>
          </form>

          <p className="text-xs text-[#AAAAAA] text-center mt-6">
            Tras 5 intentos fallidos la cuenta se bloquea 15 min.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
