# 思源知识库工具 (SiYuan Knowledge Tool)
一个基于思源笔记和向量数据库的智能知识管理工具，支持从聊天记录或文本中**自动提取知识点、语义检索去重、智能合并**，并同步到思源笔记。

---

## ✨ 功能特点
- **知识点自动提取**：使用大模型将原始文本整理为结构化 Markdown（标题、摘要、标签）
- **语义检索与去重**：基于向量数据库（ChromaDB）检索相似知识点，智能提示重复/相关笔记
- **智能合并**：将新内容与已有笔记融合，保留旧结构，补充新信息
- **思源笔记集成**：所有笔记直接存入思源，无需本地文件；提供独立同步脚本手动重建向量索引
- **命令行交互**：简洁菜单操作，支持文本直接输入或文件导入

---

## 🛠️ 技术栈
- Python 3.13
- LangGraph – 状态机与流程编排
- ChromaDB – 向量存储与检索
- Sentence-Transformers – 文本嵌入模型（`paraphrase-multilingual-MiniLM-L12-v2`）
- 豆包 API – 大语言模型服务
- 思源笔记 API – 笔记存储与同步

---

## 📦 安装步骤

### 1. 克隆仓库
```bash
git clone https://github.com/hfwl143/siyuan-knowledge-tool.git
cd siyuan-knowledge-tool
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
复制示例配置文件并填写真实值：
```bash
cp .env.example .env
```

**必填配置**：
- `DOUBAO_API_KEY`：豆包 API 密钥
- `DOUBAO_MODEL`：豆包接入点 ID（格式 `ep-xxxxxx`）
- `SIYUAN_TOKEN`：思源笔记 API Token（思源「设置 → 关于」中获取）
- `SIYUAN_NOTEBOOK_ID`：目标笔记本 ID（可通过 `sy_test.py` 获取）
- `SIYUAN_ENABLED`：设为 `true` 启用思源集成

**可选配置**：
- `SIMILARITY_TOP_K`：检索返回的最大笔记数（默认 5）
- `SIMILARITY_THRESHOLD`：相似度阈值（默认 0.5）

### 4. 首次使用：建立向量索引
确保**思源笔记已打开**，执行：
```bash
python sync_siyuan.py
```
> 该脚本会清空向量库并从思源指定笔记本重建索引  
> **日常使用无需执行**，仅在思源手动增删大量笔记后使用

---

## 🚀 使用方法

### 日常使用
```bash
python main.py
```
输入文本/文件路径（支持 `.txt`/`.md`/`.docx`/`.pdf`），程序自动执行：
1. 提取知识点并生成结构化 Markdown
2. 向量库检索相似笔记
3. 提供操作选项：**合并 / 新建 / 取消**
4. 合并则更新原笔记，新建则创建思源文档

输入 `quit` 退出程序

---

### 独立测试合并功能
```bash
python test_merge.py <旧笔记文件/文本> <新知识点文件/文本>
```

示例：
```bash
python test_merge.py old.md new.txt
```
结果自动保存至 `merge_result.md`，方便调试提示词

---

### 获取思源笔记本 ID
```bash
python sy_test.py
```
列出所有笔记本及其 ID，用于配置 `SIYUAN_NOTEBOOK_ID`

---

## 📂 项目结构
```
.
├── main.py                # 主程序入口
├── sync_siyuan.py         # 向量库同步脚本
├── siyuan_client.py       # 思源 API 客户端
├── vector_db.py           # 向量数据库操作
├── init_vector.py         # 向量库清空与重建
├── combine.py             # 知识点合并核心逻辑
├── file_utils.py          # 文件/文本读取工具
├── config.py              # 配置加载（.env）
├── prompt/                # 提示词模板
│   ├── arrange.py         # 知识点提取提示词
│   └── combine.py         # 合并提示词
├── tools/                 # 扩展工具
├── test_merge.py          # 合并功能测试
├── sy_test.py             # 思源 API 测试
├── requirements.txt       # 依赖列表
├── .env.example           # 环境变量模板
└── README.md
```

---

## 💡 设计思想

### 为什么选择思源作为存储后端？
- **数据安全**：支持本地离线存储，完全掌控数据
- **开放 API**：完整 HTTP API，无需依赖第三方云服务
- **知识网络**：内置双向链接、块引用、知识图谱，契合知识点管理理念

### 为什么使用向量数据库？
- **语义检索**：理解语义关联，优于传统关键词匹配
- **去重与合并**：通过相似度判断内容重复，减少人工整理
- **轻量级**：ChromaDB 本地运行，无需额外服务

### 合并流程设计
- **用户确认**：提供预览与选项，避免误操作
- **保留结构**：优先保留旧笔记结构，仅补充新信息
- **LLM 辅助**：实现语义融合，而非简单拼接

### 同步脚本与主程序分离
- **安全**：主程序永不自动清空向量库，防止数据丢失
- **灵活**：手动执行同步脚本，保持向量库与思源一致

---

## ⚠️ 注意事项
1. **思源笔记必须保持运行**，否则无法读写笔记
2. 首次运行 `main.py` 前，必须执行 `python sync_siyuan.py` 建立索引
3. 请勿手动删除 `chroma_db/` 目录，否则需重新同步
4. 豆包 API 调用会产生费用，请注意额度控制

---

## ❓ 常见问题
**Q: 为什么没有本地文件？**  
A: 工具完全基于思源笔记存储，不再生成本地 Markdown 文件

**Q: 向量库为空/检索不到笔记？**  
A: 确认思源有内容，执行 `python sync_siyuan.py` 重建索引

**Q: 合并效果不理想？**  
A: 调整 `SIMILARITY_THRESHOLD` 阈值，或优化 `prompt/combine.py` 提示词

**Q: 如何更新向量库？**  
A: 修改/删除思源笔记后，执行 `sync_siyuan.py` 全量重建

---

## 📄 许可证
MIT

## 🤝 贡献
欢迎提交 Issue 和 Pull Request！

## 🎬 演示
[这个是无相似保存](img/1.png) [起始](img/A.png)
[保存](img/B.png) [发现相似](img/C.png)
[合并成功](img/d.png) [结果](img/e.png)
[向量数据库统计](img/g.png)
