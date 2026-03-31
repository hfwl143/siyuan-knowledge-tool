import os
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
# 1. 检查是否是文件路径
def is_file_path(path):
    return os.path.isfile(path)#判断是否是文件路径

# 获取文件扩展名并转换为小写
def get_extension(path):
    return os.path.splitext(path)[1].lower()#获取文件扩展名并转换为小写

# 2. 读取不同格式的文件内容
def read_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def read_docx(path):
    import docx
    doc = docx.Document(path)
    return '\n'.join([para.text for para in doc.paragraphs])

def read_pdf(path):
    import PyPDF2
    with open(path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        return '\n'.join([page.extract_text() for page in reader.pages])

def unsupported_format():
    return "不支持的文件格式，请输入文本或支持的文件路径"


def get_content_from_input(user_input):
    # 1. 先判断是不是文件
    if is_file_path(user_input):
        # 2. 是文件，获取扩展名
        ext = get_extension(user_input)
        # 3. 根据扩展名选择处理方法
        if ext == '.txt':
            content = read_txt(user_input)
        elif ext == '.docx':
            content = read_docx(user_input)
        elif ext == '.pdf':
            content = read_pdf(user_input)
        else:
            content = unsupported_format()
            logging.getLogger(__name__).warning(f"不支持的文件格式: {ext}")
    else:
        # 4. 不是文件，直接当作文本
        logging.getLogger(__name__).info(f"直接当作文本处理: {user_input}")
        content = user_input   # ✅ 直接返回用户输入的文本
    
    # 5. 最终都返回纯文本
    return content