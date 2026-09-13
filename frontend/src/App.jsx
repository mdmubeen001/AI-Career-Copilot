import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import PublicRoute from './components/PublicRoute';
import { AuthProvider } from './context/AuthContext';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Profile from './pages/Profile';
import Register from './pages/Register';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="app-wrapper">
          <Navbar />
          <main className="main-content">
            <Routes>
              {/* Root redirect */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />

              {/* Public Authentication Routes */}
              <Route element={<PublicRoute />}>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
              </Route>

              {/* Protected Application Routes */}
              <Route element={<ProtectedRoute />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/profile" element={<Profile />} />
              </Route>

              {/* Catch-all fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
