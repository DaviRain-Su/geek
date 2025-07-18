# 开发环境设置指南

本指南将帮助您快速设置 Web3极客日报前端项目的开发环境。

## 🚀 快速开始

### 1. 一键安装

```bash
# 运行安装脚本
./scripts/install.sh
```

这个脚本会：
- 检查并安装 uv（如果需要）
- 创建虚拟环境
- 安装所有项目依赖

### 2. 启动开发服务器

```bash
# 运行开发脚本
./scripts/dev.sh

# 或者直接使用 uv
uv run frontend-server
```

## 📦 uv 使用指南

### 什么是 uv？

[uv](https://github.com/astral-sh/uv) 是一个极快的 Python 包和项目管理器，由 Rust 编写。它可以：
- 替代 pip、pip-tools、pipx、poetry、pyenv、virtualenv 等工具
- 提供 10-100 倍的性能提升
- 自动管理 Python 版本和虚拟环境

### 常用 uv 命令

```bash
# 安装项目依赖
uv sync

# 添加新依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 更新依赖
uv sync --upgrade

# 运行命令（无需激活虚拟环境）
uv run python script.py

# 查看已安装的包
uv pip list

# 创建依赖锁文件
uv lock
```

## 🛠️ 开发工作流

### 1. 代码格式化

在提交代码前，运行格式化脚本：

```bash
./scripts/format.sh
```

这会运行：
- **Black**: Python 代码格式化
- **Ruff**: 代码质量检查和修复
- **MyPy**: 静态类型检查

### 2. 运行测试

```bash
./scripts/test.sh
```

### 3. 手动运行各个工具

```bash
# 格式化代码
uv run black .

# 检查代码质量
uv run ruff check .

# 修复代码问题
uv run ruff check . --fix

# 类型检查
uv run mypy server.py

# 运行测试
uv run pytest
```

## 📁 项目结构

```
frontend/
├── .python-version      # Python 版本配置
├── pyproject.toml       # 项目配置和依赖
├── uv.lock             # 依赖锁文件（自动生成）
├── .venv/              # 虚拟环境（自动创建）
├── server.py           # 开发服务器
├── index.html          # 主页面
├── css/                # 样式文件
│   └── main.css
├── js/                 # JavaScript 文件
│   ├── api.js          # API 客户端
│   └── main.js         # 主逻辑
├── assets/             # 静态资源
├── scripts/            # 开发脚本
│   ├── dev.sh          # 开发服务器启动脚本
│   ├── install.sh      # 安装脚本
│   ├── format.sh       # 代码格式化脚本
│   └── test.sh         # 测试脚本
├── tests/              # 测试文件
├── README.md           # 项目说明
└── DEVELOPMENT.md      # 本文件
```

## 🔧 配置说明

### pyproject.toml

这是项目的核心配置文件，包含：
- 项目元数据（名称、版本、描述）
- Python 版本要求
- 项目依赖
- 开发工具配置（Black、Ruff、MyPy）

### .python-version

指定项目使用的 Python 版本。uv 会自动使用这个版本。

### .gitignore

配置了需要忽略的文件和目录，包括：
- Python 缓存文件
- 虚拟环境
- IDE 配置
- uv 生成的文件

## 🐛 故障排除

### uv 未找到

如果系统提示找不到 uv 命令：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 重新加载 shell 配置
source ~/.bashrc  # 或 ~/.zshrc
```

### 依赖安装失败

```bash
# 清理并重新安装
rm -rf .venv uv.lock
uv sync
```

### 端口被占用

```bash
# 使用不同端口
uv run frontend-server --port 3001
```

### Python 版本问题

uv 会自动管理 Python 版本。如果遇到问题：

```bash
# 查看可用的 Python 版本
uv python list

# 安装特定版本
uv python install 3.11
```

## 📚 更多资源

- [uv 官方文档](https://github.com/astral-sh/uv)
- [Black 代码格式化](https://black.readthedocs.io/)
- [Ruff 代码检查](https://docs.astral.sh/ruff/)
- [MyPy 类型检查](https://mypy.readthedocs.io/)
- [pytest 测试框架](https://docs.pytest.org/)

## 💡 开发建议

1. **使用 uv run**: 始终使用 `uv run` 来运行命令，这样可以确保使用正确的虚拟环境
2. **保持依赖更新**: 定期运行 `uv sync --upgrade` 更新依赖
3. **编写测试**: 为新功能编写测试，确保代码质量
4. **遵循代码规范**: 在提交前运行格式化脚本
5. **类型注解**: 尽可能添加类型注解，提高代码可维护性

---

现在您已经准备好开始开发了！如有任何问题，请查看项目的 README.md 或提交 issue。