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
    console.log('ApiClient.request called:', { url, options });

    try {
      const response = await fetch(url, {
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        ...options,
      });

      console.log('Response received:', { status: response.status, ok: response.ok });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Response data:', data);

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

  // Analytics API Methods

  /**
   * 获取技术趋势分析
   */
  async getTechnologyTrends(days = 30) {
    console.log('ApiClient.getTechnologyTrends called with days:', days);
    const result = await this.request(`/analytics/trends?days=${days}`);
    console.log('ApiClient.getTechnologyTrends result:', result);
    return result;
  }

  /**
   * 获取作者活跃度分析
   */
  async getAuthorActivity(days = 30) {
    return await this.request(`/analytics/authors?days=${days}`);
  }

  /**
   * 获取发布模式分析
   */
  async getPublicationPatterns(days = 90) {
    return await this.request(`/analytics/publishing?days=${days}`);
  }

  /**
   * 获取综合分析报告
   */
  async getComprehensiveReport(days = 30) {
    return await this.request(`/analytics/report?days=${days}`);
  }

  /**
   * 提取文章标签
   */
  async extractTags(limit = null) {
    const params = limit ? `?limit=${limit}` : '';
    return await this.request(`/analytics/tags/extract${params}`);
  }

  /**
   * 获取标签趋势分析
   */
  async getTagTrends(days = 30) {
    return await this.request(`/analytics/tags/trends?days=${days}`);
  }

  /**
   * 评估内容质量
   */
  async evaluateContentQuality(limit = null) {
    const params = limit ? `?limit=${limit}` : '';
    return await this.request(`/analytics/quality/evaluate${params}`);
  }

  /**
   * 获取质量洞察报告
   */
  async getQualityInsights(minScore = 0.7) {
    return await this.request(`/analytics/quality/insights?min_score=${minScore}`);
  }
}

// 创建全局API客户端实例
const apiClient = new ApiClient();

// 导出供其他模块使用
window.apiClient = apiClient;
