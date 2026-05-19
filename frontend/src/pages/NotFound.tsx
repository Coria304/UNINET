import { Link } from "react-router-dom";

function NotFound() {
  return (
    <div className="min-h-screen grid place-items-center text-center p-6">
      <div>
        <h1 className="text-4xl font-bold">404</h1>
        <p className="text-slate-600 mt-2">Página no encontrada.</p>
        <Link to="/" className="btn-primary mt-4">
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}

export default NotFound;
