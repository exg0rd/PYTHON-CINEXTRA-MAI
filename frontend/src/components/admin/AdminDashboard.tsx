'use client';

import React, { useState, useEffect } from 'react';
import { Users, Film, BarChart3, Settings, TrendingUp, Star, Upload } from 'lucide-react';
import { UserAnalyticsChart } from './UserAnalyticsChart';
import { MovieAnalyticsChart } from './MovieAnalyticsChart';
import { SystemMetricsPanel } from './SystemMetricsPanel';
import VideoUploadPanel from './VideoUploadPanel';

interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
}

interface AdminDashboardProps {
  user: User;
}

interface AnalyticsData {
  userAnalytics?: any;
  movieAnalytics?: any;
  systemMetrics?: any;
  moviesWithVideoStatus?: any[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ user }) => {
  const [analytics, setAnalytics] = useState<AnalyticsData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      if (!token) {
        throw new Error('No authentication token found');
      }

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Fetch all analytics data
      const [userResponse, movieResponse, systemResponse, moviesVideoResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/admin/analytics/users`, { headers }),
        fetch(`${API_BASE_URL}/api/admin/analytics/movies`, { headers }),
        fetch(`${API_BASE_URL}/api/admin/analytics/system`, { headers }),
        fetch(`${API_BASE_URL}/api/admin/movies/video-status?limit=500`, { headers })
      ]);

      if (!userResponse.ok || !movieResponse.ok || !systemResponse.ok || !moviesVideoResponse.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const [userAnalytics, movieAnalytics, systemMetrics, moviesVideoStatus] = await Promise.all([
        userResponse.json(),
        movieResponse.json(),
        systemResponse.json(),
        moviesVideoResponse.json()
      ]);

      setAnalytics({
        userAnalytics,
        movieAnalytics,
        systemMetrics,
        moviesWithVideoStatus: moviesVideoStatus.movies
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Загрузка аналитики...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">
          <BarChart3 className="mx-auto h-12 w-12" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Ошибка аналитики</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchAnalyticsData}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Повторить
        </button>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Обзор', icon: BarChart3 },
    { id: 'users', name: 'Пользователи', icon: Users },
    { id: 'analytics', name: 'Аналитика', icon: TrendingUp },
    { id: 'videos', name: 'Загрузка видео', icon: Upload },
    { id: 'system', name: 'Система', icon: Settings }
  ];

  return (
    <div className="space-y-6">
      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Всего пользователей</p>
              <p className="text-2xl font-semibold text-gray-900">
                {analytics.userAnalytics?.total_users || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Film className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Всего фильмов</p>
              <p className="text-2xl font-semibold text-gray-900">
                {analytics.systemMetrics?.database_stats?.total_movies || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Star className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Всего отзывов</p>
              <p className="text-2xl font-semibold text-gray-900">
                {analytics.systemMetrics?.database_stats?.total_reviews || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Новых за 7 дней</p>
              <p className="text-2xl font-semibold text-gray-900">
                {analytics.systemMetrics?.recent_activity?.new_users_last_7_days || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5 mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <UserAnalyticsChart data={analytics.userAnalytics} />
            <MovieAnalyticsChart data={analytics.movieAnalytics} />
          </div>
        )}

        {activeTab === 'users' && (
          <UserAnalyticsChart data={analytics.userAnalytics} detailed />
        )}

        {activeTab === 'analytics' && (
          <MovieAnalyticsChart data={analytics.movieAnalytics} detailed />
        )}

        {activeTab === 'videos' && (
          <VideoUploadPanel 
            movies={analytics.moviesWithVideoStatus || []} 
            onMoviesUpdate={fetchAnalyticsData}
          />
        )}

        {activeTab === 'system' && (
          <SystemMetricsPanel data={analytics.systemMetrics} />
        )}
      </div>
    </div>
  );
};