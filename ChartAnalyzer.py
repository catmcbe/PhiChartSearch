import json
import os
import random
import string
import shutil
import subprocess
import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk
import wave
import contextlib
import sv_ttk
import zipfile

# 配置文件路径
CONFIG_FILE = "chart_analyzer_config.json"
# 程序文件夹配置
program_folder = ""
# 当前打开的窗口
current_windows = {
    'projects': {},  # 工程窗口
    'charts': {},    # 谱面搜索窗口
    'audio': {}      # 音频搜索窗口
}

def load_config():
    """加载配置文件"""
    global program_folder
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'program_folder' in config and config['program_folder']:
                    program_folder = config['program_folder']
                return True
    except (json.JSONDecodeError, IOError) as e:
        print(f"加载配置文件失败: {e}")
    return False

def save_config():
    """保存配置文件"""
    try:
        config = {'program_folder': program_folder}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"保存配置文件失败: {e}")

def generate_random_path():
    """生成8位随机数字作为Path"""
    return ''.join(random.choices(string.digits, k=8))

def create_info_txt(project_folder, project_name):
    """创建info.txt文件"""
    path_value = generate_random_path()
    info_content = f"""#
Name: {project_name}
Path: {path_value}
Chart: {path_value}.json
Level: 
Composer: PhiChartSearch
Charter: PhiChartSearch
"""
    info_path = os.path.join(project_folder, "info.txt")
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(info_content)
    return path_value

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

def create_chart_art(project_folder, project_name, project_level, path_value, font_path=None):
    """创建曲绘图片"""
    try:
        # 图片尺寸 (16:9)
        width = 1920
        height = 1080
        
        # 创建白色背景图片
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # 选择字体
        if font_path and os.path.exists(font_path):
            try:
                title_font = ImageFont.truetype(font_path, 160)
                level_font = ImageFont.truetype(font_path, 80)
            except:
                font_path = "Source Han Sans & Saira Hybrid-Regular #2934.ttf"
        
        # 默认字体路径
        if not font_path or not os.path.exists(font_path):
            font_path = "Source Han Sans & Saira Hybrid-Regular #2934.ttf"
        
        try:
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

def scan_projects():
    """扫描程序文件夹中的所有工程"""
    projects = []
    if not program_folder or not os.path.exists(program_folder):
        return projects
    
    for item in os.listdir(program_folder):
        item_path = os.path.join(program_folder, item)
        if os.path.isdir(item_path):
            info_path = os.path.join(item_path, "info.txt")
            if os.path.exists(info_path):
                project_info = read_info_txt(item_path)
                if project_info:
                    projects.append({
                        'name': item,
                        'folder': item_path,
                        'info': project_info
                    })
    return projects

def create_project():
    """创建新工程"""
    create_window = Toplevel(top)
    create_window.title("创建新工程")
    create_window.geometry("450x400")
    create_window.resizable(0, 0)
    
    sv_ttk.set_theme("light")
    
    main_frame = ttk.Frame(create_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    title_label = ttk.Label(main_frame, text="创建新的谱面工程")
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # 工程名称（也是谱面名称）
    L_name = ttk.Label(main_frame, text="工程名称/谱面名称（必填）")
    L_name.grid(row=1, column=0, sticky=W, pady=5)
    E_name = ttk.Entry(main_frame)
    E_name.grid(row=1, column=1, sticky=(W, E), pady=5, padx=(10, 0))
    
    # 难度
    L_level = ttk.Label(main_frame, text="难度（必填）")
    L_level.grid(row=2, column=0, sticky=W, pady=5)
    E_level = ttk.Entry(main_frame)
    E_level.grid(row=2, column=1, sticky=(W, E), pady=5, padx=(10, 0))
    
    # Composer
    L_composer = ttk.Label(main_frame, text="Composer")
    L_composer.grid(row=3, column=0, sticky=W, pady=5)
    E_composer = ttk.Entry(main_frame)
    E_composer.grid(row=3, column=1, sticky=(W, E), pady=5, padx=(10, 0))
    E_composer.insert(0, "PhiChartSearch")
    
    # Charter
    L_charter = ttk.Label(main_frame, text="Charter")
    L_charter.grid(row=4, column=0, sticky=W, pady=5)
    E_charter = ttk.Entry(main_frame)
    E_charter.grid(row=4, column=1, sticky=(W, E), pady=5, padx=(10, 0))
    E_charter.insert(0, "PhiChartSearch")
    
    # 是否自创建曲绘
    var_create_art = BooleanVar()
    CB_create_art = ttk.Checkbutton(main_frame, text="是否自创建曲绘", variable=var_create_art)
    CB_create_art.grid(row=5, column=0, columnspan=2, sticky=W, pady=10)
    
    # 字体选择
    L_font = ttk.Label(main_frame, text="曲绘字体（可选）")
    L_font.grid(row=6, column=0, sticky=W, pady=5)
    
    font_frame = ttk.Frame(main_frame)
    font_frame.grid(row=6, column=1, sticky=(W, E), pady=5, padx=(10, 0))
    
    E_font = ttk.Entry(font_frame)
    E_font.pack(side=LEFT, fill=X, expand=True)
    E_font.insert(0, "Source Han Sans & Saira Hybrid-Regular #2934.ttf")
    
    B_browse_font = ttk.Button(font_frame, text="浏览", command=lambda: browse_font(E_font))
    B_browse_font.pack(side=RIGHT, padx=(5, 0))
    
    # 按钮
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=7, column=0, columnspan=2, pady=20)
    
    def create_project_action():
        project_name = E_name.get().strip()
        if not project_name:
            messagebox.showerror("错误", "请填写工程名称！")
            return
        
        level = E_level.get().strip()
        if not level:
            messagebox.showerror("错误", "请填写难度！")
            return
        
        composer = E_composer.get().strip()
        charter = E_charter.get().strip()
        
        # 创建工程文件夹
        project_folder = os.path.join(program_folder, project_name)
        if os.path.exists(project_folder):
            messagebox.showerror("错误", "工程文件夹已存在！")
            return
        
        try:
            os.makedirs(project_folder)
        except:
            messagebox.showerror("错误", "无法创建工程文件夹！")
            return
        
        # 创建info.txt
        path_value = create_info_txt(project_folder, project_name)
        
        # 更新工程信息
        project_info = read_info_txt(project_folder)
        project_info['Level'] = level
        project_info['Composer'] = composer
        project_info['Charter'] = charter
        update_info_txt(project_folder, project_info)
        
        # 如果勾选了自创建曲绘，则生成图片
        if var_create_art.get():
            font_path = E_font.get().strip() if E_font.get().strip() else None
            if create_chart_art(project_folder, project_name, level, path_value, font_path):
                messagebox.showinfo("成功", "曲绘图片创建成功！")
            else:
                messagebox.showwarning("警告", "曲绘图片创建失败，但工程已创建。")
        
        messagebox.showinfo("成功", "工程创建成功！")
        create_window.destroy()
        refresh_project_list()
        
        # 自动打开新创建的工程
        open_project(project_name)
    
    B_create = ttk.Button(button_frame, text="创建工程", command=create_project_action, style="Accent.TButton")
    B_create.pack(side=RIGHT, padx=5)
    
    main_frame.columnconfigure(1, weight=1)

def browse_font(entry_widget):
    """浏览选择字体文件"""
    font_path = filedialog.askopenfilename(
        title="选择字体文件",
        filetypes=[
            ("字体文件", "*.ttf"),
            ("字体文件", "*.otf"),
            ("字体文件", "*.ttc"),
            ("所有文件", "*.*")
        ]
    )
    if font_path:
        entry_widget.delete(0, END)
        entry_widget.insert(0, font_path)

def open_project(project_name):
    """打开工程管理页面"""
    project_folder = os.path.join(program_folder, project_name)
    project_info = read_info_txt(project_folder)
    
    if not project_info:
        messagebox.showerror("错误", "无法读取工程信息！")
        return
    
    open_project_window(project_name, project_folder, project_info)

def open_project_window(project_name, project_folder, project_info):
    """打开工程管理窗口"""
    # 如果该工程已经打开，则聚焦到该窗口
    if project_name in current_windows['projects'] and current_windows['projects'][project_name].winfo_exists():
        current_windows['projects'][project_name].lift()
        current_windows['projects'][project_name].focus_force()
        return
    
    project_window = Toplevel(top)
    project_window.title(f"工程管理 - {project_name}")
    project_window.geometry("900x750")
    project_window.resizable(0, 0)
    
    # 设置窗口为模态窗口，防止主界面被操作
    project_window.transient(top)
    project_window.grab_set()
    
    # 记录窗口
    current_windows['projects'][project_name] = project_window
    
    # 窗口关闭时清理记录
    def on_closing():
        if project_name in current_windows['projects']:
            del current_windows['projects'][project_name]
        project_window.destroy()
    
    project_window.protocol("WM_DELETE_WINDOW", on_closing)
    
    sv_ttk.set_theme("light")
    
    main_frame = ttk.Frame(project_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    # 标题
    title_label = ttk.Label(main_frame, text=f"工程管理 - {project_name}")
    title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
    
    # 文件管理区域
    files_frame = ttk.LabelFrame(main_frame, text="文件管理", padding="10")
    files_frame.grid(row=1, column=0, columnspan=4, sticky=(W, E, N, S), pady=10)
    
    # 定义文件类型
    file_types = [
        ("信息", "info.txt", "info"),
        ("谱面", ".json", "chart"),
        ("音频", ".wav", "audio"),
        ("曲绘", ".png", "art")
    ]
    
    file_widgets = {}
    
    for i, (display_name, extension, file_type) in enumerate(file_types):
        # 文件类型标签
        type_label = ttk.Label(files_frame, text=display_name)
        type_label.grid(row=i*2, column=0, sticky=W, pady=5, padx=(0, 10))
        
        # 文件名显示
        if file_type == "info":
            file_path = os.path.join(project_folder, "info.txt")
            file_name = "info.txt"
        elif file_type == "chart":
            chart_file = project_info.get("Chart", "")
            # 检查文件是否实际存在
            if chart_file and os.path.exists(os.path.join(project_folder, chart_file)):
                file_path = os.path.join(project_folder, chart_file)
                file_name = chart_file
            else:
                file_path = ""
                file_name = "未设置"
        elif file_type == "audio":
            # 查找音频文件
            audio_file = None
            for f in os.listdir(project_folder) if os.path.exists(project_folder) else []:
                if f.lower().endswith('.wav'):
                    audio_file = f
                    break
            file_path = os.path.join(project_folder, audio_file) if audio_file else ""
            file_name = audio_file if audio_file else "未设置"
        else:  # art
            art_file = f"{project_info.get('Path', '')}.png"
            file_path = os.path.join(project_folder, art_file) if project_info.get('Path') else ""
            file_name = art_file if project_info.get('Path') and os.path.exists(file_path) else "未设置"
        
        status_text = file_name
        status_label = ttk.Label(files_frame, text=status_text)
        status_label.grid(row=i*2, column=1, sticky=W, pady=5, padx=(0, 20))
        
        # 曲绘预览
        if file_type == "art":
            preview_frame = ttk.Frame(files_frame)
            preview_frame.grid(row=i*2+1, column=0, columnspan=2, pady=5)
            
            if file_path and os.path.exists(file_path):
                try:
                    # 加载并缩放图片
                    image = Image.open(file_path)
                    image.thumbnail((200, 112), Image.Resampling.LANCZOS)  # 保持16:9比例
                    photo = ImageTk.PhotoImage(image)
                    
                    preview_label = ttk.Label(preview_frame, image=photo)
                    preview_label.image = photo  # 保持引用
                    preview_label.pack()
                except:
                    preview_label = ttk.Label(preview_frame, text="预览加载失败")
                    preview_label.pack()
            else:
                preview_label = ttk.Label(preview_frame, text="无曲绘预览")
                preview_label.pack()
        
        # 按钮框架
        button_frame = ttk.Frame(files_frame)
        button_frame.grid(row=i*2, column=2, sticky=E, pady=5)
        
        # 修改按钮
        def make_modify_func(ft, pf, pi, pn):
            return lambda: modify_file(ft, pf, pi, pn, project_window)
        
        B_modify = ttk.Button(button_frame, text="修改", command=make_modify_func(file_type, project_folder, project_info, project_name))
        B_modify.pack(side=LEFT, padx=(0, 5))
        
        # 删除按钮
        def make_delete_func(ft, pf, pi, pn):
            return lambda: delete_file(ft, pf, pi, pn, project_window)
        
        B_delete = ttk.Button(button_frame, text="删除", command=make_delete_func(file_type, project_folder, project_info, project_name))
        B_delete.pack(side=LEFT)
        
        file_widgets[file_type] = {
            'status_label': status_label,
            'file_path': file_path,
            'file_name': file_name
        }
    
    # 按钮区域
    button_frame2 = ttk.Frame(main_frame)
    button_frame2.grid(row=2, column=0, columnspan=4, pady=20)
    
    def open_project_folder():
        if os.name == 'nt':  # Windows
            os.startfile(project_folder)
        elif os.name == 'posix':  # macOS and Linux
            subprocess.run(['open', project_folder])
    
    B_open_folder = ttk.Button(button_frame2, text="打开工程文件夹", command=open_project_folder)
    B_open_folder.pack(side=LEFT, padx=(0, 10))
    
    B_pack = ttk.Button(button_frame2, text="一键打包zip", command=lambda: pack_project(project_name, project_folder), style="Accent.TButton")
    B_pack.pack(side=LEFT)
    
    # 配置网格权重
    main_frame.columnconfigure(1, weight=1)

def modify_file(file_type, project_folder, project_info, project_name, parent_window):
    """修改文件"""
    if file_type == "info":
        modify_info(project_folder, project_info, project_name, parent_window)
    elif file_type == "chart":
        open_chart_search_window(project_folder, project_info, project_name, parent_window)
    elif file_type == "audio":
        open_audio_search_window(project_folder, project_info, project_name, parent_window)
    elif file_type == "art":
        modify_art(project_folder, project_info, project_name, parent_window)

def modify_info(project_folder, project_info, project_name, parent_window):
    """修改信息文件"""
    info_window = Toplevel(parent_window)
    info_window.title("修改工程信息")
    info_window.geometry("400x300")
    info_window.resizable(0, 0)
    
    # 设置窗口为模态窗口，防止父窗口被操作
    info_window.transient(parent_window)
    info_window.grab_set()
    
    sv_ttk.set_theme("light")
    
    main_frame = ttk.Frame(info_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    title_label = ttk.Label(main_frame, text="修改工程信息")
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    fields = [
        ("难度", "Level"),
        ("Composer", "Composer"),
        ("Charter", "Charter")
    ]
    
    entries = {}
    for i, (label_text, field_name) in enumerate(fields):
        label = ttk.Label(main_frame, text=label_text)
        label.grid(row=1+i, column=0, sticky=W, pady=5)
        
        entry = ttk.Entry(main_frame)
        entry.grid(row=1+i, column=1, sticky=(W, E), pady=5, padx=(10, 0))
        entry.insert(0, project_info.get(field_name, ""))
        entries[field_name] = entry
    
    def save_info():
        for field_name, entry in entries.items():
            project_info[field_name] = entry.get().strip()
        
        update_info_txt(project_folder, project_info)
        messagebox.showinfo("成功", "工程信息已更新！")
        info_window.destroy()
        # 刷新父窗口
        parent_window.destroy()
        open_project_window(project_name, project_folder, project_info)
    
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=4, column=0, columnspan=2, pady=20)
    
    B_save = ttk.Button(button_frame, text="保存", command=save_info, style="Accent.TButton")
    B_save.pack(side=RIGHT, padx=5)
    
    main_frame.columnconfigure(1, weight=1)

def open_chart_search_window(project_folder, project_info, project_name, parent_window):
    """打开谱面搜索窗口"""
    search_window = Toplevel(parent_window)
    search_window.title("谱面搜索")
    search_window.geometry("750x650")
    search_window.resizable(0, 0)
    
    # 设置窗口为模态窗口，防止父窗口被操作
    search_window.transient(parent_window)
    search_window.grab_set()
    
    sv_ttk.set_theme("light")
    
    main_frame = ttk.Frame(search_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    title_label = ttk.Label(main_frame, text="谱面搜索")
    title_label.grid(row=0, column=0, columnspan=5, pady=(0, 15))
    
    # 谱面文件夹选择
    L1 = ttk.Label(main_frame, text="谱面文件夹（TextAsset）")
    L1.grid(row=1, column=0, sticky=W, pady=5)
    
    folder_frame = ttk.Frame(main_frame)
    folder_frame.grid(row=2, column=0, columnspan=5, sticky=(W, E), pady=5)
    
    E1 = ttk.Entry(folder_frame)
    E1.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
    
    def selectPath():
        path = filedialog.askdirectory(title="打开铺面文件夹", initialdir=E1.get())
        if path:
            E1.delete(0, END)
            E1.insert(0, path)
    
    B1 = ttk.Button(folder_frame, text="选取", command=selectPath)
    B1.pack(side=RIGHT)
    
    # 筛选条件
    filter_label = ttk.Label(main_frame, text="筛选条件")
    filter_label.grid(row=3, column=0, columnspan=5, sticky=W, pady=(15, 10))

    filter_frame = ttk.Frame(main_frame)
    filter_frame.grid(row=4, column=0, columnspan=5, sticky=(W, E), pady=5)
    
    L2 = ttk.Label(filter_frame, text="关键词")
    L2.grid(row=0, column=0, sticky=W, padx=(0, 5))
    E2 = ttk.Entry(filter_frame, width=15)
    E2.grid(row=0, column=1, sticky=W, padx=(0, 15))

    L3 = ttk.Label(filter_frame, text="物量")
    L3.grid(row=0, column=2, sticky=W, padx=(0, 5))
    E3 = ttk.Entry(filter_frame, width=15)
    E3.grid(row=0, column=3, sticky=W, padx=(0, 15))

    L4 = ttk.Label(filter_frame, text="BPM")
    L4.grid(row=1, column=0, sticky=W, padx=(0, 5), pady=(10, 0))
    E4 = ttk.Entry(filter_frame, width=15)
    E4.grid(row=1, column=1, sticky=W, padx=(0, 15), pady=(10, 0))

    L5 = ttk.Label(filter_frame, text="音频长度")
    L5.grid(row=1, column=2, sticky=W, padx=(0, 5), pady=(10, 0))
    E5 = ttk.Entry(filter_frame, width=15)
    E5.grid(row=1, column=3, sticky=W, padx=(0, 15), pady=(10, 0))

    B2 = ttk.Button(filter_frame, text="开始筛选", command=lambda: search_charts(E1, E2, E3, E4, E5, T1, BL1, search_window, project_folder, project_info, project_name, parent_window), style="Accent.TButton")
    B2.grid(row=0, column=4, rowspan=2, padx=(15, 0))
    
    # 谱面列表
    list_frame = ttk.LabelFrame(main_frame, text="搜索结果", padding="10")
    list_frame.grid(row=5, column=0, columnspan=5, sticky=(W, E, N, S), pady=10)
    
    # 设置LabelFrame的字体样式
    label_frame_style = ttk.Style()
    label_frame_style.configure("TLabelframe.Label")
    
    # 创建进度条
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(list_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill=X, pady=(0, 5))
    
    # 创建表格样式
    tree_style = ttk.Style()
    tree_style.configure("Treeview")
    tree_style.configure("Treeview.Heading")
    
    T1 = ttk.Treeview(list_frame, height=18)
    T1.pack(fill=BOTH, expand=True)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=T1.yview)
    T1.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    # 按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=6, column=0, columnspan=5, pady=10)
    
    def add_chart():
        selection = T1.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要添加的谱面！")
            return
        
        item = T1.item(selection[0])
        chart_filename = item['values'][0]
        
        try:
            # 复制谱面文件到工程文件夹
            source_path = os.path.join(E1.get(), chart_filename)
            target_filename = f"{project_info['Path']}.json"
            target_path = os.path.join(project_folder, target_filename)
            
            shutil.copy2(source_path, target_path)
            
            # 更新工程信息
            project_info['Chart'] = target_filename
            update_info_txt(project_folder, project_info)
            
            messagebox.showinfo("成功", f"谱面已添加到工程 '{project_name}'！")
            search_window.destroy()
            parent_window.destroy()
            open_project_window(project_name, project_folder, project_info)
            
        except Exception as e:
            messagebox.showerror("错误", f"添加谱面失败：{str(e)}")
    
    B_add = ttk.Button(button_frame, text="添加到工程", command=add_chart, style="Accent.TButton")
    B_add.pack(side=LEFT, padx=(0, 10))
    
    # 状态栏
    BL1 = ttk.Label(main_frame, anchor="w")
    BL1.grid(row=7, column=0, columnspan=5, sticky=(W, E), pady=(10, 0))

    # 配置表格列
    T1.config(columns=("1", "2", "3", "4", "5"), show='headings')
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
    
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(5, weight=1)

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

def analyseJsonChart(chartFile: str):
    """分析铺面文件，生成 Chart 对象"""
    try:
        with open(chartFile, 'r', encoding="utf-8") as f:
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
    except Exception as e:
        print(f"分析文件 {chartFile} 时出错: {e}")
        return None

def search_charts(E1, E2, E3, E4, E5, T1, BL1, search_window, project_folder, project_info, project_name, parent_window):
    """搜索谱面"""
    global progress_var, progress_bar
    
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

    # 解析筛选条件
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

    try:
        fileList = os.listdir(fileDir)
        fileCount = len(fileList)
        chartObjectsList = []
        
        # 初始化进度条
        if 'progress_var' in globals() and progress_var is not None:
            progress_var.set(0)
            if 'progress_bar' in globals() and progress_bar is not None:
                progress_bar.update()
        
        BL1.config(text="正在分析谱面文件...")
        search_window.update()
        
        # 分析谱面文件
        for i, file in enumerate(fileList):
            # 更新进度条（分析阶段占50%）
            progress = (i / fileCount) * 50
            if 'progress_var' in globals() and progress_var is not None:
                progress_var.set(progress)
                if 'progress_bar' in globals() and progress_bar is not None:
                    progress_bar.update()
            
            # 更新UI防止未响应
            search_window.update()
            
            # 确认是否含有关键词
            skip = False
            for keyword in keyWords:
                if keyword not in file:
                    skip = True
            if skip:
                continue

            # 尝试分析铺面文件
            try:
                chart = analyseJsonChart(os.path.join(fileDir, file))
                if chart:
                    chartObjectsList.append(chart)
                    BL1.config(text=f"{i+1}/{fileCount}\t分析完成{chart}")
                    search_window.update()
            except KeyError as e:
                BL1.config(text=f"{i+1}/{fileCount}\t分析'{file}'时遇到 KeyError:" + str(e))
            except Exception as e:
                BL1.config(text=f"{i+1}/{fileCount}\t分析'{file}'时出错: {str(e)}")

        if not chartObjectsList:
            BL1.config(text="未找到匹配的谱面文件")
            return

        # 计算匹配度
        BL1.config(text=f"正在对 {len(chartObjectsList)} 个铺面文件进行匹配...")
        search_window.update()
        
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
            search_window.update()
        
        # 完成进度条
        if 'progress_var' in globals() and progress_var is not None:
            progress_var.set(100)
            if 'progress_bar' in globals() and progress_bar is not None:
                progress_bar.update()
        
        # 进行排序
        sortedList = sorted(chartObjectsList, key=lambda x: x.sortingScore, reverse=True)[:10]

        # 清空现有结果
        for child in T1.get_children():
            T1.delete(child)
        
        # 输出结果
        if len(sortedList) == 0 or sortedList[0].sortingScore <= 0:
            BL1.config(text="匹配完成。未找到任何匹配项目。")
        else:
            BL1.config(text=f"匹配完成，最佳匹配项为：{sortedList[0].fileName}")
            for chart in sortedList:
                if chart.sortingScore <= 0:
                    continue
                T1.insert("", "end", values=(
                    chart.fileName,
                    chart.objectNumber,
                    chart.bpm,
                    chart.audioLength,
                    f"{chart.sortingScore / 30:.2%}"
                ))
        
    except Exception as e:
        messagebox.showerror("错误", f"搜索失败：{str(e)}")

def open_audio_search_window(project_folder, project_info, project_name, parent_window):
    """打开音频搜索窗口"""
    audio_window = Toplevel(parent_window)
    audio_window.title("音频搜索")
    audio_window.geometry("750x750")
    audio_window.resizable(0, 0)
    
    # 设置窗口为模态窗口，防止父窗口被操作
    audio_window.transient(parent_window)
    audio_window.grab_set()
    
    sv_ttk.set_theme("light")
    
    main_frame = ttk.Frame(audio_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    title_label = ttk.Label(main_frame, text="音频筛选")
    title_label.grid(row=0, column=0, columnspan=4, pady=(0, 15))
    
    # 音频文件夹选择
    L_audio_folder = ttk.Label(main_frame, text="音频文件夹（wav）")
    L_audio_folder.grid(row=1, column=0, sticky=W, pady=5)
    
    folder_frame = ttk.Frame(main_frame)
    folder_frame.grid(row=2, column=0, columnspan=4, sticky=(W, E), pady=5)
    
    E_audio_folder = ttk.Entry(folder_frame)
    E_audio_folder.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
    
    def select_audio_folder():
        folder_path = filedialog.askdirectory(title="选择音频文件夹")
        if folder_path:
            E_audio_folder.delete(0, END)
            E_audio_folder.insert(0, folder_path)
    
    B_audio_browse = ttk.Button(folder_frame, text="选取", command=select_audio_folder)
    B_audio_browse.pack(side=RIGHT)
    
    # 音频时长筛选
    filter_frame = ttk.LabelFrame(main_frame, text="筛选条件", padding="10")
    filter_frame.grid(row=3, column=0, columnspan=4, sticky=(W, E), pady=15)
    
    L_audio_duration = ttk.Label(filter_frame, text="目标音频时长（秒，精确到小数点后两位）")
    L_audio_duration.grid(row=0, column=0, sticky=W, pady=5)
    
    duration_frame = ttk.Frame(filter_frame)
    duration_frame.grid(row=1, column=0, sticky=(W, E), pady=5)
    
    E_audio_duration = ttk.Entry(duration_frame, width=20)
    E_audio_duration.pack(side=LEFT)
    
    def search_audio():
        global progress_var_audio, progress_bar_audio
        
        folder_path = E_audio_folder.get()
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("错误", "请选择有效的音频文件夹！")
            return
        
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
        audio_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.wav')]
        audioObjectsList = []
        
        # 初始化进度条
        if 'progress_var_audio' in globals() and progress_var_audio is not None:
            progress_var_audio.set(0)
            if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
                progress_bar_audio.update()
        
        # 分析音频文件
        for i, audio_file in enumerate(audio_files):
            # 更新进度条（分析阶段占50%）
            progress = (i / len(audio_files)) * 50
            if 'progress_var_audio' in globals() and progress_var_audio is not None:
                progress_var_audio.set(progress)
                if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
                    progress_bar_audio.update()
            
            # 更新UI防止未响应
            audio_window.update()
            
            audio_path = os.path.join(folder_path, audio_file)
            duration = get_audio_duration(audio_path)
            
            if duration is not None:
                # 创建AudioFile对象
                audio_obj = type('AudioFile', (), {
                    'file': audio_file,
                    'fileName': audio_file,
                    'duration': duration,
                    'sortingScore': 0
                })()
                audioObjectsList.append(audio_obj)
                BL_audio.config(text=f"{i+1}/{len(audio_files)}\t分析完成 {audio_file}")
                audio_window.update()
        
        if not audioObjectsList:
            BL_audio.config(text="未找到匹配的音频文件")
            return
        
        # 计算匹配度
        BL_audio.config(text=f"正在对 {len(audioObjectsList)} 个音频文件进行匹配...")
        audio_window.update()
        
        # 重置分数
        for audio_obj in audioObjectsList:
            audio_obj.sortingScore = 0
        
        # 计算匹配度并更新进度
        for i, audio_obj in enumerate(audioObjectsList):
            # 匹配度计算：时长越接近，匹配度越高
            time_diff = abs(target_duration - audio_obj.duration)
            audio_obj.sortingScore = max(0, 10 - time_diff * 2)  # 每差1秒扣2分
            
            # 更新进度条（匹配阶段占50%）
            progress = 50 + (i / len(audioObjectsList)) * 50
            if 'progress_var_audio' in globals() and progress_var_audio is not None:
                progress_var_audio.set(progress)
                if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
                    progress_bar_audio.update()
            
            # 更新UI防止未响应
            audio_window.update()
        
        # 完成进度条
        if 'progress_var_audio' in globals() and progress_var_audio is not None:
            progress_var_audio.set(100)
            if 'progress_bar_audio' in globals() and progress_bar_audio is not None:
                progress_bar_audio.update()
        
        # 进行排序
        audioSortedList = sorted(audioObjectsList, key=lambda x: x.sortingScore, reverse=True)[:10]
        
        # 清空现有结果
        for child in T_audio.get_children():
            T_audio.delete(child)
        
        # 输出结果
        if len(audioSortedList) == 0 or audioSortedList[0].sortingScore <= 0:
            BL_audio.config(text="匹配完成。未找到任何匹配项目。")
        else:
            BL_audio.config(text=f"匹配完成，最佳匹配项为：{audioSortedList[0].fileName}")
            for audio_obj in audioSortedList:
                if audio_obj.sortingScore <= 0:
                    continue
                T_audio.insert("", "end", values=(
                    audio_obj.fileName,
                    audio_obj.duration,
                    f"{audio_obj.sortingScore / 10:.2%}"
                ))
        
    B_audio_filter = ttk.Button(duration_frame, text="开始筛选", command=search_audio, style="Accent.TButton")
    B_audio_filter.pack(side=LEFT, padx=(15, 0))
    
    # 音频列表
    list_frame = ttk.LabelFrame(main_frame, text="搜索结果", padding="10")
    list_frame.grid(row=4, column=0, columnspan=4, sticky=(W, E, N, S), pady=10)
    
    # 设置LabelFrame的字体样式
    label_frame_style = ttk.Style()
    label_frame_style.configure("TLabelframe.Label")
    
    # 创建进度条
    progress_var_audio = tk.DoubleVar()
    progress_bar_audio = ttk.Progressbar(list_frame, variable=progress_var_audio, maximum=100)
    progress_bar_audio.pack(fill=X, pady=(0, 5))
    
    # 创建表格样式
    tree_style = ttk.Style()
    tree_style.configure("Treeview")
    tree_style.configure("Treeview.Heading")
    
    T_audio = ttk.Treeview(list_frame, height=22)
    T_audio.pack(fill=BOTH, expand=True)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=T_audio.yview)
    T_audio.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    # 按钮区域
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=5, column=0, columnspan=4, pady=10)
    
    def play_audio():
        selection = T_audio.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要试听的音频！")
            return
        
        item = T_audio.item(selection[0])
        audio_filename = item['values'][0]
        audio_path = os.path.join(E_audio_folder.get(), audio_filename)
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(audio_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', audio_path])
        except Exception as e:
            messagebox.showerror("错误", f"无法播放音频：{str(e)}")
    
    def add_audio():
        selection = T_audio.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要添加的音频！")
            return
        
        item = T_audio.item(selection[0])
        audio_filename = item['values'][0]
        
        try:
            # 删除现有音频文件
            for f in os.listdir(project_folder):
                if f.lower().endswith('.wav'):
                    os.remove(os.path.join(project_folder, f))
            
            # 复制新文件
            source_path = os.path.join(E_audio_folder.get(), audio_filename)
            shutil.copy2(source_path, project_folder)
            
            messagebox.showinfo("成功", f"音频已添加到工程 '{project_name}'！")
            audio_window.destroy()
            parent_window.destroy()
            open_project_window(project_name, project_folder, project_info)
            
        except Exception as e:
            messagebox.showerror("错误", f"添加音频失败：{str(e)}")
    
    B_play_audio = ttk.Button(button_frame, text="试听", command=play_audio)
    B_play_audio.pack(side=LEFT, padx=(0, 5))
    
    B_add_audio = ttk.Button(button_frame, text="添加到工程", command=add_audio, style="Accent.TButton")
    B_add_audio.pack(side=LEFT, padx=(0, 10))
    
    # 状态栏
    BL_audio = ttk.Label(main_frame, anchor="w")
    BL_audio.grid(row=6, column=0, columnspan=4, sticky=(W, E), pady=(10, 0))

    # 配置表格列
    T_audio.config(columns=("1", "2", "3"), show='headings')
    T_audio.heading("1", text="文件路径")
    T_audio.heading("2", text="音频时长（秒）")
    T_audio.heading("3", text="匹配度")
    T_audio.column("1", width=400)
    T_audio.column("2", width=100)
    T_audio.column("3", width=100)
    
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(4, weight=1)

def modify_art(project_folder, project_info, project_name, parent_window):
    """修改曲绘文件"""
    art_window = Toplevel(parent_window)
    art_window.title("修改曲绘")
    art_window.geometry("450x350")
    art_window.resizable(0, 0)
    
    # 设置窗口为模态窗口，防止父窗口被操作
    art_window.transient(parent_window)
    art_window.grab_set()
    
    sv_ttk.set_theme("light")
    
    main_frame = ttk.Frame(art_window, padding="20")
    main_frame.pack(fill=BOTH, expand=True)
    
    title_label = ttk.Label(main_frame, text="修改曲绘")
    title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    # 字体选择
    L_font = ttk.Label(main_frame, text="曲绘字体（可选）")
    L_font.grid(row=1, column=0, sticky=W, pady=5)
    
    font_frame = ttk.Frame(main_frame)
    font_frame.grid(row=1, column=1, sticky=(W, E), pady=5, padx=(10, 0))
    
    E_font = ttk.Entry(font_frame)
    E_font.pack(side=LEFT, fill=X, expand=True)
    E_font.insert(0, "Source Han Sans & Saira Hybrid-Regular #2934.ttf")
    
    B_browse_font = ttk.Button(font_frame, text="浏览", command=lambda: browse_font(E_font))
    B_browse_font.pack(side=RIGHT, padx=(5, 0))
    
    # 重新生成曲绘
    def regenerate_art():
        font_path = E_font.get().strip() if E_font.get().strip() else None
        if create_chart_art(project_folder, project_info['Name'], project_info['Level'], project_info['Path'], font_path):
            messagebox.showinfo("成功", "曲绘已重新生成！")
            art_window.destroy()
            parent_window.destroy()
            open_project_window(project_name, project_folder, project_info)
        else:
            messagebox.showerror("错误", "曲绘生成失败！")
    
    B_regenerate = ttk.Button(main_frame, text="重新生成曲绘", command=regenerate_art, style="Accent.TButton")
    B_regenerate.grid(row=2, column=0, columnspan=2, pady=20, sticky=(W, E))
    
    # 选择本地图片替换
    def replace_art():
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("PNG文件", "*.png"), ("JPG文件", "*.jpg"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                target_filename = f"{project_info['Path']}.png"
                target_path = os.path.join(project_folder, target_filename)
                shutil.copy2(file_path, target_path)
                
                messagebox.showinfo("成功", "曲绘已替换！")
                art_window.destroy()
                parent_window.destroy()
                open_project_window(project_name, project_folder, project_info)
            except Exception as e:
                messagebox.showerror("错误", f"替换曲绘失败：{str(e)}")
    
    B_replace = ttk.Button(main_frame, text="选择本地图片替换", command=replace_art)
    B_replace.grid(row=3, column=0, columnspan=2, pady=10, sticky=(W, E))
    
    main_frame.columnconfigure(0, weight=1)

def delete_file(file_type, project_folder, project_info, project_name, parent_window):
    """删除文件"""
    if not messagebox.askyesno("确认", "确定要删除这个文件吗？"):
        return
    
    try:
        if file_type == "info":
            # 不允许删除info.txt
            messagebox.showwarning("警告", "不能删除信息文件！")
            return
        elif file_type == "chart":
            chart_file = project_info.get("Chart", "")
            if chart_file:
                file_path = os.path.join(project_folder, chart_file)
                if os.path.exists(file_path):
                    os.remove(file_path)
                project_info['Chart'] = ""
                update_info_txt(project_folder, project_info)
        elif file_type == "audio":
            for f in os.listdir(project_folder):
                if f.lower().endswith('.wav'):
                    os.remove(os.path.join(project_folder, f))
        elif file_type == "art":
            art_file = f"{project_info.get('Path', '')}.png"
            if project_info.get('Path'):
                file_path = os.path.join(project_folder, art_file)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        messagebox.showinfo("成功", "文件已删除！")
        parent_window.destroy()
        open_project_window(project_name, project_folder, project_info)
    except Exception as e:
        messagebox.showerror("错误", f"删除文件失败：{str(e)}")

def pack_project(project_name, project_folder):
    """一键打包工程为zip"""
    try:
        zip_filename = f"{project_name}.zip"
        zip_path = os.path.join(project_folder, zip_filename)
        
        # 定义要打包的核心文件
        core_files = []
        
        # info.txt
        info_path = os.path.join(project_folder, "info.txt")
        if os.path.exists(info_path):
            core_files.append(("info.txt", info_path))
        
        # 谱面文件
        project_info = read_info_txt(project_folder)
        if project_info and project_info.get("Chart"):
            chart_path = os.path.join(project_folder, project_info["Chart"])
            if os.path.exists(chart_path):
                core_files.append((project_info["Chart"], chart_path))
        
        # 音频文件
        for f in os.listdir(project_folder):
            if f.lower().endswith('.wav'):
                audio_path = os.path.join(project_folder, f)
                core_files.append((f, audio_path))
                break
        
        # 曲绘文件
        if project_info and project_info.get("Path"):
            art_file = f"{project_info['Path']}.png"
            art_path = os.path.join(project_folder, art_file)
            if os.path.exists(art_path):
                core_files.append((art_file, art_path))
        
        if not core_files:
            messagebox.showwarning("警告", "没有找到可打包的文件！")
            return
        
        # 创建zip文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, file_path in core_files:
                zipf.write(file_path, filename)
        
        messagebox.showinfo("成功", f"工程已打包为：{zip_filename}")
        
        # 询问是否打开文件夹
        if messagebox.askyesno("打开文件夹", "是否打开工程文件夹查看打包结果？"):
            if os.name == 'nt':  # Windows
                os.startfile(project_folder)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', project_folder])
                
    except Exception as e:
        messagebox.showerror("错误", f"打包失败：{str(e)}")

def delete_project(project_name):
    """删除工程"""
    if not messagebox.askyesno("确认删除", f"确定要删除工程 '{project_name}' 吗？\n此操作不可恢复！"):
        return
    
    try:
        project_folder = os.path.join(program_folder, project_name)
        shutil.rmtree(project_folder)
        messagebox.showinfo("成功", "工程已删除！")
        refresh_project_list()
    except Exception as e:
        messagebox.showerror("错误", f"删除工程失败：{str(e)}")

def select_program_folder():
    """选择程序文件夹"""
    global program_folder
    folder_path = filedialog.askdirectory(title="选择程序文件夹（所有工程的总存放路径）")
    if folder_path:
        program_folder = folder_path
        E_program_folder.delete(0, END)
        E_program_folder.insert(0, folder_path)
        save_config()
        refresh_project_list()

def refresh_project_list():
    """刷新工程列表"""
    # 清空现有列表
    for item in T_projects.get_children():
        T_projects.delete(item)
    
    # 扫描并显示工程
    projects = scan_projects()
    for project in projects:
        T_projects.insert("", "end", values=(
            project['name'],
            project['info'].get('Name', ''),
            project['info'].get('Level', ''),
            "完整" if all([
                project['info'].get('Chart', ''),
                any(f.lower().endswith('.wav') for f in os.listdir(project['folder']) if os.path.isfile(os.path.join(project['folder'], f))),
                os.path.exists(os.path.join(project['folder'], f"{project['info'].get('Path', '')}.png")) if project['info'].get('Path') else False
            ]) else "不完整"
        ))

def open_project_action():
    """打开选中的工程"""
    selection = T_projects.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要打开的工程！")
        return
    
    item = T_projects.item(selection[0])
    project_name = str(item['values'][0])  # 确保是字符串
    open_project(project_name)

def delete_project_action():
    """删除选中的工程"""
    selection = T_projects.selection()
    if not selection:
        messagebox.showwarning("警告", "请先选择要删除的工程！")
        return
    
    item = T_projects.item(selection[0])
    project_name = item['values'][0]
    delete_project(project_name)

# 创建主界面
top = Tk()
top.title("PhiChartSearch谱面工程管理器")
top.geometry("800x600")
top.resizable(1, 1)

# 应用Sun-Valley-ttk主题
sv_ttk.set_theme("light")

# 设置全局字体样式
style = ttk.Style()
style.configure(".", font=("微软雅黑", 10))
style.configure("TLabel", font=("微软雅黑", 10))
style.configure("TButton", font=("微软雅黑", 10))
style.configure("TEntry", font=("微软雅黑", 10))
style.configure("Treeview", font=("微软雅黑", 10))
style.configure("Treeview.Heading", font=("微软雅黑", 10))
style.configure("TLabelframe.Label", font=("微软雅黑", 10))
style.configure("TCheckbutton", font=("微软雅黑", 10))

# 创建主框架
main_frame = ttk.Frame(top, padding="20")
main_frame.pack(fill=BOTH, expand=True)

# 标题
title_label = ttk.Label(main_frame, text="PhiChartSearch谱面工程管理器")
title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

# 程序文件夹选择
folder_frame = ttk.LabelFrame(main_frame, text="程序文件夹设置", padding="10")
folder_frame.grid(row=1, column=0, columnspan=3, sticky=(W, E), pady=10)

L_program_folder = ttk.Label(folder_frame, text="程序文件夹（所有工程的总存放路径）")
L_program_folder.pack(anchor=W, pady=(0, 5))

program_folder_frame = ttk.Frame(folder_frame)
program_folder_frame.pack(fill=X, pady=(0, 5))

E_program_folder = ttk.Entry(program_folder_frame)
E_program_folder.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

B_browse_folder = ttk.Button(program_folder_frame, text="浏览", command=select_program_folder)
B_browse_folder.pack(side=RIGHT)

# 工程列表
projects_frame = ttk.LabelFrame(main_frame, text="工程列表", padding="10")
projects_frame.grid(row=2, column=0, columnspan=3, sticky=(W, E, N, S), pady=10)
main_frame.columnconfigure(0, weight=1)
main_frame.rowconfigure(2, weight=1)

# 创建表格
T_projects = ttk.Treeview(projects_frame, height=15)
T_projects.pack(fill=BOTH, expand=True)

# 配置表格列
T_projects.config(columns=("name", "chart_name", "level", "status"), show='headings')
T_projects.heading("name", text="工程名")
T_projects.heading("chart_name", text="谱面名称")
T_projects.heading("level", text="难度")
T_projects.heading("status", text="状态")
T_projects.column("name", width=200)
T_projects.column("chart_name", width=200)
T_projects.column("level", width=100)
T_projects.column("status", width=100)

# 按钮区域
button_frame = ttk.Frame(main_frame)
button_frame.grid(row=3, column=0, columnspan=3, pady=20)

B_create = ttk.Button(button_frame, text="创建新工程", command=create_project, style="Accent.TButton")
B_create.pack(side=LEFT, padx=(0, 10))

B_open = ttk.Button(button_frame, text="打开工程", command=open_project_action)
B_open.pack(side=LEFT, padx=(0, 10))

B_delete = ttk.Button(button_frame, text="删除工程", command=delete_project_action)
B_delete.pack(side=LEFT, padx=(0, 10))

B_refresh = ttk.Button(button_frame, text="刷新列表", command=refresh_project_list)
B_refresh.pack(side=LEFT)

# 状态栏
status_label = ttk.Label(main_frame, text="就绪", anchor="w")
status_label.grid(row=4, column=0, columnspan=3, sticky=(W, E), pady=(10, 0))

# 加载配置并初始化
load_config()
if program_folder:
    E_program_folder.insert(0, program_folder)
    refresh_project_list()

if __name__ == '__main__':
    mainloop()
