import os
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'
import logging
from config import SIYUAN_TOKEN, SIYUAN_NOTEBOOK_ID, SIYUAN_ENABLED
from siyuan_client import SiYuanClient
from init_vector import init_vector_store_from_siyuan

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    if not SIYUAN_ENABLED or not SIYUAN_TOKEN:
        logger.error("思源未启用或缺少 Token，请检查 .env 配置")
        return

    try:
        siyuan = SiYuanClient(SIYUAN_TOKEN)
        logger.info("开始从思源重建向量库...")
        init_vector_store_from_siyuan(siyuan, SIYUAN_NOTEBOOK_ID)
        logger.info("向量库重建完成")
    except Exception as e:
        logger.error(f"同步失败: {e}")

if __name__ == "__main__":
    main()