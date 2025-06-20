import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QLabel, QWidget, QTextEdit, QComboBox,
    QHBoxLayout, QLineEdit, QFileDialog, QInputDialog
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import QTimer
import subprocess
import requests
from requests.exceptions import RequestException

class SpeechGenApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音生成配置文件创建工具")
        self.setGeometry(100, 100, 800, 700)

        # 初始化基础配置
        from dotenv import load_dotenv
        load_dotenv()
        sovits_dir = os.getenv("SOVITS_DIR", "GPT-SoVITS-v4-20250422fix")
        self.base_dir = os.path.abspath(sovits_dir)

        # ✅ 提前初始化 audio_dirs
        self.audio_dirs = {
            "vocal": os.path.join(self.base_dir, "vocal"),
            "reference": os.path.join(self.base_dir, "reference")
        }
        self.api_bat_path = os.path.normpath(os.path.join(self.base_dir, "api.bat"))

        self.init_ui()
        QTimer.singleShot(1000, self.start_api_service)

        self.api_base = "http://127.0.0.1:9865"

    def init_cyberpunk_style(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(15, 15, 30))
        palette.setColor(QPalette.WindowText, QColor(200, 200, 255))
        self.setPalette(palette)
        self.setFont(QFont("FZShuTi", 10))

    def init_ui(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # 文件选择组件
        self.setup_file_selection()
        self.setup_reference_audio()
        self.setup_language_selection()
        self.setup_character_input()
        self.setup_prompt_input()
        self.setup_weights_selection()
        self.setup_preset_generation()
        self.setup_save_preset()
        self.setup_batch_update_lang()

        self.output_text = QTextEdit()
        self.output_text.setObjectName("output_text")
        self.layout.addWidget(self.output_text)

        button_layout = QHBoxLayout()
        self.btn_generate = QPushButton("生成配置文件")
        self.btn_generate.setObjectName("btn_generate")
        self.btn_generate.clicked.connect(self.generate_config)
        button_layout.addWidget(self.btn_generate)

        self.btn_gen_vocal = QPushButton("跳转到音频生成")
        self.btn_gen_vocal.setObjectName("btn_gen_vocal")
        self.btn_gen_vocal.clicked.connect(self.run_gen_vocal)
        button_layout.addWidget(self.btn_gen_vocal)

        self.layout.addLayout(button_layout)


    def setup_character_input(self):
        hbox = QHBoxLayout()
        self.lbl_character = QLabel("角色名:")
        self.txt_character = QLineEdit()
        self.txt_character.setPlaceholderText("例如：anon 或 tomori")
        hbox.addWidget(self.lbl_character)
        hbox.addWidget(self.txt_character)
        self.layout.addLayout(hbox)
    def list_files_in_subdirs(self, root_dir, suffixes):
        result = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                if any(file.endswith(suffix) for suffix in suffixes):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.base_dir).replace("\\", "/")
                    result.append(rel_path)
        return sorted(result)

    # 保存预设
    def setup_save_preset(self):
        hbox = QHBoxLayout()

        self.btn_save_current_preset = QPushButton("保存当前设置到预设")
        self.btn_save_current_preset.setStyleSheet(
            "background-color: #a6e22e; color: #272822; border-radius: 5px; padding: 10px; font-size: 16px;")
        self.btn_save_current_preset.clicked.connect(self.ask_and_save_preset)

        hbox.addWidget(self.btn_save_current_preset)
        self.layout.addLayout(hbox)

    from PyQt5.QtWidgets import QInputDialog

    def ask_and_save_preset(self):
        preset_file = "./preset_map.json"

        # 弹出输入框，输入键名
        key_name, ok = QInputDialog.getText(self, "保存预设", "请输入预设的键名（如 anon、tomori）:")

        if not ok or not key_name.strip():
            self.output_text.setText("❌ 保存取消或未输入有效键名")
            return

        key_name = key_name.strip()

        try:
            # 先加载已有 preset_map
            if os.path.exists(preset_file):
                with open(preset_file, "r", encoding="utf-8") as f:
                    preset_data = json.load(f)
            else:
                preset_data = {}

            # 准备当前界面的设置
            lang_map = {"中文": "all_zh", "English": "en", "日本語": "all_ja",
                        "粤语": "all_yue", "韩文": "all_ko", "中英混合": "zh",
                        "英日混和": "ja", "粤英混合": "yue", "韩英混合": "ko",
                        "多语种混合": "auto", "多语种混合(粤语)": "auto_yue"}

            text_lang = lang_map[self.cmb_text_lang.currentText()]
            prompt_lang = lang_map[self.cmb_prompt_lang.currentText()]
            ref_audio = getattr(self, 'ref_audio_path', 'archive_default.wav')
            prompt_text = self.txt_prompt.text().strip() or ""
            gpt_weight = self.cmb_gpt_weights.currentText()
            sovits_weight = self.cmb_sovits_weights.currentText()

            preset_data[key_name] = {
                "text_lang": text_lang,
                "prompt_lang": prompt_lang,
                "ref_audio_path": ref_audio,
                "prompt_text": prompt_text,
                "gpt_weight": gpt_weight,
                "sovits_weight": sovits_weight
            }

            # 写回 preset_map.json
            with open(preset_file, "w", encoding="utf-8") as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)

            self.output_text.setText(f"✅ 已保存当前设置到 preset_map.json\n▸ 键名: {key_name}")

        except Exception as e:
            self.output_text.setText(f"❌ 保存失败: {str(e)}")

    def setup_file_selection(self):
        """设置主文本文件选择"""
        hbox = QHBoxLayout()

        self.btn_choose = QPushButton("选择文本文件")
        self.btn_choose.setStyleSheet(
            "background-color: #fd971f; color: #272822; border-radius: 5px; padding: 10px; font-size: 16px;")
        self.btn_choose.clicked.connect(self.choose_text_file)

        self.lbl_file = QLabel("未选择任何文件")
        self.lbl_file.setStyleSheet("color: #66d9ef; font-size: 14px;")

        hbox.addWidget(self.btn_choose)
        hbox.addWidget(self.lbl_file)
        self.layout.addLayout(hbox)

    def setup_preset_generation(self):
        hbox = QHBoxLayout()

        self.btn_choose_scene_json = QPushButton("选择场景json并生成jsonl")
        self.btn_choose_scene_json.setStyleSheet(
            "background-color: #66d9ef; color: #272822; border-radius: 5px; padding: 10px; font-size: 16px;")
        self.btn_choose_scene_json.clicked.connect(self.choose_scene_json)

        hbox.addWidget(self.btn_choose_scene_json)
        self.layout.addLayout(hbox)

    # 选择场景
    def choose_scene_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择场景JSON文件", "./output", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.generate_jsonl_from_scene(file_path)

    # 通过预设生成
    def generate_jsonl_from_scene(self, json_file):
        try:
            lang_map = {"中文": "all_zh", "English": "en", "日本語": "all_ja",
                        "粤语": "all_yue", "韩文": "all_ko", "中英混合": "zh",
                        "英日混和": "ja", "粤英混合": "yue", "韩英混合": "ko",
                        "多语种混合": "auto", "多语种混合(粤语)": "auto_yue"}

            # 界面当前默认设置（备用兜底）
            default_text_lang = lang_map[self.cmb_text_lang.currentText()]
            default_prompt_lang = lang_map[self.cmb_prompt_lang.currentText()]
            default_ref_audio = getattr(self, 'ref_audio_path', 'archive_default.wav')
            default_prompt_text = self.txt_prompt.text().strip() or ""
            default_gpt_weight = self.cmb_gpt_weights.currentText()
            default_sovits_weight = self.cmb_sovits_weights.currentText()

            # 加载场景
            with open(json_file, "r", encoding="utf-8") as f:
                scene_data = json.load(f)

            # 加载 preset_map
            preset_path = "./preset_map.json"
            if os.path.exists(preset_path):
                with open(preset_path, "r", encoding="utf-8") as f:
                    preset_data = json.load(f)
            else:
                preset_data = {}

            # 输出在output目录下
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(project_root, "output")

            os.makedirs(output_dir, exist_ok=True)

            base_name = os.path.splitext(os.path.basename(json_file))[0]
            output_path = os.path.join(output_dir, f"{base_name}.jsonl")

            with open(output_path, "w", encoding="utf-8") as f_out:
                count = 0
                for character, lines in scene_data.items():
                    preset = preset_data.get(character, {})  # 尝试读取角色对应的预设

                    text_lang = preset.get("text_lang", default_text_lang)
                    prompt_lang = preset.get("prompt_lang", default_prompt_lang)
                    ref_audio = preset.get("ref_audio_path", default_ref_audio)
                    prompt_text = preset.get("prompt_text", default_prompt_text)
                    gpt_weight = preset.get("gpt_weight", default_gpt_weight)
                    sovits_weight = preset.get("sovits_weight", default_sovits_weight)

                    for line in lines:
                        config = {
                            "character": character,
                            "text": line,
                            "text_lang": text_lang,
                            "ref_audio_path": ref_audio,
                            "prompt_text": prompt_text,
                            "prompt_lang": prompt_lang,
                            "text_split_method": "cut5",
                            "batch_size": 1,
                            "media_type": "wav",
                            "streaming_mode": False,
                            "gpt_weight": gpt_weight,
                            "sovits_weight": sovits_weight
                        }
                        f_out.write(json.dumps(config, ensure_ascii=False) + "\n")
                        count += 1

            self.output_text.setText(
                f"✅ 场景JSON转换完成！\n▸ 输出路径：{output_path}\n▸ 总条数：{count}")

        except Exception as e:
            self.output_text.setText(f"❌ 转换失败：{str(e)}")

    # 一键切换预设语言
    def setup_batch_update_lang(self):
        hbox = QHBoxLayout()

        self.btn_batch_update_lang = QPushButton("一键切换预设内文本语言")
        self.btn_batch_update_lang.setStyleSheet(
            "background-color: #66d9ef; color: #272822; border-radius: 5px; padding: 10px; font-size: 16px;")
        self.btn_batch_update_lang.clicked.connect(self.batch_update_text_lang)

        hbox.addWidget(self.btn_batch_update_lang)
        self.layout.addLayout(hbox)

    def batch_update_text_lang(self):
        preset_file = "./preset_map.json"
        if not os.path.exists(preset_file):
            self.output_text.setText(f"❌ 未找到 preset_map.json，请确认文件存在")
            return

        lang_map = {
            "中文": "all_zh", "English": "en", "日本語": "all_ja",
            "粤语": "all_yue", "韩文": "all_ko", "中英混合": "zh",
            "日英混合": "ja", "粤英混合": "yue", "韩英混合": "ko",
            "多语种混合": "auto", "多语种混合(粤语)": "auto_yue"
        }

        new_text_lang = lang_map.get(self.cmb_text_lang.currentText(), "all_zh")

        try:
            with open(preset_file, "r", encoding="utf-8") as f:
                preset_data = json.load(f)

            for character, settings in preset_data.items():
                settings["text_lang"] = new_text_lang

            with open(preset_file, "w", encoding="utf-8") as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)

            self.output_text.setText(f"✅ 已成功更新预设语言为 {new_text_lang}！")

        except Exception as e:
            self.output_text.setText(f"❌ 更新失败: {str(e)}")


    def choose_text_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文本文件", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.selected_file = file_path
            self.lbl_file.setText(f"已选择文件：{os.path.basename(file_path)}")

    def setup_reference_audio(self):
        hbox = QHBoxLayout()
        self.cmb_audio_file = QComboBox()
        audio_files = self.list_files_in_subdirs(self.audio_dirs["vocal"], [".wav", ".mp3"])
        self.cmb_audio_file.addItems(audio_files)
        self.cmb_audio_file.currentTextChanged.connect(lambda path: setattr(self, 'ref_audio_path', path))

        self.lbl_audio = QLabel("参考音频:")
        hbox.addWidget(self.lbl_audio)
        hbox.addWidget(self.cmb_audio_file)
        self.layout.addLayout(hbox)

    def setup_prompt_input(self):
        hbox = QHBoxLayout()

        self.lbl_prompt = QLabel("提示文本:")
        self.cmb_prompt_file = QComboBox()
        prompt_files = self.list_files_in_subdirs(self.audio_dirs["reference"], [".txt"])
        self.cmb_prompt_file.addItems(prompt_files)
        self.cmb_prompt_file.currentTextChanged.connect(self.load_prompt_from_dropdown)

        self.txt_prompt = QLineEdit()

        hbox.addWidget(self.lbl_prompt)
        hbox.addWidget(self.cmb_prompt_file)
        hbox.addWidget(self.txt_prompt)
        self.layout.addLayout(hbox)

    def load_prompt_from_dropdown(self, rel_path):
        try:
            full_path = os.path.join(self.base_dir, rel_path)
            with open(full_path, "r", encoding="utf-8") as f:
                self.txt_prompt.setText(f.read().strip())
        except Exception as e:
            self.output_text.append(f"❌ 提示文本加载失败：{str(e)}")

    def setup_language_selection(self):
        hbox = QHBoxLayout()

        self.lbl_text_lang = QLabel("文本语言:")
        self.cmb_text_lang = QComboBox()
        self.cmb_text_lang.addItems(["中文", "English", "日本語", "粤语", "韩文",
                                      "中英混合", "日英混合", "粤英混合", "韩英混合",
                                      "多语种混合", "多语种混合(粤语)"])

        self.lbl_prompt_lang = QLabel("提示语言:")
        self.cmb_prompt_lang = QComboBox()
        self.cmb_prompt_lang.addItems(["中文", "English", "日本語", "粤语", "韩文",
                                       "中英混合", "日英混合", "粤英混合", "韩英混合",
                                       "多语种混合", "多语种混合(粤语)"])

        hbox.addWidget(self.lbl_text_lang)
        hbox.addWidget(self.cmb_text_lang)
        hbox.addWidget(self.lbl_prompt_lang)
        hbox.addWidget(self.cmb_prompt_lang)
        self.layout.addLayout(hbox)

    def setup_weights_selection(self):
        vbox = QVBoxLayout()

        # GPT 权重部分
        gpt_box = QHBoxLayout()
        self.cmb_gpt_weights = QComboBox()
        self.lbl_gpt = QLabel("未选择GPT权重")
        gpt_box.addWidget(QLabel("GPT 权重:"))
        gpt_box.addWidget(self.cmb_gpt_weights)
        gpt_box.addWidget(self.lbl_gpt)
        vbox.addLayout(gpt_box)

        # SoVITS 权重部分
        sovits_box = QHBoxLayout()
        self.cmb_sovits_weights = QComboBox()
        self.lbl_sovits = QLabel("未选择SoVITS权重")
        sovits_box.addWidget(QLabel("SoVITS 权重:"))
        sovits_box.addWidget(self.cmb_sovits_weights)
        sovits_box.addWidget(self.lbl_sovits)
        vbox.addLayout(sovits_box)

        self.layout.addLayout(vbox)

        # 加载权重文件
        self.load_weight_files()

        self.cmb_gpt_weights.currentTextChanged.connect(lambda: self.set_weight_from_dropdown("gpt"))
        self.cmb_sovits_weights.currentTextChanged.connect(lambda: self.set_weight_from_dropdown("sovits"))

    import re

    def load_weight_files(self):
        gpt_weights = []
        sovits_weights = []

        # 遍历 base_dir 下的所有子目录
        for folder in os.listdir(self.base_dir):
            folder_path = os.path.join(self.base_dir, folder)
            if not os.path.isdir(folder_path):
                continue

            # 匹配 GPT 或 SoVITS 前缀的目录名
            if folder.startswith("GPT_weights"):
                gpt_weights += self.list_files_in_subdirs(folder_path, [".ckpt", ".pth"])
            elif folder.startswith("SoVITS_weights"):
                sovits_weights += self.list_files_in_subdirs(folder_path, [".ckpt", ".pth"])

        # 加载到下拉框
        self.cmb_gpt_weights.addItems(sorted(gpt_weights))
        self.cmb_sovits_weights.addItems(sorted(sovits_weights))

    def set_weight_from_dropdown(self, weight_type):
        selected_path = self.cmb_gpt_weights.currentText() if weight_type == "gpt" else self.cmb_sovits_weights.currentText()
        label = self.lbl_gpt if weight_type == "gpt" else self.lbl_sovits
        label.setText(f"已选择：{selected_path}")
        self.send_weights_request(weight_type, selected_path)

    def send_weights_request(self, weight_type, rel_path):
        endpoint = "/set_gpt_weights" if weight_type == "gpt" else "/set_sovits_weights"
        url = f"{self.api_base}{endpoint}?weights_path={rel_path}"

        # 取消设置权重测试
        # try:
        #     response = requests.get(url, timeout=10)
        #     if response.status_code == 200:
        #         result = response.text
        #         self.output_text.append(f"✅ {weight_type.upper()}权重设置成功\n▸ 路径：{rel_path}\n▸ 返回信息：{result}")
        #     else:
        #         self.output_text.append(f"❌ 请求失败 HTTP {response.status_code}\n▸ URL：{url}")
        # except RequestException as e:
        #     self.output_text.append(f"❌ 网络请求失败\n▸ 错误类型：{type(e).__name__}\n▸ 详细信息：{str(e)}")

    def generate_config(self):
        if not hasattr(self, 'selected_file') or not self.selected_file:
            self.output_text.setText("错误：请先选择文本文件！")
            return

        try:
            lang_map = {"中文": "all_zh", "English": "en", "日本語": "all_ja",
                        "粤语":"all_yue","韩文":"all_ko","中英混合":"zh",
                        "英日混和":"ja","粤英混合":"yue","韩英混合":"ko",
                        "多语种混合":"auto","多语种混合(粤语)":"auto_yue"}

            text_lang = lang_map[self.cmb_text_lang.currentText()]
            prompt_lang = lang_map[self.cmb_prompt_lang.currentText()]

            ref_audio = getattr(self, 'ref_audio_path', 'archive_default.wav')
            prompt_text = self.txt_prompt.text().strip() or ""

            with open(self.selected_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            output_path = os.path.splitext(self.selected_file)[0] + ".jsonl"

            with open(output_path, "w", encoding="utf-8") as f:
                # speechgen.py 中的 generate_config 末尾：
                gpt_weight = self.cmb_gpt_weights.currentText()
                sovits_weight = self.cmb_sovits_weights.currentText()

                character = self.txt_character.text().strip() or "unknown"

                for line in lines:
                    config = {
                        "character": character,
                        "text": line,
                        "text_lang": text_lang,
                        "ref_audio_path": ref_audio,
                        "prompt_text": prompt_text,
                        "prompt_lang": prompt_lang,
                        "text_split_method": "cut5",
                        "batch_size": 1,
                        "media_type": "wav",
                        "streaming_mode": False,
                        "gpt_weight": gpt_weight,
                        "sovits_weight": sovits_weight
                    }
                    f.write(json.dumps(config, ensure_ascii=False) + "\n")

            self.output_text.setText(
                f"✅ 配置文件生成成功！\n▸ 输出路径：{output_path}\n▸ 总行数：{len(lines)}\n▸ 文本语言：{text_lang}\n▸ 提示语言：{prompt_lang}\n▸ 参考音频：{ref_audio}")

        except Exception as e:
            self.output_text.setText(f"❌ 生成失败：{str(e)}")

    def start_api_service(self):
        try:
            if not os.path.exists(self.api_bat_path):
                raise FileNotFoundError(f"API启动文件不存在：{self.api_bat_path}")

            subprocess.Popen(
                f'start cmd /k "{self.api_bat_path}"',
                shell=True,
                cwd=os.path.dirname(self.api_bat_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            self.output_text.append("🚀 API服务已启动\n▸ 独立控制台窗口已打开\n▸ 服务端口：9865\n▸ 可随时关闭本程序")

        except Exception as e:
            self.output_text.append(f"❌ API启动失败：{str(e)}")

    def run_gen_vocal(self):
        gen_vocal_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "gen_vocal.py"))
        try:
            if not os.path.exists(gen_vocal_path):
                raise FileNotFoundError(f"gen_vocal.py 文件不存在：{gen_vocal_path}")

            subprocess.Popen(
                f'start cmd /k python "{gen_vocal_path}"',
                shell=True,
                cwd=os.path.dirname(gen_vocal_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.output_text.append(f"🚀 已启动 gen_vocal.py\n▸ 路径：{gen_vocal_path}\n▸ 在新窗口中运行")
        except Exception as e:
            self.output_text.append(f"❌ 启动 gen_vocal.py 失败：{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)


    qss_path = os.path.join(os.path.dirname(__file__), "../assets/style.qss")  # 相对路径
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = SpeechGenApp()
    window.show()
    sys.exit(app.exec_())