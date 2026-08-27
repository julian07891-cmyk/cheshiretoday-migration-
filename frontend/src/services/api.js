import axios from 'axios';
import { getApiUrl } from "../utils/api";
import { buildNewsletterSignupPayload } from "../constants/newsletterSignup";

const API_BASE_URL = getApiUrl();
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
      const data = response.data;
      const articles = Array.isArray(data) ? data : (data?.articles || []);
      const searchLower = query.toLowerCase();
      
      return articles.filter(article => 
        article.title?.toLowerCase().includes(searchLower) ||
        article.content?.toLowerCase().includes(searchLower) ||
        article.category?.toLowerCase().includes(searchLower)
      );
    } catch (error) {
      console.error('Error searching articles:', error);
      throw error;
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
  async subscribe(email, signupPlacement = 'website') {
    try {
      const response = await apiClient.post(
        '/subscribe',
        buildNewsletterSignupPayload(email, signupPlacement),
      );
      return response.data;
    } catch (error) {
      console.error('Error subscribing to newsletter:', error);
      throw error;
    }
  },
};

export default articleService;
