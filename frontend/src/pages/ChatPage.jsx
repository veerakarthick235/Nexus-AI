import { useEffect, useRef, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
    fetchConversations, createConversation, fetchMessages,
    sendMessage, deleteConversation, setActiveConversation,
} from '../store/chatSlice';
import {
    HiPaperAirplane, HiPlus, HiTrash, HiChatBubbleLeftRight,
    HiSparkles, HiClock, HiEllipsisVertical,
} from 'react-icons/hi2';
import './ChatPage.css';

export default function ChatPage() {
    const dispatch = useDispatch();
    const { conversations, activeConversationId, messages, sendingMessage, loading } = useSelector(state => state.chat);
    const { user } = useSelector(state => state.auth);
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
        dispatch(fetchConversations());
    }, [dispatch]);

    useEffect(() => {
        if (activeConversationId) {
            dispatch(fetchMessages(activeConversationId));
        }
    }, [activeConversationId, dispatch]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, activeConversationId, sendingMessage]);

    const handleNewConversation = () => {
        dispatch(createConversation({}));
    };

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!inputValue.trim() || sendingMessage || !activeConversationId) return;

        dispatch(sendMessage({
            conversationId: activeConversationId,
            content: inputValue.trim(),
        }));
        setInputValue('');
        inputRef.current?.focus();
    };

    const handleDeleteConversation = (e, convId) => {
        e.stopPropagation();
        if (confirm('Delete this conversation?')) {
            dispatch(deleteConversation(convId));
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    const activeMessages = messages[activeConversationId] || [];

    const formatTime = (dateStr) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className="chat-page">
            {/* Conversation List Panel */}
            <div className="chat-sidebar">
                <div className="chat-sidebar-header">
                    <h2>Conversations</h2>
                    <button
                        className="btn btn-primary btn-sm"
                        onClick={handleNewConversation}
                        id="btn-new-conversation"
                    >
                        <HiPlus /> New
                    </button>
                </div>

                <div className="conversation-list" id="conversation-list">
                    {loading && conversations.length === 0 ? (
                        <div className="conversation-skeleton">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="skeleton" style={{ height: 60, marginBottom: 8 }}></div>
                            ))}
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="empty-state" style={{ padding: 'var(--space-8)' }}>
                            <HiChatBubbleLeftRight className="empty-icon" style={{ fontSize: '2rem' }} />
                            <p>No conversations yet</p>
                            <button className="btn btn-primary btn-sm" onClick={handleNewConversation} style={{ marginTop: 'var(--space-4)' }}>
                                Start one
                            </button>
                        </div>
                    ) : (
                        conversations.map(conv => (
                            <div
                                key={conv.id}
                                className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
                                onClick={() => dispatch(setActiveConversation(conv.id))}
                            >
                                <div className="conv-icon">
                                    <HiChatBubbleLeftRight />
                                </div>
                                <div className="conv-info">
                                    <span className="conv-title">{conv.title || 'New Conversation'}</span>
                                    <span className="conv-meta">
                                        <HiClock /> {formatTime(conv.updated_at)} · {conv.message_count || 0} msgs
                                    </span>
                                </div>
                                <button
                                    className="conv-delete"
                                    onClick={(e) => handleDeleteConversation(e, conv.id)}
                                    title="Delete conversation"
                                >
                                    <HiTrash />
                                </button>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Chat Window */}
            <div className="chat-main">
                {activeConversationId ? (
                    <>
                        {/* Messages Area */}
                        <div className="messages-container" id="messages-container">
                            {activeMessages.length === 0 && !sendingMessage ? (
                                <div className="chat-welcome">
                                    <div className="welcome-icon">
                                        <HiSparkles />
                                    </div>
                                    <h2>Start a conversation</h2>
                                    <p>Ask me anything — I'm powered by AI and ready to help!</p>
                                    <div className="welcome-suggestions">
                                        {[
                                            'What can you help me with?',
                                            'Create an automation workflow',
                                            'Explain how this platform works',
                                        ].map(suggestion => (
                                            <button
                                                key={suggestion}
                                                className="suggestion-chip"
                                                onClick={() => {
                                                    setInputValue(suggestion);
                                                    inputRef.current?.focus();
                                                }}
                                            >
                                                {suggestion}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="messages-list">
                                    {activeMessages.map((msg, idx) => (
                                        <div
                                            key={msg.id || idx}
                                            className={`message ${msg.role} animate-fade-in`}
                                        >
                                            <div className="message-avatar">
                                                {msg.role === 'user' ? (
                                                    user?.username?.charAt(0).toUpperCase() || 'U'
                                                ) : (
                                                    <HiSparkles />
                                                )}
                                            </div>
                                            <div className="message-content">
                                                <div className="message-header">
                                                    <span className="message-sender">
                                                        {msg.role === 'user' ? (user?.username || 'You') : 'NexusAI'}
                                                    </span>
                                                    <span className="message-time">{formatTime(msg.created_at)}</span>
                                                </div>
                                                <div className="message-body">
                                                    {msg.content.split('\n').map((line, i) => (
                                                        <span key={i}>
                                                            {line}
                                                            {i < msg.content.split('\n').length - 1 && <br />}
                                                        </span>
                                                    ))}
                                                </div>
                                                {msg.model && msg.role === 'assistant' && (
                                                    <span className="message-model">{msg.model}</span>
                                                )}
                                            </div>
                                        </div>
                                    ))}

                                    {sendingMessage && (
                                        <div className="message assistant animate-fade-in">
                                            <div className="message-avatar">
                                                <HiSparkles />
                                            </div>
                                            <div className="message-content">
                                                <div className="typing-indicator">
                                                    <span></span><span></span><span></span>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    <div ref={messagesEndRef} />
                                </div>
                            )}
                        </div>

                        {/* Message Input */}
                        <form className="chat-input-area" onSubmit={handleSendMessage}>
                            <div className="chat-input-container">
                                <textarea
                                    ref={inputRef}
                                    className="chat-input"
                                    placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    rows={1}
                                    disabled={sendingMessage}
                                    id="chat-input-field"
                                />
                                <button
                                    type="submit"
                                    className="btn btn-primary btn-icon send-btn"
                                    disabled={!inputValue.trim() || sendingMessage}
                                    id="btn-send-message"
                                >
                                    <HiPaperAirplane />
                                </button>
                            </div>
                            <div className="chat-input-footer">
                                <span>NexusAI may produce inaccurate responses. Verify important information.</span>
                            </div>
                        </form>
                    </>
                ) : (
                    <div className="chat-no-selection">
                        <div className="welcome-icon" style={{ fontSize: '3rem' }}>
                            <HiChatBubbleLeftRight />
                        </div>
                        <h2>Select a conversation</h2>
                        <p>Choose from the sidebar or create a new one</p>
                        <button className="btn btn-primary" onClick={handleNewConversation}>
                            <HiPlus /> New Conversation
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
