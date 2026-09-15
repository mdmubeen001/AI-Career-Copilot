import { Link, NavLink, useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="navbar-container">
      <div className="navbar-content">
        <Link to="/" className="navbar-brand">
          <span className="brand-icon">⚡</span>
          <span className="brand-text">CareerCopilot</span>
          <span className="brand-badge">AI 2.0</span>
        </Link>

        <nav className="navbar-links">
          {isAuthenticated ? (
            <>
              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
              >
                Dashboard
              </NavLink>
              <NavLink
                to="/profile"
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
              >
                Profile
              </NavLink>
              <NavLink
                to="/career-analysis"
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
              >
                Career Analysis
              </NavLink>

              <div className="user-menu">
                <span className="user-greeting" title={user?.email}>
                  {user?.full_name || user?.email}
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="btn btn-outline-danger btn-sm"
                >
                  Logout
                </button>
              </div>
            </>
          ) : (
            <>
              <NavLink
                to="/login"
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
              >
                Sign In
              </NavLink>
              <NavLink to="/register" className="btn btn-primary btn-sm">
                Get Started
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
