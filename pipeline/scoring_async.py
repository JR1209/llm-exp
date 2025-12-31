"""
Step 2: GPT 多轮评分 - 异步版本
"""
import logging
import asyncio
from typing import List, Dict

from config_async import client, GPT_MODEL, build_evaluation_prompt
from core.schemas import EvaluationOutput

logger = logging.getLogger('experiment')


async def call_api_structured_async(model: str, prompt: str, schema_class, max_retries: int = 3):
    """异步调用API"""
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            json_str = response.choices[0].message.content
            result = schema_class.model_validate_json(json_str)
            logger.debug(f"API调用成功 [{model}]: JSON 输出已验证")
            return result
                
        except Exception as e:
            logger.warning(f"API调用异常 [{model}] (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
    
    logger.error(f"API调用最终失败 [{model}]")
    return None


async def score_one_round_async(candidate, round_idx):
    """异步单轮评分"""
    output = candidate.get('output', {})
    dialogue = output.get('dialogue', [])
    
    if isinstance(dialogue, list):
        dialogue_str = '\n'.join([f"{msg['role']}: {msg['content']}" for msg in dialogue])
    else:
        dialogue_str = str(dialogue)
    
    prompt = build_evaluation_prompt(dialogue_str)
    result = await call_api_structured_async(GPT_MODEL, prompt, EvaluationOutput)
    
    if result:
        return result.dict()
    return None


async def step2_gpt_scoring_async(
    candidates: List[Dict], 
    num_rounds: int,
    scoring_mode: str = 'per_turn',
    scoring_prompt: str = None,
    top_k: int = None
) -> List[Dict]:
    """
    Step 2: 使用GPT异步评分
    
    Args:
        candidates: 候选列表
        num_rounds: 评分轮次
        scoring_mode: 'per_turn' 或 'overall' (保留参数，实际由外部路由)
        scoring_prompt: 自定义评分prompt
        top_k: 每个问题保留前K个（None表示全部保留）
    """
    logger.info("\n" + "="*80)
    logger.info("Step 2: GPT Multi-round Scoring (Async)")
    logger.info("="*80)
    logger.info(f"候选数: {len(candidates)} | 评分轮次: {num_rounds}")
    logger.info(f"\n{'QID':<5} {'CID':<5} {'Emp':<6} {'Sup':<6} {'Gui':<6} {'Saf':<6} {'Total':<8}")
    logger.info("-"*80)
    
    results = []
    
    # 对每个候选进行多轮评分
    for candidate in candidates:
        # 异步并发评分多轮
        tasks = [score_one_round_async(candidate, i) for i in range(num_rounds)]
        all_scores = await asyncio.gather(*tasks)
        
        # 过滤None
        all_scores = [s for s in all_scores if s is not None]
        
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
                "output": candidate.get('output', {}),
                "scores": avg_scores,
                "score_details": all_scores
            })
    
    logger.info("-"*80)
    logger.info(f"✅ Step 2 完成: {len(results)} 个候选评分完成\n")
    
    # Top-K筛选（如果指定）
    if top_k is not None and top_k > 0:
        # 按问题分组
        by_question = {}
        for item in results:
            qid = item['question_id']
            if qid not in by_question:
                by_question[qid] = []
            by_question[qid].append(item)
        
        # 每个问题保留Top-K
        filtered_results = []
        for qid, items in by_question.items():
            sorted_items = sorted(items, key=lambda x: x['scores']['Total'], reverse=True)
            filtered_results.extend(sorted_items[:top_k])
        
        logger.info(f"📊 Top-K筛选: {len(results)} → {len(filtered_results)}")
        return filtered_results
    
    return results
