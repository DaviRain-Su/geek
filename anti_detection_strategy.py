#!/usr/bin/env python3
"""
反检测策略建议

当遇到 "Anti-bot protection detected" 时的解决方案
"""

def get_anti_detection_tips():
    """获取反检测建议"""
    
    tips = """
🤖 **遇到反爬虫保护的解决方案：**

1️⃣ **立即停止当前爬取**
   - 微信已检测到自动化行为
   - 继续可能导致IP被封

2️⃣ **等待冷却期**
   - 建议等待 2-4 小时
   - 或更换网络环境（切换IP）

3️⃣ **降低爬取频率**
   ```bash
   # 使用更长的延迟
   python main.py series "URL" --max-articles 10
   ```

4️⃣ **使用代理轮换**
   ```bash
   # 启用代理（需要配置代理池）
   python main.py series "URL" --use-proxy --max-articles 5
   ```

5️⃣ **手动验证恢复**
   - 用浏览器正常访问几篇微信文章
   - 完成人机验证（如果有）
   - 清除浏览器数据

6️⃣ **分批次爬取**
   ```bash
   # 分小批次，每次5-10篇
   python main.py series "URL" --max-articles 5
   # 等待几小时后继续
   python main.py series "URL" --max-articles 5
   ```

⚠️ **当前建议：**
- 暂停爬取 2-4 小时
- 检查已爬取的数据：`python main.py stats`
- 导出现有数据：`python main.py export --format json`
"""
    
    return tips

if __name__ == "__main__":
    print(get_anti_detection_tips())