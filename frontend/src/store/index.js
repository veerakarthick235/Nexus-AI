import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import chatReducer from './chatSlice';
import automationReducer from './automationSlice';

export const store = configureStore({
    reducer: {
        auth: authReducer,
        chat: chatReducer,
        automation: automationReducer,
    },
});
