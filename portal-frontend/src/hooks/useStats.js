import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../services/api";

export function useStats() {
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState("");
  const request = useRef(0);
  const refreshStats = useCallback(async () => {
    const sequence = ++request.current;
    try {
      const result = await api("/api/stats");
      if (sequence === request.current) {
        setStats(result);
        setStatsError("");
      }
    } catch {
      if (sequence === request.current)
        setStatsError("No se puede actualizar el panel. Los datos pueden estar desactualizados.");
    }
  }, []);
  useEffect(() => {
    // Diferir también evita actualizaciones de estado dentro del propio efecto.
    const initial = setTimeout(refreshStats, 0);
    const interval = setInterval(refreshStats, 30000);
    return () => {
      clearTimeout(initial);
      clearInterval(interval);
    };
  }, [refreshStats]);
  return { stats, statsError, refreshStats };
}
