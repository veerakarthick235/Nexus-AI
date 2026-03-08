import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { loginUser, clearError } from '../store/authSlice';
import { HiSparkles, HiEnvelope, HiLockClosed, HiEye, HiEyeSlash } from 'react-icons/hi2';
import './Auth.css';

export default function LoginPage() {
    const dispatch = useDispatch();
    const { loading, error } = useSelector(state => state.auth);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        dispatch(loginUser({ email, password }));
    };

    return (
        <div className="auth-page">
            <div className="auth-backdrop">
                <div className="backdrop-orb orb-1"></div>
                <div className="backdrop-orb orb-2"></div>
                <div className="backdrop-orb orb-3"></div>
            </div>

            <div className="auth-container animate-scale-in">
                <div className="auth-header">
                    <div className="auth-logo">
                        <HiSparkles />
                    </div>
                    <h1>Welcome Back</h1>
                    <p>Sign in to NexusAI Platform</p>
                </div>

                {error && (
                    <div className="auth-error animate-fade-in" onClick={() => dispatch(clearError())}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="input-group">
                        <label htmlFor="login-email">Email</label>
                        <div className="input-with-icon">
                            <HiEnvelope className="input-icon" />
                            <input
                                id="login-email"
                                type="email"
                                className="input"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="input-group">
                        <label htmlFor="login-password">Password</label>
                        <div className="input-with-icon">
                            <HiLockClosed className="input-icon" />
                            <input
                                id="login-password"
                                type={showPassword ? 'text' : 'password'}
                                className="input"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                            <button
                                type="button"
                                className="password-toggle"
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                {showPassword ? <HiEyeSlash /> : <HiEye />}
                            </button>
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary btn-lg auth-submit" disabled={loading} id="btn-login">
                        {loading ? (
                            <><div className="loading-spinner" style={{ width: 18, height: 18 }}></div> Signing in...</>
                        ) : (
                            'Sign In'
                        )}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Don't have an account? <Link to="/register">Create one</Link></p>
                </div>

                <div className="auth-demo-info">
                    <p><strong>Demo Credentials:</strong></p>
                    <p>admin@chatbot.com / admin123!</p>
                    <p>demo@chatbot.com / demo1234!</p>
                </div>
            </div>
        </div>
    );
}
