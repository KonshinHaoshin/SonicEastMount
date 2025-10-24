import os
import json


def load_character_map(file_path):
    """从 JSON 文件加载角色映射表"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def read_lines(file_path):
    """逐行读取文本文件内容"""
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            yield line.strip()


def is_all_chinese(s):
    """检查字符串是否全为汉字"""
    return all('\u4e00' <= c <= '\u9fa5' for c in s)


def generate_audio_path(name, scene, count, character_map):
    """生成音频文件路径"""
    nname = character_map.get(name, "unknown")
    if nname != "unknown":
        figure_id = f"{nname}_{scene}_{count:02d}"
        return f"{nname}/{scene}/{figure_id}.wav"
    else:
        return


import re

def process_line(line, scene, insert_audio, character_map, count_map):
    """处理单行对白，统一清除原有音频路径并重新生成"""

    # ✅ 删除已有的 -figureId 和 .wav 路径
    line = re.sub(r"-figureId=[a-zA-Z0-9_]+;?", "", line)
    line = re.sub(r"-[a-zA-Z0-9/_]+\.wav", "", line)
    line = line.strip()

    # 拆分角色名与台词
    parts = line.split(":", 1)
    if len(parts) != 2:
        return line  # 非对白行，直接返回

    name, text = parts[0].strip(), parts[1].strip()
    nname = character_map.get(name)

    if not nname:
        return line  # 找不到角色映射

    # 更新角色语音编号
    count_map[nname] = count_map.get(nname, 0) + 1
    audio_path = generate_audio_path(name, scene, count_map[nname], character_map)

    # 清理文本末尾格式
    text = re.sub(r"-fontSize=default;?$", "", text).strip()
    text = re.sub(r";$", "", text).strip()

    return f"{name}:{text} -{audio_path} -fontSize=default -id -figureId={nname};"



def process_dialogue(dialogues, character_map, scene, output_folder):
    """整理角色台词到独立文件"""
    dialogue_cache = {}
    for line in dialogues:
        parts = line.split(":")
        if len(parts) != 2:
            continue
        name, text = parts
        nname = character_map.get(name)

        # 只保存台词部分
        text_content = text.split("-")[0].strip()
        if nname not in dialogue_cache:
            dialogue_cache[nname] = []
        dialogue_cache[nname].append(text_content)

    # 写入到对应的角色文件
    for nname, lines in dialogue_cache.items():
        file_path = os.path.join(output_folder, f"{nname}_{scene}.txt")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write("\n".join(lines))


def delete_files_in_folder(folder):
    """清空文件夹内的所有文件"""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


def process_file_batch(file_paths, character_map, insert_audio, organize_dialogue, emotion_analysis, output_folder):
    """
    批量处理多个txt场景文件
    
    Args:
        file_paths: txt文件路径列表
        character_map: 角色映射字典
        insert_audio: 是否插入音频 ('y' or 'n')
        organize_dialogue: 是否整理台词 ('y' or 'n')
        emotion_analysis: 是否进行情感分析 ('y' or 'n')
        output_folder: 输出文件夹路径
    """
    os.makedirs(output_folder, exist_ok=True)
    
    for file_path in file_paths:
        # 从文件名提取场景名（不含扩展名）
        scene = os.path.splitext(os.path.basename(file_path))[0]
        
        print(f"处理场景: {scene} ({file_path})")
        
        # 初始化计数器
        count_map = {name: 0 for name in character_map.keys()}
        
        # 读取对白
        dialogues = list(read_lines(file_path))
        
        # 整理台词
        if organize_dialogue == 'y':
            process_dialogue(dialogues, character_map, scene, output_folder)
        
        # 处理并输出每一行对白到场景专属文件
        scene_output_file = os.path.join(output_folder, f"{scene}.txt")
        with open(scene_output_file, 'w', encoding='utf-8') as file:
            for line in dialogues:
                processed_line = process_line(line, scene, insert_audio, character_map, count_map)
                file.write(processed_line + '\n')
        
        # 生成以场景名命名的 json 文件
        scene_output_json = os.path.join(output_folder, f"{scene}.json")
        dialogue_cache = {}
        
        for line in dialogues:
            parts = line.split(":", 1)
            if len(parts) != 2:
                continue
            name, text = parts[0].strip(), parts[1].strip()
            nname = character_map.get(name)
            if not nname:
                continue
            text_content = text.split("-")[0].strip()
            # 去除（）和()内的文字
            text_content = re.sub(r"[\(（][^）\)]+[\)）]", "", text_content).strip()
            if nname not in dialogue_cache:
                dialogue_cache[nname] = []
            dialogue_cache[nname].append(text_content)
        
        # 如果需要情感分析，调用Masque进行情感标注
        if emotion_analysis == 'y':
            try:
                import sys
                # 添加当前目录到Python路径
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.append(current_dir)
                from Masque import analyze_emotions
                dialogue_cache = analyze_emotions(dialogue_cache, character_map)
            except Exception as e:
                print(f"情感分析失败: {e}")
        
        with open(scene_output_json, 'w', encoding='utf-8') as json_file:
            json.dump(dialogue_cache, json_file, ensure_ascii=False, indent=2)
        
        print(f"✅ 场景 {scene} 处理完成")
    
    print(f"\n🎉 批量处理完成！共处理 {len(file_paths)} 个场景文件")


def main(file_path='./tool/input/usher.txt'):
    scene = input().strip()
    insert_audio = input().strip().lower()
    organize_dialogue = input().strip().lower()
    emotion_analysis = input().strip().lower()

    # 加载角色映射表
    character_map_path = './character_map.json'
    character_map = load_character_map(character_map_path)

    # 初始化计数器
    count_map = {name: 0 for name in character_map.keys()}

    # 清空 output 文件夹
    output_folder = './output'
    # delete_files_in_folder(output_folder)

    # 读取对白
    dialogues = list(read_lines(file_path))

    # 整理台词
    if organize_dialogue == 'y':
        process_dialogue(dialogues, character_map, scene, output_folder)

    # 处理并输出每一行对白
    output_file = os.path.join(output_folder, 'output.txt')
    with open(output_file, 'w', encoding='utf-8') as file:
        for line in dialogues:
            processed_line = process_line(line, scene, insert_audio, character_map, count_map)
            file.write(processed_line + '\n')
    scene_output_file = os.path.join(output_folder, f"{scene}.txt")

    # 额外生成一个以场景名命名的txt

    # 额外生成一个以场景名命名的 json 文件
    scene_output_json = os.path.join(output_folder, f"{scene}.json")
    dialogue_cache = {}

    for line in dialogues:
        parts = line.split(":", 1)
        if len(parts) != 2:
            continue
        name, text = parts[0].strip(), parts[1].strip()
        nname = character_map.get(name)
        if not nname:
            continue
        text_content = text.split("-")[0].strip()
        # 去除（）和()内的文字
        text_content = re.sub(r"[\(（][^）\)]+[\)）]", "", text_content).strip()
        if nname not in dialogue_cache:
            dialogue_cache[nname] = []
        dialogue_cache[nname].append(text_content)

    # 如果需要情感分析，调用Masque进行情感标注
    if emotion_analysis == 'y':
        try:
            import sys
            # 添加当前目录到Python路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.append(current_dir)
            from Masque import analyze_emotions
            dialogue_cache = analyze_emotions(dialogue_cache, character_map)
        except Exception as e:
            print(f"情感分析失败: {e}")

    with open(scene_output_json, 'w', encoding='utf-8') as json_file:
        json.dump(dialogue_cache, json_file, ensure_ascii=False, indent=2)


    print("转换完成，请参考output文件夹下的output.txt文件")


if __name__ == "__main__":
    main()