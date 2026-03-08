import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';

export const fetchWorkflows = createAsyncThunk('automation/fetchWorkflows', async (_, { rejectWithValue }) => {
    try {
        const response = await api.get('/api/automation/workflows?all=true');
        return response.data;
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch workflows');
    }
});

export const createWorkflow = createAsyncThunk('automation/createWorkflow', async (data, { rejectWithValue }) => {
    try {
        const response = await api.post('/api/automation/workflows', data);
        return response.data.workflow;
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to create workflow');
    }
});

export const triggerWorkflow = createAsyncThunk('automation/triggerWorkflow', async ({ workflowId, inputData }, { rejectWithValue }) => {
    try {
        const response = await api.post(`/api/automation/workflows/${workflowId}/trigger`, { input_data: inputData });
        return response.data;
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to trigger workflow');
    }
});

export const fetchWorkflowRuns = createAsyncThunk('automation/fetchRuns', async (workflowId, { rejectWithValue }) => {
    try {
        const response = await api.get(`/api/automation/workflows/${workflowId}/runs`);
        return { workflowId, runs: response.data.items || [] };
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch runs');
    }
});

const automationSlice = createSlice({
    name: 'automation',
    initialState: {
        workflows: [],
        runs: {},
        activeWorkflowId: null,
        loading: false,
        triggering: false,
        error: null,
    },
    reducers: {
        setActiveWorkflow: (state, action) => {
            state.activeWorkflowId = action.payload;
        },
        clearAutomationError: (state) => {
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchWorkflows.pending, (state) => { state.loading = true; })
            .addCase(fetchWorkflows.fulfilled, (state, action) => {
                state.loading = false;
                state.workflows = action.payload.items || [];
            })
            .addCase(fetchWorkflows.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })
            .addCase(createWorkflow.fulfilled, (state, action) => {
                state.workflows.unshift(action.payload);
            })
            .addCase(triggerWorkflow.pending, (state) => { state.triggering = true; })
            .addCase(triggerWorkflow.fulfilled, (state) => { state.triggering = false; })
            .addCase(triggerWorkflow.rejected, (state, action) => {
                state.triggering = false;
                state.error = action.payload;
            })
            .addCase(fetchWorkflowRuns.fulfilled, (state, action) => {
                state.runs[action.payload.workflowId] = action.payload.runs;
            });
    },
});

export const { setActiveWorkflow, clearAutomationError } = automationSlice.actions;
export default automationSlice.reducer;
