# combine.py，合并新旧知识点，返回字典包含：
# - success: bool
# - merged_md: str (合并后的完整Markdown，含front matter)
# - title: str
# - summary: str
# - tags: list
# - error: str (如果失败)
import yaml
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from prompt.combine import combine_prompt
logger = logging.getLogger(__name__)

def merge_knowledge(old_content: str, new_content: str, llm) -> dict:
    """
    合并新旧知识点，返回字典包含：
    - success: bool
    - merged_md: str (合并后的完整Markdown，含front matter)
    - title: str
    - summary: str
    - tags: list
    - error: str (如果失败)
    """


    prompt = combine_prompt(old_content, new_content)
    response = llm.invoke(prompt)
    merged_md = response.content.strip()

    if merged_md == "KEEP":# 如果合并结果为 KEEP，直接返回
        return {"success": False, "reason": "KEEP", "merged_md": merged_md}

    # 尝试解析 front matter
    if not merged_md.startswith('---'):
        # 降级处理：尝试从正文提取标题
        lines = merged_md.split('\n')
        title = ""
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break
        if not title:
            title = "合并后的笔记"
            front_matter = f"""---
            title: {title}
            summary: {merged_md[:150]}...
            tags: []
            ---"""
        merged_md = front_matter + "\n" + merged_md
        logger.warning("合并结果缺少 front matter，已自动补充")

    parts = merged_md.split('---', 2)
    if len(parts) < 3:
        return {"success": False, "error": "合并结果格式错误：front matter 不完整", "merged_md": merged_md}

    front_matter = parts[1].strip()
    content = parts[2].strip()
    try:
        metadata = yaml.safe_load(front_matter)
        title = metadata.get('title', '')
        summary = metadata.get('summary', '')
        tags = metadata.get('tags', [])
    except Exception as e:
        return {"success": False, "error": f"YAML解析失败: {e}", "merged_md": merged_md}

    return {
        "success": True,
        "merged_md": merged_md,
        "title": title,
        "summary": summary,
        "tags": tags,
        "content": content
    }