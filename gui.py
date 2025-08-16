import sys
import os


current_dir = os.path.dirname(os.path.abspath(__file__))


tool_dir = os.path.join(current_dir, "tool")


if tool_dir not in sys.path:
    sys.path.append(tool_dir)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QVBoxLayout, QWidget, QFileDialog,
    QMessageBox, QDialog, QHBoxLayout
)
from PyQt5.QtCore import QProcess
from PyQt5.QtGui import QFont, QPalette, QColor
import json

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

        # Scene Name Input
        self.scene_label = QLabel("请输入场景名称:", self)
        layout.addWidget(self.scene_label)

        self.scene_input = QLineEdit(self)

        layout.addWidget(self.scene_input)

        # Text Input Area
        self.text_label = QLabel("请输入或粘贴文本内容:", self)
        layout.addWidget(self.text_label)

        self.text_input = QTextEdit(self)

        layout.addWidget(self.text_input)

        # Audio Checkbox
        self.audio_checkbox = QCheckBox("是否插入音频", self)
        layout.addWidget(self.audio_checkbox)

        # Organize Dialogue Checkbox
        self.dialogue_checkbox = QCheckBox("是否整理各角色台词", self)
        layout.addWidget(self.dialogue_checkbox)

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
        """Run the usher.py script with user inputs."""
        scene_name = self.scene_input.text().strip()
        text_content = self.text_input.toPlainText().strip()
        insert_audio = "y" if self.audio_checkbox.isChecked() else "n"
        organize_dialogue = "y" if self.dialogue_checkbox.isChecked() else "n"

        if not scene_name:
            QMessageBox.warning(self, "输入错误", "请填写场景名称！")
            return

        if not text_content:
            QMessageBox.warning(self, "输入错误", "文本内容不能为空！")
            return

        # Save text content to ./tool/input/usher.txt
        input_dir = "./tool/input"
        os.makedirs(input_dir, exist_ok=True)  # Ensure the input directory exists
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
        inputs = f"{scene_name}\n{insert_audio}\n{organize_dialogue}\n"
        self.process.write(inputs.encode())

        self.process.closeWriteChannel()

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
                        from Masque import translate_json_file
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
