import { useEffect, useState } from "react";
import { isAxiosError } from "axios";
import { Navigate } from "react-router-dom";

import { useVerifyMfa } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";

function getErrorMessage(error: unknown): string {
  if (isAxiosError(error)) {
    return (
      (error.response?.data as { detail?: string } | undefined)?.detail ??
      "Código inválido o expirado. Inicia sesión de nuevo."
    );
  }
  return "Error inesperado.";
}

function VerifyMFA() {
  const pending = useAuthStore((s) => s.pendingMfa);
  const token = useAuthStore((s) => s.token);
  const usuario = useAuthStore((s) => s.usuario);
  const [code, setCode] = useState("");
  const mutation = useVerifyMfa();
  const [secondsLeft, setSecondsLeft] = useState(0);

  useEffect(() => {
    if (!pending) return;
    const tick = () => {
      setSecondsLeft(Math.max(0, Math.floor((pending.expiresAt - Date.now()) / 1000)));
    };
    tick();
    const id = setInterval(tick, 1_000);
    return () => clearInterval(id);
  }, [pending]);

  if (!pending) {
    // Tras un verify exitoso, login() limpia pendingMfa y este componente se
    // re-renderiza antes de que navigate("/") imperativo del onSuccess tome
    // efecto. Si ya hay sesión, mandar al home (RoleRedirect) — no al login.
    if (token && usuario) return <Navigate to="/" replace />;
    return <Navigate to="/login" replace />;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate({ challenge_id: pending.challengeId, code });
  };

  return (
    <div className="min-h-screen grid place-items-center bg-slate-100 px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-white rounded-lg shadow p-6 space-y-4"
      >
        <h1 className="text-xl font-semibold text-center">Verificación adicional</h1>
        <p className="text-sm text-slate-500 text-center">
          Enviamos un código de 6 dígitos a <strong>{pending.correo}</strong>.
        </p>

        {pending.devCode && (
          <p className="text-xs bg-amber-50 border border-amber-200 rounded p-2 text-center">
            <strong>Modo desarrollo:</strong> código demo{" "}
            <code className="font-mono">{pending.devCode}</code>
          </p>
        )}

        <div>
          <label htmlFor="code" className="block text-sm font-medium mb-1">
            Código MFA
          </label>
          <input
            id="code"
            type="text"
            inputMode="numeric"
            pattern="\d{6}"
            maxLength={6}
            className="input-base text-center tracking-widest text-lg"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            required
          />
        </div>

        <div className="text-xs text-slate-500 text-center">
          {secondsLeft > 0
            ? `Expira en ${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, "0")}`
            : "Código expirado — vuelve a iniciar sesión"}
        </div>

        {mutation.isError && (
          <p role="alert" className="text-sm text-red-600">
            {getErrorMessage(mutation.error)}
          </p>
        )}

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={mutation.isPending || code.length !== 6 || secondsLeft === 0}
        >
          {mutation.isPending ? "Verificando…" : "Verificar"}
        </button>
      </form>
    </div>
  );
}

export default VerifyMFA;
