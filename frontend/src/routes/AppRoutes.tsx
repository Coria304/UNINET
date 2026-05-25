import { Navigate, Route, Routes } from "react-router-dom";

import { useHydrateSession } from "@/hooks/useAuth";
import AdminLayout from "@/layouts/AdminLayout";
import TecnicoLayout from "@/layouts/TecnicoLayout";
import UsuarioLayout from "@/layouts/UsuarioLayout";
import AdminInicio from "@/pages/admin/Inicio";
import TicketsAdmin from "@/pages/admin/TicketsAdmin";
import Login from "@/pages/Login";
import NotFound from "@/pages/NotFound";
import PortalInicio from "@/pages/portal/Inicio";
import MisReportes from "@/pages/portal/MisReportes";
import ReportarFalla from "@/pages/portal/ReportarFalla";
import TecnicoInicio from "@/pages/tecnico/Inicio";
import TicketDetail from "@/pages/tecnico/TicketDetail";
import TicketsList from "@/pages/tecnico/TicketsList";
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
        path="/admin"
        element={
          <ProtectedRoute roles={["administrador_ti"]}>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<AdminInicio />} />
        <Route path="tickets" element={<TicketsAdmin />} />
      </Route>

      <Route
        path="/tecnico"
        element={
          <ProtectedRoute roles={["personal_tecnico"]}>
            <TecnicoLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<TecnicoInicio />} />
        <Route path="tickets" element={<TicketsList />} />
        <Route path="tickets/:ticketId" element={<TicketDetail />} />
      </Route>

      <Route
        path="/portal"
        element={
          <ProtectedRoute roles={["estudiante", "docente"]}>
            <UsuarioLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<PortalInicio />} />
        <Route path="reportar" element={<ReportarFalla />} />
        <Route path="mis-reportes" element={<MisReportes />} />
      </Route>

      <Route path="/" element={<RoleRedirect />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default AppRoutes;
