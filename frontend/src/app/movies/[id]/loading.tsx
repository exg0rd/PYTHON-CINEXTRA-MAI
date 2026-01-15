export default function Loading() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="animate-pulse">
        {/* Back navigation skeleton */}
        <div className="mb-6">
          <div className="h-6 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>

        {/* Movie detail skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Movie poster skeleton */}
          <div className="lg:col-span-1">
            <div className="aspect-[2/3] bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          </div>

          {/* Movie information skeleton */}
          <div className="lg:col-span-2">
            <div className="h-10 w-3/4 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
            
            <div className="flex items-center space-x-4 mb-6">
              <div className="h-6 w-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-6 w-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-6 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
              <div className="h-6 w-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>

            <div className="mb-6">
              <div className="h-6 w-24 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
              <div className="space-y-2">
                <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 w-3/4 bg-gray-200 dark:bg-gray-700 rounded"></div>
              </div>
            </div>

            <div className="mb-6">
              <div className="h-6 w-20 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
              <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}