# ======================
# 专业写法：独立工具模块
# ======================

from langchain_community.utilities import SerpAPIWrapper
from typing import Optional
# 全局变量，用于存储已初始化的SerpAPIWrapper实例
_serpapi_tool: Optional[SerpAPIWrapper] = None

def get_serpapi_tool(serpapi_key: str, SERPAPI_DEFAULT_PARAMS: dict = None):
    """
    获取SerpAPIWrapper实例
    """
    global _serpapi_tool# 全局变量，用于存储已初始化的SerpAPIWrapper实例
    if _serpapi_tool is None:
        _serpapi_tool = SerpAPIWrapper(
            serpapi_api_key=serpapi_key,
            params=SERPAPI_DEFAULT_PARAMS,
        )
    return _serpapi_tool

def search_travel_info(query: str)->str:
    """
    搜索旅行信息
    """
    if _serpapi_tool is None:
        return "❌ 工具未初始化，请先输入SerpAPI密钥"
    try:
        search_query = f"旅行信息 {query},最新信息,包含景点,美食,住宿"
        result = _serpapi_tool.run(search_query)  # 调用SerpAPITools的run方法
        return result
    except Exception as e:
        return f"搜索旅行信息时出错：{str(e)}"
