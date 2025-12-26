"""
IO 处理模块
负责所有输入输出操作
"""
import json
from pathlib import Path
from typing import List, Dict


def load_questions(file_path: str, limit: int = None) -> List[str]:
    """
    加载问题文件
    支持 .txt 和 .json 格式
    """
    file_path = Path(file_path)
    
    if file_path.suffix == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 如果是新格式 {"questions": [...]}
            if isinstance(data, dict) and 'questions' in data:
                questions = [q['text'] if isinstance(q, dict) else q for q in data['questions']]
            # 如果是简单列表 [{"id": 1, "question": "..."}, ...]
            elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                questions = [q.get('question') or q.get('text') for q in data]
            # 如果是纯字符串列表 ["...", "..."]
            else:
                questions = data
    else:
        # 原有的 txt 格式
        questions = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                q = line.strip()
                if q:
                    questions.append(q)
    
    if limit:
        return questions[:limit]
    return questions


def save_json(data: Dict, file_path: str):
    """保存为 JSON 文件（格式化）"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_jsonl(data: List[Dict], file_path: str):
    """保存为 JSONL 文件（每行一个 JSON）"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def load_json(file_path: str) -> Dict:
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_jsonl(file_path: str) -> List[Dict]:
    """加载 JSONL 文件"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data
