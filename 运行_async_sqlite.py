#!/data/zl.zhang/Code/venv/bin/python3
"""
实验主脚本 - 异步版本 + MLflow + SQLite
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path
import logging
import mlflow
import json
from datetime import datetime

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
from pipeline.generation_dual_async import step1_dual_generation_async
from pipeline.scoring_async import step2_gpt_scoring_async
from pipeline.scoring_overall_async import step2_overall_scoring_async
from pipeline.selection import step3_selection
from sqlite_handler import SQLiteHandler, load_prompts_from_file, load_code_snapshots

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
    """异步主函数 - 集成 SQLite + MLflow"""
    # 初始化 SQLite
    db = SQLiteHandler(args.db_path)
    logger = None
    
    try:
        # 配置 MLflow
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
        mlflow.set_experiment("ESC_Experiments")
        
        # 启动 MLflow run
        with mlflow.start_run(run_name=args.version):
            # 设置输出目录
            output_dir = PROJECT_ROOT / 'Outputs' / args.version
            output_dir.mkdir(parents=True, exist_ok=True)
            output_dir = str(output_dir)
            
            # 设置日志（保存到 logs 目录）
            logs_dir = PROJECT_ROOT / 'logs'
            logs_dir.mkdir(exist_ok=True)
            if args.log is None:
                args.log = str(logs_dir / f'experiment_{args.version}.log')
            logger = setup_logger(args.log)
            
            # 日志头
            logger.info("="*80)
            logger.info(f"🧪 实验配置 [{args.version}] - 异步版本 + MLflow + SQLite")
            logger.info("="*80)
            logger.info(f"输入: {args.input} | 问题数: {args.limit}")
            logger.info(f"候选数: {args.candidates} | 评分轮次: {args.score_rounds} | Top-K: {args.top_k}")
            logger.info(f"输出目录: {output_dir}")
            logger.info(f"SQLite 数据库: {args.db_path}")
            logger.info("="*80)
            
            # 加载问题
            questions = load_questions(args.input, args.limit)
            logger.info(f"\n✅ 已加载 {len(questions)} 个问题")
            
            # 加载 prompts 和代码快照
            logger.info("📝 加载 prompts 和代码快照...")
            prompts = load_prompts_from_file('prompts.json')
            code_snapshots = load_code_snapshots()
            
            # 实验配置
            config = {
                "limit": args.limit,
                "candidates": args.candidates,
                "score_rounds": args.score_rounds,
                "top_k": args.top_k,
                "input_file": args.input
            }
            
            # 获取 Git 信息
            git_info = None
            try:
                import subprocess
                git_commit = subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=PROJECT_ROOT
                ).decode('utf-8').strip()
                
                git_branch = subprocess.check_output(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=PROJECT_ROOT
                ).decode('utf-8').strip()
                
                git_status = subprocess.check_output(
                    ['git', 'status', '--porcelain'],
                    cwd=PROJECT_ROOT
                ).decode('utf-8').strip()
                
                git_info = {
                    'commit': git_commit,
                    'branch': git_branch,
                    'is_dirty': str(len(git_status) > 0)
                }
            except:
                pass
            
            # 保存实验到 SQLite（初始状态）
            logger.info("💾 保存实验元数据到 SQLite...")
            db.save_experiment(
                version=args.version,
                config=config,
                input_questions=questions,
                prompts=prompts,
                code_snapshots=code_snapshots,
                git_info=git_info
            )
            if git_info:
                logger.info(f"✅ 实验元数据已保存到 SQLite (Git: {git_info['commit'][:8]})")
            else:
                logger.info("✅ 实验元数据已保存到 SQLite (无 Git 信息)")
            
            # ═══════════════════════════════════════════════════════════
            # 📦 记录完整快照到 MLflow
            # ═══════════════════════════════════════════════════════════
            
            logger.info("\n📦 开始记录完整快照到 MLflow...")
            
            # 1️⃣ 记录实验参数
            logger.info("  ├─ 记录实验参数...")
            mlflow.log_params(config)
            mlflow.log_param("database", args.db_path)
            mlflow.log_metric("num_questions", len(questions))
            
            # 2️⃣ 记录 Git 版本信息
            logger.info("  ├─ 记录 Git 版本...")
            try:
                import subprocess
                
                git_commit = subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=PROJECT_ROOT
                ).decode('utf-8').strip()
                
                git_branch = subprocess.check_output(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=PROJECT_ROOT
                ).decode('utf-8').strip()
                
                git_status = subprocess.check_output(
                    ['git', 'status', '--porcelain'],
                    cwd=PROJECT_ROOT
                ).decode('utf-8').strip()
                
                is_dirty = len(git_status) > 0
                
                mlflow.log_param("git_commit", git_commit[:8])
                mlflow.set_tag("git.commit", git_commit)
                mlflow.set_tag("git.branch", git_branch)
                mlflow.set_tag("git.is_dirty", str(is_dirty))
                
                if is_dirty:
                    logger.warning("     ⚠️  警告: 代码有未提交的更改！")
                    mlflow.set_tag("git.warning", "Uncommitted changes detected")
                    
                    git_diff = subprocess.check_output(
                        ['git', 'diff'],
                        cwd=PROJECT_ROOT
                    ).decode('utf-8')
                    
                    diff_file = Path(output_dir) / "git_diff.patch"
                    with open(diff_file, 'w', encoding='utf-8') as f:
                        f.write(git_diff)
                    mlflow.log_artifact(str(diff_file), artifact_path="code")
                
                logger.info(f"     ✓ Git: {git_commit[:8]} ({git_branch})")
                
            except Exception as e:
                logger.warning(f"     ⚠️  Git 信息获取失败: {e}")
                mlflow.set_tag("git.error", str(e))
            
            # 3️⃣ 记录代码快照（仅核心文件）
            logger.info("  ├─ 记录代码快照...")
            import shutil
            
            # 定义需要记录的核心文件
            core_files = [
                'pipeline/generation_async.py',
                'pipeline/scoring_async.py', 
                'pipeline/selection.py',
                '运行_async_sqlite.py'
            ]
            
            # 可选：config 文件（如果存在）
            if (PROJECT_ROOT / 'config.py').exists():
                core_files.append('config.py')
            
            # 直接记录文件，不创建 code_snapshot 目录
            for file_path in core_files:
                full_path = PROJECT_ROOT / file_path
                if full_path.exists():
                    mlflow.log_artifact(str(full_path), artifact_path="code")
            
            logger.info(f"     ✓ 已保存 {len(core_files)} 个核心代码文件")
            
            # 4️⃣ 记录 Prompts（直接记录源文件）
            logger.info("  ├─ 记录 Prompts...")
            prompts_source_file = PROJECT_ROOT / 'prompts.json'
            if prompts_source_file.exists():
                mlflow.log_artifact(str(prompts_source_file), artifact_path="config")
                logger.info(f"     ✓ 已保存 prompts.json")
            
            # 如果有其他配置文件也可以加上
            if (PROJECT_ROOT / 'config.py').exists():
                mlflow.log_artifact(str(PROJECT_ROOT / 'config.py'), artifact_path="config")
            
            # 5️⃣ 记录输入数据（inputs 目录下的所有文件）
            logger.info("  ├─ 记录输入数据...")
            
            # 记录主输入文件
            if Path(args.input).exists():
                mlflow.log_artifact(args.input, artifact_path="inputs")
            
            # 记录 inputs 目录下的其他文件（如果存在）
            inputs_dir = PROJECT_ROOT / 'inputs'
            if inputs_dir.exists():
                input_files = list(inputs_dir.glob('*'))
                input_files = [f for f in input_files if f.is_file()]  # 只要文件，不要目录
                
                for input_file in input_files:
                    # 避免重复记录主输入文件
                    if str(input_file) != str(Path(args.input).absolute()):
                        mlflow.log_artifact(str(input_file), artifact_path="inputs")
                
                logger.info(f"     ✓ 已保存 {len(input_files)} 个输入文件")
            else:
                logger.info(f"     ✓ 已保存输入文件: {Path(args.input).name}")
            
            logger.info("  └─ 快照记录完成！\n")
            
            # Step 1: 生成候选答案 (根据模式选择)
            logger.info("\n" + "="*80)
            logger.info("🔄 Step 1: 生成候选答案")
            logger.info("="*80)
            
            # 加载自定义prompt（如果提供）
            generation_prompt = None
            if args.generation_prompt_file and Path(args.generation_prompt_file).exists():
                with open(args.generation_prompt_file, 'r', encoding='utf-8') as f:
                    generation_prompt = f.read()
                logger.info(f"📝 使用自定义生成Prompt: {args.generation_prompt_file}")
            
            if args.mode == 'dual':
                # 双模型对话模式
                logger.info(f"模式: 双模型对话 | User: {args.user_model} | Agent: {args.agent_model} | 轮数: {args.dialogue_rounds}")
                candidates = await step1_dual_generation_async(
                    questions, 
                    args.user_model,
                    args.agent_model,
                    args.candidates,
                    args.dialogue_rounds
                )
            else:
                # 单模型生成模式
                logger.info(f"模式: 单模型生成 | 对话轮数: {args.num_turns}")
                candidates = await step1_qwen_generation_async(questions, args.candidates, args.num_turns)
            
            # 保存Step1结果到文件
            raw_file = os.path.join(output_dir, f"qwen_candidates_raw_{args.version}.json")
            save_json(candidates, raw_file)
            logger.info(f"💾 已保存原始数据: {raw_file}")
            
            formatted_gen = format_generation_output(candidates)
            gen_file = os.path.join(output_dir, f"1_generation_{args.version}.json")
            save_json(formatted_gen, gen_file)
            logger.info(f"💾 已保存生成结果: {gen_file}")
            
            # 更新 SQLite - Step1输出
            logger.info("💾 保存 Step1 结果到 SQLite...")
            db.update_experiment_outputs(
                version=args.version,
                step1_generation=formatted_gen
            )
            
            mlflow.log_metric("num_candidates_generated", len(candidates))
            
            # Step 2: 评分 (根据模式选择)
            logger.info("\n" + "="*80)
            logger.info("🔄 Step 2: 评分")
            logger.info("="*80)
            
            # 加载自定义prompt（如果提供）
            scoring_prompt = None
            if args.scoring_prompt_file and Path(args.scoring_prompt_file).exists():
                with open(args.scoring_prompt_file, 'r', encoding='utf-8') as f:
                    scoring_prompt = f.read()
                logger.info(f"📝 使用自定义打分Prompt: {args.scoring_prompt_file}")
            
            if args.scoring_mode == 'overall':
                # 整体打分模式
                logger.info(f"模式: 整体打分 | 模型: {args.scoring_model} | Top-K: {args.scoring_top_k or '全部'}")
                scored_candidates = await step2_overall_scoring_async(
                    candidates,
                    scoring_prompt=scoring_prompt,
                    score_rounds=args.score_rounds,
                    top_k=args.scoring_top_k
                )
            else:
                # 逐轮打分模式
                logger.info(f"模式: 逐轮打分 | 模型: {args.scoring_model} | Top-K: {args.scoring_top_k or '全部'}")
                scored_candidates = await step2_gpt_scoring_async(
                    candidates,
                    args.score_rounds,
                    scoring_mode=args.scoring_mode,
                    scoring_prompt=scoring_prompt,
                    top_k=args.scoring_top_k
                )
            
            # 保存Step2结果到文件
            raw_scores_file = os.path.join(output_dir, f"gpt_scores_raw_{args.version}.json")
            save_json(scored_candidates, raw_scores_file)
            logger.info(f"💾 已保存原始评分: {raw_scores_file}")
            
            formatted_scores = format_scoring_output(scored_candidates)
            scores_file = os.path.join(output_dir, f"2_scores_{args.version}.json")
            save_json(formatted_scores, scores_file)
            logger.info(f"💾 已保存评分结果: {scores_file}")
            
            # 更新 SQLite - Step2输出
            logger.info("💾 保存 Step2 结果到 SQLite...")
            db.update_experiment_outputs(
                version=args.version,
                step2_scores=formatted_scores
            )
            
            # 计算统计信息
            if scored_candidates:
                avg_empathy = sum(c['scores']['Empathy'] for c in scored_candidates) / len(scored_candidates)
                avg_supportiveness = sum(c['scores']['Supportiveness'] for c in scored_candidates) / len(scored_candidates)
                avg_guidance = sum(c['scores']['Guidance'] for c in scored_candidates) / len(scored_candidates)
                avg_safety = sum(c['scores']['Safety'] for c in scored_candidates) / len(scored_candidates)
                avg_total = sum(c['scores']['Total'] for c in scored_candidates) / len(scored_candidates)
                
                statistics = {
                    "avg_empathy": avg_empathy,
                    "avg_supportiveness": avg_supportiveness,
                    "avg_guidance": avg_guidance,
                    "avg_safety": avg_safety,
                    "avg_total_score": avg_total,
                    "num_candidates": len(scored_candidates)
                }
                
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
            else:
                statistics = {}
            
            # Step 3: 生成最终结果
            logger.info("\n" + "="*80)
            logger.info("🔄 Step 3: 生成最终结果")
            logger.info("="*80)
            final_results = format_final_output(scored_candidates)
            final_file = os.path.join(output_dir, f"3_final_results_{args.version}.json")
            save_json(final_results, final_file)
            logger.info(f"💾 已保存最终结果: {final_file}")
            
            # 更新 SQLite - Step3输出和完成状态
            logger.info("💾 保存 Step3 结果到 SQLite...")
            db.update_experiment_outputs(
                version=args.version,
                step3_final=final_results,
                statistics=statistics,
                status='completed'
            )
            
            mlflow.log_metric("num_final_results", len(final_results))
            
            # 6️⃣ 记录输出结果到 MLflow（仅核心结果文件）
            logger.info("📦 记录输出结果到 MLflow...")
            
            # 只记录核心输出文件
            output_files = [
                gen_file,           # 1_generation_xxx.json
                scores_file,        # 2_scores_xxx.json  
                final_file,         # 3_final_results_xxx.json
                args.log            # 实验日志
            ]
            
            for file_path in output_files:
                if Path(file_path).exists():
                    mlflow.log_artifact(file_path, artifact_path="outputs")
            
            logger.info(f"  ✓ 已记录 {len(output_files)} 个核心输出文件")
            
            # 7️⃣ 记录实验摘要（使用 MLflow 的 dict 功能）
            logger.info("\n📊 记录实验摘要...")
            summary = {
                "version": args.version,
                "git_commit": git_info.get('commit', 'N/A') if git_info else 'N/A',
                "git_branch": git_info.get('branch', 'N/A') if git_info else 'N/A',
                "config": config,
                "statistics": statistics,
                "num_questions": len(questions),
                "num_prompts": len(prompts) if prompts else 0,
                "timestamp": datetime.now().isoformat()
            }
            
            # 直接用 MLflow 的 log_dict，不保存到文件
            mlflow.log_dict(summary, "summary/experiment_summary.json")
            logger.info("  ✓ 实验摘要已记录")
            
            # 完成
            logger.info("\n" + "="*80)
            logger.info("🎉 实验完成！")
            logger.info("="*80)
            logger.info(f"输出目录: {output_dir}")
            logger.info(f"📊 MLflow Run ID: {mlflow.active_run().info.run_id}")
            logger.info(f"💾 SQLite 数据库: {args.db_path}")
            logger.info(f"💾 实验版本: {args.version}")
            logger.info("="*80)
            
    except Exception as e:
        if logger:
            logger.error(f"\n❌ 实验失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        # 更新状态为失败
        try:
            db.update_experiment_outputs(
                version=args.version,
                status='failed'
            )
        except:
            pass
        
        raise
    finally:
        # 关闭数据库连接
        db.close()

def main():
    parser = argparse.ArgumentParser(description='运行实验 - 异步版本 + MLflow + SQLite')
    parser.add_argument('--limit', type=int, default=10, help='问题数量限制')
    parser.add_argument('--candidates', type=int, default=2, help='每条问题生成候选数')
    parser.add_argument('--score-rounds', type=int, default=3, help='每个候选评分次数')
    parser.add_argument('--version', type=str, default='v1_sqlite', help='实验版本号')
    parser.add_argument('--top-k', type=int, default=5, help='选择Top-K')
    parser.add_argument('--input', type=str, default=str(PROJECT_ROOT / 'inputs' / 'questions.txt'), help='输入文件')
    parser.add_argument('--log', type=str, default=None, help='日志文件路径')
    parser.add_argument('--db-path', type=str, default='experiments.db', help='SQLite 数据库文件路径')
    
    # 新增：对话模式参数
    parser.add_argument('--mode', type=str, default='single', choices=['single', 'dual'], help='对话生成模式: single=单模型, dual=双模型')
    parser.add_argument('--num-turns', type=int, default=5, help='单模型生成对话轮数')
    parser.add_argument('--user-model', type=str, default='qwen-max', help='双模型模式下的User模型')
    parser.add_argument('--agent-model', type=str, default='gpt-4o-mini', help='双模型模式下的Agent模型')
    parser.add_argument('--dialogue-rounds', type=int, default=3, help='双模型对话轮数')
    
    # 新增：打分模式参数
    parser.add_argument('--scoring-mode', type=str, default='per_turn', choices=['per_turn', 'overall'], help='打分模式: per_turn=逐轮打分, overall=整体打分')
    parser.add_argument('--scoring-model', type=str, default='gpt-4o-mini', help='打分使用的模型')
    parser.add_argument('--scoring-top-k', type=int, default=None, help='每个问题保留前K个结果（None=全部保留）')
    parser.add_argument('--generation-prompt-file', type=str, default=None, help='自定义生成prompt文件路径')
    parser.add_argument('--scoring-prompt-file', type=str, default=None, help='自定义打分prompt文件路径')
    
    args = parser.parse_args()
    
    # 运行异步主函数
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()