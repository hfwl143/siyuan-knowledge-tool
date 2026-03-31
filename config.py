import os
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件



# 豆包配置
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")
DOUBAO_MODEL = os.getenv("DOUBAO_MODEL", "doubao-seed-1-6-251015")
temperature = float(os.getenv("TEMPERATURE", "0.3"))
max_tokens = int(os.getenv("MAX_TOKENS", "1500"))
model_name = os.getenv("MODEL_NAME", "doubao-lite-32k")  # 默认值

# SerpAPI 配置
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# 思源配置
SIYUAN_TOKEN = os.getenv("SIYUAN_TOKEN")
SIYUAN_NOTEBOOK_ID = os.getenv("SIYUAN_NOTEBOOK_ID")
SIYUAN_ENABLED = os.getenv("SIYUAN_ENABLED", "false").lower() == "true"   # 转换为布尔值

SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))