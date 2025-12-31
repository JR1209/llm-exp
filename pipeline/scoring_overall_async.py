"""
Step 2B: 整体打分 - 异步版本
对完整对话JSON进行整体评估
"""
import logging
import asyncio
import json
from typing import List, Dict

from config_async import client, GPT_MODEL, build_overall_evaluation_prompt
from core.schemas import EvaluationOutput

logger = logging.getLogger('experiment')


async def call_scoring_api_async(model: str, prompt: str, max_retries: int = 3):
    """异步调用评分API"""
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )
            
            json_str = response.choices[0].message.content
            result = EvaluationOutput.model_validate_json(json_str)
            return result
                
        except Exception as e:
            logger.warning(f"评分API调用异常 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
    
    logger.error(f"评分API调用最终失败")
    return None


async def score_one_overall_async(candidate: Dict, scoring_prompt: str = None, num_rounds: int = 3):
    """
    对单个候选对话进行整体评分（多轮求平均）
    
    Args:
        candidate: 候选对话数据
        scoring_prompt: 自定义评分prompt（可选）
        num_rounds: 评分轮次
    """
    dialogue_json = json.dumps(candidate['output'], ensure_ascii=False, indent=2)
    
    # 使用自定义prompt或默认prompt
    if scoring_prompt:
        prompt = scoring_prompt.format(dialogue_json=dialogue_json)
    else:
        prompt = build_overall_evaluation_prompt(dialogue_json)
    
    # 多轮评分
    scores_list = []
    for round_idx in range(num_rounds):
        result = await call_scoring_api_async(GPT_MODEL, prompt)
        if result:
            scores_list.append({
                'Empathy': result.Empathy,
                'Supportiveness': result.Supportiveness,
                'Guidance': result.Guidance,
                'Safety': result.Safety
            })
    
    if not scores_list:
        return None
    
    # 计算平均分
    avg_scores = {
        'Empathy': sum(s['Empathy'] for s in scores_list) / len(scores_list),
        'Supportiveness': sum(s['Supportiveness'] for s in scores_list) / len(scores_list),
        'Guidance': sum(s['Guidance'] for s in scores_list) / len(scores_list),
        'Safety': sum(s['Safety'] for s in scores_list) / len(scores_list)
    }
    avg_scores['Total'] = sum(avg_scores.values())
    
    return {
        **candidate,
        'scores': avg_scores,
        'score_details': scores_list  # 保留每轮的详细分数
    }


async def step2_overall_scoring_async(
    candidates: List[Dict], 
    scoring_prompt: str = None,
    score_rounds: int = 3,
    top_k: int = None
) -> List[Dict]:
    """
    Step 2: 整体打分（异步）
    
    Args:
        candidates: 候选对话列表
        scoring_prompt: 自定义评分prompt
        score_rounds: 每个候选评分轮次
        top_k: 每个问题保留前K个结果（None表示保留全部）
    """
    logger.info("\n" + "="*80)
    logger.info("Step 2: Overall Scoring (Async)")
    logger.info("="*80)
    logger.info(f"候选数: {len(candidates)} | 评分轮次: {score_rounds} | Top-K: {top_k or '全部'}")
    logger.info(f"\n{'QID':<5} {'CID':<5} {'Emp':<6} {'Sup':<6} {'Gui':<6} {'Saf':<6} {'Total':<7}")
    logger.info("-"*80)
    
    # 异步并发评分
    tasks = [score_one_overall_async(c, scoring_prompt, score_rounds) for c in candidates]
    scored_results = await asyncio.gather(*tasks)
    
    # 过滤失败的结果
    scored_candidates = [r for r in scored_results if r is not None]
    
    # 显示评分结果
    for item in scored_candidates:
        scores = item['scores']
        logger.info(
            f"{item['question_id']:<5} {item['candidate_id']:<5} "
            f"{scores['Empathy']:<6.2f} {scores['Supportiveness']:<6.2f} "
            f"{scores['Guidance']:<6.2f} {scores['Safety']:<6.2f} "
            f"{scores['Total']:<7.2f}"
        )
    
    logger.info("-"*80)
    logger.info(f"✅ Step 2 完成: {len(scored_candidates)} 个候选评分完成\n")
    
    # Top-K筛选（如果指定）
    if top_k is not None and top_k > 0:
        # 按问题分组
        by_question = {}
        for item in scored_candidates:
            qid = item['question_id']
            if qid not in by_question:
                by_question[qid] = []
            by_question[qid].append(item)
        
        # 每个问题保留Top-K
        filtered_results = []
        for qid, items in by_question.items():
            sorted_items = sorted(items, key=lambda x: x['scores']['Total'], reverse=True)
            filtered_results.extend(sorted_items[:top_k])
        
        logger.info(f"📊 Top-K筛选: {len(scored_candidates)} → {len(filtered_results)}")
        return filtered_results
    
    return scored_candidates
