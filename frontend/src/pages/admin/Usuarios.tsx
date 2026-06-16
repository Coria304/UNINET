import { isAxiosError } from "axios";
import { useState } from "react";

import { useCrearUsuario, useUsuarios } from "@/hooks/useAdmin";
import type { UsuarioCreate } from "@/lib/types";

type FiltroRol = "todos" | "personal_tecnico" | "estudiante" | "docente";

const ROL_LABEL: Record<string, string> = {
  personal_tecnico: "Técnico",
  estudiante: "Estudiante",
  docente: "Docente",
};

const ROL_BADGE: Record<string, string> = {
  personal_tecnico: "bg-[#DBEAFE] text-[#1A4B8A]",
  estudiante: "bg-[#EDE9FE] text-[#5B21B6]",
  docente: "bg-[#D1FAE5] text-[#065F46]",
};

const FILTROS: { value: FiltroRol; label: string }[] = [
  { value: "todos", label: "Todos" },
  { value: "personal_tecnico", label: "Técnicos" },
  { value: "estudiante", label: "Estudiantes" },
  { value: "docente", label: "Docentes" },
];

const EMPTY_FORM: UsuarioCreate = {
  correo: "",
  nombre_completo: "",
  password: "",
  rol: "estudiante",
};

function getApiError(error: unknown): string {
  if (isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail;
    return detail ?? "Error al crear el usuario.";
  }
  return "Error inesperado.";
}

export default function Usuarios() {
  const { data: usuarios, isLoading } = useUsuarios();
  const crearMutation = useCrearUsuario();
  const [showForm, setShowForm] = useState(false);
  const [filtro, setFiltro] = useState<FiltroRol>("todos");
  const [form, setForm] = useState<UsuarioCreate>(EMPTY_FORM);
  const [showPassword, setShowPassword] = useState(false);

  const dominioEsperado =
    form.rol === "estudiante" ? "@alumno.ipn.mx" :
    form.rol === "docente"    ? "@docente.ipn.mx" : null;

  const correoError =
    dominioEsperado && form.correo.length > 0 &&
    !form.correo.toLowerCase().endsWith(dominioEsperado)
      ? `Debe usar correo ${dominioEsperado}`
      : "";

  const filtrados =
    filtro === "todos" ? usuarios : usuarios?.filter((u) => u.rol === filtro);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (correoError) return;
    crearMutation.mutate(form, {
      onSuccess: () => {
        setForm(EMPTY_FORM);
        setShowForm(false);
      },
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#111111]">Gestión de usuarios</h1>
          <p className="text-sm text-[#787774] mt-0.5">
            Alta de técnicos y alumnos en el sistema.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm((v) => !v)}
          className="btn-primary"
        >
          {showForm ? "Cancelar" : "+ Nuevo usuario"}
        </button>
      </div>

      {/* Formulario de alta */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-white border border-[#E2E8F0] rounded-xl p-6 space-y-4"
        >
          <h2 className="text-sm font-semibold text-[#111111]">Nuevo usuario</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-[#111111]">
                Nombre completo
              </label>
              <input
                type="text"
                className="input-base"
                value={form.nombre_completo}
                onChange={(e) => setForm((f) => ({ ...f, nombre_completo: e.target.value }))}
                placeholder="Ej. Juan Pérez López"
                required
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-[#111111]">Rol</label>
              <select
                className="input-base"
                value={form.rol}
                onChange={(e) =>
                  setForm((f) => ({ ...f, rol: e.target.value as UsuarioCreate["rol"] }))
                }
              >
                <option value="estudiante">Estudiante</option>
                <option value="docente">Docente</option>
                <option value="personal_tecnico">Técnico</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-[#111111]">
                Correo electrónico
                {dominioEsperado && (
                  <span className="text-[#94A3B8] font-normal ml-1">({dominioEsperado})</span>
                )}
              </label>
              <input
                type="email"
                className={`input-base ${correoError ? "border-red-400 focus:border-red-500 focus:ring-red-500" : ""}`}
                value={form.correo}
                onChange={(e) => setForm((f) => ({ ...f, correo: e.target.value }))}
                placeholder={
                  form.rol === "estudiante" ? `alumno${dominioEsperado}` :
                  form.rol === "docente"    ? `profesor${dominioEsperado}` :
                  "correo@ejemplo.com"
                }
                required
              />
              {correoError && (
                <p className="text-xs text-red-600">{correoError}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-[#111111]">
                Contraseña inicial
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  className="input-base pr-10"
                  value={form.password}
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  placeholder="Mínimo 8 caracteres"
                  minLength={8}
                  required
                />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 flex items-center px-3 text-[#AAAAAA] hover:text-[#111111] transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
                    {showPassword ? (
                      <>
                        <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a21.83 21.83 0 0 1 5.06-5.94" />
                        <path d="M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 8 11 8a21.77 21.77 0 0 1-3.17 4.19" />
                        <path d="M14.12 14.12A3 3 0 1 1 9.88 9.88" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </>
                    ) : (
                      <>
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
                        <circle cx="12" cy="12" r="3" />
                      </>
                    )}
                  </svg>
                </button>
              </div>
            </div>
          </div>

          {crearMutation.isError && (
            <p className="text-sm text-red-600">{getApiError(crearMutation.error)}</p>
          )}

          <div className="flex justify-end gap-3 pt-1">
            <button
              type="button"
              onClick={() => { setShowForm(false); setForm(EMPTY_FORM); }}
              className="btn-secondary"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={crearMutation.isPending || !!correoError}
            >
              {crearMutation.isPending ? "Creando…" : "Crear usuario"}
            </button>
          </div>
        </form>
      )}

      {/* Tabla de usuarios */}
      <div className="bg-white border border-[#E2E8F0] rounded-xl overflow-hidden">
        {/* Filtros */}
        <div className="flex gap-1 px-4 pt-4 border-b border-[#E2E8F0] pb-0">
          {FILTROS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setFiltro(f.value)}
              className={[
                "px-3 py-1.5 text-sm rounded-t transition-colors -mb-px border-b-2",
                filtro === f.value
                  ? "text-[#1A4B8A] font-medium border-[#1A4B8A]"
                  : "text-[#64748B] border-transparent hover:text-[#111111]",
              ].join(" ")}
            >
              {f.label}
              {f.value !== "todos" && (
                <span className="ml-1.5 text-xs text-[#94A3B8]">
                  {usuarios?.filter((u) => u.rol === f.value).length ?? 0}
                </span>
              )}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm text-[#94A3B8]">Cargando…</div>
        ) : !filtrados?.length ? (
          <div className="p-10 text-center text-sm text-[#94A3B8]">
            No hay usuarios registrados en esta categoría.
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#F1F5F9]">
                <th className="text-left px-5 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wide">
                  Nombre
                </th>
                <th className="text-left px-5 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wide">
                  Correo
                </th>
                <th className="text-left px-5 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wide">
                  Rol
                </th>
                <th className="text-left px-5 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wide">
                  Estado
                </th>
                <th className="text-left px-5 py-3 text-xs font-medium text-[#94A3B8] uppercase tracking-wide">
                  Último acceso
                </th>
              </tr>
            </thead>
            <tbody>
              {filtrados.map((u) => (
                <tr key={u.id} className="border-b border-[#F8FAFC] hover:bg-[#F8FAFC] transition-colors">
                  <td className="px-5 py-3.5 font-medium text-[#111111]">
                    {u.nombre_completo}
                  </td>
                  <td className="px-5 py-3.5 text-[#64748B]">{u.correo}</td>
                  <td className="px-5 py-3.5">
                    <span className={`badge ${ROL_BADGE[u.rol] ?? "bg-[#F1F5F9] text-[#64748B]"}`}>
                      {ROL_LABEL[u.rol] ?? u.rol}
                    </span>
                  </td>
                  <td className="px-5 py-3.5">
                    <span
                      className={`badge ${
                        u.activo !== false
                          ? "bg-[#D1FAE5] text-[#065F46]"
                          : "bg-[#FEE2E2] text-[#991B1B]"
                      }`}
                    >
                      {u.activo !== false ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td className="px-5 py-3.5 text-[#94A3B8]">
                    {u.last_login_at
                      ? new Date(u.last_login_at).toLocaleDateString("es-MX", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric",
                        })
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
