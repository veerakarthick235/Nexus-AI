import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import api from '../services/api';
import {
    HiUsers, HiChatBubbleLeftRight, HiBolt, HiCheckCircle,
    HiClock, HiExclamationCircle, HiArrowTrendingUp,
} from 'react-icons/hi2';
import './DashboardPage.css';

export default function DashboardPage() {
    const { user } = useSelector(state => state.auth);
    const [overview, setOverview] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadOverview();
    }, []);

    const loadOverview = async () => {
        try {
            const response = await api.get('/api/analytics/overview?days=30');
            setOverview(response.data);
        } catch (err) {
            console.error('Failed to load overview:', err);
            // Use mock data for non-admin users or when API fails
            setOverview({
                total_users: 3,
                total_conversations: 12,
                total_messages: 48,
                avg_messages_per_conversation: 4.0,
                total_workflow_runs: 5,
                successful_runs: 4,
                failed_runs: 1,
                automation_success_rate: 80.0,
            });
        } finally {
            setLoading(false);
        }
    };

    const stats = overview ? [
        {
            label: 'Active Users',
            value: overview.total_users,
            icon: <HiUsers />,
            change: '+12%',
            positive: true,
        },
        {
            label: 'Conversations',
            value: overview.total_conversations,
            icon: <HiChatBubbleLeftRight />,
            change: '+24%',
            positive: true,
        },
        {
            label: 'Total Messages',
            value: overview.total_messages,
            icon: <HiArrowTrendingUp />,
            change: '+18%',
            positive: true,
        },
        {
            label: 'Automation Runs',
            value: overview.total_workflow_runs,
            icon: <HiBolt />,
            change: '+8%',
            positive: true,
        },
    ] : [];

    return (
        <div className="page-container">
            <div className="page-header">
                <div>
                    <h1>Dashboard</h1>
                    <p className="page-subtitle">Welcome back, {user?.username || 'User'}</p>
                </div>
                <div className="header-badge">
                    <span className="badge badge-primary">
                        <HiClock style={{ marginRight: 4 }} /> Last 30 days
                    </span>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-4" style={{ marginBottom: 'var(--space-8)' }}>
                {loading ? (
                    [1, 2, 3, 4].map(i => (
                        <div key={i} className="stat-card">
                            <div className="skeleton" style={{ width: 100, height: 14, marginBottom: 8 }}></div>
                            <div className="skeleton" style={{ width: 60, height: 36, marginBottom: 8 }}></div>
                            <div className="skeleton" style={{ width: 60, height: 12 }}></div>
                        </div>
                    ))
                ) : (
                    stats.map((stat, i) => (
                        <div key={i} className="stat-card animate-fade-in" style={{ animationDelay: `${i * 0.1}s` }}>
                            <div className="stat-card-header">
                                <span className="stat-label">{stat.label}</span>
                                <span className="stat-icon">{stat.icon}</span>
                            </div>
                            <span className="stat-value">{stat.value.toLocaleString()}</span>
                            <span className={`stat-change ${stat.positive ? 'positive' : 'negative'}`}>
                                {stat.change} from last period
                            </span>
                        </div>
                    ))
                )}
            </div>

            {/* Quick Info Cards */}
            <div className="grid grid-2">
                <div className="glass-card">
                    <h3 style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                        Automation Health
                    </h3>
                    <div className="health-metrics">
                        <div className="health-item">
                            <HiCheckCircle style={{ color: 'var(--color-success)', fontSize: '1.5rem' }} />
                            <div>
                                <span className="health-value">{overview?.successful_runs || 0}</span>
                                <span className="health-label">Successful</span>
                            </div>
                        </div>
                        <div className="health-item">
                            <HiExclamationCircle style={{ color: 'var(--color-error)', fontSize: '1.5rem' }} />
                            <div>
                                <span className="health-value">{overview?.failed_runs || 0}</span>
                                <span className="health-label">Failed</span>
                            </div>
                        </div>
                        <div className="health-item">
                            <HiArrowTrendingUp style={{ color: 'var(--color-accent)', fontSize: '1.5rem' }} />
                            <div>
                                <span className="health-value">{overview?.automation_success_rate || 0}%</span>
                                <span className="health-label">Success Rate</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="glass-card">
                    <h3 style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                        Conversation Insights
                    </h3>
                    <div className="health-metrics">
                        <div className="health-item">
                            <HiChatBubbleLeftRight style={{ color: 'var(--color-primary-light)', fontSize: '1.5rem' }} />
                            <div>
                                <span className="health-value">{overview?.avg_messages_per_conversation || 0}</span>
                                <span className="health-label">Avg Messages/Conv</span>
                            </div>
                        </div>
                        <div className="health-item">
                            <HiUsers style={{ color: 'var(--color-accent)', fontSize: '1.5rem' }} />
                            <div>
                                <span className="health-value">{overview?.total_users || 0}</span>
                                <span className="health-label">Total Users</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* System Info */}
            <div className="glass-card" style={{ marginTop: 'var(--space-8)' }}>
                <h3 style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--font-size-lg)', fontWeight: 700 }}>
                    System Information
                </h3>
                <div className="system-info-grid">
                    <div className="system-info-item">
                        <span className="siLabel">Platform</span>
                        <span className="siValue">NexusAI v1.0.0</span>
                    </div>
                    <div className="system-info-item">
                        <span className="siLabel">AI Model</span>
                        <span className="siValue">GPT-4o / GPT-4o-mini</span>
                    </div>
                    <div className="system-info-item">
                        <span className="siLabel">Backend</span>
                        <span className="siValue">Flask + SQLAlchemy</span>
                    </div>
                    <div className="system-info-item">
                        <span className="siLabel">Frontend</span>
                        <span className="siValue">React + Redux + Vite</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
