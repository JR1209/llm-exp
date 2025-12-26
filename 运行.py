#!/usr/bin/env python3
"""
实验主脚本 v2.0 - 模块化版本
三步固定流程：生成 → 评分 → 选择
"""

import argparse
import os
from pathlib import Path
import logging

# 导入工具模块
from utils.io_handler import load_questions, save_jsonl

# 导入流程模块
from pipeline.generation import step1_qwen_generation
from pipeline.scoring import step2_gpt_scoring
from pipeline.selection import step3_selection


def setup_logger(log_file: str = None):
    """配置日志系统"""
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8') if log_file else logging.NullHandler(),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('experiment')


def main():
    parser = argparse.ArgumentParser(description='运行实验 v2.0')
    parser.add_argument('--limit', type=int, default=10, help='问题数量限制')
    parser.add_argument('--candidates', type=int, default=2, help='每条问题生成候选数')
    parser.add_argument('--score-rounds', type=int, default=3, help='每个候选评分次数')
    parser.add_argument('--version', type=str, default='v1', help='实验版本号')
    parser.add_argument('--top-k', type=int, default=5, help='选择Top-K')
    parser.add_argument('--input', type=str, default='inputs/questions.txt', help='输入文件')
    parser.add_argument('--log', type=str, default=None, help='日志文件路径')
    
    args = parser.parse_args()
    
    # 设置输出目录
    output_dir = os.path.join('Outputs', args.version)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 设置日志
    if args.log is None:
        args.log = os.path.join(output_dir, f'experiment_{args.version}.log')
    
    logger = setup_logger(args.log)
    
    # 日志头
    logger.info("="*80)
    logger.info(f"🧪 实验配置 [{args.version}] - v2.0 模块化版本")
    logger.info("="*80)
    logger.info(f"输入: {args.input} | 问题数: {args.limit}")
    logger.info(f"候选数: {args.candidates} | 评分轮次: {args.score_rounds} | Top-K: {args.top_k}")
    logger.info(f"输出目录: {output_dir}")
    logger.info("="*80)
    
    # 加载数据
    questions = load_questions(args.input, args.limit)
    logger.info(f"\n✅ 已加载 {len(questions)} 个问题")
    
    # Step 1: Qwen生成
    candidates = step1_qwen_generation(questions, args.candidates)
    output_file = os.path.join(output_dir, f"qwen_candidates_{args.version}.jsonl")
    save_jsonl(candidates, output_file)
    logger.info(f"💾 已保存: {output_file}")
    
    # Step 2: GPT评分
    scored_candidates = step2_gpt_scoring(candidates, args.score_rounds)
    output_file = os.path.join(output_dir, f"gpt_scores_{args.version}.jsonl")
    save_jsonl(scored_candidates, output_file)
    logger.info(f"💾 已保存: {output_file}")
    
    # Step 3: 选择Top-K
    top_results = step3_selection(scored_candidates, args.top_k)
    output_file = os.path.join(output_dir, f"top_results_{args.version}.jsonl")
    save_jsonl(top_results, output_file)
    logger.info(f"💾 已保存: {output_file}")
    
    # 完成
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
