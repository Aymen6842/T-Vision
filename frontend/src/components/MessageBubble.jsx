import ReactMarkdown from 'react-markdown';
import { User, Bot, Download } from 'lucide-react';

export default function MessageBubble({ message }) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
            {/* Avatar */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isUser ? 'bg-blue-500' : 'bg-gradient-to-br from-primary to-accent'
                }`}>
                {isUser ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
            </div>

            {/* Message Content */}
            <div className={`flex flex-col gap-2 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
                {/* Text */}
                {message.text && (
                    <div className={`px-4 py-3 shadow-sm ${isUser
                        ? 'bg-blue-600 text-white rounded-2xl rounded-br-none'
                        : 'bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-gray-800 dark:text-gray-100 rounded-2xl rounded-bl-none'
                        }`}>
                        <ReactMarkdown
                            components={{
                                p: ({ node, ...props }) => <p className="mb-2 last:mb-0 leading-relaxed" {...props} />,
                                ul: ({ node, ...props }) => <ul className="list-disc ml-4 mb-2 space-y-1" {...props} />,
                                ol: ({ node, ...props }) => <ol className="list-decimal ml-4 mb-2 space-y-1" {...props} />,
                                li: ({ node, ...props }) => <li className="" {...props} />,
                                code: ({ node, inline, className, children, ...props }) => {
                                    return inline ? (
                                        <code className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-sm font-mono" {...props}>
                                            {children}
                                        </code>
                                    ) : (
                                        <pre className="my-2 p-3 rounded-lg bg-gray-100 dark:bg-gray-900 overflow-x-auto whitespace-pre-wrap break-words text-sm font-mono border border-gray-200 dark:border-gray-700">
                                            <code className={className} {...props}>
                                                {children}
                                            </code>
                                        </pre>
                                    );
                                }
                            }}
                            className="text-sm md:text-base break-words"
                        >
                            {message.text}
                        </ReactMarkdown>
                    </div>
                )}

                {/* Image */}
                {message.image && (
                    <div className="rounded-lg overflow-hidden shadow-lg max-w-md border border-gray-200 dark:border-gray-700">
                        <img
                            src={message.image}
                            alt="Uploaded"
                            className="w-full h-auto"
                        />
                        {message.downloadable && (
                            <div className="bg-gray-50 dark:bg-gray-800 px-3 py-2 flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
                                <span className="text-sm text-gray-600 dark:text-gray-400 font-medium">Result image</span>
                                <button
                                    onClick={() => {
                                        const a = document.createElement('a');
                                        a.href = message.image;
                                        a.download = 'tvision-result.png';
                                        a.click();
                                    }}
                                    className="text-primary hover:text-primary-dark flex items-center gap-1.5 text-sm font-semibold transition-colors"
                                >
                                    <Download className="w-4 h-4" />
                                    Download
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* Classification - Moved outside text bubble */}
                {message.classification && (
                    <div className="flex flex-wrap gap-1.5 ml-1">
                        {Object.entries(message.classification).map(([key, value]) => (
                            <span
                                key={key}
                                className="px-2 py-0.5 text-[10px] uppercase tracking-wide font-semibold rounded-md bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-700"
                            >
                                {key.replace('is_', '')}: {(value * 100).toFixed(0)}%
                            </span>
                        ))}
                    </div>
                )}

                {/* Timestamp */}
                <span className="text-xs text-gray-400 px-2">
                    {message.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>
        </div >
    );
}
