# 测试思源API，获取所有笔记本ID
import requests
from config import SIYUAN_TOKEN

token = SIYUAN_TOKEN
url = "http://127.0.0.1:6806/api/notebook/lsNotebooks"
headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}

resp = requests.post(url, headers=headers, json={})
if resp.status_code == 200:
    data = resp.json()
    if data["code"] == 0:
        for nb in data["data"]["notebooks"]:
            print(f"{nb['name']} -> {nb['id']}")
    else:
        print("API错误:", data["msg"])
else:
    print("HTTP错误:", resp.status_code)