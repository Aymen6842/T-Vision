import { MessageSquare, FileText, Palette, Scissors } from 'lucide-react';

export default function ActionButtons({ onAction, disabled }) {
    const actions = [
        { id: 'caption', label: 'Caption', icon: MessageSquare, color: 'blue' },
        { id: 'ocr', label: 'OCR', icon: FileText, color: 'green' },
        { id: 'recolor', label: 'Recolor', icon: Palette, color: 'purple' },
        { id: 'mask', label: 'Mask', icon: Scissors, color: 'orange' },
    ];

    return (
        <div className="flex flex-wrap gap-2 mb-4">
            {actions.map((action) => (
                <button
                    key={action.id}
                    onClick={() => !action.comingSoon && onAction(action.id)}
                    disabled={disabled || action.comingSoon}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${action.comingSoon
                        ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                        : disabled
                            ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                            : `bg-${action.color}-50 dark:bg-${action.color}-900/20 text-${action.color}-600 dark:text-${action.color}-400 hover:bg-${action.color}-100 dark:hover:bg-${action.color}-900/30`
                        }`}
                >
                    <action.icon className="w-4 h-4" />
                    {action.label}
                    {action.comingSoon && <span className="text-xs">(Soon)</span>}
                </button>
            ))}
        </div>
    );
}
