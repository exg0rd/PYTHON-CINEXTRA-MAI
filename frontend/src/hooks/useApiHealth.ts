import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface UseApiHealthState {
  isHealthy: boolean;
  loading: boolean;
  error: string | null;
}

interface UseApiHealthOptions {
  autoCheck?: boolean;
  intervalMs?: number;
}

export function useApiHealth(options: UseApiHealthOptions = {}) {
  const { autoCheck = true, intervalMs = 30000 } = options; // Check every 30 seconds by default
  
  const [state, setState] = useState<UseApiHealthState>({
    isHealthy: false,
    loading: false,
    error: null,
  });

  const checkHealth = async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      await apiClient.healthCheck();
      setState({ isHealthy: true, loading: false, error: null });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'API health check failed';
      setState({ isHealthy: false, loading: false, error: errorMessage });
    }
  };

  useEffect(() => {
    if (autoCheck) {
      // Initial check
      checkHealth();
      
      // Set up interval for periodic checks
      const intervalId = setInterval(checkHealth, intervalMs);
      
      return () => clearInterval(intervalId);
    }
  }, [autoCheck, intervalMs]);

  return {
    ...state,
    checkHealth,
  };
}