#-oneline
!/usr/bin/env python3
"""
Flask API 服务器
为 Vue 前端提供 RESTful API
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """获取所有问题"""
    try:
        with open('inputs/questions.txt', 'r', encoding='utf-8') as f:
            questions = [line.strip() for line in f if line.strip()]
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/questions', methods=['POST'])
def add_question():
    """添加新问题"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': '问题不能为空'}), 400
        
        with open('inputs/questions.txt', 'a', encoding='utf-8') as f:
            f.write(question + '\n')
        
        return jsonify({'success': True, 'message': '问题添加成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/questions/batch', methods=['POST'])
def upload_questions_batch():
    """批量上传问题（覆盖原有）"""
    try:
        data = request.json
        questions = data.get('questions', [])
        
        if not questions:
            return jsonify({'success': False, 'error': '问题列表不能为空'}), 400
        
        # 覆盖写入
        with open('inputs/questions.txt', 'w', encoding='utf-8') as f:
            for q in questions:
                question_text = q if isinstance(q, str) else q.get('question', '')
                if question_text.strip():
                    f.write(question_text.strip() + '\n')
        
        return jsonify({'success': True, 'message': f'成功上传 {len(questions)} 个问题'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/experiments/run', methods=['POST'])
def run_experiment():
    """运行实验"""
    try:
        data = request.json
        limit = data.get('limit', 10)
        candidates = data.get('candidates', 2)
        score_rounds = data.get('score_rounds', 3)
        version = data.get('version', 'v1')
        top_k = data.get('top_k', 5)
        
        # 确保输出目录存在
        output_dir = Path(f'Outputs/{version}')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'python3', '运行.py',
            '--limit', str(limit),
            '--candidates', str(candidates),
            '--score-rounds', str(score_rounds),
            '--version', version,
            '--top-k', str(top_k)
        ]
        
        # 记录日志
        log_file = output_dir / 'experiment.log'
        
        print(f"[API] 启动实验: {' '.join(cmd)}")
        print(f"[API] 日志文件: {log_file}")
        
        # 后台运行，输出重定向到日志文件
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True
            )
        
        print(f"[API] 实验进程 PID: {process.pid}")
        
        return jsonify({
            'success': True,
            'message': '实验已启动',
            'pid': process.pid,
            'version': version,
            'log_file': str(log_file)
        })
    except Exception as e:
        print(f"[API] 启动实验失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/experiments/versions', methods=['GET'])
def get_versions():
    """获取所有实验版本"""
    try:
        output_dir = Path('Outputs')
        if not output_dir.exists():
            return jsonify({'success': True, 'versions': []})
        
        versions = [d.name for d in output_dir.iterdir() if d.is_dir()]
        versions.sort(reverse=True)
        
        return jsonify({'success': True, 'versions': versions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/experiments/<version>/status', methods=['GET'])
def get_experiment_status(version):
    """检查实验状态"""
    try:
        output_dir = Path(f'Outputs/{version}')
        
        if not output_dir.exists():
            return jsonify({'success': True, 'status': 'not_started'})
        
        # 检查各个阶段的输出文件
        candidates_file = output_dir / f'qwen_candidates_{version}.jsonl'
        scores_file = output_dir / f'gpt_scores_{version}.jsonl'
        top_file = output_dir / f'top_results_{version}.jsonl'
        log_file = output_dir / 'experiment.log'
        
        status = {
            'candidates': candidates_file.exists(),
            'scores': scores_file.exists(),
            'top': top_file.exists(),
            'log_exists': log_file.exists()
        }
        
        # 读取最后几行日志
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                status['log_tail'] = ''.join(lines[-10:])  # 最后10行
        
        if top_file.exists():
            return jsonify({'success': True, 'status': 'completed', 'details': status})
        elif scores_file.exists():
            return jsonify({'success': True, 'status': 'scoring', 'details': status})
        elif candidates_file.exists():
            return jsonify({'success': True, 'status': 'generating', 'details': status})
        else:
            return jsonify({'success': True, 'status': 'running', 'details': status})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/experiments/<version>/log', methods=['GET'])
def get_experiment_log(version):
    """获取实验日志"""
    try:
        log_file = Path(f'Outputs/{version}/experiment.log')
        
        if not log_file.exists():
            return jsonify({'success': False, 'error': '日志文件不存在'}), 404
        
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        return jsonify({
            'success': True, 
            'log': log_content,
            'lines': log_content.count('\n')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/results/<version>/scores', methods=['GET'])
def get_scores(version):
    """获取评分结果"""
    try:
        file_path = f'Outputs/{version}/gpt_scores_{version}.jsonl'
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        scores = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    scores.append(json.loads(line))
        
        return jsonify({'success': True, 'data': scores})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/results/<version>/top', methods=['GET'])
def get_top_results(version):
    """获取Top-K结果"""
    try:
        file_path = f'Outputs/{version}/top_results_{version}.jsonl'
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        top_results = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    top_results.append(json.loads(line))
        
        return jsonify({'success': True, 'data': top_results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)