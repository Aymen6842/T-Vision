import { Moon, Sun, Plus, Menu, X } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

export default function Sidebar({ onNewChat, sessions = [], currentSession, onSelectSession, onDelete, onShare, isOpen, onToggle, children }) {
    const { theme, toggleTheme } = useTheme();

    return (
        <>
            {/* Mobile toggle */}
            <button
                onClick={onToggle}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white dark:bg-gray-800 shadow-lg"
            >
                {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>

            {/* Sidebar */}
            <aside
                className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-gray-50 dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 transition-transform duration-300 ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
                    }`}
            >
                <div className="flex flex-col h-full">
                    {/* Logo & Title */}
                    <div className="p-4 border-b border-gray-200 dark:border-gray-800">
                        <div className="flex items-center gap-3">
                            <img src="/logo.svg" alt="T-Vision AI" className="w-10 h-10" />
                            <div>
                                <h1 className="font-bold text-lg bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                                    T-Vision AI
                                </h1>
                                <p className="text-xs text-gray-500 dark:text-gray-400">by T-Code</p>
                            </div>
                        </div>
                    </div>

                    {/* New Chat Button */}
                    <div className="p-4">
                        <button
                            onClick={onNewChat}
                            className="w-full btn-primary flex items-center justify-center gap-2"
                        >
                            <Plus className="w-5 h-5" />
                            New Chat
                        </button>
                    </div>

                    {/* Chat History */}
                    <div className="flex-1 overflow-y-auto px-2">
                        <p className="px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                            Recent Chats
                        </p>
                        {sessions.length === 0 ? (
                            <p className="px-3 py-2 text-sm text-gray-400 dark:text-gray-600">
                                No previous chats
                            </p>
                        ) : (
                            <div className="space-y-1">
                                {sessions.map((session) => (
                                    <div key={session.id} className="group flex items-center gap-1 pr-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors">
                                        <button
                                            onClick={() => onSelectSession(session)}
                                            className={`flex-1 text-left px-3 py-2 rounded-lg ${currentSession?.id === session.id
                                                ? 'text-primary font-medium'
                                                : 'text-gray-700 dark:text-gray-300'
                                                }`}
                                        >
                                            <p className="text-sm truncate opacity-90">{session.title || 'Untitled'}</p>
                                            <p className="text-xs text-gray-400 mt-0.5">
                                                {session.time}
                                            </p>
                                        </button>

                                        {/* Action Buttons (visible on hover) */}
                                        <div className="hidden group-hover:flex items-center">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); onShare(session); }}
                                                className="p-1.5 text-gray-400 hover:text-blue-500 rounded-md"
                                                title="Share"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" /><polyline points="16 6 12 2 8 6" /><line x1="12" y1="2" x2="12" y2="15" /></svg>
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); onDelete(session); }}
                                                className="p-1.5 text-gray-400 hover:text-red-500 rounded-md"
                                                title="Delete"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /></svg>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Theme Toggle */}
                    <div className="p-4 border-t border-gray-200 dark:border-gray-800">
                        <button
                            onClick={toggleTheme}
                            className="w-full btn-secondary flex items-center justify-center gap-2"
                        >
                            {theme === 'light' ? (
                                <>
                                    <Moon className="w-5 h-5" />
                                    Dark Mode
                                </>
                            ) : (
                                <>
                                    <Sun className="w-5 h-5" />
                                    Light Mode
                                </>
                            )}
                        </button>
                    </div>

                    {/* Render children (like logout button) */}
                    {children}
                </div>
            </aside>

            {/* Overlay */}
            {isOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-30"
                    onClick={onToggle}
                />
            )}
        </>
    );
}
