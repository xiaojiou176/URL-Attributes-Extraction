from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import time
import validators
import json
import re

# 从 .env 文件中加载环境变量
load_dotenv()

# 使用环境变量中的 API Key 实例化 OpenAI 客户端
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class NewsArticleExtractor:
    def __init__(self):
        # 初始化 NewsArticleExtractor 类
        
        # 从环境变量中读取 Jina 的 API Key
        self.api_key = os.getenv('JINA_API_KEY')
        self.base_url = 'https://r.jina.ai/'  # Jina API 的基本 URL

        # 确保成功读取 Jina 的 API Key
        if not self.api_key:
            raise ValueError("Jina API key not found in environment variables.")  # 如果 API Key 缺失，则抛出异常
        
        # 确保成功读取 OpenAI 的 API Key
        if not client.api_key:
            raise ValueError("OpenAI API key not found in environment variables.")  # 如果 API Key 缺失，则抛出异常

    def extract_from_url(self, url: str):
        # 从给定的 URL 中提取文章的关键信息

        # 验证 URL 是否是正确的格式
        if not validators.url(url):
            raise ValueError(f"Invalid URL format: {url}")

        # 构建完整的 API 请求 URL
        full_url = f'{self.base_url}{url}'

        # 设置 API 请求的头信息
        headers = {
            'Authorization': f'Bearer {self.api_key}',  # 使用 API Key 进行授权
            'X-Return-Format': 'markdown'  # 指定返回 Markdown 格式的内容
        }

        # 发送 GET 请求到 API
        response = requests.get(full_url, headers=headers)

        # 检查请求是否成功 (HTTP 状态码 200)
        if response.status_code == 200:
            content = response.text  # 提取文章的文本内容
            return self.extract_key_attributes(content)  # 处理并返回关键信息
        else:
            # 如果请求失败，抛出异常
            raise Exception(f"Failed to fetch the URL: {url}, Status code: {response.status_code}")

    def extract_key_attributes(self, content: str):
        # 从文章内容中提取特定的关键信息

        # 准备要发送给 OpenAI API 的消息列表
        messages = [
            {"role": "system", 
             "content": """
             你是一名擅长从新闻文章中提取详细和结构化信息的专家助手。 
             你的任务是按照下面指定的格式返回所需的信息。 
             仅包含请求的字段，不要提供任何额外的解释或无关的信息。
             将每个字段格式化为 '字段名: 值'。如果某个字段不可用，返回 '字段名: N/A'。
             你的回答必须准确、结构化和专业。
             """},
            
            {"role": "user", 
             "content": f"""
            这是以 Markdown 格式呈现的一篇新闻文章内容：
            {content}
            请按照以下格式提取信息：
            1. 作者姓名: [值]
            2. 主要话题: [值]
            3. 简短摘要: [值]
            4. 关键词: [值]
            5. 发表日期: [值]
            6. 多媒体描述 (如有): [值]
            7. 相关链接或参考资料: [值]
            8. 文章语言: [值]
            9. 来源信息: [值]
            10. 其他见解: [值]
            如果某个字段缺失或不可用，返回 'N/A' 作为值。
            """}
            ]
        
        # 调用 OpenAI API 生成响应
        retries = 3  # 设定重试次数
        for attempt in range(retries):
            try:
                # 请求 OpenAI API，生成带有提供信息的响应
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=500,  # 限制生成的响应长度
                    temperature=0.5  # 控制响应的随机性
                )
                result = response.choices[0].message.content  # 提取生成的内容
                print(result)

                # 将结果解析为 JSON 格式并保存到文件
                return self.parse_to_json(result, filename="output.json")  
            except Exception as e:
                # 记录并处理错误
                print(f"Error on attempt {attempt + 1}: {e}")
                time.sleep(2)  # 等待 2 秒后重试
                if attempt == retries - 1:
                    raise Exception("Max retries reached, unable to complete request.")  # 达到最大重试次数后停止

    def parse_to_json(self, result: str, filename: str):
        # 将结构化的响应解析为 JSON 对象，并保存到文件中
        
        attributes = {}  # 初始化一个空字典来存储属性

        # 将生成的结果按行分割，便于处理
        lines = result.split("\n")  # 按换行符分割文本
        multimedia_descriptions = []  # 存储多媒体描述的列表
        related_links = []  # 存储相关链接的列表

        # 遍历每一行，提取对应的字段信息
        for line in lines:
            line = line.strip()  # 去除行首和行尾的空格
            line = re.sub(r'^\d+\.\s*', '', line)  # 移除行中的编号
            
            # 检查特定字段的前缀并提取其值
            if "Author Name:" in line:
                attributes["author"] = line.replace("Author Name:", "").strip()  # 提取作者
            elif "Main Topic:" in line:
                attributes["main_topic"] = line.replace("Main Topic:", "").strip()  # 提取主要话题
            elif "Short Summary:" in line:
                attributes["summary"] = line.replace("Short Summary:", "").strip()  # 提取摘要
            elif "Keywords:" in line:
                attributes["keywords"] = line.replace("Keywords:", "").strip()  # 提取关键词
            elif "Publication Date:" in line:
                attributes["publication_date"] = line.replace("Publication Date:", "").strip()  # 提取发表日期
            elif "Multimedia Descriptions (if any):" in line:
                # 处理多媒体描述
                if "N/A" in line:
                    attributes["multimedia_descriptions"] = "N/A"  # 如果没有多媒体，设置为 N/A
                else:
                    continue  # 如果有多媒体描述，继续处理
            elif "Related Links or References:" in line:
                continue  # 跳过相关链接的标题行
            elif line.startswith("- "):  # 匹配文章中的相关链接
                related_links.append(line.strip())  # 将相关链接添加到列表
            elif "Language of the Article:" in line:
                attributes["language"] = line.replace("Language of the Article:", "").strip()  # 提取文章语言
            elif "Source Information:" in line:
                attributes["source_information"] = line.replace("Source Information:", "").strip()  # 提取来源信息
            elif "Other Insights:" in line:
                attributes["other_insights"] = line.replace("Other Insights:", "").strip()  # 提取其他见解

        # 将多媒体描述和相关链接添加到属性字典
        if multimedia_descriptions:
            attributes["multimedia_descriptions"] = multimedia_descriptions
        if related_links:
            attributes["related_links"] = related_links

        # 确保所有必需的字段都有值，若缺失则设置为默认值
        attributes.setdefault("author", "N/A")
        attributes.setdefault("main_topic", "N/A")
        attributes.setdefault("summary", "N/A")
        attributes.setdefault("keywords", "N/A")
        attributes.setdefault("publication_date", "N/A")
        attributes.setdefault("multimedia_descriptions", "N/A")
        attributes.setdefault("related_links", "N/A")
        attributes.setdefault("language", "N/A")
        attributes.setdefault("source_information", "N/A")
        attributes.setdefault("other_insights", "N/A")

        # 将解析后的属性保存为 JSON 文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(attributes, f, ensure_ascii=False, indent=4)

        print(f"JSON 数据已成功保存到 {filename}")  # 确认文件保存成功

        # 返回格式化后的 JSON 字符串
        return json.dumps(attributes, ensure_ascii=False, indent=4)


# 示例调用
extractor = NewsArticleExtractor()  # 实例化提取器类
url = 'https://www.cnn.com/2024/10/06/weather/tropical-storm-milton-florida-sunday/index.html'  # 一篇新闻文章的 URL
key_attributes = extractor.extract_from_url(url)  # 从文章中提取关键信息
print(key_attributes)  # 输出提取的信息
