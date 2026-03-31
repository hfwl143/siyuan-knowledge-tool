# siyuan_client.py
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SiYuanClient:
    def __init__(self, token: str, host: str = "127.0.0.1", port: int = 6806):
        self.base_url = f"http://{host}:{port}/api"
        self.token = token
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }

    def _post(self, endpoint: str, data: dict = None):
        url = f"{self.base_url}/{endpoint}"
        try:
            resp = requests.post(url, headers=self.headers, json=data or {})
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") != 0:
                logger.error(f"思源 API 错误: {result.get('msg')}")
            return result
        except Exception as e:
            logger.error(f"思源 API 请求失败: {e}")
            return None

    # 笔记本相关
    def list_notebooks(self) -> List[Dict]:
        result = self._post("notebook/lsNotebooks")
        if result and result.get("code") == 0:
            return result["data"]["notebooks"]
        return []

    # 文档相关
    def create_doc(self, notebook_id: str, path: str, markdown: str) -> Optional[str]:
        """创建文档，返回文档ID"""
        data = {
            "notebook": notebook_id,
            "path": path,
            "markdown": markdown
        }
        result = self._post("filetree/createDocWithMd", data)
        if result and result.get("code") == 0:
            return result["data"]  # 文档ID
        return None

    def get_doc_content(self, doc_id: str) -> Optional[str]:
        """通过文档ID获取Markdown内容"""
        data = {"id": doc_id}
        result = self._post("export/exportMdContent", data)
        if result and result.get("code") == 0:
            return result["data"]["content"]
        return None

    def update_doc(self, doc_id: str, markdown: str) -> bool:
        """更新文档内容（替换整个文档）"""
        data = {
            "id": doc_id,
            "dataType": "markdown",
            "data": markdown
        }
        result = self._post("block/updateBlock", data)
        return result is not None and result.get("code") == 0

    def delete_doc(self, doc_id: str) -> bool:
        """删除文档（需要知道笔记本ID和路径，这里用ID删除需要先获取路径）"""
        # 先获取文档的存储路径
        path_result = self._post("filetree/getPathByID", {"id": doc_id})
        if not path_result or path_result.get("code") != 0:
            return False
        notebook = path_result["data"]["notebook"]
        path = path_result["data"]["path"]
        data = {"notebook": notebook, "path": path}
        result = self._post("filetree/removeDoc", data)
        return result is not None and result.get("code") == 0

    def get_doc_id_by_title(self, notebook_id: str, title: str) -> Optional[str]:
        """在指定笔记本中通过标题查找文档ID（利用SQL）"""
        sql = f"SELECT id FROM blocks WHERE type='d' AND name='{title}' AND notebook_id='{notebook_id}'"
        result = self._post("query/sql", {"stmt": sql})
        if result and result.get("code") == 0:
            rows = result.get("data", [])
            if rows:
                return rows[0]["id"]
        return None

    def list_all_docs(self, notebook_id: str) -> List[Dict]:
        """获取指定笔记本下所有文档的ID和标题（递归，可通过SQL简单实现）"""
        sql = f"SELECT id, name FROM blocks WHERE type='d' AND notebook_id='{notebook_id}'"
        result = self._post("query/sql", {"stmt": sql})
        if result and result.get("code") == 0:
            return result.get("data", [])
        return []