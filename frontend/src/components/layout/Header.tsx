'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Settings } from 'lucide-react';
import UserProfile from '@/components/auth/UserProfile';
import AuthModal from '@/components/auth/AuthModal';

export default function Header() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

  const openLoginModal = () => {
    setAuthModalMode('login');
    setIsAuthModalOpen(true);
  };

  const openRegisterModal = () => {
    setAuthModalMode('register');
    setIsAuthModalOpen(true);
  };

  return (
    <>
      <header className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-md shadow-sm border-b border-gray-200/50 dark:border-gray-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Link 
                href="/" 
                className="text-xl font-bold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-200 focus-ring rounded-md px-2 py-1"
              >
                <span className="flex items-center space-x-2">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                  </svg>
                  <span>CiNEXTra v1.0</span>
                </span>
              </Link>
            </div>
            
            <div className="flex items-center space-x-8">
              <nav className="flex space-x-8">
                <Link 
                  href="/" 
                  className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-200 font-medium focus-ring rounded-md px-3 py-2"
                >
                  Фильмы
                </Link>
                
                {/* Admin Navigation */}
                {user?.is_admin && (
                  <Link 
                    href="/admin" 
                    className="flex items-center space-x-1 text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors duration-200 font-medium focus-ring rounded-md px-3 py-2"
                  >
                    <Settings className="w-4 h-4" />
                    <span>Админ</span>
                  </Link>
                )}
              </nav>

              {/* Authentication UI */}
              <div className="flex items-center space-x-4">
                {isLoading ? (
                  <div className="w-8 h-8 animate-pulse bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                ) : isAuthenticated ? (
                  <UserProfile />
                ) : (
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={openLoginModal}
                      className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-200 font-medium focus-ring rounded-md px-3 py-2"
                    >
                      Войти
                    </button>
                    <button
                      onClick={openRegisterModal}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      Регистрация
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialMode={authModalMode}
      />
    </>
  );
}