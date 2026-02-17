#!/bin/bash
# 测试运行脚本

echo "🧪 运行测试套件..."
cd "$(dirname "$0")"

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "✅ 激活虚拟环境"
    source .venv/bin/activate
else
    echo "⚠️ 未找到虚拟环境，使用系统 Python"
fi

# 运行测试
echo ""
echo "📋 运行所有测试..."
python -m pytest tests/ -v --tb=short

# 检查测试结果
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 所有测试通过！"
else
    echo ""
    echo "❌ 部分测试失败"
fi
