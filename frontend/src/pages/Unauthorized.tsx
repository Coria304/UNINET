import { Link } from "react-router-dom";

function Unauthorized() {
  return (
    <div className="min-h-screen grid place-items-center text-center p-6">
      <div>
        <h1 className="text-3xl font-bold">Acceso restringido</h1>
        <p className="text-slate-600 mt-2">
          Tu rol no tiene permisos para acceder a esta sección.
        </p>
        <Link to="/" className="btn-primary mt-4">
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}

export default Unauthorized;
