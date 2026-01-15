interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
}

export default function LoadingSpinner({ size = 'md', className = '', text }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  return (
    <div className={`flex flex-col justify-center items-center ${className}`}>
      <div className={`animate-spin rounded-full border-2 border-gray-200 dark:border-gray-700 border-t-blue-600 dark:border-t-blue-400 ${sizeClasses[size]}`}></div>
      {text && (
        <p className="mt-3 text-sm text-gray-600 dark:text-gray-400 font-medium">
          {text}
        </p>
      )}
    </div>
  );
}