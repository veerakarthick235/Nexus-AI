import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { registerUser, clearError } from '../store/authSlice';
import { HiSparkles, HiEnvelope, HiLockClosed, HiUser, HiEye, HiEyeSlash } from 'react-icons/hi2';
import './Auth.css';

export default function RegisterPage() {
    const dispatch = useDispatch();
    const { loading, error } = useSelector(state => state.auth);
    const [form, setForm] = useState({ email: '', username: '', password: '', confirmPassword: '' });
    const [showPassword, setShowPassword] = useState(false);
    const [validationError, setValidationError] = useState('');

    const handleChange = (e) => {
        setForm({ ...form, [e.target.name]: e.target.value });
        setValidationError('');
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (form.password !== form.confirmPassword) {
            setValidationError('Passwords do not match');
            return;
        }
        if (form.password.length < 8) {
            setValidationError('Password must be at least 8 characters');
            return;
        }
        dispatch(registerUser({
            email: form.email,
            username: form.username,
            password: form.password,
        }));
    };

    const displayError = validationError || error;

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
                    <h1>Create Account</h1>
                    <p>Join the NexusAI Platform</p>
                </div>

                {displayError && (
                    <div className="auth-error animate-fade-in" onClick={() => { dispatch(clearError()); setValidationError(''); }}>
                        {displayError}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="input-group">
                        <label htmlFor="reg-username">Username</label>
                        <div className="input-with-icon">
                            <HiUser className="input-icon" />
                            <input id="reg-username" name="username" type="text" className="input"
                                placeholder="johndoe" value={form.username} onChange={handleChange} required />
                        </div>
                    </div>

                    <div className="input-group">
                        <label htmlFor="reg-email">Email</label>
                        <div className="input-with-icon">
                            <HiEnvelope className="input-icon" />
                            <input id="reg-email" name="email" type="email" className="input"
                                placeholder="you@example.com" value={form.email} onChange={handleChange} required />
                        </div>
                    </div>

                    <div className="input-group">
                        <label htmlFor="reg-password">Password</label>
                        <div className="input-with-icon">
                            <HiLockClosed className="input-icon" />
                            <input id="reg-password" name="password"
                                type={showPassword ? 'text' : 'password'} className="input"
                                placeholder="Min 8 characters" value={form.password} onChange={handleChange} required />
                            <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                                {showPassword ? <HiEyeSlash /> : <HiEye />}
                            </button>
                        </div>
                    </div>

                    <div className="input-group">
                        <label htmlFor="reg-confirm">Confirm Password</label>
                        <div className="input-with-icon">
                            <HiLockClosed className="input-icon" />
                            <input id="reg-confirm" name="confirmPassword" type="password" className="input"
                                placeholder="••••••••" value={form.confirmPassword} onChange={handleChange} required />
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary btn-lg auth-submit" disabled={loading} id="btn-register">
                        {loading ? (
                            <><div className="loading-spinner" style={{ width: 18, height: 18 }}></div> Creating account...</>
                        ) : (
                            'Create Account'
                        )}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Already have an account? <Link to="/login">Sign in</Link></p>
                </div>
            </div>
        </div>
    );
}
