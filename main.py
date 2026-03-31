import os
os.environ['TRANSFORMERS_OFFLINE'] = '1'# 禁用 Transformers 的在线模型下载
os.environ['HF_HUB_OFFLINE'] = '1'# 禁用 HF Hub 的在线模型下载，避免连接超时
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'# 配置 HF 镜像，国内开发者普遍会遇到 Hugging Face 连接超时的问题
import qprompt as qp
#prompt.py，包含所有提示词的模块
from prompt.arrange import arrange_prompt
#向量数据库crud
from vector_db import add_document, delete_document, update_document, search_similar
import vector_db# 大模型（LangChain 封装）
from langchain_community.chat_models import ChatOpenAI
# 类型定义（LangGraph 必须要的）
from typing import Annotated, TypedDict, Optional, List, Dict
# 节点枚举
from init_vector import get_document_count
# 配置yaml
import yaml
# siyuan 客户端
from siyuan_client import SiYuanClient
# 配置文件
from config import DOUBAO_API_KEY, DOUBAO_MODEL, SERPAPI_KEY, temperature, max_tokens, SIYUAN_TOKEN, SIYUAN_NOTEBOOK_ID, SIYUAN_ENABLED, SIMILARITY_TOP_K, SIMILARITY_THRESHOLD
# 合并知识
from combine import merge_knowledge
# LangGraph 核心
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from datetime import datetime
from file_utils import get_content_from_input

import logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志格式
log_file = os.path.join(log_dir, f"learning_assistant_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from sentence_transformers import SentenceTransformer# 导入 SentenceTransformer 模型，用于文本嵌入

# 初始化 embedding 模型（全局，避免重复加载）
embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
# 初始化 siyuan 客户端
siyuan = None
if SIYUAN_ENABLED and SIYUAN_TOKEN:
    siyuan = SiYuanClient(SIYUAN_TOKEN)
    # 可选：打印笔记本列表确认连接
    notebooks = siyuan.list_notebooks()
    logger.info(f"思源笔记本数量: {len(notebooks)}")


class LearningState(TypedDict):
    # --- 输入层 ---
    raw_input: str#用户输入的原始文本

    # --- 处理层 ---
    cleaned_text: Optional[str]#清理后的文本

    # --- LLM 提取结果 ---
    title: Optional[str]#标题
    summary: Optional[str]#摘要
    tags: Optional[List[str]]#标签
    markdown: Optional[str]#Markdown内容

    # --- 控制信息 ---
    error: Optional[str]#错误信息
    output_message: Optional[str]#输出信息

    # --- 记忆层 ---
    messages: Annotated[list, add_messages]#消息列表，用于存储对话历史，扩展项
    merge_memory: Optional[Dict[str, str]]#合并记忆

    # --- 搜索层 ---
    search_result: Optional[str]#搜索结果

    # --- 整合层 ---
    similar_notes: Optional[List[dict]]#相似笔记
    need_confirmation: Optional[bool]   # 是否需要确认确认
    skip_save: Optional[bool]           # 是否跳过保存
    user_choice: Optional[str]          # "new", "merge", "cancel"
    merge_target: Optional[dict]        # 合并目标笔记的完整信息（file, title, ...）


if DOUBAO_API_KEY:# and SERPAPI_KEY
    logging.getLogger(__name__).info("开始初始化工具和模型...")
    logging.getLogger(__name__).info("SerpAPI工具初始化完成")

    # 直接使用正确的模型名称
    doubao_model = "doubao-seed-1-6-251015"#这个是模型名称也可以在config.py中配置，我嫌麻烦，所以直接写在这行代码中
    logging.getLogger(__name__).info(f"使用模型: {doubao_model}")

    global llm# 全局变量，用于在其他节点中访问
    llm = ChatOpenAI(
        model=doubao_model,
        api_key=DOUBAO_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
        base_url="https://ark.cn-beijing.volces.com/api/v3"
    )
    logger.info("模型初始化完成")

else:
    logger.warning("缺少API密钥，无法初始化工具和模型")
    print("密钥无效")



#节点1.用户输入
def user_input(state: LearningState) -> LearningState:
    def validate_input(s: str) -> bool:
        return bool(s and s.strip())
    user_input = qp.ask_str(
        "请输入文本或文件路径（输入 quit 退出）: ",
        dft="",               # 默认值，空字符串表示无默认
        vld=validate_input    # 自定义验证函数
    )
    if user_input.lower() in ('quit', 'exit'):
        print("再见！注意ctrl+c 退出程序也可以，嫌quit麻烦的话")
        sys.exit(0)        
    state["raw_input"] = user_input
    return state

#节点2. 文本清洗
def clean_text(state: LearningState) -> LearningState:
    raw_input = state["raw_input"]
    try:
        cleaned_text = get_content_from_input(raw_input)
    except Exception as e:
        logging.getLogger(__name__).error(f"处理输入 {raw_input} 时出错: {e}")
        state["error"] = f"处理输入 {raw_input} 时出错: {e}"
        return state
    state["cleaned_text"] = cleaned_text
    return state

#节点2. 文本清洗后判断是否出错
def after_clean(state: LearningState) -> str:
    if state.get("error"):
        return "end"
    return "llm"

#节点3.llm整理
def llm_arrange(state: LearningState) -> LearningState:
    if not state.get("cleaned_text"):
        state["error"] = "没有可处理的文本"
        return state
    # 检查是否初始化了模型
    if not 'llm' in globals():
        # 没有 API 密钥，使用简单的处理方式
        state["title"] = "未命名笔记"
        state["summary"] = state["cleaned_text"][:100] + "..." if len(state["cleaned_text"]) > 100 else state["cleaned_text"]
        state["tags"] = ["未分类"]
        state["markdown"] = state["cleaned_text"]
        return state

    for attempt in range(3):  # 最多重试3次
        try:
            prompt = arrange_prompt(state["cleaned_text"])
            response = llm.invoke(prompt)
            markdown_output = response.content.strip()
            logger.info(f"到了")
            # 解析 front matter
            if not markdown_output.startswith('---'):
                logging.getLogger(__name__).warning(f"第{attempt+1}次尝试:输出缺少front matter，重试...")
                continue
            parts = markdown_output.split('---', 2)
            if len(parts) < 3:
                logging.getLogger(__name__).warning(f"第{attempt+1}次尝试:front matter格式不完整，重试...")
                continue
            front_matter = parts[1].strip()
            content = parts[2].strip()
            metadata = yaml.safe_load(front_matter)
            if not metadata.get('title') or not metadata.get('summary'):
                logging.getLogger(__name__).warning(f"第{attempt+1}次尝试:缺少title或summary，重试...")
                continue
            #这个是降级处理，如果标题或摘要为空，从正文第一行提取，额不过测试多次感觉没用到就注释了
            '''
            # 检查必要字段
            if not metadata.get('title') or not metadata.get('summary'):
            # 如果标题仍未提取，从正文第一行提取
                lines = state['markdown'].split('\n')
                for line in lines:
                    if line.startswith('# '):
                        state['title'] = line[2:].strip()
                        break
                # 去除 Markdown 标记，简单取纯文本前 150 字符
                plain = re.sub(r'[#*`>]', '', state['markdown'])  # 简易清洗
                state['summary'] = plain[:150].strip()    
                logger.warning(f"第{attempt+1}次尝试:缺少title或summary，重试...")
                state['markdown'] = content# 更新 markdown 内容
                state['tags'] = None
                # 如果正文中也提取不到标题，则本次尝试失败
                if not state['title'] or not state['summary']:
                    logger.warning(f"第{attempt+1}次尝试：无法提取标题")
                    if attempt == max_retries - 1:
                        state['error'] = "LLM 输出缺少标题或summary或tags"
                        return state
                    continue
                '''
            state['title'] = metadata['title']
            state['summary'] = metadata['summary']
            state['tags'] = metadata.get('tags', [])
            state['markdown'] = content
            return state
        except Exception as e:
            logging.getLogger(__name__).error(f"第{attempt+1}次尝试出错: {e}")
            if attempt == 2:  # 最后一次
                state['error'] = f"LLM 处理失败(重试3次): {e}"
                return state
            continue

    # 所有重试都失败
    state['error'] = "LLM 处理失败,重试3次后仍无法获得有效输出"
    return state




#节点4. 检查记忆层
def memory_check_node(state: LearningState) -> LearningState:
    if state.get("error"):
        return state

    # 如果没有标题或摘要，直接返回
    if not state.get("title") or not state.get("summary"):
        return state
    # 检查记忆层是否有相关笔记
    if vector_db.collection.count() == 0:
        # 没有已有知识，无需检索，直接新建笔记
        state["need_confirmation"] = False
        return state
    # 用标题+摘要生成查询向量
    query_text = f"{state['title']} {state['summary']}"
    similar_notes = search_similar(query_text, top_k=SIMILARITY_TOP_K, threshold=SIMILARITY_THRESHOLD)
    if similar_notes:
        state["similar_notes"] = similar_notes
        state["need_confirmation"] = True
    else:
        state["need_confirmation"] = False# 没有相关笔记，无需确认

    return state

def route_memory(state: LearningState) -> str:
    if state.get("error"):
        return "end"
    return "confirm" if state.get("need_confirmation") else "save"

#节点5. 用户确认整合
def confirm_combine_node(state: LearningState) -> LearningState:
    if state.get("error"):
        return state

    if state.get("need_confirmation"):
        similar_notes = state["similar_notes"]
        # 构建菜单项
        menu_items = []
        for note in similar_notes:
            title = note.get("title", "无标题")# 提取标题
            sim = note.get("similarity", 0.0)# 提取相似度
            summary = note.get("summary", "")# 提取摘要
            summary_preview = (summary[:50] + "..." if len(summary) > 50 else summary)# 摘要截断，避免菜单过长
            item = f"{title}  (相似度 {sim:.2f})\n   {summary_preview}"
            menu_items.append(item)
        menu_items.append("📝 新建笔记")
        menu_items.append("❌ 取消")

        # 显示菜单，返回 1-based 索引
        print("发现相似笔记，请选择操作：")
        for i, item in enumerate(menu_items, 1):
            print(f"{i}. {item}")
        
        # 手动获取用户输入
        while True:
            try:
                choice = int(input("请输入选择的数字: "))
                if 1 <= choice <= len(menu_items):
                    break
                else:
                    print(f"请输入 1 到 {len(menu_items)} 之间的数字")
            except ValueError:
                print("请输入有效的数字")
        
        # 根据数字选择判断
        if choice <= len(similar_notes):
            # 选择了某个相似笔记
            selected = similar_notes[choice - 1]# 提取用户选择的相似笔记
            logging.getLogger(__name__).info(f"用户选择合并笔记: {selected['title']}")
            state["merge_target"] = selected
            logging.getLogger(__name__).info(f"用户选择合并笔记: {selected['title']}")
            state["user_choice"] = "merge"
            logging.getLogger(__name__).info(f"用户选择合并笔记: {selected['title']}")

        elif choice == len(similar_notes) + 1:
            # 选择新建
            state["user_choice"] = "new"
        else:
            logging.getLogger(__name__).info(f"用户选择取消（最后一项）")
            # 选择取消（最后一项）
            state["user_choice"] = "cancel"
            state["skip_save"] = True

    else:
        # 不需要确认，直接跳过保存（意味着新建）
        state["user_choice"] = "new"
        state["skip_save"] = False   # 实际上后面还是会走保存节点，这里设为 False 让保存继续

    return state
# 路由确认整合
def route_confirm(state: LearningState) -> str:
    logging.getLogger(__name__).info(f"整合操作路由: {state.get('user_choice')}")
    return state.get("user_choice","cancel")

#节点6. 整合旧笔记与新知识点
def combine_node(state: LearningState) -> LearningState:
    logging.getLogger(__name__).info(f"combine_node 被调用")
    logging.getLogger(__name__).info(f"state['user_choice']: {state.get('user_choice')}")
    logging.getLogger(__name__).info(f"state['merge_target']: {state.get('merge_target')}")
    logging.getLogger(__name__).info(f"state['error']: {state.get('error')}")
    logging.getLogger(__name__).info(f"state['skip_save']: {state.get('skip_save')}")

    if state.get("error") or state.get("skip_save"):
        return state

    target = state.get("merge_target")#要合并的笔记
    logging.getLogger(__name__).info(f"要合并的笔记: {target}")
    if not target:
        state["error"] = "没有指定要合并的笔记"
        logging.getLogger(__name__).error(state["error"])
        return state
    # 提取旧笔记的文档ID
    old_doc_id = target["doc_id"]# 提取旧笔记的文档ID
    logging.getLogger(__name__).info(f"要合并的笔记的文档ID: {old_doc_id}")
    
    try:
        # 读取旧笔记内容
        logging.getLogger(__name__).info(f"开始读取旧笔记: {target['title']}")
        old_content = siyuan.get_doc_content(old_doc_id)
        if not old_content:
            state["error"] = "获取旧笔记内容失败"
            return state
        logging.getLogger(__name__).info(f"读取旧笔记成功，内容长度: {len(old_content)}")

        # 读取新知识点内容
        new_content = state.get("markdown", "")
        if not new_content:
            state["error"] = "没有新知识点内容"
            return state
        logging.getLogger(__name__).info(f"新知识点内容长度: {len(new_content)}")
        # 调用 LLM 合并
        logging.getLogger(__name__).info(f"开始调用 LLM 合并: {target['title']} 与 新知识点内容")
        result = merge_knowledge(old_content, new_content, llm)

        if not result["success"]:
            if result.get("reason") == "KEEP":
                print("LLM 返回 KEEP,认为内容无关,放弃合并。")
                # LLM 认为内容无关，转为新建
                logging.getLogger(__name__).info("LLM 返回 KEEP，放弃合并，转为新建")
                state["user_choice"] = "cancel"
                return state
            else:
                # 其他错误（如格式错误）
                state["error"] = result.get("error", "合并失败")
                logging.getLogger(__name__).error(state["error"])
                return state

        # 合并成功，提取结果
        new_title = result["title"]
        new_summary = result["summary"]
        new_tags = result["tags"]
        merged_md = result["merged_md"]#合并后的 markdown 内容
        content = result["content"]

        # 写回文件（覆盖）
        success = siyuan.update_doc(old_doc_id, merged_md)
        if not success:
            state["error"] = "更新思源文档失败"
            return state
        logging.getLogger(__name__).info(f"已更新思源文档: {target['title']}")

        # 更新向量库（覆盖旧向量）
        new_metadata = {
            "title": new_title,
            "summary": new_summary,
            "tags": new_tags or []
        }
        add_document(old_doc_id, new_metadata)
        logging.getLogger(__name__).info(f"已更新向量数据库")

        # 更新 state
        state['title'] = new_title
        state['summary'] = new_summary
        state['tags'] = new_tags
        state['markdown'] = content
        state['output_message'] = f"已合并并更新笔记：{target['title']}"
        state["skip_save"] = True
        print(f"✅ {state['output_message']}")

    except Exception as e:
        state["error"] = f"整合失败: {e}"
        logging.getLogger(__name__).error(f"整合失败: {e}")

    return state




#节点7. 输出结果
def save_node(state: LearningState) -> LearningState:
    if state.get("error"):# 有错误信息，直接返回
        return state

    if not state.get("markdown"):# 没有 markdown 内容，直接返回
        state["error"] = "没有可保存的内容"
        return state

    try:
        # 同步到思源
        if siyuan and SIYUAN_ENABLED:
            # 生成思源文档路径（例如 /AI知识/闭包.md）
            safe_title = state.get("title", "untitled").replace('/', '_')
            # 从标签中取第一个作为分类
            category = state.get("tags", ["未分类"])[0] if state.get("tags") else "未分类"
            path = f"/{category}/{safe_title}.md"
            # 创建文档
            doc_id = siyuan.create_doc(SIYUAN_NOTEBOOK_ID, path, state["markdown"])
            if doc_id:
                logger.info(f"思源同步成功，文档ID: {doc_id}")
            else:
                logger.warning("思源同步失败")
        logger.info(f"思源文档路径: {path}")
        # 更新向量库
        new_metadata = {
                    "title": state["title"],
                    "summary": state["summary"],
                    "tags": state["tags"] or []
                }
        add_document(doc_id, new_metadata)
        state["output_message"] = f"已保存到: {doc_id}"
        logger.info(f"保存成功: {doc_id}")

    except Exception as e:
        state["error"] = f"保存失败: {e}"
        logging.getLogger(__name__).error(f"保存失败: {e}")

    return state





# 构建状态图
def build_graph()->StateGraph:
    logging.getLogger(__name__).info("开始构建状态图...")
    graph_builder = StateGraph(LearningState)# 状态图构建器
    graph_builder.add_node("user_input", user_input)# 添加节点1.用户输入
    graph_builder.add_node("clean_text", clean_text)# 添加节点2. 文本清洗
    graph_builder.add_node("llm_arrange", llm_arrange)# 添加节点3.llm整理
    graph_builder.add_node("memory_check_node", memory_check_node)# 添加节点4. 搜索相似笔记
    graph_builder.add_node("confirm", confirm_combine_node)# 添加节点5. 确认整合
    graph_builder.add_node("combine_node", combine_node)# 添加节点6. 整合旧笔记与新知识点
    graph_builder.add_node("save_node", save_node)# 添加节点7. 输出结果
    #添加边
    graph_builder.add_edge(START, "user_input")# 添加边1. 从 START 到 user_input
    graph_builder.add_edge("user_input", "clean_text")# 添加边2. 从 user_input 到 clean_text
    #判断是否出错(文本清洗后)
    graph_builder.add_conditional_edges(
        "clean_text",
        after_clean,
        {
            "llm": "llm_arrange",
            "end": END
        }
    )
    graph_builder.add_edge("llm_arrange", "memory_check_node")# 添加边3. 从 llm_arrange 到 memory_check_node
    #判断是否需要确认整合
    graph_builder.add_conditional_edges(
        "memory_check_node",
        route_memory,
        {
            "confirm": "confirm",
            "save": "save_node",
            "end": END
        }
    )
    #判断是否确认整合
    graph_builder.add_conditional_edges(
        "confirm",
        route_confirm,
        {
            "merge": "combine_node",
            "new": "save_node",
            "cancel": END
        }
    )
    # 整合旧笔记与新知识点
    graph_builder.add_edge("combine_node", END)
    graph_builder.add_edge("save_node", END)

    graph = graph_builder.compile()# 构建状态图
    logging.getLogger(__name__).info("状态图构建完成")
    return graph

def main():
    # 打印当前向量库文档数量
    logging.getLogger(__name__).info(f"向量库文档数量: {get_document_count()}")
    # 构建状态图
    graph = build_graph()

    print("个人学习助手已启动，输入内容或文件路径，输入 'quit' 退出")
    try:
        while True:
            # 每次循环都重新创建初始状态，确保新会话干净
            initial_state = LearningState(
                raw_input="",
                cleaned_text=None,
                title=None,
                summary=None,
                tags=[],
                markdown=None,
                error=None,
                output_message=None,
                messages=[],
                merge_memory=None,
                search_result=None,
                similar_notes=None,
                need_confirmation=None,
                skip_save=None,
                user_choice=None,
                merge_target=None
            )
            try:
                final_state = graph.invoke(initial_state)
                # 可选：打印最终消息（节点内部可能已经打印了，这里可省略）
                if final_state.get("output_message"):
                    print(f"\n{final_state['output_message']}")
                elif final_state.get("error"):
                    print(f"\n❌ 错误: {final_state['error']}")
            except SystemExit:
                # 用户主动退出
                print("再见！")
                break
            except Exception as e:
                print(f"程序运行出错: {e}")
                break
    except Exception as e:
        logging.getLogger(__name__).error(f"程序运行出错: {e}")
        print("\n用户中断，退出")
        sys.exit(0)



if __name__ == "__main__":
    main()
#对了，这个是思源笔记版的个人学习助手。


