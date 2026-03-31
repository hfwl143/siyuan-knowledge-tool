# 思源知识库工具 (Siyuan Knowledge Tool)

一个基于思源笔记和向量数据库的智能知识管理工具，支持知识自动整合、相似内容检索和智能问答。

## 功能特点

- **知识自动整合**：将新知识点智能合并到已有笔记中
- **向量数据库**：使用 ChromaDB 存储和检索知识向量
- **智能问答**：基于大模型的知识问答系统
- **思源笔记集成**：支持从思源笔记同步数据
- **命令行界面**：交互式命令行操作

## 技术栈

- **Python 3.13**
- **LangChain**：大模型接口封装
- **ChromaDB**：向量数据库
- **SentenceTransformers**：文本嵌入模型
- **豆包 API**：大模型服务
- **Siyuan API**：思源笔记集成

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

复制 `.env` 文件并填写相关配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下信息：

- `DOUBAO_API_KEY`：豆包 API 密钥
- `DOUBAO_MODEL`：使用的豆包模型（如 `ep-m-20251214153137-mrhqw`）
- `SERPAPI_KEY`：SerpAPI 密钥（可选，用于搜索工具）
- `SIYUAN_TOKEN`：思源笔记 API 令牌
- `SIYUAN_NOTEBOOK_ID`：思源笔记本 ID
- `SIYUAN_ENABLED`：是否启用思源集成（`true` 或 `false`）

## 核心功能

### 1. 知识整合

将新知识点智能合并到已有笔记中：

```bash
python test_merge.py <旧笔记> <新知识点>
```

- `<旧笔记>` 和 `<新知识点>` 可以是文件路径、直接文本或标准输入（使用 `-`）

### 2. 智能问答

启动交互式问答系统：

```bash
python main.py
```

- 输入问题或文件路径
- 系统会检索相关知识并生成回答

### 3. 向量库管理

- **强制同步**：清空并重建向量库
  ```bash
  python main.py --sync
  ```

## 项目结构

```
.
├── chroma_db/          # 向量数据库
├── knowledge_base/     # 知识库文件
├── logs/              # 日志文件
├── prompt/            # 提示词模板
│   ├── arrange.py     # 内容整理提示词
│   └── combine.py     # 知识合并提示词
├── tools/             # 工具模块
│   └── Serp.py        # 搜索工具
├── .env               # 环境变量配置
├── add.py             # 添加文档
├── build_index.py     # 构建索引
├── combine.py         # 知识合并逻辑
├── config.py          # 配置文件
├── file_utils.py      # 文件工具
├── init_vector.py     # 向量库初始化
├── main.py            # 主程序
├── siyuan_client.py   # 思源客户端
├── test_merge.py      # 合并测试
├── vector_db.py       # 向量数据库操作
└── README.md          # 项目说明
```

## 注意事项

1. **API 密钥**：确保正确配置豆包 API 密钥，否则无法使用大模型功能
2. **思源笔记**：如果启用思源集成，确保思源笔记已启动且 API 服务正常
3. **向量数据库**：首次运行会创建向量库，可能需要一些时间
4. **依赖安装**：确保所有依赖已正确安装，特别是 SentenceTransformers 可能需要较长时间下载模型

## 常见问题

### Q: 无法连接思源笔记

**A:** 确保：
- 思源笔记已启动
- API 服务已开启（设置 → 关于 → 高级设置 → 启用 API 服务）
- `SIYUAN_TOKEN` 和 `SIYUAN_NOTEBOOK_ID` 配置正确

### Q: 合并失败

**A:** 检查：
- 豆包 API 密钥是否正确
- 网络连接是否正常
- 输入的笔记内容是否为空

### Q: 向量库为空

**A:** 运行 `python main.py --sync` 强制同步思源笔记数据

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！