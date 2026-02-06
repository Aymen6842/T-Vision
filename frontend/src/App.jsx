import { useState, useEffect, useRef } from 'react';
import { Send, Menu, Loader2, LogOut } from 'lucide-react';
import Sidebar from './components/Sidebar';
import MessageBubble from './components/MessageBubble';
import ImageUpload from './components/ImageUpload';
import ActionButtons from './components/ActionButtons';
import Login from './pages/Login';
import Register from './pages/Register';
import { chatService } from './services/api';

function App() {
    // Auth State
    const [user, setUser] = useState(null);
    const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'

    // Chat State
    const [sessionId, setSessionId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentImage, setCurrentImage] = useState(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [classification, setClassification] = useState(null);
    const [history, setHistory] = useState([]);

    // Autoscalling textarea
    const textareaRef = useRef(null);
    const messagesEndRef = useRef(null);

    // Persist Login
    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
    }, []);

    // Initialize chat when user logs in
    useEffect(() => {
        if (user) {
            refreshHistory();
        }
    }, [user]);

    // Refresh history and load latest if available
    const refreshHistory = async () => {
        if (user) {
            try {
                const sessions = await chatService.getHistory(user.id);
                // Format dates
                const formatted = sessions.map(s => ({
                    ...s,
                    time: new Date(s.updated_at).toLocaleDateString()
                }));
                setHistory(formatted);

                // Load latest session if exists and no session currently active (or first load)
                if (formatted.length > 0 && !sessionId) {
                    handleLoadSession(formatted[0]); // formatted[0] is latest due to SQL DESC order
                } else if (formatted.length === 0 && !sessionId) {
                    // Only start new chat if absolutely no history
                    startNewChat();
                }
            } catch (e) {
                console.error("Failed to load history", e);
            }
        }
    };

    // Scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    const handleLogin = (userData) => {
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
    };

    const handleLogout = () => {
        setUser(null);
        localStorage.removeItem('user');
        localStorage.removeItem('sessionId');
    };

    const startNewChat = async () => {
        setIsLoading(true);
        try {
            const userId = user ? user.id : null;
            const data = await chatService.startChat(userId);
            setSessionId(data.session_id);
            setMessages([{
                role: 'assistant',
                text: data.message,
                timestamp: new Date().toLocaleTimeString()
            }]);
            setCurrentImage(null);
            setClassification(null);
        } catch (error) {
            console.error('Failed to start chat:', error);
            setMessages([{
                role: 'assistant',
                text: '❌ Failed to connect to server. Please ensure the backend is running.',
                timestamp: new Date().toLocaleTimeString()
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLoadSession = async (session) => {
        setIsLoading(true);
        setSessionId(session.id);
        setIsSidebarOpen(false); // Close mobile sidebar

        try {
            const msgs = await chatService.loadSession(session.id);
            // Map DB messages to UI messages
            const uiMessages = msgs.map(m => ({
                role: m.role,
                text: m.content,
                timestamp: new Date(m.timestamp).toLocaleTimeString(),
                image: m.image_path ? m.image_path : null // If you saved images
            }));
            setMessages(uiMessages);
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteSession = async (session) => {
        if (!confirm('Are you sure you want to delete this chat?')) return;
        try {
            await chatService.deleteSession(session.id);
            setHistory(prev => prev.filter(s => s.id !== session.id));
            if (sessionId === session.id) startNewChat();
        } catch (e) {
            console.error(e);
        }
    };

    const handleShareSession = async (session) => {
        try {
            const result = await chatService.shareSession(session.id);
            navigator.clipboard.writeText(result.text);
            alert('Conversation copied to clipboard!');
        } catch (e) {
            alert('Failed to share');
        }
    };

    const handleSendMessage = async (e) => {
        e?.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';

        // Add user message
        const newMessages = [...messages, {
            role: 'user',
            text: userMessage,
            timestamp: new Date().toLocaleTimeString()
        }];
        setMessages(newMessages);
        setIsLoading(true);

        try {
            const response = await chatService.sendMessage(sessionId, userMessage);

            const botMessage = {
                role: 'assistant',
                timestamp: new Date().toLocaleTimeString()
            };

            if (response.type === 'image') {
                const blob = new Blob([response.image], { type: response.headers['content-type'] });
                botMessage.image = URL.createObjectURL(blob);
                botMessage.downloadable = true;

                // Add success text if header exists
                if (response.headers['x-message']) {
                    let msg = response.headers['x-message'];
                    try { msg = decodeURIComponent(msg); } catch (e) { }

                    newMessages.push({
                        role: 'assistant',
                        text: msg,
                        timestamp: new Date().toLocaleTimeString()
                    });
                }
            } else {
                botMessage.text = response.message;
            }

            setMessages([...newMessages, botMessage]);
        } catch (error) {
            console.error('Failed to send message:', error);
            setMessages([...newMessages, {
                role: 'assistant',
                text: '❌ Sorry, I encountered an error. Please try again.',
                timestamp: new Date().toLocaleTimeString()
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileUpload = async (file) => {
        if (!sessionId || isLoading) return;

        const imageUrl = URL.createObjectURL(file);
        setCurrentImage(imageUrl);

        // Add upload message
        const uploadMsg = {
            role: 'user',
            image: imageUrl,
            timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, uploadMsg]);
        setIsLoading(true);

        try {
            const response = await chatService.uploadImage(sessionId, file);
            setClassification(response.probabilities);
            setMessages(prev => [...prev, {
                role: 'assistant',
                text: response.message,
                classification: response.probabilities,
                timestamp: new Date().toLocaleTimeString()
            }]);
        } catch (error) {
            console.error('Failed to upload:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                text: '❌ Failed to upload image. Please try again.',
                timestamp: new Date().toLocaleTimeString()
            }]);
            setCurrentImage(null);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAction = (actionId) => {
        const actionMap = {
            caption: 'Describe this image',
            ocr: 'Extract text',
            recolor: 'Recolor',
            mask: 'Create mask'
        };
        setInputValue(actionMap[actionId]);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Auth Screen
    if (!user) {
        return authMode === 'login'
            ? <Login onLogin={handleLogin} onSwitchToRegister={() => setAuthMode('register')} />
            : <Register onRegister={handleLogin} onSwitchToLogin={() => setAuthMode('login')} />;
    }

    return (
        <div className="flex h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200 overflow-hidden">
            <Sidebar
                isOpen={isSidebarOpen}
                onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
                onNewChat={startNewChat}
                sessions={history}
                currentSession={{ id: sessionId }}
                onSelectSession={handleLoadSession}
                onDelete={handleDeleteSession}
                onShare={handleShareSession}
            >
                <div className="mt-auto pt-4 border-t border-gray-700">
                    <div className="flex items-center gap-3 px-2 mb-2">
                        <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white font-bold">
                            {user.username[0].toUpperCase()}
                        </div>
                        <span className="text-sm font-medium dark:text-gray-200">{user.username}</span>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-2 py-2 text-sm text-red-400 hover:text-red-300 transition-colors"
                    >
                        <LogOut className="w-4 h-4" />
                        Log out
                    </button>
                </div>
            </Sidebar>

            <main className="flex-1 flex flex-col relative w-full h-full">
                {/* Mobile Header */}
                <div className="lg:hidden p-4 border-b border-gray-200 dark:border-gray-800 flex items-center bg-white dark:bg-gray-900 z-10">
                    <button onClick={() => setIsSidebarOpen(true)} className="p-2 -ml-2">
                        <Menu className="w-6 h-6 text-gray-600 dark:text-gray-300" />
                    </button>
                    <span className="font-semibold ml-2 text-gray-800 dark:text-white">T-Vision AI</span>
                </div>

                {/* Chat Area */}
                <div className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 space-y-6">
                    <div className="max-w-3xl mx-auto flex flex-col min-h-full">

                        {/* Empty State / Image Upload */}
                        {messages.length <= 1 && !currentImage && (
                            <div className="flex-1 flex flex-col items-center justify-center mb-8 animate-fade-in">
                                <div className="mb-8 text-center">
                                    <div className="w-16 h-16 bg-gradient-to-br from-primary to-accent rounded-2xl mx-auto mb-4 flex items-center justify-center shadow-lg shadow-primary/20">
                                        <img src="/logo.svg" alt="Logo" className="w-10 h-10 invert brightness-0" />
                                    </div>
                                    <h2 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent mb-2">
                                        How can I help you, {user.username}?
                                    </h2>
                                </div>
                                <ImageUpload onUpload={handleFileUpload} />
                            </div>
                        )}

                        {/* Messages */}
                        <div className="flex-1 space-y-6 pb-4">
                            {messages.map((msg, index) => (
                                <MessageBubble key={index} message={msg} />
                            ))}

                            {isLoading && (
                                <div className="flex items-center gap-2 text-gray-400 ml-12 animate-pulse">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span className="text-sm">Thinking...</span>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                    </div>
                </div>

                {/* Input Area */}
                <div className="p-4 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
                    <div className="max-w-3xl mx-auto">
                        {/* Recommended Actions */}
                        {currentImage && !isLoading && (
                            <div className="animate-fade-in">
                                <ActionButtons onAction={handleAction} disabled={isLoading} />
                            </div>
                        )}

                        {/* Input Box */}
                        <div className="relative flex items-end gap-2 bg-gray-100 dark:bg-gray-800 rounded-2xl p-2 border border-transparent focus-within:border-gray-300 dark:focus-within:border-gray-700 transition-all shadow-sm">
                            <textarea
                                ref={textareaRef}
                                value={inputValue}
                                onChange={(e) => {
                                    setInputValue(e.target.value);
                                    e.target.style.height = 'auto';
                                    e.target.style.height = e.target.scrollHeight + 'px';
                                }}
                                onKeyDown={handleKeyDown}
                                placeholder="Message T-Vision AI..."
                                className="flex-1 bg-transparent border-none focus:ring-0 resize-none max-h-48 py-3 px-3 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
                                rows={1}
                                disabled={isLoading}
                            />

                            {/* Persistent Upload Button */}
                            <label className={`p-3 rounded-xl transition-all cursor-pointer ${isLoading
                                ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                                : 'hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400'
                                }`}>
                                <input
                                    type="file"
                                    className="hidden"
                                    accept="image/*"
                                    disabled={isLoading}
                                    onChange={(e) => {
                                        if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
                                    }}
                                />
                                <div className="w-5 h-5 flex items-center justify-center">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" /></svg>
                                </div>
                            </label>
                            <button
                                onClick={handleSendMessage}
                                disabled={!inputValue.trim() || isLoading}
                                className={`p-3 rounded-xl transition-all ${inputValue.trim() && !isLoading
                                    ? 'bg-primary hover:bg-primary-dark text-white shadow-md'
                                    : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                                    }`}
                            >
                                <Send className="w-5 h-5" />
                            </button>
                        </div>
                        <p className="text-center text-xs text-gray-400 dark:text-gray-600 mt-2">
                            T-Vision AI can make mistakes. Consider checking important information.
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default App;
