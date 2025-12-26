#!/bin/bash
set -e

echo "开始设置 JSON 格式..."

# 1. 备份旧文件
echo "1. 备份旧的 config.py"
mv config.py config_old.py
mv config_new.py config.py
echo "   ✓ 完成"

# 2. 运行 Python 来生成 JSON 文件
echo "2. 生成 JSON 文件"
python3 << 'PYTHON_EOF'
import json

# 导入 config 会自动生成 prompts.json
try:
    import config
    print("   ✓ prompts.json 已生成")
except Exception as e:
    print(f"   ✗ 错误: {e}")
    exit(1)

# 生成 inputs/questions.json
questions = []
with open('inputs/questions.txt', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        q = line.strip()
        if q:
            questions.append({"id": idx, "question": q})

with open('inputs/questions.json', 'w', encoding='utf-8') as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print(f"   ✓ inputs/questions.json 已生成 ({len(questions)} 个问题)")
PYTHON_EOF

echo "3. 删除临时文件"
rm -f convert_to_json.py test_json_setup.py config_old.py
echo "   ✓ 完成"

echo ""
echo "✅ 设置完成！"
echo "现在可以运行: python run_experiment.py --limit 2 --version test"