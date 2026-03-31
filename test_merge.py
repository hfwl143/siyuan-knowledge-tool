
"""
独立测试合并功能：给定旧笔记和新知识点，直接调用合并逻辑并打印结果。

用法：
    python test_merge.py <old> <new>

其中 <old> 和 <new> 可以是：
    - 文件路径（如 old.md, new.txt）
    - 直接文本（需用引号包裹，例如 "这是旧笔记"）
    - 短横线 - 表示从标准输入读取（按 Ctrl+D 结束）

示例：
    # 使用文件
    python test_merge.py old.md new.txt

    # 使用标准输入（先输入旧笔记，按 Ctrl+D，再输入新知识点）
    python test_merge.py - -

    # 混合：旧笔记来自文件，新知识点从标准输入
    python test_merge.py old.md -

    # 直接文本（注意引号）
    python test_merge.py "旧笔记内容" "新知识点内容"
"""

import sys
import os

# 将项目根目录加入路径，以便导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DOUBAO_API_KEY, DOUBAO_MODEL, temperature, max_tokens
from langchain_community.chat_models import ChatOpenAI
from combine import merge_knowledge


def read_input(arg: str) -> str:
    """根据参数读取内容：文件、直接文本、标准输入"""
    if arg == '-':
        print("请输入内容（按 Ctrl+D 结束）：", file=sys.stderr)
        return sys.stdin.read()
    elif os.path.isfile(arg):
        with open(arg, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return arg


def main():
    # 参数解析
    if len(sys.argv) == 1 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    if len(sys.argv) != 3:
        print("错误：必须提供两个参数（旧笔记和新知识点）。")
        print("用法：python test_merge.py <old> <new>")
        sys.exit(1)

    old_arg = sys.argv[1]
    new_arg = sys.argv[2]

    # 读取内容
    old_content = read_input(old_arg)
    new_content = read_input(new_arg)

    if not old_content.strip():
        print("错误：旧笔记内容为空", file=sys.stderr)
        sys.exit(1)
    if not new_content.strip():
        print("错误：新知识点内容为空", file=sys.stderr)
        sys.exit(1)

    # 检查 API 密钥
    if not DOUBAO_API_KEY:
        print("错误：未配置 DOUBAO_API_KEY，请检查 config.py 或环境变量。", file=sys.stderr)
        sys.exit(1)

    print(f"调试信息：使用模型 {DOUBAO_MODEL}", file=sys.stderr)

    # 初始化 LLM
    llm = ChatOpenAI(
        model=DOUBAO_MODEL,
        api_key=DOUBAO_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
        base_url="https://ark.cn-beijing.volces.com/api/v3"
    )

    print("正在合并...", file=sys.stderr)
    result = merge_knowledge(old_content, new_content, llm)

    if not result["success"]:
        print("合并失败：", result.get("error", result.get("reason", "未知原因")), file=sys.stderr)
        if "merged_md" in result:
            print("\n=== LLM 返回内容（前500字符） ===", file=sys.stderr)
            print(result["merged_md"][:500], file=sys.stderr)
        sys.exit(1)

    print("合并成功！\n")
    print("=== 新标题 ===")
    print(result["title"])
    print("\n=== 新摘要 ===")
    print(result["summary"])
    print("\n=== 新标签 ===")
    print(result["tags"])
    print("\n=== 合并后的 Markdown（前500字符） ===")
    print(result["merged_md"][:500])
    # 可选：保存完整结果到文件
    output_file = "combine_result.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result["merged_md"])
    print(f"\n完整结果已保存到 {output_file}")


if __name__ == "__main__":
    main()