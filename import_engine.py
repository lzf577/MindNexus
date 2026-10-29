import base64
import json
import fitz  # PyMuPDF
import logging
import urllib.request
import urllib.error
import ssl

PROMPT = """
你是一个结构化数据提取专家。请分析我发送给你的图片（这可能是一张思维导图、一篇文章截图或是其他文档）。
请提取其中的逻辑层级和核心内容，并将其转换为一个思维导图的 JSON 结构。

你必须严格返回合法的 JSON，不要附带任何 Markdown 标记或多余的解释文字。

JSON 格式要求如下：
{
  "text": "中心主题名称",
  "children": [
    {
      "text": "子节点1名称",
      "children": []
    },
    {
      "text": "子节点2名称",
      "children": [
        {
          "text": "孙节点名称",
          "children": []
        }
      ]
    }
  ]
}
"""

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_mindmap_from_image(image_path, api_key, base_url=None, model="gpt-4o"):
    base64_image = encode_image_to_base64(image_path)
    return call_vision_llm(base64_image, api_key, base_url, model)

def extract_mindmap_from_pdf(pdf_path, api_key, base_url=None, model="gpt-4o", page_num=0):
    # 默认只处理 PDF 的第一页，将其转为图片
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        raise ValueError("PDF 文件为空")
        
    page = doc.load_page(page_num)
    # 提高渲染分辨率
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # 转换为 base64
    img_data = pix.tobytes("png")
    base64_image = base64.b64encode(img_data).decode('utf-8')
    doc.close()
    
    return call_vision_llm(base64_image, api_key, base_url, model)

AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-robotics-er-1.6-preview"
]

def _post_chat_completion(messages, api_key, base_url, model):
    target_base = (base_url or "https://generativelanguage.googleapis.com/v1beta/openai/").strip().rstrip("/")
    url = f"{target_base}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key.strip()}"
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 8192,
        "temperature": 0.3
    }
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='ignore')
        raise RuntimeError(f"HTTP错误 {e.code}: {err_body}") from e
    except Exception as e:
        raise RuntimeError(f"请求失败: {e}") from e

def call_vision_llm(base64_image, api_key, base_url=None, model="gpt-4o"):
    models_to_try = [model]
    for m in AVAILABLE_MODELS:
        if m != model:
            models_to_try.append(m)
            
    last_exception = None
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": PROMPT
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ]
    
    for current_model in models_to_try:
        try:
            logging.info(f"Starting request with model: {current_model}")
            content = _post_chat_completion(messages, api_key, base_url, current_model)
            
            # 清理可能包含的 Markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
                
            if content.endswith("```"):
                content = content[:-3]
                
            content = content.strip()
            
            try:
                data = json.loads(content)
                logging.info(f"Request with model {current_model} succeeded.")
                return data
            except json.JSONDecodeError as e:
                raise ValueError(f"大模型返回的数据格式错误无法解析为 JSON: \n{content}") from e
                
        except Exception as e:
            last_exception = e
            logging.warning(f"Model {current_model} failed, retrying with next... Error: {e}")
            continue
            
    logging.error(f"所有模型请求均失败，最后一次错误: {last_exception}")
    raise ValueError(f"所有模型请求均失败，最后一次错误: {last_exception}")


TEXT_PROMPT = """
你是一个结构化数据提取专家。请分析我发送给你的文本内容。
请提取其中的逻辑层级和核心内容，并将其转换为一个思维导图的 JSON 结构。

你必须严格返回合法的 JSON，不要附带任何 Markdown 标记或多余的解释文字。

JSON 格式要求如下：
{
  "text": "中心主题名称",
  "children": [
    {
      "text": "子节点1名称",
      "children": []
    },
    {
      "text": "子节点2名称",
      "children": [
        {
          "text": "孙节点名称",
          "children": []
        }
      ]
    }
  ]
}
"""

def extract_mindmap_from_text(text_content, api_key, base_url=None, model="gpt-4o"):
    return call_text_llm(text_content, api_key, base_url, model)


def call_text_llm(text_content, api_key, base_url=None, model="gpt-4o"):
    models_to_try = [model]
    for m in AVAILABLE_MODELS:
        if m != model:
            models_to_try.append(m)
            
    last_exception = None
    messages = [
        {
            "role": "user",
            "content": f"{TEXT_PROMPT}\n\n文本内容如下：\n{text_content}"
        }
    ]
    
    for current_model in models_to_try:
        try:
            logging.info(f"Starting text request with model: {current_model}")
            content = _post_chat_completion(messages, api_key, base_url, current_model)
            
            # 清理可能包含的 Markdown 代码块标记
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
                
            if content.endswith("```"):
                content = content[:-3]
                
            content = content.strip()
            
            try:
                data = json.loads(content)
                logging.info(f"Text request with model {current_model} succeeded.")
                return data
            except json.JSONDecodeError as e:
                raise ValueError(f"大模型返回的数据格式错误无法解析为 JSON: \n{content}") from e
                
        except Exception as e:
            last_exception = e
            logging.warning(f"Model {current_model} text request failed, retrying with next... Error: {e}")
            continue
            
    logging.error(f"所有模型文本请求均失败，最后一次错误: {last_exception}")
    raise ValueError(f"所有模型文本请求均失败，最后一次错误: {last_exception}")

