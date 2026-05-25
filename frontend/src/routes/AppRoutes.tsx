import { Navigate, Route, Routes } from "react-router-dom";

import { useHydrateSession } from "@/hooks/useAuth";
import AdminLayout from "@/layouts/AdminLayout";
import TecnicoLayout from "@/layouts/TecnicoLayout";
import UsuarioLayout from "@/layouts/UsuarioLayout";
import Dashboard from "@/pages/Dashboard";
import Login from "@/pages/Login";
import NotFound from "@/pages/NotFound";
import Unauthorized from "@/pages/Unauthorized";
import VerifyMFA from "@/pages/VerifyMFA";
import ProtectedRoute from "@/routes/ProtectedRoute";
import { useAuthStore } from "@/stores/authStore";

/** Redirige a la raíz del dashboard correspondiente al rol autenticado. */
function RoleRedirect() {
  const usuario = useAuthStore((s) => s.usuario);
  if (!usuario) return <Navigate to="/login" replace />;
  switch (usuario.rol) {
    case "administrador_ti":
      return <Navigate to="/admin" replace />;
    case "personal_tecnico":
      return <Navigate to="/tecnico" replace />;
    default:
      return <Navigate to="/portal" replace />;
  }
}

function AppRoutes() {
  // Hidrata el usuario desde /auth/me cuando hay token persistido.
  useHydrateSession();

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/verify-mfa" element={<VerifyMFA />} />
      <Route path="/unauthorized" element={<Unauthorized />} />

      <Route
        path="/admin/*"
        element={
          <ProtectedRoute roles={["administrador_ti"]}>
            <AdminLayout>
              <Dashboard />
            </AdminLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/tecnico/*"
        element={
          <ProtectedRoute roles={["personal_tecnico"]}>
            <TecnicoLayout>
              <Dashboard />
            </TecnicoLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/portal/*"
        element={
          <ProtectedRoute roles={["estudiante", "docente"]}>
            <UsuarioLayout>
              <Dashboard />
            </UsuarioLayout>
          </ProtectedRoute>
        }
      />

      <Route path="/" element={<RoleRedirect />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default AppRoutes;
