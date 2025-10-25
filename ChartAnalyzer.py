import json
import os
import random
import string
import shutil
import subprocess
import tkinter as tk  # 添加tk模块的导入
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import wave
import contextlib
import sv_ttk  # 导入Sun-Valley-ttk主题

# 配置文件路径
CONFIG_FILE = "chart_analyzer_config.json"
# 工程配置文件路径
PROJECT_CONFIG_FILE = "project_config.json"
# 音频文件夹配置
audio_folder = ""

def load_config():
    """加载配置文件"""
    global fileDir, audio_folder
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'last_folder' in config and config['last_folder']:
                    fileDir = config['last_folder']
                if 'audio_folder' in config and config['audio_folder']:
                    audio_folder = config['audio_folder']
                return True
    except (json.JSONDecodeError, IOError) as e:
        print(f"加载配置文件失败: {e}")
    return False

def save_config(folder_path):
    """保存配置文件"""
    try:
        config = {'last_folder': folder_path, 'audio_folder': audio_folder}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"保存配置文件失败: {e}")

def generate_random_path():
    """生成8位随机数字作为Path"""
    return ''.join(random.choices(string.digits, k=8))

def load_project_config():
    """加载工程配置"""
    try:
        if os.path.exists(PROJECT_CONFIG_FILE):
            with open(PROJECT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}

def save_project_config(config):
    """保存工程配置"""
    try:
        with open(PROJECT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"保存工程配置失败: {e}")

def create_info_txt(project_folder, project_info):
    """创建info.txt文件"""
    info_content = f"""#
Name: {project_info['Name']}
Path: {project_info['Path']}
Chart: {project_info['Chart']}
Level: {project_info['Level']}
Composer: {project_info['Composer']}
Charter: {project_info['Charter']}
"""
    info_path = os.path.join(project_folder, "info.txt")
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(info_content)

def read_info_txt(project_folder):
    """读取info.txt文件"""
    info_path = os.path.join(project_folder, "info.txt")
    if not os.path.exists(info_path):
        return None
    
    project_info = {}
    with open(info_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                project_info[key.strip()] = value.strip()
    return project_info

def update_info_txt(project_folder, project_info):
    """更新info.txt文件"""
    create_info_txt(project_folder, project_info)

def get_audio_duration(audio_path):
    """获取音频时长（秒）"""
    try:
        with contextlib.closing(wave.open(audio_path, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return round(duration, 2)
    except:
        return None

def create_chart_art(project_folder, project_name, project_level, path_value):
    """创建曲绘图片"""
    try:
        # 图片尺寸 (16:9)
        width = 1920
        height = 1080
        
        # 创建白色背景图片
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # 尝试加载字体
        font_path = "Source Han Sans & Saira Hybrid-Regular #2934.ttf"
        try:
            # 尝试不同的字体大小
            title_font = ImageFont.truetype(font_path, 160)
            level_font = ImageFont.truetype(font_path, 80)
        except:
            # 如果字体加载失败，使用默认字体
            title_font = ImageFont.load_default()
            level_font = ImageFont.load_default()
        
        # 获取文本尺寸
        title_bbox = draw.textbbox((0, 0), project_name, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        
        level_bbox = draw.textbbox((0, 0), project_level, font=level_font)
        level_width = level_bbox[2] - level_bbox[0]
        level_height = level_bbox[3] - level_bbox[1]
        
        # 计算居中位置
        title_x = (width - title_width) // 2
        title_y = (height - title_height) // 2
        
        # 计算难度位置（右下角偏左上）
        level_x = width - level_width - 100  # 距离右边100像素
        level_y = height - level_height - 100  # 距离底部100像素
        
        # 绘制文本
        draw.text((title_x, title_y), project_name, font=title_font, fill='black')
        draw.text((level_x, level_y), project_level, font=level_font, fill='black')
        
        # 保存图片
        image_path = os.path.join(project_folder, f"{path_value}.png")
        image.save(image_path)
        
        return True
    except Exception as e:
        print(f"创建曲绘图片失败: {e}")
        return False


### 用户自定义变量 ###
### 留空请填 None ###

# 铺面文件夹，即 TextAsset 文件夹
fileDir = u"D:"
# 难度
difficulty = "AT"
# 目标物量
targetNumber = 1156
# 目标时长 (单位：秒)
targetMaxTime = 162
# 目标bpm (单位：拍/分钟)
targetBPM = 174
keyWords = ["#", difficulty]
# 输出列表
chartObjectsList: list["Chart"] = []
# 匹配队列
sortedList: list["Chart"] = []
# 文件列表及其长度
fileCount = None
fileList = []
# 已完成扫描
scanned = False


class Chart:
    def __init__(self, file, bpm, aboveNumber, belowNumber, keyMaxTime, eventMaxTime):
        # 文件名称
        self.file = file
        self.fileName = file
        # 铺面 bpm
        self.bpm = bpm
        # 物量
        self.aboveNumber = aboveNumber
        self.belowNumber = belowNumber
        self.objectNumber = aboveNumber + belowNumber
        # 最后一个键的时间
        self.keyMaxTime = keyMaxTime
        self.keyMaxSecond = round(self.keyMaxTime / bpm * 1.875, 2)
        # 最后一个事件的事件
        self.eventMaxTime = eventMaxTime
        self.eventMaxSecond = round(self.eventMaxTime / bpm * 1.875, 2)
        # 曲长
        self.maxTime = max(eventMaxTime, keyMaxTime)
        self.audioLength = round(self.maxTime / bpm * 1.875, 2)
        # 排名分数
        self.sortingScore = 0

    def __str__(self) -> str:
        return f"<Chart '{self.fileName}', bpm={self.bpm}, number={self.objectNumber}, maxTime={self.maxTime}, audioLength={self.audioLength}s>"

    def __repr__(self) -> str:
        return f"<Chart {self.fileName}>"

class AudioFile:
    def __init__(self, file, duration):
        # 文件名称
        self.file = file
        self.fileName = file
        # 音频时长
        self.duration = duration
        # 排名分数
        self.sortingScore = 0

    def __str__(self) -> str:
        return f"<AudioFile '{self.fileName}', duration={self.duration}s>"

    def __repr__(self) -> str:
        return f"<AudioFile {self.fileName}>"

def sortingCallBack(chart: Chart):
    # 给 sorted() 函数排序用的回调函数
    return chart.sortingScore

def audioSortingCallBack(audio: AudioFile):
    # 给 sorted() 函数排序用的回调函数
    return audio.sortingScore

def analyseJsonChart(chartFile: str):
    # 分析铺面文件，生成 Chart 对象
    # 提取物量、bpm、时长等内容
    f = open(chartFile, 'r', encoding="utf-8")
    jsonData = json.load(f)

    # 铺面 bpm
    bpm = jsonData["judgeLineList"][0]["bpm"]
    # 物量
    aboveNumber = 0
    belowNumber = 0
    # 最后一个键的时间
    keyMaxTime = 0
    # 最后一个事件的时间
    eventMaxTime = 0

    # 统计最后一个判定线动画的时间
    for line in jsonData["judgeLineList"]:
        aboveNumber += len(line["notesAbove"])
        belowNumber += len(line["notesBelow"])

        eventList = line["speedEvents"] + line["judgeLineMoveEvents"] + line["judgeLineRotateEvents"] + line["judgeLineDisappearEvents"]
        for event in eventList:
            eventMaxTime = max(event["startTime"], eventMaxTime)
    
    # 统计最后一个note的时间
    for line in jsonData["judgeLineList"]:
        for note in line["notesAbove"]:
            keyMaxTime = max(note["time"], keyMaxTime)

    return Chart(
        chartFile,
        bpm,
        aboveNumber,
        belowNumber,
        keyMaxTime,
        eventMaxTime
    )

def info(*msg, step=" ", end=""):
    msg = step.join(msg)+end
    if 'BL1' in globals() and BL1.winfo_exists():
        BL1.config(text=msg)
    top.update()

# 工程相关变量
current_project = None

# 音频相关变量
audioObjectsList = []
audioSortedList = []
audio_window = None

def create_project_first():
    """首次创建工程"""
    create_window = Toplevel(top)
    create_window.title("创建谱面工程")
    create_window.geometry("550x500")
    create_window.resizable(0, 0)
    
    # 应用亮色主题
    sv_ttk.set_theme("light")
    
    # 创建一个框架作为容器
    main_frame = ttk.Frame(create_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    # 标题
    title_label = ttk.Label(main_frame, text="创建新的谱面工程", font=("微软雅黑", 14, "bold"))
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # 工程文件夹选择
    L_folder = ttk.Label(main_frame, text="工程文件夹（必填）", font=("微软雅黑", 10))
    L_folder.grid(row=1, column=0, sticky=W, pady=5)
    
    folder_frame = ttk.Frame(main_frame)
    folder_frame.grid(row=2, column=0, columnspan=2, sticky=(W, E), pady=5)
    
    E_folder = ttk.Entry(folder_frame, font=("微软雅黑", 10))
    E_folder.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
    
    # 创建按钮样式
    button_style = ttk.Style()
    button_style.configure("TButton", font=("微软雅黑", 10))
    
    B_browse_folder = ttk.Button(folder_frame, text="浏览", command=lambda: browse_project_folder(E_folder))
    B_browse_folder.pack(side=RIGHT)
    
    # 分隔线
    separator1 = ttk.Separator(main_frame, orient=HORIZONTAL)
    separator1.grid(row=3, column=0, columnspan=2, sticky=(W, E), pady=15)
    
    # 谱面信息输入
    info_label = ttk.Label(main_frame, text="谱面信息", font=("Microsoft YaHei", 12, "bold"))
    info_label.grid(row=4, column=0, columnspan=2, sticky=W, pady=(0, 10))
    
    fields = [
        ("谱面名称（必填）", "Name", ""),
        ("难度（必填）", "Level", ""),
        ("Composer（默认：phigros）", "Composer", "phigros"),
        ("Charter（默认：phigros）", "Charter", "phigros")
    ]
    
    entries = {}
    for i, (label_text, field_name, default_value) in enumerate(fields):
        label = ttk.Label(main_frame, text=label_text, font=("微软雅黑", 10))
        label.grid(row=5+i, column=0, sticky=W, pady=5)
        
        entry = ttk.Entry(main_frame, font=("微软雅黑", 10))
        entry.grid(row=5+i, column=1, sticky=(W, E), pady=5, padx=(10, 0))
        entry.insert(0, default_value)
        entries[field_name] = entry
    
    # 创建按钮和复选框样式
    button_style = ttk.Style()
    button_style.configure("TButton", font=("微软雅黑", 10))
    button_style.configure("TCheckbutton", font=("微软雅黑", 10))
    
    # 是否自创建曲绘复选框
    var_create_art = BooleanVar()
    CB_create_art = ttk.Checkbutton(main_frame, text="是否自创建曲绘", variable=var_create_art)
    CB_create_art.grid(row=9, column=0, columnspan=2, sticky=W, pady=10)
    
    # 按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=10, column=0, columnspan=2, pady=20)
    
    # 创建按钮
    def create_project():
        global current_project
        
        folder_path = E_folder.get().strip()
        if not folder_path:
            messagebox.showerror("错误", "请选择工程文件夹！")
            return
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
            except:
                messagebox.showerror("错误", "无法创建工程文件夹！")
                return
        
        # 验证必填字段
        name = entries["Name"].get().strip()
        level = entries["Level"].get().strip()
        
        if not name:
            messagebox.showerror("错误", "请填写谱面名称！")
            return
        if not level:
            messagebox.showerror("错误", "请填写难度！")
            return
        
        # 生成随机Path
        path_value = generate_random_path()
        
        # 创建工程信息
        project_info = {
            "Name": name,
            "Path": path_value,
            "Chart": "",
            "Level": level,
            "Composer": entries["Composer"].get().strip(),
            "Charter": entries["Charter"].get().strip()
        }
        
        # 创建info.txt
        create_info_txt(folder_path, project_info)
        
        # 如果勾选了自创建曲绘，则生成图片
        if var_create_art.get():
            if create_chart_art(folder_path, name, level, path_value):
                messagebox.showinfo("成功", "曲绘图片创建成功！")
            else:
                messagebox.showwarning("警告", "曲绘图片创建失败，但工程已创建。")
        
        # 设置当前工程
        current_project = {
            "folder": folder_path,
            "info": project_info
        }
        
        # 保存工程配置
        project_config = load_project_config()
        project_config[path_value] = current_project
        save_project_config(project_config)
        
        messagebox.showinfo("成功", "工程创建成功！")
        create_window.destroy()
        
        # 打开搜索窗口
        open_search_window()
    
    B_create = ttk.Button(button_frame, text="创建工程", command=create_project, style="Accent.TButton")
    B_create.pack(side=RIGHT, padx=5)
    
    # 配置网格权重
    main_frame.columnconfigure(1, weight=1)

def browse_project_folder(entry_widget):
    """浏览选择工程文件夹"""
    folder_path = filedialog.askdirectory(title="选择工程文件夹")
    if folder_path:
        entry_widget.delete(0, END)
        entry_widget.insert(0, folder_path)

def add_chart_to_project():
    """添加选中的谱面到当前工程"""
    global current_project
    
    # 检查是否有当前工程
    if not current_project:
        messagebox.showwarning("警告", "请先创建工程！")
        return
    
    # 检查工程是否已有谱面
    if current_project["info"].get("Chart", ""):
        messagebox.showwarning("警告", "当前工程已添加谱面，无法重复添加！")
        return
    
    # 获取选中的谱面
    selection = T1.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要添加的谱面！")
        return
    
    item = T1.item(selection[0])
    chart_filename = item['values'][0]  # 谱面文件名
    
    try:
        # 复制谱面文件到工程文件夹
        source_path = os.path.join(fileDir, chart_filename)
        target_filename = f"{current_project['info']['Path']}.json"
        target_path = os.path.join(current_project['folder'], target_filename)
        
        shutil.copy2(source_path, target_path)
        
        # 更新工程信息
        current_project['info']['Chart'] = target_filename
        update_info_txt(current_project['folder'], current_project['info'])
        
        # 更新工程配置
        project_config = load_project_config()
        project_config[current_project['info']['Path']]['info'] = current_project['info']
        save_project_config(project_config)
        
        messagebox.showinfo("成功", f"谱面已添加到工程 '{current_project['info']['Name']}'！")
        update_project_display()
        
        # 关闭谱面搜索窗口
        search_window.destroy()
        
        # 打开音频筛选窗口
        open_audio_search_window()
        
    except Exception as e:
        messagebox.showerror("错误", f"添加谱面失败：{str(e)}")

def open_project_folder():
    """打开当前工程文件夹"""
    if not current_project:
        messagebox.showwarning("警告", "没有当前工程！")
        return
    
    folder_path = current_project['folder']
    try:
        if os.path.exists(folder_path):
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', folder_path])
        else:
            messagebox.showerror("错误", f"工程文件夹不存在：{folder_path}")
    except Exception as e:
        messagebox.showerror("错误", f"无法打开文件夹：{str(e)}")

def update_project_display():
    """更新工程信息显示"""
    if current_project:
        project_info = current_project["info"]
        # 可以在界面上显示当前工程信息
        if 'BL1' in globals() and BL1.winfo_exists():
            BL1.config(text=f"当前工程: {project_info['Name']} ({project_info['Level']})")

def selectPath():
    global fileDir
    path = filedialog.askdirectory(title="打开铺面文件夹", initialdir=fileDir)
    if not path:
        return
    else:
        E1.delete(0, END)
        E1.insert(0, path)
        fileDir = path
        save_config(path)

def main():
    global chartObjectsList
    global fileList, chartObjectsList
    global fileDir, fileCount
    global scanned
    global keyWords
    global targetBPM, targetNumber, targetMaxTime, difficulty

    # 预处理数据
    fileDir = E1.get()
    if not os.path.exists(fileDir):
        messagebox.showerror("错误", "路径不存在。")
        return

    difficulty = E2.get()
    targetNumber = E3.get()
    targetBPM = E4.get()
    targetMaxTime = E5.get()

    if targetNumber == "" and targetBPM == "" and targetMaxTime == "":
        messagebox.showerror("缺少筛选条件", "请至少填写一个筛选条件！")
        return

    if difficulty == "":
        difficulty = None
        keyWords = ["#"]
    else:
        keyWords = ["#", difficulty]
    if targetNumber == "":
        targetNumber = None
    else:
        targetNumber = int(targetNumber)
    if targetBPM == "":
        targetBPM = None
    else:
        targetBPM = int(targetBPM)
    if targetMaxTime == "":
        targetMaxTime = None
    else:
        targetMaxTime = int(targetMaxTime)

    # 开始逐个分析谱面
    scanned = True
    fileList = os.listdir(fileDir)
    fileCount = len(fileList)
    chartObjectsList = []
    
    # 初始化进度条
    if 'progress_var_audio' in globals() and progress_var_audio is not None:
        progress_var_audio.set(0)
        if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
            progress_bar_audio.update()
    
    processed_count = 0

    for i in range(len(fileList)):
        file = fileList[i]
        fileName = fileList[i]
        
        # 更新进度条
        progress = (i / fileCount) * 50  # 分析阶段占50%
        if 'progress_var' in globals() and progress_var is not None:
            progress_var.set(progress)
            if 'progress_bar' in globals() and progress_bar is not None:
                progress_bar.update()
        
        # 更新UI防止未响应
        if 'top' in globals() and top is not None:
            top.update()

        # 确认是否含有关键词
        # 跳过不含关键词的文件
        skip = False
        for keyword in keyWords:
            if keyword not in file:
                skip = True
        if skip:
            continue

        # 尝试分析铺面文件
        try:
            chart = analyseJsonChart(os.path.join(fileDir, file))
            chartObjectsList.append(chart)
            processed_count += 1
            if 'BL1' in globals() and BL1.winfo_exists():
                BL1.config(text=f"{i+1}/{fileCount}\t分析完成{chart}")
        except KeyError as e:
            if 'BL1' in globals() and BL1.winfo_exists():
                BL1.config(text=f"{i+1}/{fileCount}\t分析'{file}'时遇到 KeyError:" + str(e))
        except Exception as e:
            if 'BL1' in globals() and BL1.winfo_exists():
                BL1.config(text=f"{i+1}/{fileCount}\t分析'{file}'时出错: {str(e)}")

    # 计算匹配度
    if 'BL1' in globals() and BL1.winfo_exists():
        BL1.config(text=f"正在对 {len(chartObjectsList)} 个铺面文件进行匹配。")
    
    # 重置分数
    for chart in chartObjectsList:
        chart.sortingScore = 0
    
    # 计算匹配度并更新进度
    for i, chart in enumerate(chartObjectsList):
        if targetNumber is not None:
            chart.sortingScore += max(0, 10 - abs(targetNumber - chart.objectNumber))
        if targetBPM is not None:
            chart.sortingScore += max(0, 10 - 0.2 * abs(targetBPM - chart.bpm))
        if targetMaxTime is not None:
            chart.sortingScore += max(0, 10 - 0.2 * abs(targetMaxTime - chart.audioLength))
        
        # 更新进度条（匹配阶段占50%）
        progress = 50 + (i / len(chartObjectsList)) * 50
        if 'progress_var' in globals() and progress_var is not None:
            progress_var.set(progress)
            if 'progress_bar' in globals() and progress_bar is not None:
                progress_bar.update()
        
        # 更新UI防止未响应
        if 'top' in globals() and top is not None:
            top.update()
    
    # 完成进度条
    if 'progress_var' in globals() and progress_var is not None:
        progress_var.set(100)
        if 'progress_bar' in globals() and progress_bar is not None:
            progress_bar.update()
    
    # 进行排序
    sortedList: list["Chart"] = sorted(chartObjectsList, key=sortingCallBack, reverse=True)[:10]

    # 输出到T1
    for child in T1.get_children():
        T1.delete(child)
    if len(sortedList) == 0:
        if 'BL1' in globals() and BL1.winfo_exists():
            BL1.config(text="匹配完成。未找到任何匹配项目。")
    elif sortedList[0].sortingScore <= 0:
        if 'BL1' in globals() and BL1.winfo_exists():
            BL1.config(text="匹配完成。未找到任何匹配项目。")
    else:
        if 'BL1' in globals() and BL1.winfo_exists():
            BL1.config(text="匹配完成，最佳匹配项为："+sortedList[0].fileName)
        for i in range(len(sortedList)):
            chart = sortedList[i]
            if chart.sortingScore <= 0:
                continue
            T1.insert("", "end",
              values=(
                  chart.fileName,
                  chart.objectNumber,
                  chart.bpm,
                  chart.audioLength,
                  f"{chart.sortingScore / 30:.2%}"
            ))

def check_existing_project():
    """检查是否有现有工程"""
    global current_project
    project_config = load_project_config()
    
    # 查找没有设置Chart的工程（可以继续添加谱面的工程）
    for path_value, project_data in project_config.items():
        project_info = project_data.get("info", {})
        if not project_info.get("Chart", ""):  # Chart为空表示可以继续使用
            current_project = {
                "folder": project_data["folder"],
                "info": project_info
            }
            return True
    
    return False

def open_audio_search_window():
    """打开音频搜索窗口"""
    global audio_window, E_audio_folder, E_audio_duration, T_audio, BL_audio, progress_var_audio, progress_bar_audio
    
    # 关闭其他窗口
    if 'search_window' in globals() and search_window is not None and search_window.winfo_exists():
        search_window.destroy()
    
    # 导入tk模块（用于进度条）
    import tkinter as tk
    
    audio_window = Toplevel(top)
    audio_window.title("音频搜索")
    audio_window.geometry("750x750")  # 增加窗口高度
    audio_window.resizable(0, 0)
    
    # 应用主题到新窗口
    sv_ttk.set_theme("light")
    
    # 创建一个框架作为容器
    main_frame = ttk.Frame(audio_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    # 标题
    title_label = ttk.Label(main_frame, text="音频筛选", font=("微软雅黑", 14, "bold"))
    title_label.grid(row=0, column=0, columnspan=4, pady=(0, 15))
    
    # 音频文件夹选择
    L_audio_folder = ttk.Label(main_frame, text="音频文件夹（wav）", font=("微软雅黑", 10))
    L_audio_folder.grid(row=1, column=0, sticky=W, pady=5)
    
    folder_frame = ttk.Frame(main_frame)
    folder_frame.grid(row=2, column=0, columnspan=4, sticky=(W, E), pady=5)
    
    E_audio_folder = ttk.Entry(folder_frame, font=("微软雅黑", 10))
    E_audio_folder.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
    
    # 如果有保存的音频文件夹路径，则加载
    if 'audio_folder' in globals() and audio_folder:
        E_audio_folder.insert(0, audio_folder)
    
    # 创建按钮样式
    button_style = ttk.Style()
    button_style.configure("TButton", font=("微软雅黑", 10))
    
    # 选取按钮
    B_audio_browse = ttk.Button(folder_frame, text="选取", command=select_audio_folder)
    B_audio_browse.pack(side=RIGHT)
    
    # 音频时长筛选
    filter_frame = ttk.LabelFrame(main_frame, text="筛选条件", padding="10")
    filter_frame.grid(row=3, column=0, columnspan=4, sticky=(W, E), pady=15)
    
    L_audio_duration = ttk.Label(filter_frame, text="目标音频时长（秒，精确到小数点后两位）", font=("微软雅黑", 10))
    L_audio_duration.grid(row=0, column=0, sticky=W, pady=5)
    
    duration_frame = ttk.Frame(filter_frame)
    duration_frame.grid(row=1, column=0, sticky=(W, E), pady=5)
    
    E_audio_duration = ttk.Entry(duration_frame, font=("微软雅黑", 10), width=20)
    E_audio_duration.pack(side=LEFT)
    
    # 创建按钮样式
    button_style = ttk.Style()
    button_style.configure("TButton", font=("微软雅黑", 10))
    
    B_audio_filter = ttk.Button(duration_frame, text="开始筛选", command=audio_main, style="Accent.TButton")
    B_audio_filter.pack(side=LEFT, padx=(15, 0))
    
    # 当前工程信息显示
    if current_project:
        project_info = current_project["info"]
        project_frame = ttk.LabelFrame(main_frame, text="当前工程", padding="10")
        project_frame.grid(row=4, column=0, columnspan=4, sticky=(W, E), pady=15)
        
        L_project = ttk.Label(project_frame, text=f"{project_info['Name']} ({project_info['Level']})", font=("微软雅黑", 10, "bold"))
        L_project.pack()

    # 音频列表
    list_frame = ttk.LabelFrame(main_frame, text="搜索结果", padding="10")
    list_frame.grid(row=6, column=0, columnspan=5, sticky=(W, E, N, S), pady=10)
    
    # 设置LabelFrame的字体样式
    label_frame_style = ttk.Style()
    label_frame_style.configure("TLabelframe.Label", font=("微软雅黑", 10, "bold"))
    
    # 创建进度条
    progress_var_audio = tk.DoubleVar()
    progress_bar_audio = ttk.Progressbar(list_frame, variable=progress_var_audio, maximum=100)
    progress_bar_audio.pack(fill=X, pady=(0, 5))
    
    # 创建表格样式
    tree_style = ttk.Style()
    tree_style.configure("Treeview", font=("微软雅黑", 10))
    tree_style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
    
    T_audio = ttk.Treeview(list_frame, height=22)  # 增加表格高度
    T_audio.pack(fill=BOTH, expand=True)
    
    # 按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=6, column=0, columnspan=4, pady=10)
    
    # 创建按钮样式
    button_style = ttk.Style()
    button_style.configure("TButton", font=("微软雅黑", 10))
    
    B_add_audio_to_project = ttk.Button(button_frame, text="添加到工程", command=add_audio_to_project, style="Accent.TButton")
    B_add_audio_to_project.pack(side=LEFT, padx=(0, 10))
    
    B_play_audio = ttk.Button(button_frame, text="播放选中音频", command=play_audio)
    B_play_audio.pack(side=LEFT, padx=(0, 10))
    
    B_open_project_folder = ttk.Button(button_frame, text="打开工程文件夹", command=open_project_folder)
    B_open_project_folder.pack(side=LEFT)

    # 状态栏
    BL_audio = ttk.Label(main_frame, anchor="w", font=("微软雅黑", 10))
    BL_audio.grid(row=7, column=0, columnspan=4, sticky=(W, E), pady=(10, 0))

    # 配置表格列
    column = ["1", "2", "3"]
    T_audio.config(columns=column, show='headings')
    T_audio.heading("1", text="文件路径")
    T_audio.heading("2", text="音频时长（秒）")
    T_audio.heading("3", text="匹配度")
    T_audio.column("1", width=400)
    T_audio.column("2", width=100)
    T_audio.column("3", width=100)
    
    # 配置网格权重
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(5, weight=1)

def select_audio_folder():
    """选择音频文件夹"""
    global audio_folder
    folder_path = filedialog.askdirectory(title="选择音频文件夹")
    if folder_path:
        E_audio_folder.delete(0, END)
        E_audio_folder.insert(0, folder_path)
        audio_folder = folder_path
        save_config(fileDir)  # 保存音频文件夹配置

def audio_main():
    """音频筛选主函数"""
    global audioObjectsList, audioSortedList, audio_window
    
    # 获取音频文件夹路径
    audio_folder = E_audio_folder.get()
    if not audio_folder or not os.path.exists(audio_folder):
        messagebox.showerror("错误", "请选择有效的音频文件夹！")
        return
    
    # 获取目标音频时长
    target_duration_str = E_audio_duration.get()
    if not target_duration_str:
        messagebox.showerror("错误", "请填写目标音频时长！")
        return
    
    try:
        target_duration = float(target_duration_str)
    except ValueError:
        messagebox.showerror("错误", "音频时长必须是数字！")
        return
    
    # 扫描音频文件
    audio_files = [f for f in os.listdir(audio_folder) if f.lower().endswith('.wav')]
    audioObjectsList = []
    
    # 初始化进度条
    if 'progress_var_audio' in globals() and progress_var_audio is not None:
        progress_var_audio.set(0)
        if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
            progress_bar_audio.update()
    
    for i, audio_file in enumerate(audio_files):
        # 更新进度条（分析阶段占50%）
        progress = (i / len(audio_files)) * 50
        if 'progress_var_audio' in globals() and progress_var_audio is not None:
            progress_var_audio.set(progress)
            if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
                progress_bar_audio.update()
        
        # 更新UI防止未响应
        if 'audio_window' in globals() and audio_window is not None:
            audio_window.update()
        
        audio_path = os.path.join(audio_folder, audio_file)
        duration = get_audio_duration(audio_path)
        
        if duration is not None:
            audio_obj = AudioFile(audio_file, duration)
            audioObjectsList.append(audio_obj)
            if 'BL_audio' in globals() and BL_audio.winfo_exists():
                BL_audio.config(text=f"{i+1}/{len(audio_files)}\t分析完成 {audio_file}")
            audio_window.update()
    
    # 计算匹配度
    if 'BL_audio' in globals() and BL_audio.winfo_exists():
        BL_audio.config(text=f"正在对 {len(audioObjectsList)} 个音频文件进行匹配...")
    audio_window.update()
    
    for i, audio_obj in enumerate(audioObjectsList):
        # 更新进度条（匹配阶段占40%）
        progress = 50 + (i / len(audioObjectsList)) * 40
        if 'progress_var_audio' in globals() and progress_var_audio is not None:
            progress_var_audio.set(progress)
            if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
                progress_bar_audio.update()
        
        # 匹配度计算：时长越接近，匹配度越高
        time_diff = abs(target_duration - audio_obj.duration)
        audio_obj.sortingScore = max(0, 10 - time_diff * 2)  # 每差1秒扣2分
    
    # 进行排序
    audioSortedList = sorted(audioObjectsList, key=audioSortingCallBack, reverse=True)[:10]
    
    # 输出到T_audio
    for child in T_audio.get_children():
        T_audio.delete(child)
    
    if len(audioSortedList) == 0:
        if 'BL_audio' in globals() and BL_audio.winfo_exists():
            BL_audio.config(text="匹配完成。未找到任何匹配项目。")
    elif audioSortedList[0].sortingScore <= 0:
        if 'BL_audio' in globals() and BL_audio.winfo_exists():
            BL_audio.config(text="匹配完成。未找到任何匹配项目。")
    else:
        if 'BL_audio' in globals() and BL_audio.winfo_exists():
            BL_audio.config(text=f"匹配完成，最佳匹配项为：{audioSortedList[0].fileName}")
        for audio_obj in audioSortedList:
            if audio_obj.sortingScore <= 0:
                continue
            T_audio.insert("", "end",
                values=(
                    audio_obj.fileName,
                    audio_obj.duration,
                    f"{audio_obj.sortingScore / 10:.2%}"
                ))
    
    # 更新进度条完成
    if 'progress_var_audio' in globals() and progress_var_audio is not None:
        progress_var_audio.set(100)
        if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
            progress_bar_audio.update()

def add_audio_to_project():
    """添加选中的音频到工程"""
    global current_project, E_audio_folder, T_audio, audio_window
    
    if not current_project:
        messagebox.showwarning("警告", "没有当前工程！")
        return
    
    # 获取选中的音频
    selection = T_audio.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要添加的音频！")
        return
    
    item = T_audio.item(selection[0])
    audio_filename = item['values'][0]  # 音频文件名
    
    try:
        # 获取文件扩展名
        file_ext = os.path.splitext(audio_filename)[1]
        
        # 生成目标文件名（8位数字+原扩展名）
        target_filename = f"{current_project['info']['Path']}{file_ext}"
        target_path = os.path.join(current_project['folder'], target_filename)
        
        # 复制音频文件到工程文件夹
        source_path = os.path.join(E_audio_folder.get(), audio_filename)
        shutil.copy2(source_path, target_path)
        
        # 关闭音频搜索窗口
        # if 'audio_window' in globals() and audio_window.winfo_exists():
        #     audio_window.destroy()
        
        messagebox.showinfo("成功", f"音频已添加到工程 '{current_project['info']['Name']}'！")
        
    except Exception as e:
        messagebox.showerror("错误", f"添加音频失败：{str(e)}")

def play_audio():
    """播放选中的音频"""
    selection = T_audio.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要播放的音频！")
        return
    
    item = T_audio.item(selection[0])
    audio_filename = item['values'][0]
    audio_path = os.path.join(E_audio_folder.get(), audio_filename)
    
    try:
        if os.path.exists(audio_path):
            if os.name == 'nt':  # Windows
                os.startfile(audio_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', audio_path])
        else:
            messagebox.showerror("错误", f"音频文件不存在：{audio_path}")
    except Exception as e:
        messagebox.showerror("错误", f"无法播放音频：{str(e)}")

def open_search_window():
    """打开谱面搜索窗口"""
    global search_window, E1, E2, E3, E4, E5, T1, BL1, progress_var, progress_bar
    
    # 关闭其他窗口
    if 'audio_window' in globals() and audio_window is not None and audio_window.winfo_exists():
        audio_window.destroy()
    
    # 导入tk模块（用于进度条）
    import tkinter as tk
    
    search_window = Toplevel(top)
    search_window.title("谱面搜索")
    search_window.geometry("750x650")
    search_window.resizable(0, 0)
    
    # 应用主题到新窗口
    sv_ttk.set_theme("light")
    
    # 创建一个框架作为容器
    main_frame = ttk.Frame(search_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    # 标题
    title_label = ttk.Label(main_frame, text="谱面搜索", font=("微软雅黑", 14, "bold"))
    title_label.grid(row=0, column=0, columnspan=5, pady=(0, 15))
    
    # 谱面文件夹选择
    L1 = ttk.Label(main_frame, text="谱面文件夹（TextAsset）", font=("微软雅黑", 10))
    L1.grid(row=1, column=0, sticky=W, pady=5)
    
    folder_frame = ttk.Frame(main_frame)
    folder_frame.grid(row=2, column=0, columnspan=5, sticky=(W, E), pady=5)
    
    E1 = ttk.Entry(folder_frame, font=("微软雅黑", 10))
    E1.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
    
    # 创建按钮样式
    button_style = ttk.Style()
    button_style.configure("TButton", font=("微软雅黑", 10))
    
    B1 = ttk.Button(folder_frame, text="选取", command=selectPath)
    B1.pack(side=RIGHT)
    
    # 设置初始文件夹路径
    E1.insert(0, fileDir)

    # 筛选条件
    filter_label = ttk.Label(main_frame, text="筛选条件", font=("微软雅黑", 12, "bold"))
    filter_label.grid(row=3, column=0, columnspan=5, sticky=W, pady=(15, 10))

    # 筛选条件框架
    filter_frame = ttk.Frame(main_frame)
    filter_frame.grid(row=4, column=0, columnspan=5, sticky=(W, E), pady=5)
    
    L2 = ttk.Label(filter_frame, text="关键词", font=("微软雅黑", 10))
    L2.grid(row=0, column=0, sticky=W, padx=(0, 5))
    E2 = ttk.Entry(filter_frame, font=("微软雅黑", 10), width=15)
    E2.grid(row=0, column=1, sticky=W, padx=(0, 15))

    L3 = ttk.Label(filter_frame, text="物量", font=("微软雅黑", 10))
    L3.grid(row=0, column=2, sticky=W, padx=(0, 5))
    E3 = ttk.Entry(filter_frame, font=("微软雅黑", 10), width=15)
    E3.grid(row=0, column=3, sticky=W, padx=(0, 15))

    L4 = ttk.Label(filter_frame, text="BPM", font=("微软雅黑", 10))
    L4.grid(row=1, column=0, sticky=W, padx=(0, 5), pady=(10, 0))
    E4 = ttk.Entry(filter_frame, font=("微软雅黑", 10), width=15)
    E4.grid(row=1, column=1, sticky=W, padx=(0, 15), pady=(10, 0))

    L5 = ttk.Label(filter_frame, text="音频长度", font=("微软雅黑", 10))
    L5.grid(row=1, column=2, sticky=W, padx=(0, 5), pady=(10, 0))
    E5 = ttk.Entry(filter_frame, font=("微软雅黑", 10), width=15)
    E5.grid(row=1, column=3, sticky=W, padx=(0, 15), pady=(10, 0))

    # 创建按钮样式
    button_style = ttk.Style()
    button_style.configure("TButton", font=("微软雅黑", 10))
    
    B2 = ttk.Button(filter_frame, text="开始筛选", command=main, style="Accent.TButton")
    B2.grid(row=0, column=4, rowspan=2, padx=(15, 0))
    
    # 当前工程信息显示
    if current_project:
        project_info = current_project["info"]
        project_frame = ttk.LabelFrame(main_frame, text="当前工程", padding="10")
        project_frame.grid(row=5, column=0, columnspan=5, sticky=(W, E), pady=15)
        
        L_project = ttk.Label(project_frame, text=f"{project_info['Name']} ({project_info['Level']})", font=("Microsoft YaHei", 10, "bold"))
        L_project.pack()

    # 谱面列表
    list_frame = ttk.LabelFrame(main_frame, text="搜索结果", padding="10")
    list_frame.grid(row=6, column=0, columnspan=5, sticky=(W, E, N, S), pady=10)
    
    # 设置LabelFrame的字体样式
    label_frame_style = ttk.Style()
    label_frame_style.configure("TLabelframe.Label", font=("微软雅黑", 10, "bold"))
    
    # 创建进度条
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(list_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill=X, pady=(0, 5))
    
    # 创建表格样式
    tree_style = ttk.Style()
    tree_style.configure("Treeview", font=("微软雅黑", 10))
    tree_style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
    
    T1 = ttk.Treeview(list_frame, height=18)
    T1.pack(fill=BOTH, expand=True)
    
    # 按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=7, column=0, columnspan=5, pady=10)
    
    # 创建按钮样式
    button_style = ttk.Style()
    button_style.configure("TButton", font=("微软雅黑", 10))
    
    B_add_to_project = ttk.Button(button_frame, text="添加到工程", command=add_chart_to_project)
    B_add_to_project.pack(side=LEFT, padx=(0, 10))
    
    B_open_folder = ttk.Button(button_frame, text="打开工程文件夹", command=open_project_folder)
    B_open_folder.pack(side=LEFT)

    # 状态栏
    BL1 = ttk.Label(main_frame, anchor="w", font=("微软雅黑", 10))
    BL1.grid(row=8, column=0, columnspan=5, sticky=(W, E), pady=(10, 0))

    # 配置表格列
    column = ["1", "2", "3", "4", "5"]
    T1.config(columns=column, show='headings')
    T1.heading("1", text="文件路径")
    T1.heading("2", text="物量")
    T1.heading("3", text="BPM")
    T1.heading("4", text="谱面时长（秒）")
    T1.heading("5", text="匹配度")
    T1.column("1", width=300)
    T1.column("2", width=80)
    T1.column("3", width=80)
    T1.column("4", width=100)
    T1.column("5", width=80)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=T1.yview)
    T1.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    # 配置网格权重
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(6, weight=1)
    
    # 关闭主窗口
    top.withdraw()

if __name__ == '__main__':
    # 加载配置文件
    load_config()
    
    # 创建主窗口（隐藏）
    top = Tk()
    top.withdraw()  # 立即隐藏主窗口
    top.title("ChartAnalyzer")
    
    # 应用Sun-Valley-ttk主题
    sv_ttk.set_theme("dark")  # 设置为深色主题
    
    # 设置全局字体
    top.option_add("*Font", "微软雅黑 10")
    
    # 应用亮色主题
    sv_ttk.set_theme("light")
    
    # 检查是否有现有工程，如果没有则强制创建
    if not check_existing_project():
        top.after(100, create_project_first)  # 延迟100ms后弹出创建窗口
    else:
        top.after(100, open_search_window)  # 直接打开搜索窗口
    
    mainloop()