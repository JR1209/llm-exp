"""
Step 1B: 双模型对话生成 - 异步版本
User模型和Agent模型交替对话
"""
import logging
import asyncio
from typing import List, Dict

from config_async import client, AVAILABLE_MODELS, GENERATION_NUM_TURNS
from core.schemas import GenerationOutput

logger = logging.getLogger('experiment')


def build_user_prompt(question: str, conversation_history: List[Dict] = None) -> str:
    """构建User模型的prompt"""
    if conversation_history is None or len(conversation_history) == 0:
        # 第一轮：用户提出问题
        return f"""你是一个寻求心理咨询帮助的用户。

你当前的困扰是：{question}

请表达你的困扰和感受，开始这次心理咨询对话。要求：
1. 真实表达你的情绪和想法
2. 说明你遇到的具体情况
3. 保持自然的对话风格
4. 字数控制在50-150字

直接输出你要说的话，不要添加任何前缀或解释。"""
    else:
        # 后续轮次：根据咨询师的回复继续对话
        agent_last = conversation_history[-1]['content']
        return f"""你是一个寻求心理咨询帮助的用户。

咨询师刚才对你说：
{agent_last}

请根据咨询师的回复继续对话。要求：
1. 回应咨询师的建议或问题
2. 可以提出新的疑问或分享更多细节
3. 保持自然的对话风格
4. 字数控制在50-150字

直接输出你要说的话，不要添加任何前缀或解释。"""


def build_agent_prompt(question: str, conversation_history: List[Dict]) -> str:
    """构建Agent模型的prompt"""
    user_last = conversation_history[-1]['content']
    
    context = ""
    if len(conversation_history) > 1:
        context = "\n\n之前的对话：\n"
        for i, turn in enumerate(conversation_history[:-1]):
            speaker = "用户" if turn['speaker'] == 'user' else "你"
            context += f"{speaker}: {turn['content']}\n"
    
    return f"""你是一位专业的心理咨询师，正在为用户提供心理咨询服务。

用户的核心问题是：{question}
{context}

用户刚才对你说：
{user_last}

请作为心理咨询师回复用户。要求：
1. 展现共情和理解
2. 提供专业的建议或引导
3. 适当提出探索性问题
4. 保持温暖、支持的语气
5. 字数控制在80-200字

直接输出你要说的话，不要添加任何前缀或解释。"""


async def call_model_async(model: str, prompt: str, max_retries: int = 3) -> str:
    """异步调用模型生成文本"""
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            # 检查响应是否有效
            if response and response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if message and message.content:
                    return message.content.strip()
            
            logger.warning(f"API返回空响应 [{model}] (尝试 {attempt+1}/{max_retries})")
                
        except Exception as e:
            logger.warning(f"API调用异常 [{model}] (尝试 {attempt+1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(2)
    
    logger.error(f"API调用最终失败 [{model}]")
    return None


async def generate_dual_dialogue_async(
    question: str, 
    user_model: str, 
    agent_model: str, 
    num_rounds: int = 3
) -> Dict:
    """
    双模型对话生成
    
    Args:
        question: 用户问题
        user_model: User模型名称
        agent_model: Agent模型名称
        num_rounds: 对话轮数
    
    Returns:
        包含完整对话的字典
    """
    conversation = []
    
    # CoT: 记录对话生成思路
    cot = f"使用双模型对话模式生成，User模型: {user_model}, Agent模型: {agent_model}, 轮数: {num_rounds}"
    
    for round_num in range(num_rounds):
        # User发言
        user_prompt = build_user_prompt(question, conversation)
        user_response = await call_model_async(user_model, user_prompt)
        
        if user_response is None:
            logger.error(f"User模型生成失败 (Round {round_num + 1})")
            break
        
        conversation.append({
            "speaker": "user",
            "content": user_response
        })
        
        # Agent回复
        agent_prompt = build_agent_prompt(question, conversation)
        agent_response = await call_model_async(agent_model, agent_prompt)
        
        if agent_response is None:
            logger.error(f"Agent模型生成失败 (Round {round_num + 1})")
            break
        
        conversation.append({
            "speaker": "agent",
            "content": agent_response
        })
    
    return {
        "question": question,
        "cot": cot,
        "dialogue": conversation
    }


async def generate_one_dual_async(task):
    """异步生成单个双模型对话候选"""
    idx, question, cand_id, user_model, agent_model, num_rounds = task
    
    result = await generate_dual_dialogue_async(
        question, 
        user_model, 
        agent_model, 
        num_rounds
    )
    
    if result and len(result['dialogue']) > 0:
        return idx, question, cand_id, result
    else:
        return idx, question, cand_id, None


async def step1_dual_generation_async(
    questions: List[str], 
    user_model_name: str,
    agent_model_name: str,
    num_candidates: int,
    num_rounds: int = 3
) -> List[Dict]:
    """
    Step 1: 使用双模型异步生成候选对话
    
    Args:
        questions: 问题列表
        user_model_name: User模型键名
        agent_model_name: Agent模型键名
        num_candidates: 每个问题生成的候选数
        num_rounds: 每个对话的轮数
    """
    # 获取实际模型名称
    user_model = AVAILABLE_MODELS.get(user_model_name, user_model_name)
    agent_model = AVAILABLE_MODELS.get(agent_model_name, agent_model_name)
    
    logger.info("\n" + "="*80)
    logger.info("Step 1: Dual-Model Dialogue Generation (Async)")
    logger.info("="*80)
    logger.info(f"问题数: {len(questions)} | 每题候选: {num_candidates}")
    logger.info(f"User模型: {user_model} | Agent模型: {agent_model} | 对话轮数: {num_rounds}")
    logger.info(f"\n{'QID':<5} {'CID':<5} {'Status':<10} {'Turns':<10}")
    logger.info("-"*80)
    
    results = []
    tasks = []
    
    # 构建任务列表
    for idx, question in enumerate(questions, 1):
        for cand_idx in range(num_candidates):
            tasks.append((idx, question, cand_idx + 1, user_model, agent_model, num_rounds))
    
    # 异步并发执行
    coroutines = [generate_one_dual_async(task) for task in tasks]
    completed_results = await asyncio.gather(*coroutines)
    
    # 处理结果
    for idx, question, cand_id, output in completed_results:
        if output:
            results.append({
                "question_id": idx,
                "question": question,
                "candidate_id": cand_id,
                "mode": "dual",
                "models": {
                    "user": user_model,
                    "agent": agent_model
                },
                "output": output
            })
            turns = len(output.get('dialogue', []))
            logger.info(f"{idx:<5} {cand_id:<5} {'✓ Success':<10} {turns:<10}")
        else:
            logger.info(f"{idx:<5} {cand_id:<5} {'✗ Failed':<10} {0:<10}")
    
    logger.info("-"*80)
    logger.info(f"✅ Step 1 完成: {len(results)}/{len(tasks)} 成功\n")
    return results