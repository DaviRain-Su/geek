/**
 * 主要应用逻辑
 * 负责页面交互、数据展示和用户界面
 */

class GeekDailyApp {
    constructor() {
        console.log('GeekDailyApp constructor called');
        this.currentPage = 1;
        this.articlesPerPage = 20;
        this.currentFilters = {
            account: '',
            author: '',
            search: ''
        };
        
        this.init();
    }

    /**
     * 初始化应用
     */
    async init() {
        this.setupEventListeners();
        await this.checkAPIConnection();
        await this.loadInitialData();
    }

    /**
     * 检查API连接
     */
    async checkAPIConnection() {
        const isHealthy = await apiClient.healthCheck();
        if (!isHealthy) {
            this.showError('无法连接到API服务器，请确保后端服务正在运行');
            return false;
        }
        return true;
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 导航切换
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = link.getAttribute('data-section');
                this.showSection(section);
            });
        });

        // 搜索功能
        const searchInput = document.getElementById('search-input');
        const searchBtn = document.getElementById('search-btn');
        
        searchBtn.addEventListener('click', () => this.performSearch());
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // 过滤器
        document.getElementById('account-filter').addEventListener('change', (e) => {
            this.currentFilters.account = e.target.value;
            this.loadArticles(1);
        });

        document.getElementById('author-filter').addEventListener('change', (e) => {
            this.currentFilters.author = e.target.value;
            this.loadArticles(1);
        });

        // 模态框关闭
        document.getElementById('modal-close').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('article-modal').addEventListener('click', (e) => {
            if (e.target.id === 'article-modal') {
                this.closeModal();
            }
        });

        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });

        // Analytics事件监听器
        const refreshAnalyticsBtn = document.getElementById('refresh-analytics');
        const analyticsDaysSelect = document.getElementById('analytics-days');
        
        if (refreshAnalyticsBtn) {
            refreshAnalyticsBtn.addEventListener('click', () => {
                this.loadAnalyticsData();
            });
        }
        
        if (analyticsDaysSelect) {
            analyticsDaysSelect.addEventListener('change', () => {
                this.loadAnalyticsData();
            });
        }
    }

    /**
     * 显示指定部分
     */
    showSection(sectionName) {
        // 隐藏所有部分
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        // 移除所有导航活动状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        // 显示指定部分
        const targetSection = document.getElementById(sectionName);
        const targetNavLink = document.querySelector(`[data-section="${sectionName}"]`);
        
        console.log('Showing section:', sectionName, { targetSection, targetNavLink });
        
        if (targetSection) {
            targetSection.classList.add('active');
            console.log('Section activated:', sectionName);
        } else {
            console.error('Target section not found:', sectionName);
        }
        
        if (targetNavLink) {
            targetNavLink.classList.add('active');
        }

        // 根据部分加载相应数据
        switch (sectionName) {
            case 'home':
                this.loadHomeData();
                break;
            case 'articles':
                this.loadArticles(1);
                this.loadFilters();
                break;
            case 'stats':
                this.loadStatsData();
                break;
            case 'analytics':
                console.log('Switching to analytics section');
                // 添加小延迟确保DOM完全渲染
                setTimeout(() => {
                    this.loadAnalyticsData();
                }, 100);
                break;
        }
    }

    /**
     * 加载初始数据
     */
    async loadInitialData() {
        try {
            await this.loadHomeData();
        } catch (error) {
            console.error('加载初始数据失败:', error);
            this.showError('加载数据失败，请刷新页面重试');
        }
    }

    /**
     * 加载首页数据
     */
    async loadHomeData() {
        try {
            // 加载统计信息
            const stats = await apiClient.getStats();
            
            document.getElementById('total-articles').textContent = 
                this.formatNumber(stats.overview.total_articles);
            document.getElementById('total-authors').textContent = 
                this.formatNumber(stats.overview.total_authors);
            document.getElementById('total-accounts').textContent = 
                this.formatNumber(stats.overview.total_accounts);

            // 加载最新文章
            const recentArticles = await apiClient.getRecentArticles(6);
            this.renderRecentArticles(recentArticles);

        } catch (error) {
            console.error('加载首页数据失败:', error);
        }
    }

    /**
     * 渲染最新文章
     */
    renderRecentArticles(articles) {
        const container = document.getElementById('recent-articles-list');
        
        if (!articles || articles.length === 0) {
            container.innerHTML = '<p class="text-center">暂无文章数据</p>';
            return;
        }

        container.innerHTML = articles.map(article => `
            <div class="article-card" onclick="app.showArticleDetail(${article.id})">
                <h4 class="article-title">${this.escapeHtml(article.title)}</h4>
                <div class="article-meta">
                    <span><i class="fas fa-user"></i> ${this.escapeHtml(article.author)}</span>
                    <span><i class="fas fa-building"></i> ${this.escapeHtml(article.account_name)}</span>
                    ${article.publish_time ? `<span><i class="fas fa-calendar"></i> ${this.formatDate(article.publish_time)}</span>` : ''}
                </div>
                <p class="article-preview">${this.escapeHtml(article.content_preview || '暂无预览')}</p>
            </div>
        `).join('');
    }

    /**
     * 加载文章列表
     */
    async loadArticles(page = 1) {
        this.showLoading(true);
        this.currentPage = page;

        try {
            const params = {
                limit: this.articlesPerPage,
                offset: (page - 1) * this.articlesPerPage
            };

            if (this.currentFilters.account) {
                params.account = this.currentFilters.account;
            }

            if (this.currentFilters.search) {
                params.search = this.currentFilters.search;
            }

            const response = await apiClient.getArticles(params);
            
            this.renderArticlesList(response.articles);
            this.renderPagination(response.pagination);

        } catch (error) {
            console.error('加载文章列表失败:', error);
            this.showError('加载文章列表失败');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * 渲染文章列表
     */
    renderArticlesList(articles) {
        const container = document.getElementById('articles-list');
        
        if (!articles || articles.length === 0) {
            container.innerHTML = `
                <div class="text-center" style="padding: 3rem;">
                    <i class="fas fa-search" style="font-size: 3rem; color: var(--text-muted); margin-bottom: 1rem;"></i>
                    <p style="color: var(--text-secondary); font-size: 1.125rem;">没有找到匹配的文章</p>
                </div>
            `;
            return;
        }

        container.innerHTML = articles.map(article => `
            <div class="article-item" onclick="app.showArticleDetail(${article.id})">
                <h3 class="article-title">${this.escapeHtml(article.title)}</h3>
                <div class="article-meta">
                    <span><i class="fas fa-user"></i> ${this.escapeHtml(article.author)}</span>
                    <span><i class="fas fa-building"></i> ${this.escapeHtml(article.account_name)}</span>
                    ${article.publish_time ? `<span><i class="fas fa-calendar"></i> ${this.formatDate(article.publish_time)}</span>` : ''}
                    <span><i class="fas fa-eye"></i> ${this.formatNumber(article.read_count || 0)} 阅读</span>
                </div>
                <p class="article-preview">${this.escapeHtml(article.content_preview || '暂无预览')}</p>
            </div>
        `).join('');
    }

    /**
     * 渲染分页
     */
    renderPagination(pagination) {
        const container = document.getElementById('pagination');
        const currentPage = Math.floor(pagination.offset / pagination.limit) + 1;
        const totalPages = Math.ceil(pagination.total / pagination.limit);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let paginationHTML = '';
        
        // 上一页按钮
        paginationHTML += `
            <button ${currentPage === 1 ? 'disabled' : ''} 
                    onclick="app.loadArticles(${currentPage - 1})">
                <i class="fas fa-chevron-left"></i> 上一页
            </button>
        `;

        // 页码按钮
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            paginationHTML += `<button onclick="app.loadArticles(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += `<span>...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button ${i === currentPage ? 'class="active"' : ''} 
                        onclick="app.loadArticles(${i})">
                    ${i}
                </button>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHTML += `<span>...</span>`;
            }
            paginationHTML += `<button onclick="app.loadArticles(${totalPages})">${totalPages}</button>`;
        }

        // 下一页按钮
        paginationHTML += `
            <button ${currentPage === totalPages ? 'disabled' : ''} 
                    onclick="app.loadArticles(${currentPage + 1})">
                下一页 <i class="fas fa-chevron-right"></i>
            </button>
        `;

        container.innerHTML = paginationHTML;
    }

    /**
     * 加载过滤器选项
     */
    async loadFilters() {
        try {
            const accounts = await apiClient.getAccounts();
            const stats = await apiClient.getStats();

            // 填充账号过滤器
            const accountFilter = document.getElementById('account-filter');
            accountFilter.innerHTML = '<option value="">所有账号</option>' +
                accounts.accounts.map(account => 
                    `<option value="${this.escapeHtml(account.name)}">${this.escapeHtml(account.name)} (${account.article_count})</option>`
                ).join('');

            // 填充作者过滤器
            const authorFilter = document.getElementById('author-filter');
            authorFilter.innerHTML = '<option value="">所有作者</option>' +
                stats.top_authors.map(author => 
                    `<option value="${this.escapeHtml(author.name)}">${this.escapeHtml(author.name)} (${author.count})</option>`
                ).join('');

        } catch (error) {
            console.error('加载过滤器失败:', error);
        }
    }

    /**
     * 执行搜索
     */
    async performSearch() {
        const searchInput = document.getElementById('search-input');
        const query = searchInput.value.trim();
        
        if (!query) {
            this.showError('请输入搜索关键词');
            return;
        }

        this.currentFilters.search = query;
        this.showSection('articles');
        await this.loadArticles(1);
    }

    /**
     * 显示文章详情
     */
    async showArticleDetail(articleId) {
        try {
            const article = await apiClient.getArticle(articleId);
            
            document.getElementById('modal-title').textContent = article.title;
            document.getElementById('modal-author').textContent = `作者: ${article.author}`;
            document.getElementById('modal-account').textContent = `账号: ${article.account_name}`;
            document.getElementById('modal-time').textContent = 
                article.publish_time ? `发布时间: ${this.formatDate(article.publish_time)}` : '发布时间: 未知';
            document.getElementById('modal-content').innerHTML = 
                this.formatContent(article.content || '暂无内容');
            document.getElementById('modal-url').href = article.url;

            document.getElementById('article-modal').classList.remove('hidden');
            document.body.style.overflow = 'hidden';

        } catch (error) {
            console.error('加载文章详情失败:', error);
            this.showError('加载文章详情失败');
        }
    }

    /**
     * 关闭模态框
     */
    closeModal() {
        document.getElementById('article-modal').classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    /**
     * 加载统计数据
     */
    async loadStatsData() {
        try {
            const stats = await apiClient.getStats();
            
            // 渲染概览统计
            this.renderStatsOverview(stats.overview);
            
            // 渲染热门账号
            this.renderTopAccounts(stats.top_accounts);
            
            // 渲染热门作者
            this.renderTopAuthors(stats.top_authors);

        } catch (error) {
            console.error('加载统计数据失败:', error);
            this.showError('加载统计数据失败');
        }
    }

    /**
     * 渲染统计概览
     */
    renderStatsOverview(overview) {
        const container = document.getElementById('stats-overview');
        
        container.innerHTML = `
            <div class="overview-card">
                <h4>${this.formatNumber(overview.total_articles)}</h4>
                <p>总文章数</p>
            </div>
            <div class="overview-card">
                <h4>${this.formatNumber(overview.total_accounts)}</h4>
                <p>账号数量</p>
            </div>
            <div class="overview-card">
                <h4>${this.formatNumber(overview.total_authors)}</h4>
                <p>作者数量</p>
            </div>
        `;
    }

    /**
     * 渲染热门账号
     */
    renderTopAccounts(accounts) {
        const container = document.getElementById('top-accounts-list');
        
        container.innerHTML = accounts.map((account, index) => `
            <div class="top-item">
                <div class="top-item-name">
                    <strong>#${index + 1}</strong> ${this.escapeHtml(account.name)}
                </div>
                <div class="top-item-count">${this.formatNumber(account.count)}</div>
            </div>
        `).join('');
    }

    /**
     * 渲染热门作者
     */
    renderTopAuthors(authors) {
        const container = document.getElementById('top-authors-list');
        
        container.innerHTML = authors.map((author, index) => `
            <div class="top-item">
                <div class="top-item-name">
                    <strong>#${index + 1}</strong> ${this.escapeHtml(author.name)}
                </div>
                <div class="top-item-count">${this.formatNumber(author.count)}</div>
            </div>
        `).join('');
    }

    /**
     * 显示/隐藏加载状态
     */
    showLoading(show) {
        const loading = document.getElementById('loading');
        if (show) {
            loading.classList.remove('hidden');
        } else {
            loading.classList.add('hidden');
        }
    }

    /**
     * 显示错误消息
     */
    showError(message) {
        // 创建临时错误提示
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-toast';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span>${message}</span>
        `;
        
        // 添加错误提示样式
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: var(--error-color);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-lg);
            z-index: 1001;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(errorDiv);

        // 3秒后自动移除
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }

    /**
     * 工具方法：转义HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 工具方法：格式化数字
     */
    formatNumber(num) {
        return num.toLocaleString('zh-CN');
    }

    /**
     * 工具方法：格式化日期
     */
    formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch {
            return '未知日期';
        }
    }

    /**
     * 工具方法：格式化内容
     */
    formatContent(content) {
        return content
            .split('\n')
            .map(paragraph => paragraph.trim())
            .filter(paragraph => paragraph.length > 0)
            .map(paragraph => `<p>${this.escapeHtml(paragraph)}</p>`)
            .join('');
    }

    // Analytics相关方法

    /**
     * 加载数据分析
     */
    async loadAnalyticsData() {
        const daysSelect = document.getElementById('analytics-days');
        if (!daysSelect) {
            console.error('Analytics days selector not found');
            return;
        }
        
        const days = parseInt(daysSelect.value);
        console.log('Loading analytics data for', days, 'days');
        
        // 并行加载所有分析数据
        const analysisPromises = [
            this.loadTrendsAnalysis(days),
            this.loadAuthorsAnalysis(days),
            this.loadQualityAnalysis(),
            this.loadTagsAnalysis(days),
            this.loadPublishingAnalysis(days),
            this.loadComprehensiveReport(days)
        ];

        // 等待所有分析完成
        try {
            const results = await Promise.allSettled(analysisPromises);
            console.log('Analytics data loading completed', results);
            
            // 检查每个结果
            results.forEach((result, index) => {
                if (result.status === 'rejected') {
                    console.error(`Analytics module ${index} failed:`, result.reason);
                }
            });
        } catch (error) {
            console.error('Analytics loading error:', error);
        }
    }

    /**
     * 加载技术趋势分析
     */
    async loadTrendsAnalysis(days) {
        console.log('Loading trends analysis for', days, 'days');
        
        const statusEl = document.getElementById('trends-status');
        const contentEl = document.getElementById('trends-content');
        
        if (!statusEl || !contentEl) {
            console.error('Trends analysis DOM elements not found:', { statusEl, contentEl });
            return;
        }
        
        try {
            console.log('Setting loading status...');
            statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 分析中...';
            statusEl.className = 'module-status';
            
            console.log('Fetching technology trends from API...');
            const data = await apiClient.getTechnologyTrends(days);
            console.log('Trends data received:', data);
            
            console.log('Setting success status...');
            statusEl.innerHTML = '<i class="fas fa-check"></i> 分析完成';
            statusEl.className = 'module-status success';
            
            contentEl.innerHTML = `
                <div class="trends-summary">
                    <p>📄 分析文章: <strong>${data.total_articles}</strong> 篇</p>
                    <p>🏷️ 发现关键词: <strong>${data.total_keywords}</strong> 个</p>
                </div>
                <div class="trends-list">
                    ${data.top_trends.slice(0, 10).map((trend, index) => `
                        <div class="trend-item">
                            <span class="trend-name">${index + 1}. ${trend.keyword}</span>
                            <div class="trend-stats">
                                <span>${trend.count} 次</span>
                                <span>${trend.percentage}%</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
        } catch (error) {
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 分析失败';
            statusEl.className = 'module-status error';
            contentEl.innerHTML = `<div class="error-message">分析失败: ${error.message}</div>`;
        }
    }

    /**
     * 加载作者活跃度分析
     */
    async loadAuthorsAnalysis(days) {
        const statusEl = document.getElementById('authors-status');
        const contentEl = document.getElementById('authors-content');
        
        try {
            statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 分析中...';
            statusEl.className = 'module-status';
            
            const data = await apiClient.getAuthorActivity(days);
            
            statusEl.innerHTML = '<i class="fas fa-check"></i> 分析完成';
            statusEl.className = 'module-status success';
            
            contentEl.innerHTML = `
                <div class="authors-summary">
                    <p>👨‍💻 活跃作者: <strong>${data.total_authors}</strong> 人</p>
                    <p>📄 分析文章: <strong>${data.total_articles}</strong> 篇</p>
                </div>
                <div class="authors-list">
                    ${data.top_authors.slice(0, 8).map((author, index) => `
                        <div class="author-item">
                            <span class="author-name">${index + 1}. ${author.author}</span>
                            <div class="author-stats">
                                <span>${author.article_count} 篇</span>
                                <span>影响力: ${author.influence_score}</span>
                                <span>日均: ${author.productivity}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
        } catch (error) {
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 分析失败';
            statusEl.className = 'module-status error';
            contentEl.innerHTML = `<div class="error-message">分析失败: ${error.message}</div>`;
        }
    }

    /**
     * 加载内容质量分析
     */
    async loadQualityAnalysis() {
        const statusEl = document.getElementById('quality-status');
        const contentEl = document.getElementById('quality-content');
        
        try {
            statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 评估中...';
            statusEl.className = 'module-status';
            
            const data = await apiClient.evaluateContentQuality(50); // 限制50篇文章
            
            statusEl.innerHTML = '<i class="fas fa-check"></i> 评估完成';
            statusEl.className = 'module-status success';
            
            const summary = data.summary;
            const qualityDist = summary.quality_distribution;
            
            contentEl.innerHTML = `
                <div class="quality-overview">
                    <div class="quality-grade grade-a">
                        <h4>${qualityDist.A}</h4>
                        <p>A级 (优秀)</p>
                    </div>
                    <div class="quality-grade grade-b">
                        <h4>${qualityDist.B}</h4>
                        <p>B级 (良好)</p>
                    </div>
                    <div class="quality-grade grade-c">
                        <h4>${qualityDist.C}</h4>
                        <p>C级 (一般)</p>
                    </div>
                    <div class="quality-grade grade-d">
                        <h4>${qualityDist.D}</h4>
                        <p>D级 (待改进)</p>
                    </div>
                </div>
                <div class="quality-metrics">
                    <div class="metric-item">
                        <span class="metric-name">高质量率</span>
                        <span class="metric-value">${summary.quality_insights.high_quality_rate}%</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-name">平均字数</span>
                        <span class="metric-value">${summary.quality_insights.average_word_count}</span>
                    </div>
                    <div class="metric-item">
                        <span class="metric-name">平均阅读时间</span>
                        <span class="metric-value">${summary.quality_insights.average_reading_time}分钟</span>
                    </div>
                </div>
            `;
            
        } catch (error) {
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 评估失败';
            statusEl.className = 'module-status error';
            contentEl.innerHTML = `<div class="error-message">评估失败: ${error.message}</div>`;
        }
    }

    /**
     * 加载标签分析
     */
    async loadTagsAnalysis(days) {
        const statusEl = document.getElementById('tags-status');
        const contentEl = document.getElementById('tags-content');
        
        try {
            statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 分析中...';
            statusEl.className = 'module-status';
            
            const data = await apiClient.getTagTrends(days);
            
            statusEl.innerHTML = '<i class="fas fa-check"></i> 分析完成';
            statusEl.className = 'module-status success';
            
            const summary = data.summary;
            
            contentEl.innerHTML = `
                <div class="tags-summary">
                    <p>🏷️ 独特标签: <strong>${summary.total_unique_tags}</strong> 个</p>
                    <p>📊 平均每篇: <strong>${summary.average_tags_per_article}</strong> 个标签</p>
                </div>
                <div class="tags-list">
                    ${Object.entries(data.trending_tags).map(([category, trends]) => 
                        trends.slice(0, 3).map(trend => `
                            <div class="tag-item">
                                <span class="tag-name">${category}: ${trend.tag}</span>
                                <div class="tag-stats">
                                    <span>${trend.count} 次</span>
                                    <span>${trend.percentage}%</span>
                                </div>
                            </div>
                        `).join('')
                    ).join('')}
                </div>
            `;
            
        } catch (error) {
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 分析失败';
            statusEl.className = 'module-status error';
            contentEl.innerHTML = `<div class="error-message">分析失败: ${error.message}</div>`;
        }
    }

    /**
     * 加载发布模式分析
     */
    async loadPublishingAnalysis(days) {
        const statusEl = document.getElementById('publishing-status');
        const contentEl = document.getElementById('publishing-content');
        
        try {
            statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 分析中...';
            statusEl.className = 'module-status';
            
            const data = await apiClient.getPublicationPatterns(days);
            
            statusEl.innerHTML = '<i class="fas fa-check"></i> 分析完成';
            statusEl.className = 'module-status success';
            
            const dailyStats = data.daily_statistics;
            const temporal = data.temporal_patterns;
            
            contentEl.innerHTML = `
                <div class="publishing-stats">
                    <div class="stat-card">
                        <h4>${dailyStats.average}</h4>
                        <p>日均发布</p>
                    </div>
                    <div class="stat-card">
                        <h4>${dailyStats.maximum}</h4>
                        <p>最高单日</p>
                    </div>
                    <div class="stat-card">
                        <h4>${temporal.most_active_hour.hour}:00</h4>
                        <p>最活跃时段</p>
                    </div>
                    <div class="stat-card">
                        <h4>${data.distribution_summary.coverage_rate}%</h4>
                        <p>覆盖率</p>
                    </div>
                </div>
            `;
            
        } catch (error) {
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 分析失败';
            statusEl.className = 'module-status error';
            contentEl.innerHTML = `<div class="error-message">分析失败: ${error.message}</div>`;
        }
    }

    /**
     * 加载综合报告
     */
    async loadComprehensiveReport(days) {
        const statusEl = document.getElementById('report-status');
        const contentEl = document.getElementById('report-content');
        
        try {
            statusEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';
            statusEl.className = 'module-status';
            
            const data = await apiClient.getComprehensiveReport(days);
            
            statusEl.innerHTML = '<i class="fas fa-check"></i> 生成完成';
            statusEl.className = 'module-status success';
            
            const summary = data.summary;
            
            contentEl.innerHTML = `
                <div class="comprehensive-summary">
                    <div class="summary-item">
                        <h4>${summary.total_articles_analyzed}</h4>
                        <p>分析文章总数</p>
                    </div>
                    <div class="summary-item">
                        <h4>${summary.total_authors}</h4>
                        <p>活跃作者数量</p>
                    </div>
                    <div class="summary-item">
                        <h4>${summary.daily_average}</h4>
                        <p>日均发布量</p>
                    </div>
                </div>
                <div class="report-highlights">
                    <div class="highlight-item">
                        <h4>🔥 最热门技术</h4>
                        <p>${summary.most_discussed_tech}</p>
                    </div>
                    <div class="highlight-item">
                        <h4>🏆 最高产作者</h4>
                        <p>${summary.most_productive_author}</p>
                    </div>
                </div>
            `;
            
        } catch (error) {
            statusEl.innerHTML = '<i class="fas fa-exclamation-triangle"></i> 生成失败';
            statusEl.className = 'module-status error';
            contentEl.innerHTML = `<div class="error-message">报告生成失败: ${error.message}</div>`;
        }
    }
}

// 创建应用实例
const app = new GeekDailyApp();

// 添加错误处理
window.addEventListener('unhandledrejection', event => {
    console.error('未处理的Promise错误:', event.reason);
    app.showError('发生了未知错误，请刷新页面重试');
});

// 添加动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);