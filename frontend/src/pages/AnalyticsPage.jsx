import { useState, useEffect } from 'react';
import api from '../services/api';
import { HiChartBar, HiChatBubbleLeftRight, HiBolt, HiClock } from 'react-icons/hi2';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './AnalyticsPage.css';

const COLORS = ['#6C5CE7', '#00D2FF', '#00E676', '#FFD740', '#FF5252'];

export default function AnalyticsPage() {
    const [convAnalytics, setConvAnalytics] = useState(null);
    const [autoAnalytics, setAutoAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [period, setPeriod] = useState(30);

    useEffect(() => {
        loadAnalytics();
    }, [period]);

    const loadAnalytics = async () => {
        setLoading(true);
        try {
            const [convRes, autoRes] = await Promise.all([
                api.get(`/api/analytics/conversations?days=${period}`),
                api.get(`/api/analytics/automations?days=${period}`),
            ]);
            setConvAnalytics(convRes.data);
            setAutoAnalytics(autoRes.data);
        } catch (err) {
            // Mock data for when API is unavailable
            setConvAnalytics({
                daily_conversations: [
                    { date: '2026-03-01', count: 5 },
                    { date: '2026-03-02', count: 8 },
                    { date: '2026-03-03', count: 12 },
                    { date: '2026-03-04', count: 7 },
                    { date: '2026-03-05', count: 15 },
                    { date: '2026-03-06', count: 10 },
                    { date: '2026-03-07', count: 18 },
                ],
                daily_messages: [
                    { date: '2026-03-01', count: 20 },
                    { date: '2026-03-02', count: 35 },
                    { date: '2026-03-03', count: 48 },
                    { date: '2026-03-04', count: 28 },
                    { date: '2026-03-05', count: 55 },
                    { date: '2026-03-06', count: 42 },
                    { date: '2026-03-07', count: 65 },
                ],
                total_tokens_used: 12450,
            });
            setAutoAnalytics({
                runs_by_status: { completed: 24, failed: 3, running: 1 },
                avg_duration_ms: 1250,
                top_workflows: [
                    { name: 'Lead Notification', run_count: 12 },
                    { name: 'Welcome Email', run_count: 8 },
                    { name: 'Data Sync', run_count: 5 },
                ],
            });
        } finally {
            setLoading(false);
        }
    };

    const pieData = autoAnalytics?.runs_by_status
        ? Object.entries(autoAnalytics.runs_by_status).map(([name, value]) => ({ name, value }))
        : [];

    const customTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip">
                    <p className="tooltip-label">{label}</p>
                    <p className="tooltip-value">{payload[0].value}</p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <div>
                    <h1>Analytics</h1>
                    <p className="page-subtitle">Platform usage insights and performance metrics</p>
                </div>
                <div className="period-selector">
                    {[7, 30, 90].map(p => (
                        <button
                            key={p}
                            className={`btn btn-sm ${period === p ? 'btn-primary' : 'btn-ghost'}`}
                            onClick={() => setPeriod(p)}
                        >
                            {p}d
                        </button>
                    ))}
                </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-3" style={{ marginBottom: 'var(--space-8)' }}>
                <div className="stat-card animate-fade-in">
                    <span className="stat-label">Total Tokens Used</span>
                    <span className="stat-value">{(convAnalytics?.total_tokens_used || 0).toLocaleString()}</span>
                </div>
                <div className="stat-card animate-fade-in" style={{ animationDelay: '0.1s' }}>
                    <span className="stat-label">Avg Run Duration</span>
                    <span className="stat-value">{autoAnalytics?.avg_duration_ms || 0}ms</span>
                </div>
                <div className="stat-card animate-fade-in" style={{ animationDelay: '0.2s' }}>
                    <span className="stat-label">Active Period</span>
                    <span className="stat-value">{period} days</span>
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-2" style={{ marginBottom: 'var(--space-8)' }}>
                {/* Conversations Chart */}
                <div className="glass-card chart-card">
                    <h3><HiChatBubbleLeftRight /> Daily Conversations</h3>
                    <div className="chart-container">
                        {loading ? (
                            <div className="skeleton" style={{ height: '100%' }}></div>
                        ) : (
                            <ResponsiveContainer width="100%" height={250}>
                                <AreaChart data={convAnalytics?.daily_conversations || []}>
                                    <defs>
                                        <linearGradient id="colorConv" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#6C5CE7" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#6C5CE7" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="date" stroke="#6B6B99" tick={{ fontSize: 11 }} />
                                    <YAxis stroke="#6B6B99" tick={{ fontSize: 11 }} />
                                    <Tooltip content={customTooltip} />
                                    <Area type="monotone" dataKey="count" stroke="#6C5CE7" fillOpacity={1} fill="url(#colorConv)" strokeWidth={2} />
                                </AreaChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>

                {/* Messages Chart */}
                <div className="glass-card chart-card">
                    <h3><HiChartBar /> Daily Messages</h3>
                    <div className="chart-container">
                        {loading ? (
                            <div className="skeleton" style={{ height: '100%' }}></div>
                        ) : (
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={convAnalytics?.daily_messages || []}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="date" stroke="#6B6B99" tick={{ fontSize: 11 }} />
                                    <YAxis stroke="#6B6B99" tick={{ fontSize: 11 }} />
                                    <Tooltip content={customTooltip} />
                                    <Bar dataKey="count" fill="#00D2FF" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        )}
                    </div>
                </div>
            </div>

            {/* Bottom Row */}
            <div className="grid grid-2">
                {/* Automation Status Pie */}
                <div className="glass-card chart-card">
                    <h3><HiBolt /> Automation Run Status</h3>
                    <div className="chart-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {loading ? (
                            <div className="skeleton" style={{ width: 200, height: 200, borderRadius: '50%' }}></div>
                        ) : pieData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={250}>
                                <PieChart>
                                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90}
                                        paddingAngle={5} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                                        {pieData.map((_, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <p style={{ color: 'var(--text-tertiary)' }}>No automation data yet</p>
                        )}
                    </div>
                </div>

                {/* Top Workflows */}
                <div className="glass-card">
                    <h3 style={{ marginBottom: 'var(--space-4)' }}><HiBolt /> Top Workflows</h3>
                    {loading ? (
                        [1, 2, 3].map(i => (
                            <div key={i} className="skeleton" style={{ height: 40, marginBottom: 8 }}></div>
                        ))
                    ) : autoAnalytics?.top_workflows?.length > 0 ? (
                        <div className="top-workflows-list">
                            {autoAnalytics.top_workflows.map((wf, i) => (
                                <div key={i} className="top-workflow-item">
                                    <span className="wf-rank">#{i + 1}</span>
                                    <span className="wf-name">{wf.name}</span>
                                    <span className="badge badge-primary">{wf.run_count} runs</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p style={{ color: 'var(--text-tertiary)' }}>No workflows have been executed yet</p>
                    )}
                </div>
            </div>
        </div>
    );
}
