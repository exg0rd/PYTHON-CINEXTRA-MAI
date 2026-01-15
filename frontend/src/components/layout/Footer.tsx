export default function Footer() {
  return (
    <footer className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-t border-gray-200/50 dark:border-gray-700/50 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="flex justify-center items-center space-x-2 mb-4">
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
            </svg>
            <span className="text-gray-600 dark:text-gray-400 font-medium">Online Cinema</span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            &copy; 2024 Online Cinema. All rights reserved.
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-600 mt-2">
            Discover and enjoy movies from around the world
          </p>
        </div>
      </div>
    </footer>
  );
}