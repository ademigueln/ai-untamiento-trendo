const API_BASE = import.meta.env.VITE_API_BASE || "";

export async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 180000);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: options.signal || controller.signal,
    });
    const data = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) {
      const error = new Error(
        data?.reply ||
          (typeof data?.detail === "string"
            ? data.detail
            : "No se ha podido completar la solicitud."),
      );
      error.status = response.status;
      error.data = data;
      throw error;
    }
    return data;
  } finally {
    clearTimeout(timeout);
  }
}
