import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';
import { formatApiError } from '../utils/errorHandler';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(formData);
      const destination = location.state?.from?.pathname || '/dashboard';
      navigate(destination, { replace: true });
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-badge">Secure Authentication</div>
          <h1>Welcome Back</h1>
          <p>Sign in to your AI Career Copilot to resume your roadmap and progress</p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert">
            <span className="alert-icon">⚠️</span>
            <div className="alert-content">{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="you@example.com"
              required
              autoComplete="email"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <div className="label-wrapper">
              <label htmlFor="password">Password</label>
            </div>
            <input
              id="password"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
              autoComplete="current-password"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block btn-lg"
            disabled={loading}
          >
            {loading ? (
              <span className="btn-loading">
                <span className="spinner-sm"></span> Signing in...
              </span>
            ) : (
              'Sign In to Dashboard'
            )}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don&apos;t have an account?{' '}
            <Link to="/register" className="auth-link">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
