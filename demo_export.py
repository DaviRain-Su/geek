#!/usr/bin/env python3
"""
Markdown 导出演示脚本
用于演示导出功能的使用
"""

import os
import sys
from pathlib import Path

def demo_export():
    """演示 Markdown 导出功能"""
    print("🚀 Web3极客日报 Markdown 导出演示")
    print("=" * 50)
    
    # 检查数据库中是否有文章
    print("\n1. 检查数据库中的文章数量...")
    os.system("python3 main.py stats")
    
    print("\n2. 导出前 3 篇文章作为演示...")
    export_dir = "demo_export"
    
    # 删除旧的演示目录
    if os.path.exists(export_dir):
        import shutil
        shutil.rmtree(export_dir)
    
    # 执行导出
    cmd = f"python3 main.py export --format markdown --limit 3 --output {export_dir}"
    print(f"执行命令: {cmd}")
    os.system(cmd)
    
    # 检查导出结果
    if os.path.exists(export_dir):
        print(f"\n3. 导出完成！查看结果:")
        print(f"   导出目录: {export_dir}")
        
        # 显示目录结构
        print("\n   目录结构:")
        for root, dirs, files in os.walk(export_dir):
            level = root.replace(export_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        # 显示统计
        readme_path = Path(export_dir) / "README.md"
        if readme_path.exists():
            print(f"\n   查看详细统计: {readme_path}")
            print("   或运行: cat demo_export/README.md")
        
        print(f"\n✅ 演示完成！")
        print(f"   📁 查看导出的文章: ls -la {export_dir}")
        print(f"   📖 查看单篇文章: cat {export_dir}/其他/*.md")
        print(f"   🧹 清理演示文件: rm -rf {export_dir}")
    else:
        print("\n❌ 导出失败，请检查数据库中是否有文章")

if __name__ == "__main__":
    demo_export()