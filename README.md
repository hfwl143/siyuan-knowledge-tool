```markdown
# 思源知识库工具 (SiYuan Knowledge Tool)

一个基于思源笔记和向量数据库的智能知识管理工具，支持从聊天记录或文本中自动提取知识点、语义检索去重、智能合并，并同步到思源笔记。

## 功能特点

- **知识点自动提取**：使用大模型将原始文本整理为结构化 Markdown（标题、摘要、标签）
- **语义检索与去重**：基于向量数据库（ChromaDB）检索相似知识点，智能提示重复或相关笔记
- **智能合并**：将新内容与已有笔记融合，保留旧结构，补充新信息
- **思源笔记集成**：所有笔记直接存入思源，无需本地文件；提供独立同步脚本手动重建向量索引
- **命令行交互**：简洁的菜单操作，支持文本直接输入或文件导入

## 技术栈

- Python 3.13
- LangGraph – 状态机与流程编排
- ChromaDB – 向量存储与检索
- Sentence-Transformers – 文本嵌入模型（`paraphrase-multilingual-MiniLM-L12-v2`）
- 豆包 API – 大语言模型服务
- 思源笔记 API – 笔记存储与同步

## 安装步骤

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

编辑 `.env`，至少需要配置：

- `DOUBAO_API_KEY`：豆包 API 密钥
- `DOUBAO_MODEL`：豆包接入点 ID（格式 `ep-xxxxxx`）
- `SIYUAN_TOKEN`：思源笔记 API Token（在思源「设置 → 关于」中获取）
- `SIYUAN_NOTEBOOK_ID`：目标笔记本 ID（可通过 `sy_test.py` 脚本获取）
- `SIYUAN_ENABLED`：设为 `true` 启用思源集成

可选配置：
- `SIMILARITY_TOP_K`：检索返回的最大笔记数（默认 5）
- `SIMILARITY_THRESHOLD`：相似度阈值（默认 0.5）

### 4. 首次使用：建立向量索引

确保思源笔记已打开，运行：

```bash
python sync_siyuan.py
```

该脚本会清空向量库并从思源指定笔记本重建索引。**日常使用时无需再运行**，只有在思源中手动增删了大量笔记后才需要再次执行。

## 使用方法

### 日常使用

```bash
python main.py
```

在提示符后输入文本或文件路径（支持 `.txt`、`.md`、`.docx`、`.pdf`）。程序将自动：

1. 提取知识点并生成结构化 Markdown
2. 在向量库中检索相似笔记
3. 若发现重复或相关笔记，展示菜单让你选择：**合并**、**新建**或**取消**
4. 若合并，自动更新思源中的原笔记；若新建，则在思源中创建新文档

输入 `quit` 退出程序。

### 独立测试合并功能

```bash
python test_merge.py <旧笔记文件或文本> <新知识点文件或文本>
```

例如：
```bash
python test_merge.py old.md new.txt
```

该脚本会直接调用合并逻辑，并将结果保存到 `merge_result.md`，便于调试提示词。

### 获取思源笔记本 ID

```bash
python sy_test.py
```

会列出所有笔记本及其 ID，供你配置 `SIYUAN_NOTEBOOK_ID`。

## 项目结构

```
.
├── main.py                # 主程序入口
├── sync_siyuan.py         # 独立向量库同步脚本
├── siyuan_client.py       # 思源 API 客户端
├── vector_db.py           # 向量数据库 CRUD
├── init_vector.py         # 向量库清空与重建
├── combine.py             # 合并知识点核心逻辑
├── file_utils.py          # 文件/文本读取工具
├── config.py              # 配置加载（从 .env）
├── prompt/                # 提示词模板
│   ├── arrange.py         # 知识点提取提示词
│   └── combine.py         # 合并提示词
├── tools/                 # 扩展工具（如搜索）
├── test_merge.py          # 合并功能测试脚本
├── sy_test.py             # 思源 API 测试脚本
├── requirements.txt       # 依赖列表
├── .env.example           # 环境变量模板
└── README.md
```

## 设计思想

### 为什么选择思源作为存储后端？

- **数据安全**：思源笔记支持本地离线存储，用户完全掌控自己的数据。
- **开放 API**：提供完整的 HTTP API，便于程序读写笔记，无需依赖第三方云服务。
- **知识网络**：思源内置双向链接、块引用、知识图谱，与“知识点管理”的理念高度契合。

### 为什么使用向量数据库？

- **语义检索**：传统关键词匹配无法理解“闭包”与“匿名函数”之间的关联，向量检索能捕捉语义相似性。
- **去重与合并**：通过向量相似度判断新内容是否与已有笔记重复，减少人工整理负担。
- **轻量级**：ChromaDB 完全本地运行，无需额外服务，适合个人知识库。

### 合并流程的设计考量

- **用户确认**：避免自动合并可能带来的误操作，提供合并预览和选项（新建/合并/取消）。
- **保留结构**：合并时优先保留旧笔记的章节标题、示例等结构，仅补充新信息，不破坏原有组织。
- **LLM 辅助**：利用大模型理解语义，实现真正意义上的“融合”，而非简单拼接。

### 同步脚本与主程序分离

- **安全**：主程序永不自动清空向量库，避免因配置错误导致数据丢失。
- **灵活**：用户可随时运行 `sync_siyuan.py` 手动重建索引，保持向量库与思源一致。

## 注意事项

- **思源笔记必须保持运行**，否则程序无法读写笔记。
- 首次运行 `main.py` 前请先执行 `python sync_siyuan.py` 建立向量索引。
- 向量库（`chroma_db/` 目录）不要手动删除，否则需重新运行同步脚本。
- 豆包 API 调用会产生费用，请注意额度控制。

## 常见问题

**Q: 为什么没有本地文件了？**  
A: 本工具已完全切换到思源笔记作为存储后端，所有笔记直接保存在思源中，不再生成本地 Markdown 文件。

**Q: 向量库为空或检索不到相似笔记？**  
A: 请先确认思源笔记本中有内容，然后运行 `python sync_siyuan.py` 重建索引。

**Q: 合并后的内容不理想？**  
A: 可以调整 `SIMILARITY_THRESHOLD` 阈值（改低会提示更多合并），或优化 `prompt/combine.py` 中的提示词。

**Q: 如何更新向量库？**  
A: 在思源中修改或删除笔记后，运行 `python sync_siyuan.py` 即可全量重建索引。

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！

## 演示

（待补充截图和录屏）
```
