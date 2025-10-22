import json
import os
import random
import string
import shutil
import subprocess
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import wave
import contextlib

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
    create_window.geometry("500x450")
    create_window.resizable(0, 0)
    
    # 工程文件夹选择
    L_folder = Label(create_window, text="工程文件夹（必填）")
    L_folder.place(x=20, y=20)
    
    E_folder = ttk.Entry(create_window)
    E_folder.place(x=20, y=45, width=380, height=30)
    
    B_browse_folder = ttk.Button(create_window, text="浏览", command=lambda: browse_project_folder(E_folder))
    B_browse_folder.place(x=410, y=45, width=70, height=30)
    
    # 谱面信息输入
    fields = [
        ("谱面名称（必填）", "Name", ""),
        ("难度（必填）", "Level", ""),
        ("Composer（默认：phigros）", "Composer", "phigros"),
        ("Charter（默认：phigros）", "Charter", "phigros")
    ]
    
    entries = {}
    for i, (label_text, field_name, default_value) in enumerate(fields):
        label = Label(create_window, text=label_text)
        label.place(x=20, y=90 + i*40)
        
        entry = ttk.Entry(create_window)
        entry.place(x=20, y=115 + i*40, width=460, height=30)
        entry.insert(0, default_value)
        entries[field_name] = entry
    
    # 是否自创建曲绘复选框
    var_create_art = BooleanVar()
    CB_create_art = ttk.Checkbutton(create_window, text="是否自创建曲绘", variable=var_create_art)
    CB_create_art.place(x=20, y=270)
    
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
    
    B_create = ttk.Button(create_window, text="创建工程", command=create_project)
    B_create.place(x=350, y=400, width=120, height=40)

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
        info(f"当前工程: {project_info['Name']} ({project_info['Level']})")

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

    for i in range(len(fileList)):
        file = fileList[i]
        fileName = fileList[i]

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
            info(f"{i}/{fileCount}\t分析完成{chart}")
        except KeyError as e:
            info(f"{i}/{fileCount}\t分析'{file}'时遇到 KeyError:" + str(e))

    # 计算匹配度
    info(f"正在对 {fileCount} 个铺面文件进行匹配。")
    chart.sortingScore = 0
    for chart in chartObjectsList:
        if targetNumber is not None:
            chart.sortingScore += max(0, 10 - abs(targetNumber - chart.objectNumber))
        if targetBPM is not None:
            chart.sortingScore += max(0, 10 - 0.2 * abs(targetBPM - chart.bpm))
        if targetMaxTime is not None:
            chart.sortingScore += max(0, 10 - 0.2 * abs(targetMaxTime - chart.audioLength))
    # 进行排序
    sortedList: list["Chart"] = sorted(chartObjectsList, key=sortingCallBack, reverse=True)[:10]

    # 输出到T1
    for child in T1.get_children():
        T1.delete(child)
    if len(sortedList) == 0:
        info("匹配完成。未找到任何匹配项目。")
    elif sortedList[0].sortingScore <= 0:
        info("匹配完成。未找到任何匹配项目。")
    else:
        info("匹配完成，最佳匹配项为："+sortedList[0].fileName)
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
    """打开音频筛选窗口"""
    global audio_window, E_audio_folder, E_audio_duration, T_audio, BL_audio
    
    # 关闭其他窗口
    if 'search_window' in globals() and search_window is not None and search_window.winfo_exists():
        search_window.destroy()
    
    audio_window = Toplevel(top)
    audio_window.title("音频筛选")
    audio_window.geometry("700x500")
    audio_window.resizable(0, 0)
    
    # 全局变量引用
    global E_audio_folder, E_audio_duration, T_audio, BL_audio
    
    # 音频文件夹选择
    L_audio_folder = Label(audio_window, text="音频文件夹（wav）")
    L_audio_folder.place(x=20,y=20)
    E_audio_folder = ttk.Entry(audio_window)
    E_audio_folder.place(x=20,y=40,width=560,height=30)
    B_audio_browse = ttk.Button(audio_window, text="选取", command=select_audio_folder)
    B_audio_browse.place(x=600,y=40,width=80,height=30)
    
    # 音频时长筛选
    L_audio_duration = Label(audio_window, text="目标音频时长（秒，精确到小数点后两位）")
    L_audio_duration.place(x=20,y=80)
    E_audio_duration = ttk.Entry(audio_window)
    E_audio_duration.place(x=20,y=100,width=200,height=30)
    
    B_audio_filter = ttk.Button(audio_window, text="开始筛选", command=audio_main)
    B_audio_filter.place(x=240,y=80,width=90,height=50)
    
    # 当前工程信息显示
    if current_project:
        project_info = current_project["info"]
        L_project = Label(audio_window, text=f"当前工程: {project_info['Name']} ({project_info['Level']})", fg="blue")
        L_project.place(x=20, y=140)

    # 音频列表
    T_audio = ttk.Treeview(audio_window)
    T_audio.place(x=20,y=170,width=660,height=250)
    
    # 按钮区域
    B_add_audio_to_project = ttk.Button(audio_window, text="添加到工程", command=add_audio_to_project)
    B_add_audio_to_project.place(x=20,y=430,width=120,height=40)
    
    B_play_audio = ttk.Button(audio_window, text="打开音频播放", command=play_audio)
    B_play_audio.place(x=150,y=430,width=120,height=40)
    
    B_open_project_folder = ttk.Button(audio_window, text="打开工程文件夹", command=open_project_folder)
    B_open_project_folder.place(x=280,y=430,width=120,height=40)

    # 状态栏
    BL_audio = Label(audio_window, bg="white", anchor="w")
    BL_audio.place(x=0,y=480,width=700,height=20)

    # 配置表格列
    column = ["1", "2", "3"]
    T_audio.config(columns=column, show='headings')
    T_audio.heading("1", text="文件路径")
    T_audio.heading("2", text="音频时长（秒）")
    T_audio.heading("3", text="匹配度")
    T_audio.column("1", width=400)
    T_audio.column("2", width=100)
    T_audio.column("3", width=100)

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
    
    for i, audio_file in enumerate(audio_files):
        audio_path = os.path.join(audio_folder, audio_file)
        duration = get_audio_duration(audio_path)
        
        if duration is not None:
            audio_obj = AudioFile(audio_file, duration)
            audioObjectsList.append(audio_obj)
            BL_audio.config(text=f"{i+1}/{len(audio_files)}\t分析完成 {audio_file}")
            audio_window.update()
    
    # 计算匹配度
    BL_audio.config(text=f"正在对 {len(audioObjectsList)} 个音频文件进行匹配...")
    audio_window.update()
    
    for audio_obj in audioObjectsList:
        # 匹配度计算：时长越接近，匹配度越高
        time_diff = abs(target_duration - audio_obj.duration)
        audio_obj.sortingScore = max(0, 10 - time_diff * 2)  # 每差1秒扣2分
    
    # 进行排序
    audioSortedList = sorted(audioObjectsList, key=audioSortingCallBack, reverse=True)[:10]
    
    # 输出到T_audio
    for child in T_audio.get_children():
        T_audio.delete(child)
    
    if len(audioSortedList) == 0:
        BL_audio.config(text="匹配完成。未找到任何匹配项目。")
    elif audioSortedList[0].sortingScore <= 0:
        BL_audio.config(text="匹配完成。未找到任何匹配项目。")
    else:
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

def add_audio_to_project():
    """添加选中的音频到工程"""
    global current_project
    
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
    # 关闭其他窗口
    if 'audio_window' in globals() and audio_window is not None and audio_window.winfo_exists():
        audio_window.destroy()
    
    search_window = Toplevel(top)
    search_window.title("谱面搜索")
    search_window.geometry("700x500")
    search_window.resizable(0, 0)
    
    # 全局变量引用
    global E1, E2, E3, E4, E5, T1, BL1
    
    # 谱面文件夹选择
    L1 = Label(search_window, text="谱面文件夹（TextAsset）")
    L1.place(x=20,y=20)
    E1 = ttk.Entry(search_window)
    E1.place(x=20,y=40,width=560,height=30)
    B1 = ttk.Button(search_window, text="选取", command=selectPath)
    B1.place(x=600,y=40,width=80,height=30)
    
    # 设置初始文件夹路径
    E1.insert(0, fileDir)

    # 筛选条件
    L2 = Label(search_window, text="关键词(填写EZ.HD.IN.AT等)")
    L2.place(x=20,y=80)
    E2 = ttk.Entry(search_window)
    E2.place(x=20,y=100,width=100,height=30)

    L3 = Label(search_window, text="物量")
    L3.place(x=140,y=80)
    E3 = ttk.Entry(search_window)
    E3.place(x=140,y=100,width=100,height=30)

    L4 = Label(search_window, text="BPM")
    L4.place(x=260,y=80)
    E4 = ttk.Entry(search_window)
    E4.place(x=260,y=100,width=100,height=30)

    L5 = Label(search_window, text="音频长度")
    L5.place(x=380,y=80)
    E5 = ttk.Entry(search_window)
    E5.place(x=380,y=100,width=100,height=30)

    B2 = ttk.Button(search_window, text="开始筛选", command=main)
    B2.place(x=500,y=80,width=90,height=50)
    
    # 当前工程信息显示
    if current_project:
        project_info = current_project["info"]
        L_project = Label(search_window, text=f"当前工程: {project_info['Name']} ({project_info['Level']})", fg="blue")
        L_project.place(x=20, y=140)

    # 谱面列表
    T1 = ttk.Treeview(search_window)
    T1.place(x=20,y=170,width=660,height=250)
    
    # 按钮区域
    B_add_to_project = ttk.Button(search_window, text="添加到工程", command=add_chart_to_project)
    B_add_to_project.place(x=20,y=430,width=120,height=40)
    
    B_open_folder = ttk.Button(search_window, text="打开工程文件夹", command=open_project_folder)
    B_open_folder.place(x=150,y=430,width=120,height=40)

    # 状态栏
    BL1 = Label(search_window, bg="white", anchor="w")
    BL1.place(x=0,y=480,width=700,height=20)

    # 配置表格列
    column = ["1", "2", "3", "4", "5"]
    T1.config(columns=column, show='headings')
    T1.heading("1", text="文件路径")
    T1.heading("2", text="物量")
    T1.heading("3", text="BPM")
    T1.heading("4", text="谱面时长（秒）")
    T1.heading("5", text="匹配度")
    T1.column("1", width=200)
    T1.column("2", width=1)
    T1.column("3", width=1)
    T1.column("4", width=1)
    T1.column("5", width=1)
    
    # 关闭主窗口
    top.withdraw()

if __name__ == '__main__':
    # 加载配置文件
    load_config()
    
    # 创建主窗口（隐藏）
    top = Tk()
    top.withdraw()  # 立即隐藏主窗口
    top.title("ChartAnalyzer")
    
    # 检查是否有现有工程，如果没有则强制创建
    if not check_existing_project():
        top.after(100, create_project_first)  # 延迟100ms后弹出创建窗口
    else:
        top.after(100, open_search_window)  # 直接打开搜索窗口
    
    mainloop()
