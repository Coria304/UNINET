import { Navigate, useLocation } from "react-router-dom";

import type { Rol } from "@/lib/types";
import { useAuthStore } from "@/stores/authStore";

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: Rol[];
}

/**
 * Protege rutas requiriendo sesión activa y, opcionalmente, un rol específico
 * (RF009: control de acceso por roles).
 */
function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const location = useLocation();
  const token = useAuthStore((s) => s.token);
  const usuario = useAuthStore((s) => s.usuario);

  if (!token || !usuario) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (roles && !roles.includes(usuario.rol)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
}

export default ProtectedRoute;
