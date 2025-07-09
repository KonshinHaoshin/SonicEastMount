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

# 加载角色名称映射（用于替换）
def load_character_map(path="trans_map_ja.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

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
            replaced = replace_names(line, character_map)
            cleaned_text = remove_parentheses(replaced)
            print(f"🔄 正在翻译：{cleaned_text}")
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
