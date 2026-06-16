import { isAxiosError } from "axios";
import { useEffect, useState } from "react";

import { useCambiarPassword } from "@/hooks/useAuth";

interface Props {
  onClose: () => void;
}

export default function CambiarPasswordModal({ onClose }: Props) {
  const mutation = useCambiarPassword();
  const [form, setForm] = useState({
    password_actual: "",
    password_nueva: "",
    confirmar: "",
  });
  const [showFields, setShowFields] = useState({
    actual: false,
    nueva: false,
    confirmar: false,
  });

  const confirmarError =
    form.confirmar.length > 0 && form.password_nueva !== form.confirmar
      ? "Las contraseñas no coinciden"
      : "";

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (confirmarError) return;
    mutation.mutate(
      { password_actual: form.password_actual, password_nueva: form.password_nueva },
    );
  }

  // Cerrar con Esc
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  function getError() {
    if (isAxiosError(mutation.error)) {
      return (
        (mutation.error.response?.data as { detail?: string } | undefined)?.detail ??
        "Error al cambiar la contraseña."
      );
    }
    return "Error inesperado.";
  }

  function EyeButton({
    field,
  }: {
    field: keyof typeof showFields;
  }) {
    return (
      <button
        type="button"
        tabIndex={-1}
        onClick={() => setShowFields((s) => ({ ...s, [field]: !s[field] }))}
        className="absolute inset-y-0 right-0 flex items-center px-3 text-[#AAAAAA] hover:text-[#111111] transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
          {showFields[field] ? (
            <>
              <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a21.83 21.83 0 0 1 5.06-5.94" />
              <path d="M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 8 11 8a21.77 21.77 0 0 1-3.17 4.19" />
              <path d="M14.12 14.12A3 3 0 1 1 9.88 9.88" /><line x1="1" y1="1" x2="23" y2="23" />
            </>
          ) : (
            <>
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
              <circle cx="12" cy="12" r="3" />
            </>
          )}
        </svg>
      </button>
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        {mutation.isSuccess ? (
          <div className="text-center py-4 space-y-3">
            <div className="w-12 h-12 rounded-full bg-[#D1FAE5] flex items-center justify-center mx-auto">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="#065F46" className="w-6 h-6">
                <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z" clipRule="evenodd" />
              </svg>
            </div>
            <p className="font-medium text-[#111111]">Contraseña actualizada</p>
            <p className="text-sm text-[#787774]">Tu nueva contraseña ya está activa.</p>
            <button type="button" onClick={onClose} className="btn-primary w-full mt-2">
              Cerrar
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-base font-semibold text-[#111111]">Cambiar contraseña</h2>
              <button
                type="button"
                onClick={onClose}
                className="text-[#94A3B8] hover:text-[#111111] transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                  <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-[#111111]">
                  Contraseña actual
                </label>
                <div className="relative">
                  <input
                    type={showFields.actual ? "text" : "password"}
                    className="input-base pr-10"
                    value={form.password_actual}
                    onChange={(e) => setForm((f) => ({ ...f, password_actual: e.target.value }))}
                    required
                    autoFocus
                  />
                  <EyeButton field="actual" />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-[#111111]">
                  Nueva contraseña
                  <span className="text-[#94A3B8] font-normal ml-1">(mín. 8 caracteres)</span>
                </label>
                <div className="relative">
                  <input
                    type={showFields.nueva ? "text" : "password"}
                    className="input-base pr-10"
                    value={form.password_nueva}
                    onChange={(e) => setForm((f) => ({ ...f, password_nueva: e.target.value }))}
                    minLength={8}
                    required
                  />
                  <EyeButton field="nueva" />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-[#111111]">
                  Confirmar nueva contraseña
                </label>
                <div className="relative">
                  <input
                    type={showFields.confirmar ? "text" : "password"}
                    className={`input-base pr-10 ${confirmarError ? "border-red-400" : ""}`}
                    value={form.confirmar}
                    onChange={(e) => setForm((f) => ({ ...f, confirmar: e.target.value }))}
                    required
                  />
                  <EyeButton field="confirmar" />
                </div>
                {confirmarError && (
                  <p className="text-xs text-red-600">{confirmarError}</p>
                )}
              </div>

              {mutation.isError && (
                <p className="text-sm text-red-600">{getError()}</p>
              )}

              <button
                type="submit"
                className="btn-primary w-full"
                disabled={mutation.isPending || !!confirmarError}
              >
                {mutation.isPending ? "Guardando…" : "Guardar contraseña"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
