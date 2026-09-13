import { Navigate, Outlet } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function PublicRoute() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
