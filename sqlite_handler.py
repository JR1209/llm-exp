#!/usr/bin/env python3
"""
SQLite 数据处理模块
存储完整的实验数据：输入、prompt、代码、输出
支持多机器独立运行，最后合并
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class SQLiteHandler:
    """SQLite 数据库处理类"""
    
    def __init__(self, db_path: str = 'experiments.db'):
        """
        初始化 SQLite 连接
        
        Args:
            d这个_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 返回字典形式
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        # 主实验表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP,
                
                -- 配置信息（JSON）
                config TEXT NOT NULL,
                
                -- 输入数据（JSON）
                input_questions TEXT NOT NULL,
                num_questions INTEGER NOT NULL,
                
                -- Prompts（JSON）
                prompts TEXT,
                
                -- Git 版本信息（推荐使用 Git 管理代码）
                git_commit TEXT,
                git_branch TEXT,
                git_is_dirty TEXT,
                
                -- 代码快照（可选，仅在没有 Git 时使用）
                code_snapshots TEXT,
                
                -- 输出结果（JSON）
                step1_generation TEXT,
                step2_scores TEXT,
                step3_final TEXT,
                
                -- 统计信息（JSON）
                statistics TEXT
            )
        ''')
        
        # 创建索引
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_version ON experiments(version)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON experiments(status)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON experiments(created_at)
        ''')
        
        self.conn.commit()
    
    def save_experiment(
        self,
        version: str,
        config: Dict[str, Any],
        input_questions: List[str],
        prompts: Dict[str, str] = None,
        code_snapshots: Dict[str, str] = None,
        git_info: Dict[str, str] = None
    ) -> str:
        """
        保存实验（初始状态）
        
        Args:
            version: 实验版本号
            config: 实验配置
            input_questions: 输入问题列表
            prompts: Prompt 字典
            code_snapshots: 代码快照字典（可选，推荐使用 Git）
            git_info: Git 版本信息 {'commit': 'xxx', 'branch': 'main', 'is_dirty': 'false'}
            
        Returns:
            实验版本号
        """
        now = datetime.now().isoformat()
        
        # Git 信息（推荐）
        git_commit = git_info.get('commit') if git_info else None
        git_branch = git_info.get('branch') if git_info else None
        git_is_dirty = git_info.get('is_dirty') if git_info else None
        
        # 代码快照（备用）
        code_snapshots_json = None
        if code_snapshots:
            code_snapshots_json = json.dumps(code_snapshots, ensure_ascii=False)
        
        self.cursor.execute('''
            INSERT OR REPLACE INTO experiments (
                version, status, created_at, updated_at,
                config, input_questions, num_questions,
                prompts, git_commit, git_branch, git_is_dirty, code_snapshots
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            version,
            'running',
            now,
            now,
            json.dumps(config, ensure_ascii=False),
            json.dumps(input_questions, ensure_ascii=False),
            len(input_questions),
            json.dumps(prompts, ensure_ascii=False) if prompts else None,
            git_commit,
            git_branch,
            git_is_dirty,
            code_snapshots_json
        ))
        
        self.conn.commit()
        return version
    
    def update_experiment_outputs(
        self,
        version: str,
        step1_generation: List[Dict] = None,
        step2_scores: List[Dict] = None,
        step3_final: List[Dict] = None,
        statistics: Dict = None,
        status: str = None
    ):
        """
        更新实验输出
        
        Args:
            version: 实验版本号
            step1_generation: Step1 生成结果
            step2_scores: Step2 评分结果
            step3_final: Step3 最终结果
            statistics: 统计信息
            status: 状态
        """
        updates = []
        params = []
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        if step1_generation is not None:
            updates.append("step1_generation = ?")
            params.append(json.dumps(step1_generation, ensure_ascii=False))
        
        if step2_scores is not None:
            updates.append("step2_scores = ?")
            params.append(json.dumps(step2_scores, ensure_ascii=False))
        
        if step3_final is not None:
            updates.append("step3_final = ?")
            params.append(json.dumps(step3_final, ensure_ascii=False))
            if status is None:
                status = 'completed'
        
        if statistics is not None:
            updates.append("statistics = ?")
            params.append(json.dumps(statistics, ensure_ascii=False))
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        params.append(version)
        
        sql = f"UPDATE experiments SET {', '.join(updates)} WHERE version = ?"
        self.cursor.execute(sql, params)
        self.conn.commit()
    
    def get_experiment(self, version: str) -> Optional[Dict]:
        """获取实验数据"""
        self.cursor.execute('SELECT * FROM experiments WHERE version = ?', (version,))
        row = self.cursor.fetchone()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all_experiments(self, limit: int = 100) -> List[Dict]:
        """获取所有实验"""
        self.cursor.execute('''
            SELECT * FROM experiments 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        return [self._row_to_dict(row) for row in self.cursor.fetchall()]
    
    def get_experiments_by_status(self, status: str) -> List[Dict]:
        """根据状态获取实验"""
        self.cursor.execute('''
            SELECT * FROM experiments 
            WHERE status = ? 
            ORDER BY created_at DESC
        ''', (status,))
        
        return [self._row_to_dict(row) for row in self.cursor.fetchall()]
    
    def delete_experiment(self, version: str) -> bool:
        """删除实验"""
        self.cursor.execute('DELETE FROM experiments WHERE version = ?', (version,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def get_statistics(self) -> Dict:
        """获取数据库统计信息"""
        self.cursor.execute('SELECT COUNT(*) as total FROM experiments')
        total = self.cursor.fetchone()['total']
        
        self.cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM experiments 
            GROUP BY status
        ''')
        status_counts = {row['status']: row['count'] for row in self.cursor.fetchall()}
        
        return {
            'total_experiments': total,
            'by_status': status_counts,
            'database_path': self.db_path
        }
    
    def _row_to_dict(self, row) -> Dict:
        """将数据库行转换为字典"""
        data = dict(row)
        
        # 解析 JSON 字段
        json_fields = ['config', 'input_questions', 'prompts', 'code_snapshots',
                      'step1_generation', 'step2_scores', 'step3_final', 'statistics']
        
        for field in json_fields:
            if data.get(field):
                try:
                    data[field] = json.loads(data[field])
                except:
                    pass
        
        return data
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def load_prompts_from_file(prompts_file: str = "prompts.json") -> Dict[str, str]:
    """从文件加载 prompts"""
    if Path(prompts_file).exists():
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_code_snapshots(
    additional_patterns: List[str] = None,
    exclude_patterns: List[str] = None
) -> Dict[str, Any]:
    """加载代码快照 - 分层结构
    
    Args:
        additional_patterns: 额外要包含的 glob 模式，如 ['rag/**/*.py', 'utils/**/*.py']
        exclude_patterns: 要排除的 glob 模式，如 ['**/__init__.py', '**/test_*.py']
    
    Returns:
        {
            'step1': '核心步骤1代码',
            'step2': '核心步骤2代码',
            'step3': '核心步骤3代码',
            'additional': {
                'rag/indexing.py': '辅助代码内容',
                'utils/io_handler.py': '辅助代码内容',
                ...
            }
        }
    """
    # 1. 核心步骤代码（单独存储）
    core_files = {
        'step1': 'pipeline/generation_async.py',
        'step2': 'pipeline/scoring_async.py',
        'step3': 'pipeline/selection.py'
    }
    
    snapshots = {}
    for key, filepath in core_files.items():
        if Path(filepath).exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                snapshots[key] = f.read()
        else:
            snapshots[key] = f"# 文件不存在: {filepath}"
    
    # 2. 其他辅助代码（打包到 additional）
    additional_code = {}
    
    # 默认要包含的目录
    default_patterns = [
        'rag/**/*.py',
        'utils/**/*.py',
        'core/**/*.py'
    ]
    
    # 默认排除的文件
    default_exclude = [
        '**/__init__.py',
        '**/__pycache__/**',
        '**/test_*.py',
        '**/venv/**',
        '**/.venv/**'
    ]
    
    patterns = additional_patterns or default_patterns
    exclude = exclude_patterns or default_exclude
    
    # 收集所有匹配的文件
    all_files = set()
    for pattern in patterns:
        all_files.update(Path('.').glob(pattern))
    
    # 过滤排除的文件
    for pattern in exclude:
        exclude_files = set(Path('.').glob(pattern))
        all_files -= exclude_files
    
    # 读取文件内容
    for filepath in sorted(all_files):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # 使用相对路径作为 key
                relative_path = str(filepath)
                additional_code[relative_path] = f.read()
        except Exception as e:
            additional_code[str(filepath)] = f"# 读取失败: {e}"
    
    snapshots['additional'] = additional_code
    
    return snapshots


# 使用示例
if __name__ == "__main__":
    # 初始化数据库
    db = SQLiteHandler('test_experiments.db')
    
    # 测试保存
    print("📝 测试保存实验...")
    db.save_experiment(
        version='test_v1',
        config={'limit': 5, 'candidates': 2},
        input_questions=['问题1', '问题2'],
        prompts={'test': 'prompt'},
        code_snapshots={'step1': 'code'}
    )
    print("✅ 保存成功")
    
    # 测试更新
    print("\n📝 测试更新输出...")
    db.update_experiment_outputs(
        version='test_v1',
        step1_generation=[{'question': 'q1', 'candidates': ['a1', 'a2']}],
        statistics={'avg_score': 8.5}
    )
    print("✅ 更新成功")
    
    # 测试查询
    print("\n📊 测试查询...")
    exp = db.get_experiment('test_v1')
    print(f"版本: {exp['version']}")
    print(f"状态: {exp['status']}")
    print(f"问题数: {exp['num_questions']}")
    
    # 统计信息
    print("\n📊 数据库统计:")
    stats = db.get_statistics()
    print(f"总实验数: {stats['total_experiments']}")
    print(f"状态分布: {stats['by_status']}")
    
    db.close()
    print("\n✅ SQLite 测试完成！")