'use client';

import React from 'react';
import { Users, UserPlus, Shield } from 'lucide-react';

interface UserAnalyticsData {
  total_users: number;
  new_users_period: number;
  new_registrations_today: number;
  admin_users: number;
  active_users_today: number;
  average_session_duration: number;
}

interface UserAnalyticsChartProps {
  data?: UserAnalyticsData;
  detailed?: boolean;
}

export const UserAnalyticsChart: React.FC<UserAnalyticsChartProps> = ({ 
  data, 
  detailed = false 
}) => {
  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Аналитика пользователей</h3>
        <div className="text-center py-8">
          <div className="text-gray-400">Нет данных о пользователях</div>
        </div>
      </div>
    );
  }

  const stats = [
    {
      name: 'Всего пользователей',
      value: data.total_users,
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      name: 'Новых сегодня',
      value: data.new_registrations_today,
      icon: UserPlus,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      name: 'Администраторов',
      value: data.admin_users,
      icon: Shield,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">Аналитика пользователей</h3>
      
      <div className="space-y-6">
        {/* Stats Grid */}
        <div className={`grid ${detailed ? 'grid-cols-1 sm:grid-cols-3' : 'grid-cols-3'} gap-4`}>
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.name} className="text-center">
                <div className={`inline-flex items-center justify-center w-12 h-12 ${stat.bgColor} rounded-lg mb-3`}>
                  <Icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div className="text-2xl font-semibold text-gray-900">{stat.value}</div>
                <div className="text-sm text-gray-500">{stat.name}</div>
              </div>
            );
          })}
        </div>

        {detailed && (
          <>
            {/* Additional Details */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Активность пользователей</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Активных сегодня</span>
                  <span className="text-sm font-medium text-gray-900">
                    {data.active_users_today}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Средняя длительность сессии</span>
                  <span className="text-sm font-medium text-gray-900">
                    {data.average_session_duration.toFixed(1)} мин
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Новых пользователей (за период)</span>
                  <span className="text-sm font-medium text-gray-900">
                    {data.new_users_period}
                  </span>
                </div>
              </div>
            </div>

            {/* User Growth Chart Placeholder */}
            <div className="border-t pt-6">
              <h4 className="text-md font-medium text-gray-900 mb-4">Рост пользователей</h4>
              <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Users className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500">График роста пользователей</p>
                  <p className="text-sm text-gray-400">Требуется интеграция с библиотекой графиков</p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};