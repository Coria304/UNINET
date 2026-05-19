import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";

/**
 * Placeholder de Sprint 0. La integración real contra el endpoint
 * `/auth/login` se implementa en Sprint 1 (RF009, CU-10).
 */
function Login() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [correo, setCorreo] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!correo.endsWith("@escom.ipn.mx")) {
      setError("Use su correo institucional @escom.ipn.mx");
      return;
    }
    // STUB: en Sprint 1 sustituir por `api.post('/auth/login', ...)`.
    login("dev-token", {
      id: "00000000-0000-0000-0000-000000000000",
      correo,
      nombre_completo: "Usuario Demo",
      rol: correo.startsWith("admin") ? "administrador_ti" : "estudiante",
    });
    navigate("/");
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
          <label className="block text-sm font-medium mb-1">
            Correo institucional
          </label>
          <input
            type="email"
            className="input-base"
            value={correo}
            onChange={(e) => setCorreo(e.target.value)}
            placeholder="usuario@escom.ipn.mx"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Contraseña</label>
          <input type="password" className="input-base" required />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" className="btn-primary w-full">
          Iniciar sesión
        </button>
        <p className="text-xs text-slate-400 text-center">
          Sprint 0 — autenticación real se conecta en Sprint 1.
        </p>
      </form>
    </div>
  );
}

export default Login;
