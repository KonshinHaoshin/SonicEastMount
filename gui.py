import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))


tool_dir = os.path.join(current_dir, "tool")


if tool_dir not in sys.path:
    sys.path.append(tool_dir)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QVBoxLayout, QWidget, QFileDialog,
    QMessageBox, QDialog, QHBoxLayout, QComboBox, QScrollArea, QFrame, QGridLayout, QSplitter
)
from PyQt5.QtCore import QProcess
from PyQt5.QtGui import QFont, QPalette, QColor
import json

class EmotionEditorDialog(QDialog):
    """情感标签编辑对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("情感标签编辑器")
        self.resize(800, 600)
        self.json_data = {}
        self.json_file_path = ""
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.select_file_button = QPushButton("选择JSON文件")
        self.select_file_button.clicked.connect(self.select_json_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_file_button)
        layout.addLayout(file_layout)
        
        # 创建分割器
        splitter = QSplitter()
        
        # 左侧：角色列表
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("角色列表:"))
        self.character_list = QComboBox()
        self.character_list.currentTextChanged.connect(self.on_character_changed)
        left_layout.addWidget(self.character_list)
        left_widget.setLayout(left_layout)
        
        # 右侧：台词和情感编辑区域
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("台词和情感编辑:"))
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(self.scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        right_layout.addWidget(scroll_area)
        
        right_widget.setLayout(right_layout)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 600])
        layout.addWidget(splitter)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_json_file)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def select_json_file(self):
        """选择JSON文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择JSON文件", "./output", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.json_file_path = file_path
            self.file_label.setText(f"已选择: {os.path.basename(file_path)}")
            self.load_json_file(file_path)
    
    def load_json_file(self, file_path):
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
            
            # 更新角色列表
            self.character_list.clear()
            self.character_list.addItems(list(self.json_data.keys()))
            
            # 加载第一个角色的数据
            if self.json_data:
                self.on_character_changed(list(self.json_data.keys())[0])
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载JSON文件失败: {e}")
    
    def on_character_changed(self, character_name):
        """角色改变时的处理"""
        if not character_name or character_name not in self.json_data:
            return
        
        # 清除之前的控件
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)
        
        # 获取角色的台词数据
        lines = self.json_data[character_name]
        
        # 加载情感配置
        emotions_config = self.load_emotions_config()
        character_emotions = emotions_config.get(character_name, {})
        available_emotions = list(character_emotions.keys())
        
        if not available_emotions:
            available_emotions = ["idle", "happy", "sad", "angry", "weak"]
        
        # 为每句台词创建编辑控件
        for i, line in enumerate(lines):
            frame = QFrame()
            frame.setFrameStyle(QFrame.Box)
            frame_layout = QVBoxLayout()
            
            # 台词文本
            text_label = QLabel(f"台词 {i+1}:")
            frame_layout.addWidget(text_label)
            
            text_edit = QTextEdit()
            if isinstance(line, dict) and "text" in line:
                text_edit.setText(line["text"])
            else:
                text_edit.setText(str(line))
            text_edit.setMaximumHeight(60)
            frame_layout.addWidget(text_edit)
            
            # 情感选择
            emotion_layout = QHBoxLayout()
            emotion_layout.addWidget(QLabel("情感:"))
            emotion_combo = QComboBox()
            emotion_combo.addItems(available_emotions)
            
            # 设置当前情感
            if isinstance(line, dict) and "emotion" in line:
                current_emotion = line["emotion"]
                if current_emotion in available_emotions:
                    emotion_combo.setCurrentText(current_emotion)
            
            emotion_layout.addWidget(emotion_combo)
            frame_layout.addLayout(emotion_layout)
            
            frame.setLayout(frame_layout)
            self.scroll_layout.addWidget(frame)
            
            # 保存引用以便后续保存
            if not hasattr(self, 'line_widgets'):
                self.line_widgets = {}
            self.line_widgets[f"{character_name}_{i}"] = {
                'text_edit': text_edit,
                'emotion_combo': emotion_combo,
                'original_line': line
            }
    
    def load_emotions_config(self):
        """加载情感配置文件"""
        emotions_path = "assets/emotions.json"
        if os.path.exists(emotions_path):
            with open(emotions_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def save_json_file(self):
        """保存JSON文件"""
        if not self.json_file_path:
            QMessageBox.warning(self, "错误", "请先选择JSON文件")
            return
        
        try:
            # 更新数据
            current_character = self.character_list.currentText()
            if current_character and hasattr(self, 'line_widgets'):
                lines = self.json_data[current_character]
                for i, line in enumerate(lines):
                    widget_key = f"{current_character}_{i}"
                    if widget_key in self.line_widgets:
                        widget = self.line_widgets[widget_key]
                        text = widget['text_edit'].toPlainText().strip()
                        emotion = widget['emotion_combo'].currentText()
                        
                        # 更新数据
                        if isinstance(line, dict):
                            line['text'] = text
                            line['emotion'] = emotion
                        else:
                            # 如果是旧格式，转换为新格式
                            self.json_data[current_character][i] = {
                                'text': text,
                                'emotion': emotion
                            }
            
            # 保存到文件
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.json_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "成功", "JSON文件已保存")
            # 不退出对话框，让用户可以继续编辑
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存JSON文件失败: {e}")

class UsherGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle("EASTMOUNT_WEBGAL 辅助工具")
        self.resize(600, 700)

        # 设置赛博朋克风格的主色调
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(15, 15, 30))  # 背景为深蓝色
        palette.setColor(QPalette.WindowText, QColor(200, 200, 255))  # 字体为浅蓝
        self.setPalette(palette)

        # 设置全局字体
        font = QFont("FZShuTi", 10)
        self.setFont(font)

        # Layout
        layout = QVBoxLayout()

        # 文件选择按钮
        self.file_select_button = QPushButton("选择场景文件 (支持多选)", self)
        self.file_select_button.clicked.connect(self.select_files)
        layout.addWidget(self.file_select_button)

        # 显示已选择的文件
        self.selected_files_label = QLabel("未选择文件", self)
        layout.addWidget(self.selected_files_label)

        # 存储选择的文件路径
        self.selected_file_paths = []

        # Scene Name Input
        self.scene_label = QLabel("手动输入场景名称 (可选，用于单条文本):", self)
        layout.addWidget(self.scene_label)

        self.scene_input = QLineEdit(self)

        layout.addWidget(self.scene_input)

        # Text Input Area
        self.text_label = QLabel("或直接粘贴单条文本内容:", self)
        layout.addWidget(self.text_label)

        self.text_input = QTextEdit(self)

        layout.addWidget(self.text_input)

        # Audio Checkbox
        self.audio_checkbox = QCheckBox("是否插入音频", self)
        layout.addWidget(self.audio_checkbox)

        # Organize Dialogue Checkbox
        self.dialogue_checkbox = QCheckBox("是否整理各角色台词", self)
        layout.addWidget(self.dialogue_checkbox)

        # Emotion Analysis Checkbox
        self.emotion_checkbox = QCheckBox("是否进行AI情感分析", self)
        layout.addWidget(self.emotion_checkbox)

        # Run Button
        self.run_button = QPushButton("运行脚本", self)

        self.run_button.clicked.connect(self.run_script)
        layout.addWidget(self.run_button)

        # Open Output Folder Button
        self.output_button = QPushButton("打开台词文件夹", self)

        self.output_button.clicked.connect(self.open_output_folder)
        layout.addWidget(self.output_button)

        # Speech Generation Button
        self.speechgen_button = QPushButton("生成语音所需的json文件", self)

        self.speechgen_button.clicked.connect(self.run_speechgen_script)
        layout.addWidget(self.speechgen_button)

        # Emotion Editor Button
        self.emotion_editor_button = QPushButton("编辑情感标签", self)
        self.emotion_editor_button.clicked.connect(self.open_emotion_editor)
        layout.addWidget(self.emotion_editor_button)

        # Status Label
        self.status_label = QLabel("", self)
        layout.addWidget(self.status_label)

        # Set Central Widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Process handler
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        # --- 新增角色映射输入区 ---
        self.char_map_layout = QHBoxLayout()

        self.char_name_input = QLineEdit()
        self.char_name_input.setPlaceholderText("输入角色中文名 (如 爱音)")

        self.char_id_input = QLineEdit()
        self.char_id_input.setPlaceholderText("输入角色英文ID (如 anon)")

        self.add_char_map_button = QPushButton("添加角色映射")

        self.view_char_map_button = QPushButton("查看角色映射")
        self.view_char_map_button.clicked.connect(self.show_character_map)
        self.char_map_layout.addWidget(self.view_char_map_button)

        self.add_char_map_button.clicked.connect(self.add_character_mapping)

        self.char_map_layout.addWidget(self.char_name_input)
        self.char_map_layout.addWidget(self.char_id_input)
        self.char_map_layout.addWidget(self.add_char_map_button)

        # 要不要生成日语版本
        self.translate_checkbox = QCheckBox("是否生成日语翻译版本", self)
        layout.addWidget(self.translate_checkbox)

        layout.addLayout(self.char_map_layout)

    # 查看角色映射
    def show_character_map(self):
        """读取并显示 character_map.json 的内容"""
        character_map_path = "./character_map.json"
        if not os.path.exists(character_map_path):
            QMessageBox.information(self, "未找到映射", "当前未保存任何角色映射。")
            return

        try:
            with open(character_map_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "读取错误", f"无法读取角色映射文件: {e}")
            return

        # 构造显示文本
        content = "\n".join([f"{k} ➜ {v}" for k, v in data.items()])

        # 弹出窗口显示映射
        dialog = QDialog(self)
        dialog.setWindowTitle("角色映射列表")
        dialog.resize(400, 300)
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(content)
        layout.addWidget(text_edit)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.setLayout(layout)
        dialog.exec_()


    def select_files(self):
        """选择多个txt场景文件"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self,
            "选择场景文件（可多选）",
            "./",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_paths:
            self.selected_file_paths = file_paths
            file_names = [os.path.basename(fp) for fp in file_paths]
            self.selected_files_label.setText(f"已选择 {len(file_paths)} 个文件：\n" + "\n".join(file_names))
        else:
            self.selected_files_label.setText("未选择文件")

    def add_character_mapping(self):
        """把用户输入的角色名和ID添加到 character_map.json"""
        character_map_path = "./character_map.json"
        name = self.char_name_input.text().strip()
        cid = self.char_id_input.text().strip()

        if not name or not cid:
            QMessageBox.warning(self, "输入错误", "请输入角色中文名和英文ID！")
            return

        try:
            if os.path.exists(character_map_path):
                with open(character_map_path, "r", encoding="utf-8") as f:
                    character_map = json.load(f)
            else:
                character_map = {}

            character_map[name] = cid

            with open(character_map_path, "w", encoding="utf-8") as f:
                json.dump(character_map, f, ensure_ascii=False, indent=2)

            self.status_label.setText(f"✅ 添加成功: {name} ➔ {cid}")
            self.char_name_input.clear()
            self.char_id_input.clear()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加失败: {str(e)}")

    def run_script(self):
        """批量处理选中的txt文件，或处理手动输入的单条文本"""
        insert_audio = "y" if self.audio_checkbox.isChecked() else "n"
        organize_dialogue = "y" if self.dialogue_checkbox.isChecked() else "n"
        emotion_analysis = "y" if self.emotion_checkbox.isChecked() else "n"
        
        # 优先处理选中的文件（批量模式）
        if self.selected_file_paths:
            self.run_batch_processing(insert_audio, organize_dialogue, emotion_analysis)
        else:
            # 回退到单条文本模式
            self.run_single_text_processing(insert_audio, organize_dialogue, emotion_analysis)
    
    def run_batch_processing(self, insert_audio, organize_dialogue, emotion_analysis):
        """批量处理多个txt文件"""
        try:
            from tool.Usher import process_file_batch
            
            self.status_label.setText(f"正在批量处理 {len(self.selected_file_paths)} 个文件...")
            
            # 加载角色映射
            character_map_path = "./character_map.json"
            if os.path.exists(character_map_path):
                with open(character_map_path, "r", encoding="utf-8") as f:
                    character_map = json.load(f)
            else:
                character_map = {}
            
            output_folder = "./output"
            os.makedirs(output_folder, exist_ok=True)
            
            # 批量处理每个文件
            process_file_batch(
                self.selected_file_paths,
                character_map,
                insert_audio,
                organize_dialogue,
                emotion_analysis,
                output_folder
            )
            
            self.status_label.setText(f"✅ 批量处理完成！共处理 {len(self.selected_file_paths)} 个场景")
            
            # 如果需要翻译
            if self.translate_checkbox.isChecked():
                self.batch_translate()
            
            QMessageBox.information(self, "成功", f"已成功处理 {len(self.selected_file_paths)} 个场景文件！")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"批量处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def run_single_text_processing(self, insert_audio, organize_dialogue, emotion_analysis):
        """处理手动输入的单条文本（原有逻辑）"""
        scene_name = self.scene_input.text().strip()
        text_content = self.text_input.toPlainText().strip()

        if not scene_name:
            QMessageBox.warning(self, "输入错误", "请填写场景名称或选择文件！")
            return

        if not text_content:
            QMessageBox.warning(self, "输入错误", "文本内容不能为空！")
            return

        # Save text content to ./tool/input/usher.txt
        input_dir = "./tool/input"
        os.makedirs(input_dir, exist_ok=True)
        input_file_path = os.path.join(input_dir, "usher.txt")

        try:
            with open(input_file_path, "w", encoding="utf-8") as file:
                file.write(text_content)
        except Exception as e:
            QMessageBox.critical(self, "文件错误", f"无法保存文本内容到文件: {e}")
            return

        # Check if usher.py exists
        script_path = "./tool/usher.py"
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "错误", f"未找到脚本文件: {script_path}")
            return

        # Run usher.py with inputs
        self.status_label.setText("正在运行脚本，请稍候...")
        self.process.start("python", [script_path])

        # Write inputs to the script
        inputs = f"{scene_name}\n{insert_audio}\n{organize_dialogue}\n{emotion_analysis}\n"
        self.process.write(inputs.encode())

        self.process.closeWriteChannel()

    def batch_translate(self):
        """批量翻译所有生成的场景json文件"""
        try:
            from tool.Masque import translate_json_file
            
            output_folder = "./output"
            json_files = [f for f in os.listdir(output_folder) if f.endswith('.json') and not f.endswith('_ja.json')]
            
            if not json_files:
                QMessageBox.warning(self, "没有文件", "未找到需要翻译的JSON文件")
                return
            
            self.status_label.setText(f"正在翻译 {len(json_files)} 个JSON文件...")
            
            for json_file in json_files:
                json_path = os.path.join(output_folder, json_file)
                try:
                    translate_json_file(json_path)
                    self.status_label.setText(f"已翻译: {json_file}")
                except Exception as e:
                    print(f"翻译 {json_file} 失败: {e}")
            
            self.status_label.setText(f"✅ 翻译完成！共翻译 {len(json_files)} 个文件")
            
        except Exception as e:
            QMessageBox.warning(self, "翻译失败", f"批量翻译失败: {str(e)}")

    def run_speechgen_script(self):
        """使用独立 QProcess 后台运行 speechgen.py，不影响主进程监听 usher.py"""
        script_path = os.path.abspath("./tool/speechgen.py")
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "错误", f"未找到脚本文件: {script_path}")
            return

        python_executable = sys.executable
        process = QProcess(self)
        process.startDetached(python_executable, [script_path])

    def handle_stdout(self):
        """Handle standard output from the process."""
        output = self.process.readAllStandardOutput().data().decode("utf-8", errors="ignore")
        self.status_label.setText(output)

    def handle_stderr(self):
        """Handle error output from the process."""
        error = self.process.readAllStandardError().data().decode("utf-8", errors="ignore")
        QMessageBox.critical(self, "脚本错误", error)

    def open_emotion_editor(self):
        """打开情感标签编辑器"""
        dialog = EmotionEditorDialog(self)
        dialog.exec_()

    def open_output_folder(self):
        """Open the output directory."""
        output_dir = os.path.abspath("./output")  # 使用绝对路径确保准确
        if not os.path.exists(output_dir):
            QMessageBox.warning(self, "错误", f"未找到输出文件夹: {output_dir}")
        os.startfile(output_dir)

    def process_finished(self):
        """Handle process completion and display output file."""
        self.status_label.setText("脚本运行完成！")

        # 自动翻译 usher 输出的 json 文件（如 output/dialogue.json）
        if self.translate_checkbox.isChecked():
            scene_name = self.scene_input.text().strip()
            original_json = os.path.abspath(f"./output/{scene_name}.json")
            if os.path.exists(original_json):
                try:
                    try:
                        from tool.Masque import translate_json_file
                    except Exception as e:
                        QMessageBox.critical(self, "翻译模块加载失败", f"无法导入翻译功能: {e}")
                        return

                    try:
                        output_path = translate_json_file(original_json)
                        QMessageBox.information(self, "翻译成功", f"已生成日语版本:\n{output_path}")
                    except Exception as e:
                        QMessageBox.warning(self, "翻译失败", f"翻译失败: {e}")

                    QMessageBox.information(self, "翻译成功", f"已生成日语版本:\n{output_path}")
                except Exception as e:
                    QMessageBox.warning(self, "翻译失败", f"翻译失败: {e}")
            else:
                QMessageBox.warning(self, "未找到 JSON", f"未找到需要翻译的 JSON 文件: {original_json}")

        # 检查 output.txt 文件是否存在
        output_file_path = os.path.abspath("./output/output.txt")
        if not os.path.exists(output_file_path):
            QMessageBox.warning(self, "文件未找到", f"未找到输出文件: {output_file_path}")
            return

        # 打开一个新窗口，显示 output.txt 文件的内容
        self.show_output_file(output_file_path)

    def show_output_file(self, file_path):
        """Show the content of the output file in a new window."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()
        except Exception as e:
            QMessageBox.critical(self, "文件错误", f"无法读取输出文件: {e}")
            return

        # 创建一个新窗口
        dialog = QDialog(self)
        dialog.setWindowTitle("可以运行在WEBGAL上的代码")
        dialog.setGeometry(100, 100, 600, 400)

        # 设置布局
        layout = QVBoxLayout()

        # 创建 QTextEdit 用于显示文件内容
        output_text_edit = QTextEdit(dialog)
        output_text_edit.setText(file_content)
        output_text_edit.setReadOnly(True)  # 设置为只读
        layout.addWidget(output_text_edit)

        # 添加关闭按钮
        close_button = QPushButton("关闭", dialog)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        # 设置布局并显示窗口
        dialog.setLayout(layout)
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 加载 QSS 样式
    qss_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    window = UsherGUI()
    window.show()
    sys.exit(app.exec_())
