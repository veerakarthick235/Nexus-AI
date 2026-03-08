import { NavLink, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { logout } from '../../store/authSlice';
import { HiChatBubbleLeftRight, HiCog6Tooth, HiChartBar, HiBolt, HiArrowRightOnRectangle, HiSparkles } from 'react-icons/hi2';
import './Sidebar.css';

export default function Sidebar() {
    const navigate = useNavigate();
    const dispatch = useDispatch();
    const { user } = useSelector(state => state.auth);

    const handleLogout = () => {
        dispatch(logout());
        navigate('/login');
    };

    const navItems = [
        { to: '/chat', icon: <HiChatBubbleLeftRight />, label: 'Chat' },
        { to: '/automation', icon: <HiBolt />, label: 'Automation' },
        { to: '/analytics', icon: <HiChartBar />, label: 'Analytics' },
        { to: '/dashboard', icon: <HiCog6Tooth />, label: 'Dashboard' },
    ];

    return (
        <aside className="sidebar" id="main-sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <div className="logo-icon">
                        <HiSparkles />
                    </div>
                    <div className="logo-text">
                        <span className="logo-name">NexusAI</span>
                        <span className="logo-tagline">Platform</span>
                    </div>
                </div>
            </div>

            <nav className="sidebar-nav">
                {navItems.map(item => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                        id={`nav-${item.label.toLowerCase()}`}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            <div className="sidebar-footer">
                {user && (
                    <div className="user-info">
                        <div className="user-avatar" id="user-avatar">
                            {user.username?.charAt(0).toUpperCase()}
                        </div>
                        <div className="user-details">
                            <span className="user-name">{user.username}</span>
                            <span className="user-role">{user.role}</span>
                        </div>
                    </div>
                )}
                <button className="btn btn-ghost nav-item" onClick={handleLogout} id="btn-logout">
                    <span className="nav-icon"><HiArrowRightOnRectangle /></span>
                    <span className="nav-label">Logout</span>
                </button>
            </div>
        </aside>
    );
}
