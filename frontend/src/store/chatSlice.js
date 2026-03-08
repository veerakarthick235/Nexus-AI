import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';

export const fetchConversations = createAsyncThunk('chat/fetchConversations', async (_, { rejectWithValue }) => {
    try {
        const response = await api.get('/api/chat/conversations');
        return response.data;
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch conversations');
    }
});

export const createConversation = createAsyncThunk('chat/createConversation', async (data = {}, { rejectWithValue }) => {
    try {
        const response = await api.post('/api/chat/conversations', data);
        return response.data.conversation;
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to create conversation');
    }
});

export const fetchMessages = createAsyncThunk('chat/fetchMessages', async (conversationId, { rejectWithValue }) => {
    try {
        const response = await api.get(`/api/chat/conversations/${conversationId}`);
        return { conversationId, ...response.data };
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch messages');
    }
});

export const sendMessage = createAsyncThunk('chat/sendMessage', async ({ conversationId, content }, { rejectWithValue }) => {
    try {
        const response = await api.post(`/api/chat/conversations/${conversationId}/messages`, { content });
        return { conversationId, ...response.data };
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to send message');
    }
});

export const deleteConversation = createAsyncThunk('chat/deleteConversation', async (conversationId, { rejectWithValue }) => {
    try {
        await api.delete(`/api/chat/conversations/${conversationId}`);
        return conversationId;
    } catch (error) {
        return rejectWithValue(error.response?.data?.error?.message || 'Failed to delete conversation');
    }
});

const chatSlice = createSlice({
    name: 'chat',
    initialState: {
        conversations: [],
        activeConversationId: null,
        messages: {},
        isStreaming: false,
        streamingContent: '',
        loading: false,
        sendingMessage: false,
        error: null,
    },
    reducers: {
        setActiveConversation: (state, action) => {
            state.activeConversationId = action.payload;
        },
        appendStreamChunk: (state, action) => {
            state.streamingContent += action.payload;
        },
        clearStream: (state) => {
            state.streamingContent = '';
            state.isStreaming = false;
        },
        startStream: (state) => {
            state.isStreaming = true;
            state.streamingContent = '';
        },
        addMessage: (state, action) => {
            const { conversationId, message } = action.payload;
            if (!state.messages[conversationId]) {
                state.messages[conversationId] = [];
            }
            state.messages[conversationId].push(message);
        },
    },
    extraReducers: (builder) => {
        builder
            .addCase(fetchConversations.pending, (state) => {
                state.loading = true;
            })
            .addCase(fetchConversations.fulfilled, (state, action) => {
                state.loading = false;
                state.conversations = action.payload.items || [];
            })
            .addCase(fetchConversations.rejected, (state, action) => {
                state.loading = false;
                state.error = action.payload;
            })
            .addCase(createConversation.fulfilled, (state, action) => {
                state.conversations.unshift(action.payload);
                state.activeConversationId = action.payload.id;
                state.messages[action.payload.id] = [];
            })
            .addCase(fetchMessages.fulfilled, (state, action) => {
                const { conversationId, messages } = action.payload;
                state.messages[conversationId] = messages || [];
            })
            .addCase(sendMessage.pending, (state) => {
                state.sendingMessage = true;
            })
            .addCase(sendMessage.fulfilled, (state, action) => {
                state.sendingMessage = false;
                const { conversationId, user_message, assistant_message } = action.payload;
                if (!state.messages[conversationId]) {
                    state.messages[conversationId] = [];
                }
                state.messages[conversationId].push(user_message);
                state.messages[conversationId].push(assistant_message);

                // Update conversation in list
                const conv = state.conversations.find(c => c.id === conversationId);
                if (conv) {
                    conv.message_count = (conv.message_count || 0) + 2;
                    conv.updated_at = new Date().toISOString();
                }
            })
            .addCase(sendMessage.rejected, (state, action) => {
                state.sendingMessage = false;
                state.error = action.payload;
            })
            .addCase(deleteConversation.fulfilled, (state, action) => {
                state.conversations = state.conversations.filter(c => c.id !== action.payload);
                if (state.activeConversationId === action.payload) {
                    state.activeConversationId = state.conversations[0]?.id || null;
                }
                delete state.messages[action.payload];
            });
    },
});

export const { setActiveConversation, appendStreamChunk, clearStream, startStream, addMessage } = chatSlice.actions;
export default chatSlice.reducer;
