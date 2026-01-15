interface MovieCardSkeletonProps {
  className?: string;
}

export default function MovieCardSkeleton({ className = '' }: MovieCardSkeletonProps) {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700 ${className}`}>
      <div className="animate-pulse">
        <div className="aspect-[2/3] bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600"></div>
        
        <div className="p-4 space-y-3">
          <div className="space-y-2">
            <div className="h-4 bg-gradient-to-r from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 rounded-md"></div>
            <div className="h-4 bg-gradient-to-r from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 rounded-md w-3/4"></div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="h-3 bg-gradient-to-r from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 rounded-full w-12"></div>
            <div className="h-5 bg-gradient-to-r from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 rounded-full w-16"></div>
          </div>
          
          <div className="flex items-center space-x-1">
            <div className="h-4 w-4 bg-gradient-to-r from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 rounded"></div>
            <div className="h-3 bg-gradient-to-r from-gray-200 to-gray-300 dark:from-gray-700 dark:to-gray-600 rounded w-8"></div>
          </div>
        </div>
      </div>
    </div>
  );
}