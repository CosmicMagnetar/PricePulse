import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    
    try {
      setError('');
      setLoading(true);
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError('Failed to sign in');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{width:"100vh", display:"flex",justifyContent:"center"}} className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100 px-4">
    <div className="w-full max-w-md bg-white shadow-2xl rounded-2xl p-8 sm:p-10">
      <div className="text-center mb-6">
        <h2 className="text-3xl font-bold text-gray-800">Sign in to your account</h2>
        <p className="text-sm text-gray-500 mt-2">Welcome back! Please enter your credentials.</p>
      </div>
      <form className="space-y-5" onSubmit={handleSubmit}>
        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded-md text-sm">{error}</div>
        )}
        <div>
          <label className="block mb-1 text-sm font-medium text-gray-700" htmlFor="email">
            Email
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="you@example.com"
            required
          />
        </div>
        <div>
          <label className="block mb-1 text-sm font-medium text-gray-700" htmlFor="password">
            Password
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            placeholder="••••••••"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 transition duration-200 text-white font-semibold rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>
      <div className="text-sm text-center text-gray-600 mt-6">
        Don’t have an account?{' '}
        <Link to="/signup" className="text-blue-600 hover:underline font-medium">
          Sign up
        </Link>
      </div>
    </div>
</div>


  );
} 