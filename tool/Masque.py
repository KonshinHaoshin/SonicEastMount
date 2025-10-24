import os
import json
import time
from dotenv import load_dotenv
import openai
import re

# 加载 .env 中的 API 密钥
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("请在 .env 文件中配置 DEEPSEEK_API_KEY")

# 使用 deepseek chat endpoint
client = openai.OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"  # 注意 DeepSeek API 地址
)

# 加载情感映射配置
def load_emotions_config(path="assets/emotions.json"):
    """加载情感配置文件"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def analyze_emotions(dialogue_cache, character_map):
    """
    对对话进行情感分析，为每句话添加情感标签
    
    Args:
        dialogue_cache: 对话缓存字典 {角色名: [台词列表]}
        character_map: 角色映射字典 {中文名: 英文ID}
    
    Returns:
        更新后的对话缓存，每句话包含情感标签
    """
    emotions_config = load_emotions_config()
    
    result = {}
    for character_name, lines in dialogue_cache.items():
        # 获取该角色的可用情感
        character_emotions = emotions_config.get(character_name, {})
        available_emotions = list(character_emotions.keys())
        
        if not available_emotions:
            # 如果没有配置情感，保持原样
            result[character_name] = lines
            continue
        
        analyzed_lines = []
        for line in lines:
            # 对每句话进行情感分析
            emotion = analyze_single_line_emotion(line, available_emotions)
            analyzed_lines.append({
                "text": line,
                "emotion": emotion
            })
        
        result[character_name] = analyzed_lines
    
    return result

def analyze_single_line_emotion(text, available_emotions, retries=3, delay=1):
    """
    分析单句话的情感
    
    Args:
        text: 要分析的文本
        available_emotions: 可用的情感列表
    
    Returns:
        分析出的情感标签
    """
    emotion_options = ", ".join(available_emotions)
    
    for i in range(retries):
        try:
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"你是一个情感分析专家。请分析以下文本的情感，并从给定的选项中选择最合适的情感标签。"
                    },
                    {
                        "role": "user",
                        "content": f"请分析这句话的情感：\n\n{text}\n\n可选情感：{emotion_options}\n\n请只回答情感标签名称，不要添加任何解释。"
                    }
                ],
                temperature=0.1
            )
            
            emotion = res.choices[0].message.content.strip()
            
            # 验证返回的情感是否在可用列表中
            if emotion in available_emotions:
                return emotion
            else:
                # 如果返回的情感不在列表中，返回默认情感
                return available_emotions[0]
                
        except Exception as e:
            print(f"❗情感分析失败，第 {i+1} 次尝试: {e}")
            time.sleep(delay)
    
    # 如果所有尝试都失败，返回默认情感
    return available_emotions[0] if available_emotions else "idle"

def replace_names(text, character_map):
    for name, jp_name in character_map.items():
        text = text.replace(name, jp_name)
    return text


def remove_parentheses(text):
    # 删除中文括号内容
    text = re.sub(r"（[^）]*）", "", text)
    # 删除英文括号内容
    text = re.sub(r"\([^)]*\)", "", text)
    return text.strip()
# 翻译函数
def masque_translate(text, retries=3, delay=1):
    for i in range(retries):
        try:
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个擅长日语口语的 AI，请以日本女子高中生的语气翻译以下内容。"
                    },
                    {
                        "role": "user",
                        "content": f"请将下面的句子翻译成自然的日语，尽量使用假名表达外来语。不要添加任何解释或注释。\n\n{text}"
                    }
                ],
                temperature=0.3
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            print(f"❗翻译失败，第 {i+1} 次尝试: {e}")
            time.sleep(delay)
    return text + " [翻译失败]"



# 主函数：处理 json 文件

def translate_json_file(input_path):
    character_map = load_character_map()

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = {}
    for speaker, lines in data.items():
        translated_lines = []
        for line in lines:
            # 检查是否是包含情感标签的新格式
            if isinstance(line, dict) and "text" in line and "emotion" in line:
                # 新格式：包含情感标签
                text = line["text"]
                emotion = line["emotion"]
                replaced = replace_names(text, character_map)
                cleaned_text = remove_parentheses(replaced)
                print(f"正在翻译：{cleaned_text}")
                translated = masque_translate(cleaned_text)
                translated_lines.append({
                    "text": translated,
                    "emotion": emotion
                })
            else:
                # 旧格式：纯文本
                replaced = replace_names(line, character_map)
                cleaned_text = remove_parentheses(replaced)
                print(f"正在翻译：{cleaned_text}")
                translated = masque_translate(cleaned_text)
                translated_lines.append(translated)
        result[speaker] = translated_lines

    # 输出文件名
    name, ext = os.path.splitext(input_path)
    output_path = f"{name}_ja.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存翻译结果到 {output_path}")
    return output_path


if __name__ == "__main__":
    input_file = input("请输入要翻译的 json 文件路径（例如 trans_map_ja.json）: ").strip()
    if not os.path.exists(input_file):
        print(f"文件不存在：{input_file}")
    else:
        translate_json_file(input_file)
