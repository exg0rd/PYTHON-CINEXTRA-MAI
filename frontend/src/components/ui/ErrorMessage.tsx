interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

export default function ErrorMessage({ message, onRetry, className = '' }: ErrorMessageProps) {
  return (
    <div className={`bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-6 w-6 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-4 flex-1">
          <h3 className="text-sm font-semibold text-red-800 dark:text-red-200 mb-1">
            Something went wrong
          </h3>
          <p className="text-sm text-red-700 dark:text-red-300">
            {message}
          </p>
        </div>
        {onRetry && (
          <div className="ml-4">
            <button
              onClick={onRetry}
              className="bg-red-100 dark:bg-red-800 text-red-800 dark:text-red-200 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-200 dark:hover:bg-red-700 transition-colors duration-200 focus-ring"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}