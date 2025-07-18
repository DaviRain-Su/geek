# Web3极客日报 - 前端应用

一个现代化的Web应用，用于浏览和搜索Web3极客日报的文章内容。

## 🎯 功能特性

### 📰 核心功能
- **文章浏览** - 分页浏览所有文章，支持无限滚动
- **智能搜索** - 全文搜索文章标题、作者和内容
- **高级筛选** - 按账号、作者等维度筛选文章
- **文章详情** - 模态框显示完整文章内容
- **数据统计** - 可视化展示数据统计信息

### 🎨 用户体验
- **响应式设计** - 完美适配桌面、平板和手机
- **现代界面** - 简洁美观的Material Design风格
- **暗色模式** - 自动适配系统主题偏好
- **快速加载** - 优化的API调用和缓存策略
- **错误处理** - 友好的错误提示和重试机制

### ⚡ 技术特点
- **原生JavaScript** - 无框架依赖，轻量高效
- **模块化设计** - 清晰的代码结构和组件化
- **API集成** - 完整的RESTful API客户端
- **缓存优化** - 智能缓存减少重复请求
- **SEO友好** - 语义化HTML结构

## 🚀 快速开始

### 使用 uv 管理项目

本项目现在使用 [uv](https://github.com/astral-sh/uv) 作为 Python 项目管理工具。

#### 安装 uv（如果尚未安装）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv

# 或使用 Homebrew (macOS)
brew install uv
```

### 1. 设置开发环境

```bash
# 进入前端目录
cd frontend

# 安装依赖（会自动创建虚拟环境）
uv sync

# 激活虚拟环境
source .venv/bin/activate

# 或者直接使用 uv run 运行命令（无需激活虚拟环境）
uv run python server.py
```

### 2. 确保后端服务运行

```bash
# 回到项目根目录
cd ..

# 启动API服务器（根据后端项目的设置）
python main.py api --port 8000
```

### 3. 启动前端服务器

```bash
# 在前端目录下

# 方法1: 使用 uv 运行脚本命令
uv run frontend-server --port 3000

# 方法2: 使用 uv run 直接运行
uv run python server.py --port 3000

# 方法3: 激活虚拟环境后运行
source .venv/bin/activate
python server.py --port 3000

# 方法4: 使用Python内置服务器
uv run python -m http.server 3000
```

### 4. 访问应用

打开浏览器访问: **http://localhost:3000**

## 📱 页面结构

### 🏠 首页 (Home)
- **快速统计** - 显示文章总数、作者数量、账号数量
- **搜索框** - 全局搜索入口
- **最新文章** - 展示最近发布的文章卡片

### 📰 文章列表 (Articles)
- **过滤器** - 按账号、作者筛选
- **文章列表** - 分页显示所有文章
- **分页导航** - 支持跳转到任意页面
- **文章详情** - 点击文章查看完整内容

### 📊 统计信息 (Stats)
- **数据概览** - 总体统计数字
- **热门账号** - 按文章数量排序的账号列表
- **热门作者** - 按文章数量排序的作者列表

### ℹ️ 关于页面 (About)
- **项目介绍** - 项目背景和目标
- **技术栈** - 使用的技术和工具
- **API文档** - 链接到完整的API文档

## 🔍 使用说明

### 搜索功能
1. 在首页搜索框输入关键词
2. 支持搜索文章标题、作者名称和内容
3. 自动跳转到文章列表页面显示结果
4. 支持中文和英文搜索

### 筛选功能
1. 进入文章列表页面
2. 使用顶部的筛选器：
   - **账号筛选**: 选择特定的微信公众号
   - **作者筛选**: 选择特定的文章作者
   - **排序方式**: 按时间或标题排序

### 文章浏览
1. 在文章列表中点击任意文章
2. 弹出模态框显示文章详情
3. 点击"阅读原文"跳转到原始链接
4. 按ESC键或点击关闭按钮关闭详情

### 分页导航
- 使用底部分页器浏览不同页面
- 支持快速跳转到首页、末页
- 显示当前页码和总页数

## 🛠️ 技术实现

### 文件结构
```
frontend/
├── index.html          # 主页面
├── css/
│   └── main.css        # 样式文件
├── js/
│   ├── api.js          # API客户端
│   └── main.js         # 主要逻辑
├── server.py           # 开发服务器
└── README.md           # 说明文档
```

### API集成
- **ApiClient类** - 封装所有API调用
- **缓存机制** - 减少重复请求，提升性能
- **错误处理** - 网络错误的优雅处理
- **类型安全** - 完整的数据验证

### 响应式设计
- **CSS Grid & Flexbox** - 现代布局技术
- **媒体查询** - 适配不同屏幕尺寸
- **触摸友好** - 移动设备优化
- **可访问性** - 支持键盘导航

## 🎨 界面设计

### 设计原则
- **简洁清晰** - 突出内容，减少干扰
- **一致性** - 统一的视觉语言和交互模式
- **可读性** - 优化的字体和行间距
- **可用性** - 直观的操作流程

### 色彩方案
- **主色调**: 蓝色系 (#2563eb) - 专业、可信
- **辅助色**: 灰色系 - 平衡、优雅
- **强调色**: 橙色 (#f59e0b) - 活力、创新
- **自适应**: 支持浅色/深色模式

### 组件设计
- **卡片式布局** - 清晰的信息层次
- **微交互** - 悬停效果和过渡动画
- **图标语言** - Font Awesome图标系统
- **排版系统** - Inter字体家族

## 🛠️ 开发工具

### 代码质量工具

本项目集成了以下开发工具：

```bash
# 运行代码格式化
uv run black .

# 运行代码检查
uv run ruff check .

# 运行类型检查
uv run mypy server.py

# 运行测试（需要编写测试文件）
uv run pytest
```

### 开发依赖管理

```bash
# 添加新的项目依赖
uv add requests

# 添加开发依赖
uv add --dev pytest-cov

# 更新所有依赖
uv sync --upgrade

# 查看已安装的包
uv pip list
```

## 🔧 自定义配置

### API端点配置
在 `js/api.js` 中修改API服务器地址：
```javascript
const apiClient = new ApiClient('http://your-api-server:port');
```

### 样式定制
在 `css/main.css` 中修改CSS变量：
```css
:root {
    --primary-color: #your-color;
    --border-radius: 8px;
    /* 其他变量... */
}
```

### 功能扩展
- 添加新的页面：在HTML中添加新的section
- 扩展API功能：在ApiClient类中添加新方法
- 自定义组件：创建可复用的UI组件

## 🚀 部署建议

### 开发环境
- 使用内置的Python服务器进行本地开发
- 支持热重载和CORS跨域请求
- 完整的错误日志和调试信息

### 生产环境
- 使用Nginx或Apache作为Web服务器
- 启用Gzip压缩减少传输大小
- 配置CDN加速静态资源加载
- 设置HTTPS证书保证安全

### 性能优化
- 图片懒加载和压缩
- CSS/JS文件合并和压缩
- 启用浏览器缓存
- 使用Service Worker离线支持

## 📞 技术支持

如果遇到问题：

1. **检查后端API** - 确保API服务器正常运行
2. **浏览器控制台** - 查看JavaScript错误信息
3. **网络连接** - 确认可以访问API端点
4. **端口冲突** - 尝试使用不同的端口号

---

🎉 现在你有了一个功能完整的Web3极客日报前端应用！

✨ 特色功能一览：
- 📚 浏览数百篇精选文章
- 🔍 强大的搜索和筛选功能  
- 📊 详细的数据统计分析
- 📱 完美的移动端体验
- ⚡ 快速的加载和响应