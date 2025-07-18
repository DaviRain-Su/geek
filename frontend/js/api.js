/**
 * API集成模块
 * 负责与后端API的所有通信
 */

class ApiClient {
  constructor(baseUrl = null) {
    // 自动检测API服务器地址
    this.baseUrl = baseUrl || 
                   window.API_BASE_URL || 
                   (window.location.hostname === 'localhost' ? 
                    "http://127.0.0.1:8000" : 
                    `${window.location.protocol}//${window.location.hostname}:8000`);
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5分钟缓存
  }

  /**
   * 通用API请求方法
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "API请求失败");
      }

      return data.data;
    } catch (error) {
      console.error(`API请求失败 [${endpoint}]:`, error);
      throw error;
    }
  }

  /**
   * 带缓存的GET请求
   */
  async cachedRequest(endpoint, cacheDuration = this.cacheTimeout) {
    const cacheKey = endpoint;
    const cached = this.cache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < cacheDuration) {
      return cached.data;
    }

    const data = await this.request(endpoint);

    this.cache.set(cacheKey, {
      data,
      timestamp: Date.now(),
    });

    return data;
  }

  /**
   * 获取文章列表
   */
  async getArticles(params = {}) {
    const searchParams = new URLSearchParams();

    if (params.account) searchParams.append("account", params.account);
    if (params.limit) searchParams.append("limit", params.limit);
    if (params.offset) searchParams.append("offset", params.offset);
    if (params.search) searchParams.append("search", params.search);

    const endpoint = `/articles${searchParams.toString() ? "?" + searchParams.toString() : ""}`;
    return await this.request(endpoint);
  }

  /**
   * 获取文章详情
   */
  async getArticle(id) {
    return await this.cachedRequest(`/articles/${id}`);
  }

  /**
   * 搜索文章
   */
  async searchArticles(query, limit = 20) {
    const searchParams = new URLSearchParams({
      search: query,
      limit: limit.toString(),
    });

    return await this.request(`/articles?${searchParams.toString()}`);
  }

  /**
   * 获取统计信息
   */
  async getStats() {
    return await this.cachedRequest("/stats", 10 * 60 * 1000); // 10分钟缓存
  }

  /**
   * 获取账号列表
   */
  async getAccounts() {
    return await this.cachedRequest("/accounts", 30 * 60 * 1000); // 30分钟缓存
  }

  /**
   * 健康检查
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * 获取热门作者
   */
  async getTopAuthors(limit = 10) {
    const stats = await this.getStats();
    return stats.top_authors.slice(0, limit);
  }

  /**
   * 获取热门账号
   */
  async getTopAccounts(limit = 10) {
    const stats = await this.getStats();
    return stats.top_accounts.slice(0, limit);
  }

  /**
   * 获取最新文章
   */
  async getRecentArticles(limit = 6) {
    const response = await this.getArticles({ limit });
    return response.articles;
  }
}

// 创建全局API客户端实例
const apiClient = new ApiClient();

// 导出供其他模块使用
window.apiClient = apiClient;
