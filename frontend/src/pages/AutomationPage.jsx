import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
    fetchWorkflows, createWorkflow, triggerWorkflow,
    fetchWorkflowRuns, setActiveWorkflow,
} from '../store/automationSlice';
import {
    HiBolt, HiPlus, HiPlay, HiCheckCircle, HiXCircle,
    HiClock, HiEye, HiArrowPath,
} from 'react-icons/hi2';
import './AutomationPage.css';

export default function AutomationPage() {
    const dispatch = useDispatch();
    const { workflows, runs, activeWorkflowId, loading, triggering } = useSelector(state => state.automation);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newWorkflow, setNewWorkflow] = useState({
        name: '', description: '',
        trigger: { type: 'manual', config: {} },
        steps: [{ type: 'log', config: { message: 'Workflow executed', level: 'info' } }],
    });

    useEffect(() => {
        dispatch(fetchWorkflows());
    }, [dispatch]);

    useEffect(() => {
        if (activeWorkflowId) {
            dispatch(fetchWorkflowRuns(activeWorkflowId));
        }
    }, [activeWorkflowId, dispatch]);

    const handleCreate = () => {
        if (!newWorkflow.name) return;
        dispatch(createWorkflow(newWorkflow));
        setShowCreateModal(false);
        setNewWorkflow({
            name: '', description: '',
            trigger: { type: 'manual', config: {} },
            steps: [{ type: 'log', config: { message: 'Workflow executed', level: 'info' } }],
        });
    };

    const handleTrigger = (workflowId) => {
        dispatch(triggerWorkflow({ workflowId, inputData: {} }));
        setTimeout(() => dispatch(fetchWorkflowRuns(workflowId)), 1000);
    };

    const statusIcon = (status) => {
        switch (status) {
            case 'completed': return <HiCheckCircle style={{ color: 'var(--color-success)' }} />;
            case 'failed': return <HiXCircle style={{ color: 'var(--color-error)' }} />;
            case 'running': return <HiArrowPath className="animate-spin" style={{ color: 'var(--color-accent)' }} />;
            default: return <HiClock style={{ color: 'var(--text-tertiary)' }} />;
        }
    };

    const activeRuns = activeWorkflowId ? (runs[activeWorkflowId] || []) : [];
    const activeWorkflow = workflows.find(w => w.id === activeWorkflowId);

    return (
        <div className="page-container">
            <div className="page-header">
                <div>
                    <h1>Automation</h1>
                    <p className="page-subtitle">Create and manage workflow automations</p>
                </div>
                <button className="btn btn-primary" onClick={() => setShowCreateModal(true)} id="btn-create-workflow">
                    <HiPlus /> New Workflow
                </button>
            </div>

            <div className="automation-layout">
                {/* Workflows List */}
                <div className="automation-list">
                    <h3 className="section-title">Workflows ({workflows.length})</h3>
                    {loading ? (
                        [1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: 80, marginBottom: 8 }}></div>)
                    ) : workflows.length === 0 ? (
                        <div className="empty-state" style={{ padding: 'var(--space-10)' }}>
                            <HiBolt className="empty-icon" />
                            <h3>No workflows yet</h3>
                            <p>Create your first automation workflow</p>
                        </div>
                    ) : (
                        workflows.map(wf => (
                            <div
                                key={wf.id}
                                className={`workflow-card ${wf.id === activeWorkflowId ? 'active' : ''}`}
                                onClick={() => dispatch(setActiveWorkflow(wf.id))}
                            >
                                <div className="wf-card-header">
                                    <div className="wf-card-icon">
                                        <HiBolt />
                                    </div>
                                    <div className="wf-card-info">
                                        <span className="wf-card-name">{wf.name}</span>
                                        <span className="wf-card-desc">{wf.description || 'No description'}</span>
                                    </div>
                                    <span className={`badge ${wf.is_active ? 'badge-success' : 'badge-warning'}`}>
                                        {wf.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </div>
                                <div className="wf-card-meta">
                                    <span><HiClock /> {wf.run_count || 0} runs</span>
                                    <span>Trigger: {wf.trigger_config?.type || 'manual'}</span>
                                    <span>{wf.steps?.length || 0} steps</span>
                                </div>
                                <div className="wf-card-actions">
                                    <button
                                        className="btn btn-sm btn-secondary"
                                        onClick={(e) => { e.stopPropagation(); handleTrigger(wf.id); }}
                                        disabled={triggering || !wf.is_active}
                                        title="Run workflow"
                                    >
                                        <HiPlay /> Run
                                    </button>
                                    <button
                                        className="btn btn-sm btn-ghost"
                                        onClick={(e) => { e.stopPropagation(); dispatch(setActiveWorkflow(wf.id)); }}
                                    >
                                        <HiEye /> Details
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Workflow Details */}
                <div className="automation-details">
                    {activeWorkflow ? (
                        <>
                            <div className="glass-card" style={{ marginBottom: 'var(--space-6)' }}>
                                <h3 style={{ marginBottom: 'var(--space-4)' }}>
                                    {activeWorkflow.name}
                                </h3>
                                <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>
                                    {activeWorkflow.description || 'No description provided'}
                                </p>

                                <h4 style={{ marginBottom: 'var(--space-3)', color: 'var(--text-secondary)' }}>Steps</h4>
                                <div className="steps-timeline">
                                    {activeWorkflow.steps?.map((step, i) => (
                                        <div key={i} className="step-item">
                                            <div className="step-number">{i + 1}</div>
                                            <div className="step-info">
                                                <span className="step-type">{step.type}</span>
                                                <span className="step-config">
                                                    {JSON.stringify(step.config).slice(0, 80)}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="glass-card">
                                <h3 style={{ marginBottom: 'var(--space-4)' }}>Execution History</h3>
                                {activeRuns.length === 0 ? (
                                    <p style={{ color: 'var(--text-tertiary)' }}>No executions yet</p>
                                ) : (
                                    <div className="runs-list">
                                        {activeRuns.map(run => (
                                            <div key={run.id} className="run-item">
                                                <span className="run-status">{statusIcon(run.status)}</span>
                                                <span className="run-id">{run.id?.slice(0, 8)}...</span>
                                                <span className={`badge badge-${run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'primary'}`}>
                                                    {run.status}
                                                </span>
                                                <span className="run-duration">
                                                    {run.duration_ms ? `${run.duration_ms}ms` : '-'}
                                                </span>
                                                <span className="run-time">
                                                    {run.started_at ? new Date(run.started_at).toLocaleString() : '-'}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="empty-state" style={{ height: '100%' }}>
                            <HiEye className="empty-icon" />
                            <h3>Select a workflow</h3>
                            <p>Click on a workflow to view its details and execution history</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Create Modal */}
            {showCreateModal && (
                <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Create Workflow</h2>
                            <button className="btn btn-ghost btn-icon" onClick={() => setShowCreateModal(false)}>✕</button>
                        </div>

                        <div className="auth-form">
                            <div className="input-group">
                                <label htmlFor="wf-name">Workflow Name</label>
                                <input
                                    id="wf-name"
                                    className="input"
                                    placeholder="e.g. New Lead Notification"
                                    value={newWorkflow.name}
                                    onChange={e => setNewWorkflow({ ...newWorkflow, name: e.target.value })}
                                />
                            </div>

                            <div className="input-group">
                                <label htmlFor="wf-desc">Description</label>
                                <textarea
                                    id="wf-desc"
                                    className="input"
                                    placeholder="What does this workflow do?"
                                    value={newWorkflow.description}
                                    onChange={e => setNewWorkflow({ ...newWorkflow, description: e.target.value })}
                                />
                            </div>

                            <div className="input-group">
                                <label>Trigger Type</label>
                                <select
                                    className="input"
                                    value={newWorkflow.trigger.type}
                                    onChange={e => setNewWorkflow({
                                        ...newWorkflow,
                                        trigger: { ...newWorkflow.trigger, type: e.target.value },
                                    })}
                                >
                                    <option value="manual">Manual</option>
                                    <option value="webhook">Webhook</option>
                                    <option value="schedule">Schedule</option>
                                    <option value="event">Event</option>
                                </select>
                            </div>

                            <button className="btn btn-primary btn-lg" style={{ width: '100%' }} onClick={handleCreate}>
                                <HiPlus /> Create Workflow
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
