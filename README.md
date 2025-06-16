# 🎵 SonicEastMount

**SonicEastMount** 是一个基于 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 的中文语音生成图形化工具，旨在让用户通过 GUI 界面一键完成文本到语音的推理与生成。
建议结合gpt_sovits以及[webgal](https://github.com/OpenWebGAL/WebGAL)使用
本项目整合了 GPT 语义建模、SoVITS 声音合成等模块，使用者只需准备好音频与台词文本，即可快速生成符合角色风格的配音。

---

## 🧩 项目结构与依赖

> ✅ 本项目默认使用 [GPT-SoVITS v4（20250422fix）整合包](https://github.com/RVC-Boss/GPT-SoVITS)

请前往原始项目下载整合包，解压并放置到本项目目录下，**文件夹名保持为：`GPT-SoVITS-v4-20250422fix`**。
如果您使用的并不是该整合包，可以在.env文件里面更换目录名
**.env文件如下**
```.env
SOVITS_DIR=GPT-SoVITS-v4-20250422fix
```

```
SonicEastMount/
├── GPT-SoVITS-v4-20250422fix/   # GPT-SoVITS 核心目录（需自行下载）
│   ├── vocal/                   # 存放待推理的参考音频（需手动创建）
│   ├── reference/               # 存放每段音频的文本内容（需手动创建
├── tool/
│   ├── gen_vocal.py             
│   ├── usher.py                 # 台词预处理脚本，生成webgal代码
│   ├── speechgen.py             # 推理配置生成脚本
├── gui.py                       # 图形化启动器
├── run.bat                      # 第一次使用：安装依赖
└── gui.bat                      # 正常使用：启动 GUI
```

---

## 🚀 使用方法

### 🛠 第一次使用

1. 克隆或下载本项目；

2. 前往 [GPT-SoVITS 仓库](https://github.com/RVC-Boss/GPT-SoVITS) 下载 `20250422v4` 整合包；

3. 解压整合包至当前项目目录，确保路径如下：

   ```
   ./GPT-SoVITS-v4-20250422fix/
   ```

4. 在GPT-SoVITS-v4-20250422fix目录下新建两个目录：

   ```
   ./vocal/        # 存放参考音频，如 anon_0001.wav
   ./reference/    # 存放对应文本文件，如 anon_0001.txt
   ```

5. 运行安装依赖脚本（仅第一次）：

   ```bash
   run.bat
   ```

---

### 🧪 后续使用

直接运行图形化界面：

```bash
gui.bat
```

在窗口中填写场景名称、输入台词文本，选择是否插入音频或整理台词，即可生成 `output/output.txt` 可用于 WebGAL、Live2D 等项目集成。

---

## 📁 数据准备说明

| 文件夹       | 内容                                              |
| ------------ | ------------------------------------------------- |
| `vocal/`     | 存放参考音频，每段语音需对应一个 `.txt` 文件      |
| `reference/` | 存放每段音频的台词内容，文件名需与音频一致        |
| 示例：       | `vocal/anon_0001.wav` + `reference/anon_0001.txt` |

---

## 📦 依赖说明

本项目使用独立的 Python 环境，路径为：

```
GPT-SoVITS-v4-20250422fix/runtime/python.exe
```

依赖安装由 `run.bat` 自动完成，无需手动处理。之后使用 `gui.bat` 统一调用此环境。

---

## 💡 功能特色

- 🎛 图形化操作界面，零代码门槛；
- 🗣 支持角色台词识别与语音推理配置生成；
- 🔄 语音文件与文本自动对应；
- 💾 可直接导出用于 WebGAL 项目的台词脚本。


---

## 📜 License

本项目基于 MIT协议