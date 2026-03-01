import React from 'react';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  suggestion?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title,
  message,
  suggestion,
  onConfirm,
  onCancel,
  isLoading = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden border border-gray-100 transform transition-all scale-100">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
          <h3 className="text-lg font-bold text-gray-900">{title}</h3>
        </div>

        {/* Body */}
        <div className="px-6 py-6 space-y-4">
          <p className="text-gray-700 leading-relaxed">
            {message}
          </p>
          
          {suggestion && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
              <div className="flex gap-2">
                <span className="text-blue-600 font-semibold shrink-0">AI 建议:</span>
                <p className="text-blue-800 text-sm leading-relaxed">{suggestion}</p>
              </div>
            </div>
          )}

          <div className="text-sm text-gray-500 italic border-l-2 border-gray-300 pl-3">
            注意：选择“确认”将自动同步更新所有相关的上级任务时间。
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-200 disabled:opacity-50 transition-colors"
          >
            取消 (不更改)
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 shadow-sm transition-all hover:shadow-md"
          >
            {isLoading ? '处理中...' : '确认更改'}
          </button>
        </div>
      </div>
    </div>
  );
};
