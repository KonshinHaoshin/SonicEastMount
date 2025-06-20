import requests
import json
import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
                             QFileDialog, QTreeWidget, QTreeWidgetItem, QMessageBox, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressBar
from pygame import mixer
import time

# 初始化 pygame.mixer
mixer.init()

# API 地址
url = "http://127.0.0.1:9865/tts"

# 后台生成音频线程
# class WorkerThread(QThread):
#     update_status = pyqtSignal(str)
#     add_audio = pyqtSignal(str)
#
#     def __init__(self, data_list, base_name, output_dir):
#         super().__init__()
#         self.data_list = data_list
#         self.base_name = base_name
#         self.output_dir = output_dir
#         self.last_weights = (None, None)  # ➕ 添加缓存字段 (gpt, sovits)
#
#     def run(self):
#         os.makedirs(self.output_dir, exist_ok=True)
#         for i, data in enumerate(self.data_list):
#             try:
#                 # 设置权重（如字段存在）
#                 gpt_weight = data.get("gpt_weight")
#                 sovits_weight = data.get("sovits_weight")
#
#                 # ⚠️ 仅当权重变化时才发送请求
#                 if (gpt_weight, sovits_weight) != self.last_weights:
#                     if gpt_weight and gpt_weight != self.last_weights[0]:
#                         requests.get(f"http://127.0.0.1:9865/set_gpt_weights?weights_path={gpt_weight}")
#                     if sovits_weight and sovits_weight != self.last_weights[1]:
#                         requests.get(f"http://127.0.0.1:9865/set_sovits_weights?weights_path={sovits_weight}")
#                     self.last_weights = (gpt_weight, sovits_weight)  # ✅ 更新缓存
#
#                 # 再发送主 TTS 请求
#                 response = requests.post(url, json=data)
#                 if response.status_code == 200:
#                     output_filename = os.path.join(self.output_dir, f"{self.base_name}_{i + 1:02d}.wav")
#                     with open(output_filename, "wb") as f:
#                         f.write(response.content)
#                     self.add_audio.emit(os.path.basename(output_filename))
#                     self.update_status.emit(f"已生成 {i + 1}/{len(self.data_list)}")
#                 else:
#                     self.update_status.emit(f"第 {i + 1} 条失败: {response.text}")
#                 time.sleep(1)
#             except Exception as e:
#                 self.update_status.emit(f"第 {i + 1} 条错误: {str(e)}")
#         self.update_status.emit("生成完成")
class WorkerThread(QThread):
    update_status = pyqtSignal(str)
    add_audio = pyqtSignal(str)
    progress_changed = pyqtSignal(int)

    def __init__(self, data_list, base_name, output_root, sleep_time=1):
        super().__init__()
        self.data_list = data_list
        self.base_name = base_name  # 场景名
        self.output_root = output_root
        self.last_weights = (None, None)
        self.character_counters = {}  # 每个角色当前编号（无论是否成功，都会前进）
        self.sleep_time = sleep_time

    def run(self):
        os.makedirs(self.output_root, exist_ok=True)

        for i, data in enumerate(self.data_list):
            try:
                character = data.get("character", "unknown")
                if character == "unknown":
                    self.update_status.emit(f"第 {i + 1} 条警告：缺少 character 字段")
                    self.progress_changed.emit(i + 1)
                    continue

                # ✅ 分配当前编号（无论成功失败）
                if character not in self.character_counters:
                    self.character_counters[character] = 1
                else:
                    self.character_counters[character] += 1
                index_number = self.character_counters[character]

                # 拆分 base_name 为角色与场景（例如 anon_test → anon, test）
                if "_" in self.base_name:
                    parts = self.base_name.split("_", 1)
                    folder_character = parts[0]
                    folder_scene = parts[1]
                else:
                    folder_character = character
                    folder_scene = self.base_name

                filename = f"{character}_{folder_scene}_{index_number:02d}.wav"
                output_dir = os.path.join(self.output_root, folder_character, folder_scene)
                # output_dir = os.path.join(self.output_root, character, self.base_name)
                os.makedirs(output_dir, exist_ok=True)
                full_output_path = os.path.join(output_dir, filename)

                # 切换权重
                gpt_weight = data.get("gpt_weight")
                sovits_weight = data.get("sovits_weight")
                if (gpt_weight, sovits_weight) != self.last_weights:
                    try:
                        if gpt_weight and gpt_weight != self.last_weights[0]:
                            requests.get(f"http://127.0.0.1:9865/set_gpt_weights?weights_path={gpt_weight}", timeout=10)
                        if sovits_weight and sovits_weight != self.last_weights[1]:
                            requests.get(f"http://127.0.0.1:9865/set_sovits_weights?weights_path={sovits_weight}", timeout=10)
                        self.last_weights = (gpt_weight, sovits_weight)
                    except requests.RequestException as e:
                        self.update_status.emit(f"第 {i + 1} 条警告：切换权重失败 {str(e)}")
                        self.progress_changed.emit(i + 1)
                        continue

                # 请求生成
                try:
                    response = requests.post(url, json=data, timeout=600) ## 我不信一条语音十分钟跑不出来
                except requests.RequestException as e:
                    self.update_status.emit(f"第 {i + 1} 条错误: 网络请求失败 {str(e)}")
                    self.progress_changed.emit(i + 1)
                    continue

                if response.status_code != 200:
                    self.update_status.emit(f"第 {i + 1} 条失败: {response.status_code} {response.text}")
                    self.progress_changed.emit(i + 1)
                    continue

                if not response.content or len(response.content) < 500:
                    self.update_status.emit(f"第 {i + 1} 条错误: 返回内容为空或无效！")
                    self.progress_changed.emit(i + 1)
                    continue

                # 写入成功音频
                with open(full_output_path, "wb") as f:
                    f.write(response.content)

                relative_path = os.path.relpath(full_output_path, self.output_root)
                self.add_audio.emit(relative_path)
                self.update_status.emit(f"已生成 {relative_path}")

            except Exception as e:
                self.update_status.emit(f"第 {i + 1} 条异常: {str(e)}")

            self.progress_changed.emit(i + 1)
            time.sleep(self.sleep_time)

        self.update_status.emit("全部生成完成")



# 主界面
class TTSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TTS 音频生成器")
        self.setGeometry(100, 100, 600, 400)

        self.jsonl_file = ""
        self.output_root = ""
        self.base_name = ""
        self.character_name = ""
        self.scene_name = ""
        self.data_list = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.jsonl_label = QLabel("JSONL 文件: 未选择")
        self.layout.addWidget(self.jsonl_label)
        self.select_jsonl_btn = QPushButton("选择 JSONL 文件")
        self.select_jsonl_btn.clicked.connect(self.select_jsonl_file)
        self.layout.addWidget(self.select_jsonl_btn)

        self.output_label = QLabel("保存目录: 未选择")
        self.layout.addWidget(self.output_label)
        self.select_output_btn = QPushButton("选择保存目录")
        self.select_output_btn.clicked.connect(self.select_output_directory)
        self.layout.addWidget(self.select_output_btn)

        self.generate_btn = QPushButton("生成音频")
        self.generate_btn.clicked.connect(self.start_generation)
        self.layout.addWidget(self.generate_btn)

        self.audio_list = QTreeWidget()
        self.audio_list.setHeaderLabels(["已生成音频文件"])
        self.audio_list.setColumnWidth(0, 400)
        self.audio_list.itemSelectionChanged.connect(self.on_audio_select)
        self.layout.addWidget(self.audio_list)

        self.button_layout = QHBoxLayout()
        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.play_audio)
        self.play_btn.setEnabled(False)
        self.button_layout.addWidget(self.play_btn)
        self.layout.addLayout(self.button_layout)

        self.regenerate_btn = QPushButton("重新生成")
        self.regenerate_btn.clicked.connect(self.regenerate_audio)
        self.regenerate_btn.setEnabled(False)
        self.button_layout.addWidget(self.regenerate_btn)


        self.status_label = QLabel("状态: 就绪")
        self.layout.addWidget(self.status_label)

        # 显示进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("进度: %p%")
        self.layout.addWidget(self.progress_bar)

        self.select_jsonl_btn.setObjectName("btn_select_jsonl")
        self.select_output_btn.setObjectName("btn_select_output")
        self.generate_btn.setObjectName("btn_generate_audio")
        self.play_btn.setObjectName("btn_play")
        self.regenerate_btn.setObjectName("btn_regen")
        self.status_label.setObjectName("status_label")
        self.progress_bar.setObjectName("progress_bar")
        self.audio_list.setObjectName("audio_list")

    def select_jsonl_file(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_dir = os.path.join(project_root, "output")
        os.makedirs(default_dir, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(self, "选择 JSONL 文件", default_dir, "JSONL Files (*.jsonl);;All Files (*)")
        if file_path:
            self.jsonl_file = file_path
            self.base_name = os.path.splitext(os.path.basename(file_path))[0]
            parts = self.base_name.split("_")
            self.character_name, self.scene_name = (parts + ["default"])[:2]

            self.output_root = os.path.join(default_dir)
            os.makedirs(self.output_root, exist_ok=True)
            self.output_label.setText(f"保存目录: {self.output_root}")
            self.jsonl_label.setText(f"JSONL 文件: {os.path.basename(file_path)}")

            self.load_jsonl_data()

    def quick_generate_from_jsonl(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_dir = os.path.join(project_root, "output")
        os.makedirs(default_dir, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择场景 JSONL 文件", default_dir, "JSONL Files (*.jsonl);;All Files (*)"
        )
        if not file_path:
            return

        # 解析文件名
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        parts = base_name.split("_")

        if len(parts) >= 2:
            character_name = parts[0]
            scene_name = parts[1]
        else:
            character_name = "unknown"
            scene_name = "default"

        # 输出目录
        output_dir = os.path.join(default_dir, character_name, scene_name)
        os.makedirs(output_dir, exist_ok=True)

        try:
            # 读取jsonl数据
            with open(file_path, 'r', encoding='utf-8') as f:
                data_list = [json.loads(line.strip()) for line in f if line.strip()]

            if not data_list:
                QMessageBox.warning(self, "警告", "选中的 JSONL 文件为空或格式错误")
                return

            # 启动后台线程生成音频
            self.worker = WorkerThread(data_list, base_name, output_dir)
            self.worker.update_status.connect(self.update_status)
            self.worker.add_audio.connect(self.add_audio_to_list)
            self.worker.finished.connect(self.generation_finished)
            self.worker.start()

            self.status_label.setText(f"状态: 开始从 {base_name}.jsonl 生成音频...")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取 JSONL 文件失败: {e}")


    def select_output_directory(self):
        output_dir = QFileDialog.getExistingDirectory(self, "选择保存目录", os.getcwd())
        if output_dir:
            self.output_root = output_dir
            self.output_label.setText(f"保存目录: {self.output_root}")

    def load_jsonl_data(self):
        try:
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                self.data_list = [json.loads(line.strip()) for line in f if line.strip()]

            # 如果有 character 字段，使用第一个的值覆盖 self.character_name
            if self.data_list and "character" in self.data_list[0]:
                self.character_name = self.data_list[0]["character"]

            self.status_label.setText(f"状态: 已加载 {len(self.data_list)} 条数据")
            self.generate_btn.setEnabled(True)
        except Exception as e:
            self.data_list = []
            self.generate_btn.setEnabled(False)
            QMessageBox.critical(self, "错误", f"读取 JSONL 文件失败: {e}")

    def process_and_save(self, data, index):
        response = requests.post(url, json=data)
        if response.status_code == 200:
            output_filename = os.path.join(self.output_dir, f"{self.base_name}_{index:02d}.wav")
            with open(output_filename, "wb") as f:
                f.write(response.content)
            return output_filename
        else:
            raise Exception(f"请求失败: {response.text}")

    def start_generation(self):
        if not self.jsonl_file or not self.output_root or not self.data_list:
            QMessageBox.warning(self, "警告", "请检查 JSONL 文件和保存目录")
            return

        self.generate_btn.setEnabled(False)
        self.audio_list.clear()

        self.worker = WorkerThread(self.data_list, self.base_name, self.output_root)
        self.worker.update_status.connect(self.update_status)
        self.worker.add_audio.connect(self.add_audio_to_list)
        self.worker.finished.connect(lambda: self.generate_btn.setEnabled(True))
        self.worker.start()

        self.progress_bar.setMaximum(len(self.data_list))
        self.progress_bar.setValue(0)
        self.worker.progress_changed.connect(self.progress_bar.setValue)


    def update_status(self, status):
        self.status_label.setText(f"状态: {status}")

    def add_audio_to_list(self, relative_path):
        item = QTreeWidgetItem([relative_path])
        self.audio_list.addTopLevelItem(item)

    def generation_finished(self):
        self.generate_btn.setEnabled(True)
        self.progress_bar.setValue(self.progress_bar.maximum())

    def on_audio_select(self):
        has_selection = bool(self.audio_list.selectedItems())
        self.play_btn.setEnabled(has_selection)
        self.regenerate_btn.setEnabled(has_selection)

    def play_audio(self):
        selected_items = self.audio_list.selectedItems()
        if not selected_items:
            return

        relative_path = selected_items[0].text(0)
        audio_file = os.path.join(self.output_root, relative_path)

        if os.path.exists(audio_file):
            if mixer.music.get_busy():
                mixer.music.stop()
            mixer.music.load(audio_file)
            mixer.music.play()
            self.status_label.setText(f"状态: 正在播放 {relative_path}")
        else:
            QMessageBox.critical(self, "错误", "音频文件不存在")

    def regenerate_audio(self):
        selected_items = self.audio_list.selectedItems()
        if not selected_items:
            return

        relative_path = selected_items[0].text(0)
        filename = os.path.basename(relative_path)

        # 解析角色名、场景名、序号
        try:
            name_parts = filename.replace(".wav", "").split("_")
            character = name_parts[0]
            scene = name_parts[1]
            index = int(name_parts[2]) - 1
        except Exception:
            QMessageBox.critical(self, "错误", "文件名解析失败，无法定位数据")
            return

        if 0 <= index < len(self.data_list):
            self.status_label.setText(f"状态: 重新生成 {filename}...")
            try:
                data = self.data_list[index]
                full_output_path = os.path.join(self.output_root, relative_path)
                response = requests.post(url, json=data)

                if response.status_code == 200:
                    with open(full_output_path, "wb") as f:
                        f.write(response.content)
                    self.status_label.setText(f"状态: {filename} 重新生成完成")
                else:
                    raise Exception(response.text)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重新生成失败: {e}")
        else:
            QMessageBox.critical(self, "错误", "索引超出范围")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ✅ 加载外部 QSS 样式
    qss_path = os.path.join(os.path.dirname(__file__), "../assets/style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = TTSApp()
    window.show()
    sys.exit(app.exec_())