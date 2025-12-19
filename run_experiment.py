#!/usr/bin/env python3
"""
实验主脚本：三步固定流程
Step 1: Qwen批量生成
Step 2: GPT多轮评分
Step 3: 选择Top-K
"""

import json
import requests
import argparse
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import yaml

with open("params.yaml") as f:
    params = yaml.safe_load(f)

prompt_version = params["prompt_version"]

from config import (
    API_KEY, API_BASE_URL,
    QWEN_MODEL, GPT_MODEL,
    QWEN_GENERATION_PROMPT,
    GPT_SCORING_PROMPT
)


# ============================================
# 日志配置
# ============================================

def setup_logger(log_file: str = "experiment.log"):
    """配置日志系统 - 表格化输出"""
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',  # 简化格式
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    return logger

# 全局logger
logger = None


# ============================================
# API调用
# ============================================

def call_api(model: str, prompt: str, max_retries: int = 3) -> str:
    """调用API"""
    url = f"{API_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"]
                if logger:
                    logger.debug(f"API调用成功 [{model}]: {len(result)} 字符")
                return result
            else:
                if logger:
                    logger.warning(f"API调用失败 [{model}]: HTTP {response.status_code}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
                
        except Exception as e:
            if logger:
                logger.warning(f"API调用异常 [{model}]: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    if logger:
        logger.error(f"API调用最终失败 [{model}]")
    return ""


# ============================================
# 数据加载
# ============================================

def load_questions(file_path: str, limit: int) -> List[str]:
    """加载问题（限制数量）"""
    questions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            q = line.strip()
            if q:
                questions.append(q)
    return questions


def save_jsonl(data: List[Dict], file_path: str):
    """保存JSONL"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    if logger:
        logger.info(f"💾 已保存: {file_path}")


# ============================================
# Step 1: Qwen批量生成
# ============================================

def step1_qwen_generation(questions: List[str], num_candidates: int, output_file: str):
    """Step 1: 使用Qwen并行生成候选对话"""
    logger.info("\n" + "="*80)
    logger.info("Step 1: Qwen Batch Generation (Parallel)")
    logger.info("="*80)
    logger.info(f"问题数: {len(questions)} | 每题候选: {num_candidates} | 并行数: 100")
    logger.info(f"\n{'QID':<5} {'CID':<5} {'Status':<10} {'Length':<10}")
    logger.info("-"*80)
    
    results = []
    tasks = []
    
    # 构建任务列表
    for idx, question in enumerate(questions, 1):
        for cand_idx in range(num_candidates):
            tasks.append((idx, question, cand_idx + 1))
    
    # 并行执行
    def generate_one(task):
        idx, question, cand_id = task
        prompt = QWEN_GENERATION_PROMPT.format(question=question)
        dialogue = call_api(QWEN_MODEL, prompt)
        return idx, question, cand_id, dialogue
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(generate_one, task): task for task in tasks}
        
        for future in as_completed(futures):
            idx, question, cand_id, dialogue = future.result()
            if dialogue:
                results.append({
                    "question_id": idx,
                    "question": question,
                    "candidate_id": cand_id,
                    "dialogue": dialogue,
                    "model": QWEN_MODEL
                })
                logger.info(f"{idx:<5} {cand_id:<5} {'✓ Success':<10} {len(dialogue):<10}")
            else:
                logger.info(f"{idx:<5} {cand_id:<5} {'✗ Failed':<10} {0:<10}")
    
    save_jsonl(results, output_file)
    logger.info("-"*80)
    logger.info(f"✅ Step 1 完成: {len(results)}/{len(tasks)} 成功\n")
    return results


# ============================================
# Step 2: GPT多轮评分
# ============================================

def parse_scores(score_text: str) -> Dict[str, float]:
    """解析评分文本"""
    scores = {}
    for line in score_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            try:
                scores[key] = float(value.strip())
            except:
                scores[key] = 0.0
    return scores


def step2_gpt_scoring(candidates: List[Dict], num_rounds: int, output_file: str):
    """Step 2: 使用GPT并行评分"""
    logger.info("\n" + "="*80)
    logger.info("Step 2: GPT Multi-round Scoring (Parallel)")
    logger.info("="*80)
    logger.info(f"候选数: {len(candidates)} | 评分轮次: {num_rounds} | 并行数: 100")
    logger.info(f"\n{'QID':<5} {'CID':<5} {'Emp':<6} {'Sup':<6} {'Gui':<6} {'Saf':<6} {'Total':<8}")
    logger.info("-"*80)
    
    results = []
    
    def score_one_round(candidate, round_idx):
        prompt = GPT_SCORING_PROMPT.format(dialogue=candidate['dialogue'])
        score_text = call_api(GPT_MODEL, prompt)
        if score_text:
            return parse_scores(score_text)
        return None
    
    # 对每个候选进行多轮评分
    for candidate in candidates:
        all_scores = []
        
        # 并行评分多轮
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(score_one_round, candidate, i) for i in range(num_rounds)]
            for future in as_completed(futures):
                score = future.result()
                if score:
                    all_scores.append(score)
        
        # 计算平均分
        if all_scores:
            avg_scores = {}
            for key in ['Empathy', 'Supportiveness', 'Guidance', 'Safety']:
                scores_list = [s.get(key, 0.0) for s in all_scores]
                avg_scores[key] = sum(scores_list) / len(scores_list) if scores_list else 0.0
            
            avg_scores['Total'] = sum(avg_scores.values())
            
            logger.info(f"{candidate['question_id']:<5} {candidate['candidate_id']:<5} "
                       f"{avg_scores['Empathy']:<6.2f} {avg_scores['Supportiveness']:<6.2f} "
                       f"{avg_scores['Guidance']:<6.2f} {avg_scores['Safety']:<6.2f} "
                       f"{avg_scores['Total']:<8.2f}")
            
            results.append({
                "question_id": candidate['question_id'],
                "question": candidate['question'],
                "candidate_id": candidate['candidate_id'],
                "dialogue": candidate['dialogue'],
                "scores": avg_scores,
                "score_details": all_scores
            })
    
    save_jsonl(results, output_file)
    logger.info("-"*80)
    logger.info(f"✅ Step 2 完成: {len(results)} 个候选评分完成\n")
    return results


# ============================================
# Step 3: 选择Top-K
# ============================================

def step3_selection(scored_candidates: List[Dict], top_k: int, output_file: str):
    """Step 3: 根据总分选择Top-K"""
    logger.info("\n" + "="*80)
    logger.info("Step 3: Top-K Selection")
    logger.info("="*80)
    
    # 按总分排序
    sorted_candidates = sorted(
        scored_candidates,
        key=lambda x: x['scores']['Total'],
        reverse=True
    )
    
    # 选择Top-K
    top_results = sorted_candidates[:top_k]
    
    # 表格化输出
    logger.info(f"\n{'Rank':<6} {'QID':<5} {'CID':<5} {'Emp':<6} {'Sup':<6} {'Gui':<6} {'Saf':<6} {'Total':<8} {'Question':<30}")
    logger.info("-"*80)
    for rank, item in enumerate(top_results, 1):
        q_short = item['question'][:27] + '...' if len(item['question']) > 30 else item['question']
        logger.info(f"#{rank:<5} {item['question_id']:<5} {item['candidate_id']:<5} "
                   f"{item['scores']['Empathy']:<6.2f} {item['scores']['Supportiveness']:<6.2f} "
                   f"{item['scores']['Guidance']:<6.2f} {item['scores']['Safety']:<6.2f} "
                   f"{item['scores']['Total']:<8.2f} {q_short:<30}")
    
    save_jsonl(top_results, output_file)
    logger.info("-"*80)
    logger.info(f"✅ Step 3 完成: Top-{len(top_results)} 已保存\n")
    return top_results


# ============================================
# 主函数
# ============================================

def main():
    global logger
    
    parser = argparse.ArgumentParser(description='运行实验')
    parser.add_argument('--limit', type=int, default=10, help='问题数量限制')
    parser.add_argument('--candidates', type=int, default=2, help='每条问题生成候选数')
    parser.add_argument('--score-rounds', type=int, default=3, help='每个候选评分次数')
    parser.add_argument('--version', type=str, default='v1', help='版本号')
    parser.add_argument('--top-k', type=int, default=5, help='选择Top-K')
    parser.add_argument('--input', type=str, default='inputs/questions.txt', help='输入文件')
    parser.add_argument('--log', type=str, default=None, help='日志文件路径（默认自动生成）')
    
    args = parser.parse_args()
    
    # 设置输出目录
    # 如果在SSH服务器上，使用 /data/zl.zhang/Block2/{version}
    # 如果在本地，使用 ./outputs/{version}
    if os.path.exists('/data'):
        output_dir = os.path.join('Outputs', args.version)
    else:
        output_dir = os.path.join('Outputs', args.version)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 设置日志文件路径
    if args.log is None:
        args.log = os.path.join(output_dir, f'experiment_{args.version}.log')
    
    # 初始化日志系统
    logger = setup_logger(args.log)
    
    # 日志头
    logger.info("="*80)
    logger.info(f"🧪 实验配置 [{args.version}]")
    logger.info("="*80)
    logger.info(f"输入: {args.input} | 问题数: {args.limit}")
    logger.info(f"候选数: {args.candidates} | 评分轮次: {args.score_rounds} | Top-K: {args.top_k}")
    logger.info(f"输出目录: {output_dir}")
    logger.info("="*80)
    
    # 加载数据
    questions = load_questions(args.input, args.limit)
    logger.info(f"\n✅ 已加载 {len(questions)} 个问题")
    
    # Step 1: Qwen生成
    candidates = step1_qwen_generation(
        questions,
        args.candidates,
        os.path.join(output_dir, f"qwen_candidates_{args.version}.jsonl")
    )
    
    # Step 2: GPT评分
    scored_candidates = step2_gpt_scoring(
        candidates,
        args.score_rounds,
        os.path.join(output_dir, f"gpt_scores_{args.version}.jsonl")
    )
    
    # Step 3: 选择
    top_results = step3_selection(
        scored_candidates,
        args.top_k,
        os.path.join(output_dir, f"top_results_{args.version}.jsonl")
    )
    
    logger.info("\n" + "="*80)
    logger.info("🎉 实验完成！")
    logger.info("="*80)
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"  - qwen_candidates_{args.version}.jsonl")
    logger.info(f"  - gpt_scores_{args.version}.jsonl")
    logger.info(f"  - top_results_{args.version}.jsonl")
    logger.info(f"  - experiment_{args.version}.log")
    logger.info("="*80)


if __name__ == "__main__":
    main()

