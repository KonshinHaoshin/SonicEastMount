
# 🎵 SonicEastMount

**SonicEastMount** 是一个基于 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 的中文语音生成图形化工具，旨在让用户通过 GUI 界面一键完成文本到语音的推理与生成。

建议结合 [GPT-SoVITS] 以及 [WebGAL](https://github.com/OpenWebGAL/WebGAL) 使用。本项目整合了 GPT 语义建模、SoVITS 声音合成等模块，使用者只需准备好音频与台词文本，即可快速生成符合角色风格的配音。

---

## 🧩 项目结构与依赖

> ✅ 默认使用 [GPT-SoVITS v4（20250422fix）整合包](https://github.com/RVC-Boss/GPT-SoVITS)

请前往原始项目下载整合包，解压并放置到本项目目录下，**文件夹名保持为：`GPT-SoVITS-v4-20250422fix`**。

如需自定义路径，请在 `.env` 中配置：

```
SOVITS_DIR=GPT-SoVITS-v4-20250422fix
MOONSHOT_API_KEY=sk-xxx     # 若使用 Kimi 翻译
```

```
SonicEastMount/
├── GPT-SoVITS-v4-20250422fix/   # GPT-SoVITS 核心目录（需自行下载）
│   ├── vocal/                   # 存放参考音频（需手动创建）
│   ├── reference/               # 存放文本内容（需手动创建）
├── tool/
│   ├── gen_vocal.py             # 根据 reference 自动生成音频名列表
│   ├── usher.py                 # 台词预处理脚本，生成 WebGAL 文本
│   ├── speechgen.py             # 推理配置生成
│   ├── masque.py                # 支持批量翻译 + 角色映射替换
│   ├── gen_jsonl.py             # 批量构建推理用 JSONL 文件
├── gui.py                       # 图形化启动器
├── gui.bat                      # 正常启动（推荐）
├── run.bat                      # 第一次使用安装依赖
└── assets/style.qss             # 可选界面美化样式
```

---

## 🚀 使用方法

### 🛠 第一次使用

1. 克隆或下载本项目；
2. 下载 `GPT-SoVITS 20250422fix` 整合包并解压至项目根目录；
3. 新建以下文件夹：

```bash
mkdir GPT-SoVITS-v4-20250422fix/vocal
mkdir GPT-SoVITS-v4-20250422fix/reference
```

4. 安装依赖：

```bash
run.bat
```

---

## 🧪 常规使用

```bash
gui.bat
```

使用图形界面选择 JSONL 文件、保存目录，点击生成按钮，即可按角色和场景名称输出音频。

---

## 🔧 新功能亮点

### ✅ 1. masque.py：一键翻译支持角色映射与假名替换

- 自动加载 `trans_map_ja.json`，支持中日角色名映射；
- 支持过滤括号 `()` 和 `（）` 内容，避免被翻译；
- 自动为每行文本添加“日本女子高中生语气”提示；
- 输出为 `xxx_ja.json`，可配合 `gen_jsonl.py` 使用。

#### 使用方式：

```bash
python tool/masque.py
# 选择 JSON 文件，如：test.json
# 自动生成 test_ja.json
```

---

### ✅ 2. gen_jsonl.py：批量生成推理用 JSONL 文件

支持从目录中批量生成推理输入，自动编号并支持：

- 多模型路径设置；
- 合并为单个 composite 模型；
- 自动排除无效模型子目录；
- 可直接用于 GUI 音频生成。

---

### ✅ 3. gui.py 图形界面：支持角色+场景音频批量生成

- 支持自动根据 JSONL 文件名识别角色与场景；
- 支持以 `{角色}_{场景}_{编号}` 命名输出；
- 支持点击播放、重新生成；
- 自带进度条与状态提示；
- 默认过滤 `_ja` `_zh` 等语言后缀；

---

## 📁 数据准备说明

| 文件夹       | 内容                                              |
| ------------ | ------------------------------------------------- |
| `vocal/`     | 存放参考音频，如 `anon_0001.wav`                  |
| `reference/` | 存放对应文本，如 `anon_0001.txt`                  |
| `output/`    | 音频输出路径，由 GUI 自动管理                     |

---

## 📦 依赖说明

- 本项目依赖于 GPT-SoVITS 中的 Python 环境（runtime/python.exe）；
- 所有依赖均由 `run.bat` 自动安装，无需手动操作；
- 图形界面基于 PyQt5 + Pygame，支持播放 `.wav` 音频。

---

## 📜 License

本项目基于 MIT 协议开源，所有资源仅供学习交流使用，请勿用于商业用途。
