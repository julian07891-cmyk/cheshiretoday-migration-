import axios from 'axios';

// RUNTIME URL DETECTION
// Always determine the API URL at runtime based on the current page location
// This ensures the frontend works correctly on any domain (production, preview, or custom)
const getApiBaseUrl = () => {
  if (typeof window !== 'undefined') {
    // Check if we're on localhost (development mode)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      // In development, always use localhost:8001 for the local backend
      return 'http://localhost:8001';
    }
    // In production/preview, use the current origin (Ingress routes /api to backend)
    return window.location.origin;
  }
  // SSR fallback
  return process.env.REACT_APP_BACKEND_URL || '';
};

const API_BASE_URL = getApiBaseUrl();
const API_URL = `${API_BASE_URL}/api`;

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const articleService = {
  /**
   * Fetch all articles with optional filtering
   */
  async fetchArticles(category = null, skip = 0, limit = 20) {
    try {
      const params = { skip, limit };
      if (category && category !== 'all') {
        params.category = category;
      }
      const response = await apiClient.get('/articles', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching articles:', error);
      throw error;
    }
  },

  /**
   * Search articles by query
   */
  async searchArticles(query) {
    try {
      // Fetch all articles and filter client-side for now
      // In production, you'd want a dedicated search endpoint
      const response = await apiClient.get('/articles', { params: { limit: 100 } });
      const articles = response.data;
      const searchLower = query.toLowerCase();
      
      return articles.filter(article => 
        article.title?.toLowerCase().includes(searchLower) ||
        article.content?.toLowerCase().includes(searchLower) ||
        article.category?.toLowerCase().includes(searchLower)
      );
    } catch (error) {
      console.error('Error searching articles:', error);
      return [];
    }
  },

  /**
   * Fetch a single article by ID
   */
  async fetchArticle(articleId) {
    try {
      const response = await apiClient.get(`/articles/${articleId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching article:', error);
      throw error;
    }
  },

  /**
   * Generate new articles (admin function)
   */
  async generateArticles(count = 10, includeUkNews = true) {
    try {
      const response = await apiClient.post('/generate-articles', {
        count,
        include_uk_news: includeUkNews,
      });
      return response.data;
    } catch (error) {
      console.error('Error generating articles:', error);
      throw error;
    }
  },

  /**
   * Delete an article by ID (admin function)
   */
  async deleteArticle(articleId) {
    try {
      const response = await apiClient.delete(`/articles/${articleId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting article:', error);
      throw error;
    }
  },
};

export const newsletterService = {
  /**
   * Subscribe to newsletter
   */
  async subscribe(email) {
    try {
      const response = await apiClient.post('/subscribe', { email });
      return response.data;
    } catch (error) {
      console.error('Error subscribing to newsletter:', error);
      throw error;
    }
  },
};

export default articleService;