import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminApi } from "@/lib/admin";
import type { UsuarioCreate } from "@/lib/types";

export function useTecnicos() {
  return useQuery({
    queryKey: ["admin", "tecnicos"],
    queryFn: () => adminApi.tecnicos(),
    staleTime: 5 * 60_000,
  });
}

export function useUsuarios() {
  return useQuery({
    queryKey: ["admin", "usuarios"],
    queryFn: () => adminApi.listarUsuarios(),
    staleTime: 2 * 60_000,
  });
}

export function useCrearUsuario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UsuarioCreate) => adminApi.crearUsuario(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "usuarios"] });
      qc.invalidateQueries({ queryKey: ["admin", "tecnicos"] });
    },
  });
}
