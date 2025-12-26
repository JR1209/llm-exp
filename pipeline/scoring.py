"""
Step 2: GPT 多轮评分
"""
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import client, GPT_MODEL, build_evaluation_prompt
from core.schemas import EvaluationOutput

logger = logging.getLogger('experiment')


def call_api_structured(model: str, prompt: str, schema_class, max_retries: int = 3):
    """调用API - 使用 JSON 模式 + Pydantic 验证"""
    for attempt in range(max_retries):
        try:
            # 使用标准 API（兼容公司内部接口）
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            # 获取 JSON 字符串并用 Pydantic 验证
            json_str = response.choices[0].message.content
            
            # 使用 Pydantic 解析和验证
            result = schema_class.model_validate_json(json_str)
            logger.debug(f"API调用成功 [{model}]: JSON 输出已验证")
            return result
                
        except Exception as e:
            logger.warning(f"API调用异常 [{model}] (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
    
    logger.error(f"API调用最终失败 [{model}]")
    return None


def score_one_round(candidate, round_idx):
    """单轮评分 - 使用结构化输出"""
    # 格式化对话内容
    output = candidate.get('output', {})
    dialogue = output.get('dialogue', [])
    
    if isinstance(dialogue, list):
        # JSON 格式的对话列表
        dialogue_str = '\n'.join([f"{msg['role']}: {msg['content']}" for msg in dialogue])
    else:
        # 纯文本（兼容旧格式）
        dialogue_str = str(dialogue)
    
    prompt = build_evaluation_prompt(dialogue_str)
    
    # 使用结构化输出
    result = call_api_structured(GPT_MODEL, prompt, EvaluationOutput)
    
    if result:
        return result.dict()
    return None


def step2_gpt_scoring(candidates: List[Dict], num_rounds: int) -> List[Dict]:
    """
    Step 2: 使用GPT并行评分
    
    Args:
        candidates: 候选对话列表
        num_rounds: 每个候选的评分轮次
    
    Returns:
        评分结果列表
    """
    logger.info("\n" + "="*80)
    logger.info("Step 2: GPT Multi-round Scoring (Parallel)")
    logger.info("="*80)
    logger.info(f"候选数: {len(candidates)} | 评分轮次: {num_rounds} | 并行数: 100")
    logger.info(f"\n{'QID':<5} {'CID':<5} {'Emp':<6} {'Sup':<6} {'Gui':<6} {'Saf':<6} {'Total':<8}")
    logger.info("-"*80)
    
    results = []
    
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
                "output": candidate.get('output', {}),  # 包含 question, cot, dialogue
                "scores": avg_scores,
                "score_details": all_scores
            })
    
    logger.info("-"*80)
    logger.info(f"✅ Step 2 完成: {len(results)} 个候选评分完成\n")
    return results
