'use client';

import React from 'react';
import { Database, Activity, Clock, AlertCircle } from 'lucide-react';

interface SystemMetricsData {
  database_stats: {
    total_movies: number;
    total_reviews: number;
    total_users: number;
  };
  recent_activity: {
    reviews_last_7_days: number;
    new_users_last_7_days: number;
  };
  api_response_times: Record<string, number>;
  error_rates: Record<string, number>;
  active_sessions: number;
}

interface SystemMetricsPanelProps {
  data?: SystemMetricsData;
}

export const SystemMetricsPanel: React.FC<SystemMetricsPanelProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Системные метрики</h3>
        <div className="text-center py-8">
          <div className="text-gray-400">Нет системных данных</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Database Statistics */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-6">
          <Database className="h-6 w-6 text-blue-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Статистика базы данных</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {data.database_stats.total_movies.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Всего фильмов</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">
              {data.database_stats.total_reviews.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Всего отзывов</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">
              {data.database_stats.total_users.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Всего пользователей</div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-6">
          <Activity className="h-6 w-6 text-green-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Недавняя активность (за 7 дней)</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {data.recent_activity.reviews_last_7_days}
                </div>
                <div className="text-sm text-green-700">Новых отзывов</div>
              </div>
              <div className="text-green-600">
                <Activity className="h-8 w-8" />
              </div>
            </div>
          </div>
          
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {data.recent_activity.new_users_last_7_days}
                </div>
                <div className="text-sm text-blue-700">Новых пользователей</div>
              </div>
              <div className="text-blue-600">
                <Activity className="h-8 w-8" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center mb-6">
          <Clock className="h-6 w-6 text-orange-600 mr-3" />
          <h3 className="text-lg font-medium text-gray-900">Метрики производительности</h3>
        </div>
        
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Активные сессии</span>
              <span className="text-lg font-semibold text-gray-900">
                {data.active_sessions}
              </span>
            </div>
            <div className="text-xs text-gray-500">
              Текущие активные сессии пользователей
            </div>
          </div>

          {/* API Response Times */}
          {Object.keys(data.api_response_times).length > 0 && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm font-medium text-gray-700 mb-3">Время отклика API</div>
              <div className="space-y-2">
                {Object.entries(data.api_response_times).map(([endpoint, time]) => (
                  <div key={endpoint} className="flex justify-between items-center">
                    <span className="text-xs text-gray-600">{endpoint}</span>
                    <span className="text-xs font-medium text-gray-900">{time}мс</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Rates */}
          {Object.keys(data.error_rates).length > 0 && (
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center mb-3">
                <AlertCircle className="h-4 w-4 text-red-600 mr-2" />
                <span className="text-sm font-medium text-red-700">Частота ошибок</span>
              </div>
              <div className="space-y-2">
                {Object.entries(data.error_rates).map(([endpoint, rate]) => (
                  <div key={endpoint} className="flex justify-between items-center">
                    <span className="text-xs text-red-600">{endpoint}</span>
                    <span className="text-xs font-medium text-red-900">{rate}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Placeholder for when no performance data is available */}
          {Object.keys(data.api_response_times).length === 0 && 
           Object.keys(data.error_rates).length === 0 && (
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <Clock className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <div className="text-sm text-gray-500">
                Метрики производительности появятся здесь по мере сбора данных
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};