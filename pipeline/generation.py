"""
Step 1: Qwen 批量生成对话
"""
import logging
import json
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import client, QWEN_MODEL, build_generation_prompt
from core.schemas import GenerationOutput

logger = logging.getLogger('experiment')


def call_api_structured(model: str, prompt: str, schema_class, max_retries: int = 3):
    """调用API - 使用 JSON 模式"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            # 获取 JSON 字符串并解析为 Pydantic 对象
            json_str = response.choices[0].message.content
            logger.debug(f"LLM 返回的 JSON: {json_str[:200]}...")
            
            # 尝试解析
            try:
                result = schema_class.parse_raw(json_str)
                logger.debug(f"API调用成功 [{model}]: JSON 输出")
                return result
            except Exception as e:
                logger.error(f"JSON 解析失败: {e}")
                logger.error(f"原始内容: {json_str[:500]}")
                raise
                
        except Exception as e:
            logger.warning(f"API调用异常 [{model}] (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
    
    logger.error(f"API调用最终失败 [{model}]")
    return None


def generate_one(task):
    """生成单个候选对话 - 使用结构化输出"""
    idx, question, cand_id = task
    prompt = build_generation_prompt(question)
    
    # 使用结构化输出
    result = call_api_structured(QWEN_MODEL, prompt, GenerationOutput)
    
    if result:
        # 转换为字典格式
        output = {
            "question": result.question,
            "cot": result.cot,
            "dialogue": [turn.dict() for turn in result.dialogue]
        }
        return idx, question, cand_id, output
    else:
        return idx, question, cand_id, None


def step1_qwen_generation(questions: List[str], num_candidates: int) -> List[Dict]:
    """
    Step 1: 使用Qwen并行生成候选对话
    
    Args:
        questions: 问题列表
        num_candidates: 每个问题生成的候选数
    
    Returns:
        候选对话列表
    """
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
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(generate_one, task): task for task in tasks}
        
        for future in as_completed(futures):
            idx, question, cand_id, output = future.result()
            if output:
                results.append({
                    "question_id": idx,
                    "question": question,
                    "candidate_id": cand_id,
                    "output": output,  # 包含 question, cot, dialogue
                    "model": QWEN_MODEL
                })
                dialogue_len = len(output.get('dialogue', []))
                logger.info(f"{idx:<5} {cand_id:<5} {'✓ Success':<10} {dialogue_len:<10}")
            else:
                logger.info(f"{idx:<5} {cand_id:<5} {'✗ Failed':<10} {0:<10}")
    
    logger.info("-"*80)
    logger.info(f"✅ Step 1 完成: {len(results)}/{len(tasks)} 成功\n")
    return results
