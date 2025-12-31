"""
Step 1: Qwen 批量生成对话 - 异步版本
"""
import logging
import asyncio
from typing import List, Dict

from config_async import client, QWEN_MODEL, build_generation_prompt
from core.schemas import GenerationOutput

logger = logging.getLogger('experiment')


async def call_api_structured_async(model: str, prompt: str, schema_class, max_retries: int = 3):
    """异步调用API - 使用 JSON 模式 + Pydantic 验证"""
    for attempt in range(max_retries):
        try:
            # 使用异步 API
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            json_str = response.choices[0].message.content
            logger.debug(f"LLM 返回: {json_str[:200]}...")
            
            result = schema_class.model_validate_json(json_str)
            logger.debug(f"API调用成功 [{model}]: JSON 输出已验证")
            return result
                
        except Exception as e:
            logger.warning(f"API调用异常 [{model}] (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)  # 异步睡眠
    
    logger.error(f"API调用最终失败 [{model}]")
    return None


async def generate_one_async(task):
    """异步生成单个候选对话"""
    idx, question, cand_id, num_turns = task
    prompt = build_generation_prompt(question, num_turns)
    
    result = await call_api_structured_async(QWEN_MODEL, prompt, GenerationOutput)
    
    if result:
        output = {
            "question": result.question,
            "cot": result.cot,
            "dialogue": [turn.dict() for turn in result.dialogue]
        }
        return idx, question, cand_id, output
    else:
        return idx, question, cand_id, None


async def step1_qwen_generation_async(questions: List[str], num_candidates: int, num_turns: int = 5) -> List[Dict]:
    """
    Step 1: 使用Qwen异步生成候选对话
    
    Args:
        questions: 问题列表
        num_candidates: 每个问题生成的候选数
        num_turns: 生成的对话轮数
    """
    logger.info("\n" + "="*80)
    logger.info("Step 1: Qwen Batch Generation (Async)")
    logger.info("="*80)
    logger.info(f"问题数: {len(questions)} | 每题候选: {num_candidates} | 对话轮数: {num_turns}")
    logger.info(f"\n{'QID':<5} {'CID':<5} {'Status':<10} {'Length':<10}")
    logger.info("-"*80)
    
    results = []
    tasks = []
    
    # 构建任务列表
    for idx, question in enumerate(questions, 1):
        for cand_idx in range(num_candidates):
            tasks.append((idx, question, cand_idx + 1, num_turns))
    
    # 异步并发执行
    coroutines = [generate_one_async(task) for task in tasks]
    completed_results = await asyncio.gather(*coroutines)
    
    # 处理结果
    for idx, question, cand_id, output in completed_results:
        if output:
            results.append({
                "question_id": idx,
                "question": question,
                "candidate_id": cand_id,
                "output": output,
                "model": QWEN_MODEL
            })
            dialogue_len = len(output.get('dialogue', []))
            logger.info(f"{idx:<5} {cand_id:<5} {'✓ Success':<10} {dialogue_len:<10}")
        else:
            logger.info(f"{idx:<5} {cand_id:<5} {'✗ Failed':<10} {0:<10}")
    
    logger.info("-"*80)
    logger.info(f"✅ Step 1 完成: {len(results)}/{len(tasks)} 成功\n")
    return results
