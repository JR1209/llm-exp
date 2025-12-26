"""
Step 3: Top-K 选择
"""
import logging
from typing import List, Dict

logger = logging.getLogger('experiment')


def step3_selection(scored_candidates: List[Dict], top_k: int) -> List[Dict]:
    """
    Step 3: 根据总分选择Top-K
    
    Args:
        scored_candidates: 评分结果列表
        top_k: 选择前 K 个
    
    Returns:
        Top-K 结果列表
    """
    logger.info("\n" + "="*80)
    logger.info("Step 3: Top-K Selection")
    logger.info("="*80)
    
    # 按总分排序
    sorted_candidates = sorted(
        scored_candidates,
        key=lambda x: x['scores']['Total'],
        reverse=True
    )
    
    # 选择Top-K
    top_results = sorted_candidates[:top_k]
    
    # 表格化输出
    logger.info(f"\n{'Rank':<6} {'QID':<5} {'CID':<5} {'Emp':<6} {'Sup':<6} {'Gui':<6} {'Saf':<6} {'Total':<8} {'Question':<30}")
    logger.info("-"*80)
    for rank, item in enumerate(top_results, 1):
        q_short = item['question'][:27] + '...' if len(item['question']) > 30 else item['question']
        logger.info(f"#{rank:<5} {item['question_id']:<5} {item['candidate_id']:<5} "
                   f"{item['scores']['Empathy']:<6.2f} {item['scores']['Supportiveness']:<6.2f} "
                   f"{item['scores']['Guidance']:<6.2f} {item['scores']['Safety']:<6.2f} "
                   f"{item['scores']['Total']:<8.2f} {q_short:<30}")
    
    logger.info("-"*80)
    logger.info(f"✅ Step 3 完成: Top-{len(top_results)} 已保存\n")
    return top_results
