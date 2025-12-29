#!/usr/bin/env python3
"""
实验主脚本 - 异步版本 + MLflow 追踪
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path
import logging
import mlflow

PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from utils.io_handler import (
    load_questions,
    save_json,
    format_generation_output,
    format_scoring_output,
    format_final_output
)
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
    # 配置 MLflow
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("ESC_Experiments")
    
    # 启动 MLflow run
    with mlflow.start_run(run_name=args.version):
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
        logger.info(f"🧪 实验配置 [{args.version}] - 异步版本 + MLflow")
        logger.info("="*80)
        logger.info(f"输入: {args.input} | 问题数: {args.limit}")
        logger.info(f"候选数: {args.candidates} | 评分轮次: {args.score_rounds} | Top-K: {args.top_k}")
        logger.info(f"输出目录: {output_dir}")
        logger.info("="*80)
        
        # 记录实验参数到 MLflow
        mlflow.log_params({
            "version": args.version,
            "limit": args.limit,
            "candidates": args.candidates,
            "score_rounds": args.score_rounds,
            "top_k": args.top_k,
            "input_file": args.input
        })
        
        # 加载数据
        questions = load_questions(args.input, args.limit)
        logger.info(f"\n✅ 已加载 {len(questions)} 个问题")
        mlflow.log_metric("num_questions", len(questions))
        
        # Step 1: Qwen生成 (异步)
        candidates = await step1_qwen_generation_async(questions, args.candidates)
        
        # 保存原始生成结果
        raw_file = os.path.join(output_dir, f"qwen_candidates_raw_{args.version}.json")
        save_json(candidates, raw_file)
        logger.info(f"💾 已保存原始数据: {raw_file}")
        
        # 保存格式化的生成结果
        formatted_gen = format_generation_output(candidates)
        gen_file = os.path.join(output_dir, f"1_generation_{args.version}.json")
        save_json(formatted_gen, gen_file)
        logger.info(f"💾 已保存生成结果: {gen_file}")
        mlflow.log_metric("num_candidates_generated", len(candidates))
        
        # Step 2: GPT评分 (异步)
        scored_candidates = await step2_gpt_scoring_async(candidates, args.score_rounds)
        
        # 保存原始评分结果
        raw_scores_file = os.path.join(output_dir, f"gpt_scores_raw_{args.version}.json")
        save_json(scored_candidates, raw_scores_file)
        logger.info(f"💾 已保存原始评分: {raw_scores_file}")
        
        # 保存格式化的评分结果
        formatted_scores = format_scoring_output(scored_candidates)
        scores_file = os.path.join(output_dir, f"2_scores_{args.version}.json")
        save_json(formatted_scores, scores_file)
        logger.info(f"💾 已保存评分结果: {scores_file}")
        
        # 计算并记录平均分数
        if scored_candidates:
            avg_empathy = sum(c['scores']['Empathy'] for c in scored_candidates) / len(scored_candidates)
            avg_supportiveness = sum(c['scores']['Supportiveness'] for c in scored_candidates) / len(scored_candidates)
            avg_guidance = sum(c['scores']['Guidance'] for c in scored_candidates) / len(scored_candidates)
            avg_safety = sum(c['scores']['Safety'] for c in scored_candidates) / len(scored_candidates)
            avg_total = sum(c['scores']['Total'] for c in scored_candidates) / len(scored_candidates)
            
            mlflow.log_metrics({
                "avg_empathy": avg_empathy,
                "avg_supportiveness": avg_supportiveness,
                "avg_guidance": avg_guidance,
                "avg_safety": avg_safety,
                "avg_total_score": avg_total
            })
            
            logger.info(f"\n📊 平均分数:")
            logger.info(f"  Empathy: {avg_empathy:.2f}")
            logger.info(f"  Supportiveness: {avg_supportiveness:.2f}")
            logger.info(f"  Guidance: {avg_guidance:.2f}")
            logger.info(f"  Safety: {avg_safety:.2f}")
            logger.info(f"  Total: {avg_total:.2f}")
        
        # Step 3: 生成最终结果
        final_results = format_final_output(scored_candidates)
        final_file = os.path.join(output_dir, f"3_final_results_{args.version}.json")
        save_json(final_results, final_file)
        logger.info(f"💾 已保存最终结果: {final_file}")
        mlflow.log_metric("num_final_results", len(final_results))
        
        # 记录输入输出文件到 MLflow
        mlflow.log_artifact(args.input, artifact_path="inputs")
        mlflow.log_artifacts(output_dir, artifact_path="outputs")
        
        # 完成
        logger.info("\n" + "="*80)
        logger.info("🎉 实验完成！")
        logger.info("="*80)
        logger.info(f"输出目录: {output_dir}")
        logger.info(f"📊 MLflow Run ID: {mlflow.active_run().info.run_id}")
        logger.info("="*80)

def main():
    parser = argparse.ArgumentParser(description='运行实验 - 异步版本 + MLflow')
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