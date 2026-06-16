import { useState } from "react";

import { useAlertas, useAtenderAlerta } from "@/hooks/useMonitoreo";
import type { AlertaOut } from "@/lib/monitoreo";

const TIPO_LABEL: Record<string, string> = {
  saturacion_carga: "Saturación de carga",
  latencia_alta:    "Latencia alta",
  nodo_caido:       "Nodo caído",
};

const ESTADO_STYLE: Record<string, string> = {
  activa:      "bg-red-50 text-red-700",
  atendida:    "bg-emerald-50 text-emerald-700",
  cerrada_auto:"bg-[#F4F3F0] text-[#787774]",
  escalada:    "bg-amber-50 text-amber-700",
};

function fmtFecha(iso: string) {
  return new Date(iso).toLocaleString("es-MX", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function AlertaRow({
  alerta,
  onAtender,
}: {
  alerta: AlertaOut;
  onAtender: (id: string) => void;
}) {
  return (
    <tr className="border-b border-[#EAEAEA] hover:bg-[#F7F6F3]">
      <td className="px-4 py-3">
        <div className="font-medium text-sm">{alerta.ap_codigo}</div>
        <div className="text-xs text-[#787774]">{alerta.ap_nombre}</div>
      </td>
      <td className="px-4 py-3 text-sm text-[#787774]">
        {alerta.edificio_codigo ?? "—"}
      </td>
      <td className="px-4 py-3 text-sm">
        {TIPO_LABEL[alerta.tipo] ?? alerta.tipo}
      </td>
      <td className="px-4 py-3 tabular-nums text-sm">
        {alerta.valor_observado.toFixed(1)}{" "}
        <span className="text-[#AAAAAA]">/ {alerta.umbral_violado.toFixed(0)}</span>
      </td>
      <td className="px-4 py-3">
        <span className={`badge ${ESTADO_STYLE[alerta.estado] ?? ""}`}>
          {alerta.estado.replace("_", " ")}
        </span>
      </td>
      <td className="px-4 py-3 text-xs text-[#787774] whitespace-nowrap">
        {fmtFecha(alerta.detectada_at)}
      </td>
      <td className="px-4 py-3">
        {alerta.estado === "activa" && (
          <button
            type="button"
            onClick={() => onAtender(alerta.id)}
            className="text-xs underline text-[#111111] hover:no-underline"
          >
            Atender
          </button>
        )}
      </td>
    </tr>
  );
}

function Alertas() {
  const [soloActivas, setSoloActivas] = useState(true);
  const { data: alertas, isLoading, isError } = useAlertas(soloActivas);
  const atender = useAtenderAlerta();

  const activas = alertas?.filter((a) => a.estado === "activa").length ?? 0;

  return (
    <div className="space-y-5 max-w-6xl">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold">Alertas de saturación</h2>
          <p className="text-sm text-[#787774] mt-1">
            Notificaciones automáticas cuando un AP supera sus umbrales.
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-[#787774] select-none cursor-pointer">
          <input
            type="checkbox"
            checked={soloActivas}
            onChange={(e) => setSoloActivas(e.target.checked)}
            className="rounded border-[#EAEAEA] accent-[#111111]"
          />
          Solo activas
        </label>
      </header>

      {activas > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-800">
          {activas} alerta{activas > 1 ? "s" : ""} activa{activas > 1 ? "s" : ""} requieren atención.
        </div>
      )}

      {isLoading && <p className="text-[#787774] text-sm">Cargando…</p>}
      {isError && (
        <p className="text-red-600 text-sm">No se pudieron cargar las alertas.</p>
      )}

      {alertas && (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="text-left text-[#787774] border-b border-[#EAEAEA]">
              <tr>
                <th className="px-4 py-2 font-medium">Access Point</th>
                <th className="px-4 py-2 font-medium">Edificio</th>
                <th className="px-4 py-2 font-medium">Tipo</th>
                <th className="px-4 py-2 font-medium">Valor / Umbral</th>
                <th className="px-4 py-2 font-medium">Estado</th>
                <th className="px-4 py-2 font-medium">Detectada</th>
                <th className="px-4 py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {alertas.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-8 text-center text-[#787774]"
                  >
                    {soloActivas
                      ? "No hay alertas activas."
                      : "No hay alertas registradas."}
                  </td>
                </tr>
              ) : (
                alertas.map((a) => (
                  <AlertaRow
                    key={a.id}
                    alerta={a}
                    onAtender={(id) => atender.mutate({ id })}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Alertas;
