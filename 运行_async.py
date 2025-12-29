#!/usr/bin/env python3
"""
实验主脚本 - 异步版本
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from utils.io_handler import load_questions, save_json
from pipeline.generation_async import step1_qwen_generation_async
from pipeline.scoring_async import step2_gpt_scoring_async
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


async def main_async(args):
    """异步主函数"""
    # 设置输出目录
    output_dir = PROJECT_ROOT / 'Outputs' / args.version
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir = str(output_dir)
    
    # 设置日志
    if args.log is None:
        args.log = os.path.join(output_dir, f'experiment_{args.version}.log')
    
    logger = setup_logger(args.log)
    
    # 日志头
    logger.info("="*80)
    logger.info(f"🧪 实验配置 [{args.version}] - 异步版本")
    logger.info("="*80)
    logger.info(f"输入: {args.input} | 问题数: {args.limit}")
    logger.info(f"候选数: {args.candidates} | 评分轮次: {args.score_rounds} | Top-K: {args.top_k}")
    logger.info(f"输出目录: {output_dir}")
    logger.info("="*80)
    
    # 加载数据
    questions = load_questions(args.input, args.limit)
    logger.info(f"\n✅ 已加载 {len(questions)} 个问题")
    
    # Step 1: Qwen生成 (异步)
    candidates = await step1_qwen_generation_async(questions, args.candidates)
    output_file = os.path.join(output_dir, f"qwen_candidates_{args.version}.json")
    save_json(candidates, output_file)
    logger.info(f"💾 已保存: {output_file}")
    
    # Step 2: GPT评分 (异步)
    scored_candidates = await step2_gpt_scoring_async(candidates, args.score_rounds)
    output_file = os.path.join(output_dir, f"gpt_scores_{args.version}.json")
    save_json(scored_candidates, output_file)
    logger.info(f"💾 已保存: {output_file}")
    
    # Step 3: 选择Top-K (同步,不需要改)
    top_results = step3_selection(scored_candidates, args.top_k)
    output_file = os.path.join(output_dir, f"top_results_{args.version}.json")
    save_json(top_results, output_file)
    logger.info(f"💾 已保存: {output_file}")
    
    # 完成
    logger.info("\n" + "="*80)
    logger.info("🎉 实验完成！")
    logger.info("="*80)
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"  - qwen_candidates_{args.version}.json")
    logger.info(f"  - gpt_scores_{args.version}.json")
    logger.info(f"  - top_results_{args.version}.json")
    logger.info(f"  - experiment_{args.version}.log")
    logger.info("="*80)


def main():
    parser = argparse.ArgumentParser(description='运行实验 - 异步版本')
    parser.add_argument('--limit', type=int, default=10, help='问题数量限制')
    parser.add_argument('--candidates', type=int, default=2, help='每条问题生成候选数')
    parser.add_argument('--score-rounds', type=int, default=3, help='每个候选评分次数')
    parser.add_argument('--version', type=str, default='v1_async', help='实验版本号')
    parser.add_argument('--top-k', type=int, default=5, help='选择Top-K')
    parser.add_argument('--input', type=str, default=str(PROJECT_ROOT / 'inputs' / 'questions.txt'), help='输入文件')
    parser.add_argument('--log', type=str, default=None, help='日志文件路径')
    
    args = parser.parse_args()
    
    # 运行异步主函数
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
