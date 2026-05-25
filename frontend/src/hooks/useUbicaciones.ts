import { useQuery } from "@tanstack/react-query";

import { ubicacionesApi } from "@/lib/ubicaciones";

/** Cache 5 min: el árbol del campus cambia muy rara vez. */
export function useEdificios() {
  return useQuery({
    queryKey: ["ubicaciones", "edificios"],
    queryFn: ubicacionesApi.listEdificios,
    staleTime: 5 * 60_000,
  });
}
