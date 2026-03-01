import axios from 'axios';
import type {
  DecomposeRequest,
  DecomposeResponse,
  ClarifyRequest,
  ClarifyResponse,
} from '../types/task';

// Create axios instance
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 120000, // 2 minutes timeout for AI processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response:`, response.data);
    return response;
  },
  (error) => {
    console.error('[API] Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Task API - aligned with backend task_decomposer v2.0
 */
export const taskApi = {
  /**
   * Main decompose endpoint
   * POST /api/v2/decompose
   */
  decompose: async (data: DecomposeRequest): Promise<DecomposeResponse> => {
    try {
      const response = await api.post<DecomposeResponse>('/api/v2/decompose', data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '任务拆解失败，请检查网络或稍后重试'
        );
      }
      throw error;
    }
  },

  /**
   * Clarify questions endpoint
   * POST /api/v2/clarify
   */
  clarify: async (data: ClarifyRequest): Promise<ClarifyResponse> => {
    try {
      const response = await api.post<ClarifyResponse>('/api/v2/clarify', data);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '生成澄清问题失败'
        );
      }
      throw error;
    }
  },

  /**
   * Get user profile
   * GET /api/v2/profile/{user_id}
   */
  getUserProfile: async (userId: string): Promise<unknown> => {
    try {
      const response = await api.get(`/api/v2/profile/${userId}`);
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '获取用户画像失败'
        );
      }
      throw error;
    }
  },

  /**
   * Update user preferences
   * POST /api/v2/preferences
   */
  updatePreferences: async (
    userId: string,
    preferences: Record<string, unknown>
  ): Promise<{ status: string; message: string }> => {
    try {
      const response = await api.post('/api/v2/preferences', {
        user_id: userId,
        preferences,
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '更新用户偏好失败'
        );
      }
      throw error;
    }
  },

  /**
   * List available tools
   * GET /api/v2/tools
   */
  listTools: async (): Promise<{ tools: string[] }> => {
    try {
      const response = await api.get('/api/v2/tools');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '获取工具列表失败'
        );
      }
      throw error;
    }
  },

  /**
   * Health check
   * GET /health
   */
  healthCheck: async (): Promise<{ status: string; service: string }> => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '服务健康检查失败'
        );
      }
      throw error;
    }
  },
};

// Legacy API interfaces (for backward compatibility)
export interface AssessImpactTask {
  title: string;
  start_date: string;
  end_date: string;
}

export interface AssessImpactRequest {
  original_task: AssessImpactTask;
  updated_task: AssessImpactTask;
  parent_task: AssessImpactTask;
  change_type: 'move' | 'resize';
}

export interface AssessImpactResponse {
  impact_level: string;
  parent_adjustment_needed: boolean;
  suggestion: string;
  recommended_parent_end_date: string | null;
}

/**
 * Legacy assess impact endpoint
 * TODO: Implement this in backend
 */
export const assessImpact = async (data: AssessImpactRequest): Promise<AssessImpactResponse> => {
  const impactLevel = data.change_type === 'move' ? 'low' : 'medium';
  return {
    impact_level: impactLevel,
    parent_adjustment_needed: false,
    suggestion: '任务调整在合理范围内',
    recommended_parent_end_date: null,
  };
};
