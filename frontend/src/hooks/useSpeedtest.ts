import { useQuery, useQueryClient } from "@tanstack/react-query";

import { speedtestApi } from "@/lib/speedtest";

export function useHistorialSpeedtest() {
  return useQuery({
    queryKey: ["speedtest", "historial"],
    queryFn: speedtestApi.historial,
  });
}

export function useInvalidateSpeedtest() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: ["speedtest"] });
}
