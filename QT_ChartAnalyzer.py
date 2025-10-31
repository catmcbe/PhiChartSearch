#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import random
import string
import shutil
import subprocess
import wave
import contextlib
import zipfile
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qfluentwidgets import *
from PIL import Image, ImageDraw, ImageFont

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
Composer: Phigros
Charter: Phigros
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

# 移除find_system_font函数，因为我们不再需要系统字体查找功能

def create_chart_art(project_folder, project_name, project_level, path_value, font_path=None):
    """创建曲绘图片"""
    try:
        # 图片尺寸 (16:9)
        width = 1920
        height = 1080
        
        # 创建白色背景图片
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # 初始化字体变量
        title_font = None
        level_font = None
        
        # 选择字体
        if font_path and os.path.exists(font_path):
            # 尝试将输入视为字体文件路径
            try:
                title_font = ImageFont.truetype(font_path, 160)
                level_font = ImageFont.truetype(font_path, 80)
            except:
                # 字体文件加载失败，使用默认字体
                title_font = ImageFont.load_default()
                level_font = ImageFont.load_default()
        else:
            # 没有提供字体或字体文件不存在，使用默认字体
            title_font = ImageFont.load_default()
            level_font = ImageFont.load_default()
        
        # 确保字体有效，如果默认字体不可用则使用基本字体
        try:
            # 测试字体是否可用
            draw.text((0, 0), "Test", font=title_font)
        except:
            # 如果字体不可用，使用基本的位图字体
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.load_config_and_refresh()
        
    def initUI(self):
        self.setWindowTitle('PhiChartSearch谱面工程管理器')
        self.setGeometry(100, 100, 1000, 700)  # 扩大主界面尺寸
        
        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = TitleLabel('PhiChartSearch谱面工程管理器')
        main_layout.addWidget(title_label)
        
        # 程序文件夹设置
        folder_group = CardWidget()
        folder_layout = QVBoxLayout(folder_group)
        folder_layout.setContentsMargins(20, 20, 20, 20)
        
        folder_label = StrongBodyLabel('程序文件夹（所有工程的总存放路径）')
        folder_layout.addWidget(folder_label)
        
        folder_h_layout = QHBoxLayout()
        self.folder_line_edit = LineEdit()
        self.folder_line_edit.setPlaceholderText('请选择程序文件夹')
        folder_h_layout.addWidget(self.folder_line_edit)
        
        self.browse_button = PushButton('浏览')
        self.browse_button.clicked.connect(self.select_program_folder)
        folder_h_layout.addWidget(self.browse_button)
        
        folder_layout.addLayout(folder_h_layout)
        main_layout.addWidget(folder_group)
        
        # 工程列表
        project_group = CardWidget()
        project_layout = QVBoxLayout(project_group)
        project_layout.setContentsMargins(10, 10, 10, 10)
        
        project_label = StrongBodyLabel('工程列表')
        project_layout.addWidget(project_label)
        
        # 创建表格
        self.project_table = TableWidget()
        self.project_table.setBorderRadius(8)
        self.project_table.setBorderVisible(True)
        self.project_table.setColumnCount(4)
        self.project_table.setHorizontalHeaderLabels(['工程名', '谱面名称', '难度', '状态'])
        self.project_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        project_layout.addWidget(self.project_table)
        
        main_layout.addWidget(project_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.create_button = PrimaryPushButton('创建新工程')
        self.create_button.clicked.connect(self.create_project)
        button_layout.addWidget(self.create_button)
        
        self.open_button = PushButton('打开工程')
        self.open_button.clicked.connect(self.open_project_action)
        button_layout.addWidget(self.open_button)
        
        self.delete_button = PushButton('删除工程')
        self.delete_button.clicked.connect(self.delete_project_action)
        button_layout.addWidget(self.delete_button)
        
        self.refresh_button = PushButton('刷新列表')
        self.refresh_button.clicked.connect(self.refresh_project_list)
        button_layout.addWidget(self.refresh_button)
        
        # 添加关于按钮
        self.about_button = PushButton('关于')
        self.about_button.clicked.connect(self.show_about)
        button_layout.addWidget(self.about_button)
        
        main_layout.addLayout(button_layout)
        
        # 状态栏
        self.status_label = BodyLabel("就绪")
        main_layout.addWidget(self.status_label)
        
    def load_config_and_refresh(self):
        """加载配置并刷新工程列表"""
        load_config()
        if program_folder:
            self.folder_line_edit.setText(program_folder)
            self.refresh_project_list()
            
    def select_program_folder(self):
        """选择程序文件夹"""
        global program_folder
        folder_path = QFileDialog.getExistingDirectory(self, "选择程序文件夹（所有工程的总存放路径）")
        if folder_path:
            program_folder = folder_path
            self.folder_line_edit.setText(folder_path)
            save_config()
            self.refresh_project_list()
            
    def refresh_project_list(self):
        """刷新工程列表"""
        # 清空现有列表
        self.project_table.setRowCount(0)
        
        # 扫描并显示工程
        projects = scan_projects()
        for project in projects:
            row = self.project_table.rowCount()
            self.project_table.insertRow(row)
            
            # 添加项目到表格
            self.project_table.setItem(row, 0, QTableWidgetItem(project['name']))
            self.project_table.setItem(row, 1, QTableWidgetItem(project['info'].get('Name', '')))
            self.project_table.setItem(row, 2, QTableWidgetItem(project['info'].get('Level', '')))
            
            # 检查工程完整性
            is_complete = all([
                project['info'].get('Chart', ''),
                any(f.lower().endswith('.wav') for f in os.listdir(project['folder']) if os.path.isfile(os.path.join(project['folder'], f))),
                os.path.exists(os.path.join(project['folder'], f"{project['info'].get('Path', '')}.png")) if project['info'].get('Path') else False
            ])
            status = "完整" if is_complete else "不完整"
            self.project_table.setItem(row, 3, QTableWidgetItem(status))
            
    def create_project(self):
        """创建新工程"""
        dialog = CreateProjectDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 获取用户输入的数据
            project_name = dialog.name_edit.text().strip()
            level = dialog.level_edit.text().strip()
            composer = dialog.composer_edit.text().strip()
            charter = dialog.charter_edit.text().strip()
            create_art = dialog.create_art_check.isChecked()
            font_path = dialog.font_edit.text().strip()
            use_local_art = dialog.use_local_art_check.isChecked()
            local_art_path = dialog.local_art_edit.text().strip()
            
            # 验证必填字段
            if not project_name:
                MessageBox("错误", "请填写工程名称！", self).exec_()
                return
                
            if not level:
                MessageBox("错误", "请填写难度！", self).exec_()
                return
            
            # 检查工程文件夹是否已存在
            project_folder = os.path.join(program_folder, project_name)
            if os.path.exists(project_folder):
                MessageBox("错误", "工程文件夹已存在！", self).exec_()
                return
            
            try:
                # 创建工程文件夹
                os.makedirs(project_folder)
                
                # 创建info.txt
                path_value = create_info_txt(project_folder, project_name)
                
                # 更新工程信息
                project_info = read_info_txt(project_folder)
                project_info['Level'] = level
                project_info['Composer'] = composer
                project_info['Charter'] = charter
                update_info_txt(project_folder, project_info)
                
                # 处理曲绘文件
                art_created = False
                if use_local_art and local_art_path and os.path.exists(local_art_path):
                    # 使用本地曲绘文件
                    try:
                        target_art_path = os.path.join(project_folder, f"{path_value}.png")
                        shutil.copy2(local_art_path, target_art_path)
                        art_created = True
                    except Exception as e:
                        MessageBox("警告", f"复制本地曲绘文件失败：{str(e)}", self).exec_()
                elif create_art:
                    # 自动生成曲绘
                    if not font_path:
                        MessageBox("警告", "未设置曲绘字体，无法生成曲绘！", self).exec_()
                    elif create_chart_art(project_folder, project_name, level, path_value, font_path):
                        art_created = True
                    else:
                        MessageBox("警告", "曲绘图片创建失败，但工程已创建。", self).exec_()
                
                if art_created:
                    MessageBox("成功", "工程创建成功，曲绘已处理！", self).exec_()
                else:
                    MessageBox("成功", "工程创建成功！", self).exec_()
                
                self.refresh_project_list()
                
                # 自动打开新创建的工程
                self.open_project(project_name)
                
            except Exception as e:
                MessageBox("错误", f"创建工程失败：{str(e)}", self).exec_()
        
    def open_project_action(self):
        """打开选中的工程"""
        selected_rows = self.project_table.selectedItems()
        if not selected_rows:
            MessageBox("警告", "请先选择要打开的工程！", self).exec_()
            return
            
        # 获取选中行的工程名
        row = selected_rows[0].row()
        project_name = self.project_table.item(row, 0).text()
        self.open_project(project_name)
        
    def open_project(self, project_name):
        """打开工程管理页面"""
        project_folder = os.path.join(program_folder, project_name)
        project_info = read_info_txt(project_folder)
        
        if not project_info:
            MessageBox("错误", "无法读取工程信息！", self).exec_()
            return
            
        # 如果该工程已经打开，则聚焦到该窗口
        if project_name in current_windows['projects'] and current_windows['projects'][project_name]:
            current_windows['projects'][project_name].raise_()
            current_windows['projects'][project_name].activateWindow()
            return
            
        # 创建并显示工程管理窗口
        project_window = ProjectWindow(project_name, project_folder, project_info, self)
        current_windows['projects'][project_name] = project_window
        project_window.show()
        
    def delete_project_action(self):
        """删除选中的工程"""
        selected_rows = self.project_table.selectedItems()
        if not selected_rows:
            MessageBox("警告", "请先选择要删除的工程！", self).exec_()
            return
            
        # 获取选中行的工程名
        row = selected_rows[0].row()
        project_name = self.project_table.item(row, 0).text()
        
        # 确认删除
        if not MessageBox("确认删除", f"确定要删除工程 '{project_name}' 吗？\n此操作不可恢复！", self).exec_():
            return
            
        try:
            project_folder = os.path.join(program_folder, project_name)
            shutil.rmtree(project_folder)
            MessageBox("成功", "工程已删除！", self).exec_()
            self.refresh_project_list()
        except Exception as e:
            MessageBox("错误", f"删除工程失败：{str(e)}", self).exec_()
            
    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()

class CreateProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建新工程")
        self.setFixedSize(450, 700)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = TitleLabel("创建新的谱面工程")
        layout.addWidget(title_label)
        
        # 工程名称
        name_label = BodyLabel("工程名称/谱面名称（必填）")
        layout.addWidget(name_label)
        
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("请输入工程名称")
        layout.addWidget(self.name_edit)
        
        # 难度
        level_label = BodyLabel("难度（必填）")
        layout.addWidget(level_label)
        
        self.level_edit = LineEdit()
        self.level_edit.setPlaceholderText("请输入难度")
        layout.addWidget(self.level_edit)
        
        # Composer
        composer_label = BodyLabel("Composer")
        layout.addWidget(composer_label)
        
        self.composer_edit = LineEdit()
        self.composer_edit.setText("Phigros")
        layout.addWidget(self.composer_edit)
        
        # Charter
        charter_label = BodyLabel("Charter")
        layout.addWidget(charter_label)
        
        self.charter_edit = LineEdit()
        self.charter_edit.setText("Phigros")
        layout.addWidget(self.charter_edit)
        
        # 曲绘创建选项
        art_card = CardWidget()
        art_layout = QVBoxLayout(art_card)
        art_layout.setContentsMargins(15, 15, 15, 15)
        art_layout.setSpacing(10)
        
        art_title = StrongBodyLabel("曲绘创建选项")
        art_layout.addWidget(art_title)
        
        # 是否自创建曲绘
        self.create_art_check = CheckBox("自动生成曲绘")
        self.create_art_check.stateChanged.connect(self.on_create_art_check_changed)
        art_layout.addWidget(self.create_art_check)
        
        # 字体选择
        self.font_label = BodyLabel("曲绘字体（可选）")
        self.font_label.setEnabled(False)
        art_layout.addWidget(self.font_label)
        
        font_layout = QHBoxLayout()
        self.font_edit = LineEdit()
        self.font_edit.setPlaceholderText("请选择字体文件")
        self.font_edit.setEnabled(False)
        font_layout.addWidget(self.font_edit)
        
        self.font_button = PushButton("浏览")
        self.font_button.clicked.connect(self.browse_font)
        self.font_button.setEnabled(False)
        font_layout.addWidget(self.font_button)
        art_layout.addLayout(font_layout)
        
        # 使用本地曲绘文件
        self.use_local_art_check = CheckBox("使用本地曲绘文件")
        self.use_local_art_check.stateChanged.connect(self.on_use_local_art_check_changed)
        art_layout.addWidget(self.use_local_art_check)
        
        # 本地曲绘文件选择
        self.local_art_label = BodyLabel("本地曲绘文件")
        self.local_art_label.setEnabled(False)
        art_layout.addWidget(self.local_art_label)
        
        local_art_layout = QHBoxLayout()
        self.local_art_edit = LineEdit()
        self.local_art_edit.setPlaceholderText("请选择本地曲绘文件")
        self.local_art_edit.setEnabled(False)
        local_art_layout.addWidget(self.local_art_edit)
        
        self.local_art_button = PushButton("浏览")
        self.local_art_button.clicked.connect(self.browse_local_art)
        self.local_art_button.setEnabled(False)
        local_art_layout.addWidget(self.local_art_button)
        art_layout.addLayout(local_art_layout)
        
        layout.addWidget(art_card)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.create_button = PrimaryPushButton("创建工程")
        self.create_button.clicked.connect(self.accept)
        button_layout.addWidget(self.create_button)
        
        layout.addLayout(button_layout)
        
    def on_create_art_check_changed(self, state):
        """处理自动生成曲绘复选框状态变化"""
        enabled = state == Qt.Checked
        self.font_label.setEnabled(enabled)
        self.font_edit.setEnabled(enabled)
        self.font_button.setEnabled(enabled)
        # 如果启用了自动生成曲绘，则禁用使用本地曲绘文件
        if enabled:
            self.use_local_art_check.setChecked(False)
    
    def on_use_local_art_check_changed(self, state):
        """处理使用本地曲绘文件复选框状态变化"""
        enabled = state == Qt.Checked
        self.local_art_label.setEnabled(enabled)
        self.local_art_edit.setEnabled(enabled)
        self.local_art_button.setEnabled(enabled)
        # 如果启用了使用本地曲绘文件，则禁用自动生成曲绘
        if enabled:
            self.create_art_check.setChecked(False)
    
    def browse_font(self):
        """浏览选择字体文件"""
        font_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择字体文件",
            "",
            "字体文件 (*.ttf *.otf *.ttc);;所有文件 (*.*)"
        )
        if font_path:
            self.font_edit.setText(font_path)
    
    def browse_local_art(self):
        """浏览选择本地曲绘文件"""
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择曲绘文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg);;所有文件 (*.*)"
        )
        if image_path:
            self.local_art_edit.setText(image_path)

class ProjectWindow(QMainWindow):
    def __init__(self, project_name, project_folder, project_info, parent=None):
        super().__init__(parent)
        self.project_name = project_name
        self.project_folder = project_folder
        self.project_info = project_info
        self.parent = parent
        # 连接窗口关闭事件
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.initUI()
        
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 从当前窗口字典中移除引用
        if self.project_name in current_windows['projects']:
            del current_windows['projects'][self.project_name]
        event.accept()
        
    def initUI(self):
        self.setWindowTitle(f"工程管理 - {self.project_name}")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = TitleLabel(f"工程管理 - {self.project_name}")
        main_layout.addWidget(title_label)
        
        # 文件管理区域
        file_group = CardWidget()
        file_layout = QVBoxLayout(file_group)
        file_layout.setContentsMargins(15, 15, 15, 15)
        file_layout.setSpacing(10)
        
        file_title = StrongBodyLabel("文件管理")
        file_layout.addWidget(file_title)
        
        # 定义文件类型
        file_types = [
            ("信息", "info.txt", "info"),
            ("谱面", ".json", "chart"),
            ("音频", ".wav", "audio"),
            ("曲绘", ".png", "art")
        ]
        
        self.file_widgets = {}
        
        for i, (display_name, extension, file_type) in enumerate(file_types):
            # 文件类型标签
            type_layout = QHBoxLayout()
            type_layout.setSpacing(10)
            
            type_label = BodyLabel(display_name)
            type_label.setFixedWidth(60)  # 设置固定宽度
            type_layout.addWidget(type_label)
            
            # 文件名显示
            file_name, file_path = self.get_file_info(file_type)
            status_label = BodyLabel(file_name)
            status_label.setWordWrap(False)  # 禁止换行
            status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 设置大小策略
            type_layout.addWidget(status_label)
            
            # 曲绘预览（仅对曲绘文件类型）
            if file_type == "art" and file_path and os.path.exists(file_path):
                # 创建预览标签
                preview_label = QLabel()
                preview_label.setFixedSize(80, 45)  # 16:9比例的缩略图
                preview_label.setAlignment(Qt.AlignCenter)
                preview_label.setStyleSheet("border: 1px solid gray;")
                
                # 加载并缩放图片
                try:
                    pixmap = QPixmap(file_path)
                    pixmap = pixmap.scaled(80, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    preview_label.setPixmap(pixmap)
                except Exception as e:
                    preview_label.setText("预览失败")
                
                type_layout.addWidget(preview_label)
            
            # 按钮框架
            button_layout = QHBoxLayout()
            button_layout.setSpacing(5)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            modify_button = PushButton("修改")
            modify_button.setFixedWidth(60)  # 设置固定宽度
            modify_button.clicked.connect(lambda _, ft=file_type: self.modify_file(ft))
            button_layout.addWidget(modify_button)
            
            delete_button = PushButton("删除")
            delete_button.setFixedWidth(60)  # 设置固定宽度
            delete_button.clicked.connect(lambda _, ft=file_type: self.delete_file(ft))
            button_layout.addWidget(delete_button)
            
            type_layout.addLayout(button_layout)
            file_layout.addLayout(type_layout)
            
            self.file_widgets[file_type] = {
                'status_label': status_label,
                'file_path': file_path,
                'file_name': file_name
            }
        
        main_layout.addWidget(file_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.open_folder_button = PushButton("打开工程文件夹")
        self.open_folder_button.setFixedWidth(120)
        self.open_folder_button.clicked.connect(self.open_project_folder)
        button_layout.addWidget(self.open_folder_button)
        
        self.pack_button = PrimaryPushButton("一键打包zip")
        self.pack_button.setFixedWidth(120)
        self.pack_button.clicked.connect(self.pack_project)
        button_layout.addWidget(self.pack_button)
        
        # 添加弹性空间
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 设置主布局的边距
        main_layout.setContentsMargins(20, 20, 20, 20)
        
    def get_file_info(self, file_type):
        """获取文件信息"""
        if file_type == "info":
            file_path = os.path.join(self.project_folder, "info.txt")
            file_name = "info.txt"
        elif file_type == "chart":
            chart_file = self.project_info.get("Chart", "")
            # 检查文件是否实际存在
            if chart_file and os.path.exists(os.path.join(self.project_folder, chart_file)):
                file_path = os.path.join(self.project_folder, chart_file)
                file_name = chart_file
            else:
                file_path = ""
                file_name = "未设置"
        elif file_type == "audio":
            # 查找音频文件
            audio_file = None
            for f in os.listdir(self.project_folder) if os.path.exists(self.project_folder) else []:
                if f.lower().endswith('.wav'):
                    audio_file = f
                    break
            file_path = os.path.join(self.project_folder, audio_file) if audio_file else ""
            file_name = audio_file if audio_file else "未设置"
        else:  # art
            art_file = f"{self.project_info.get('Path', '')}.png"
            file_path = os.path.join(self.project_folder, art_file) if self.project_info.get('Path') else ""
            file_name = art_file if self.project_info.get('Path') and os.path.exists(file_path) else "未设置"
            
        return file_name, file_path
        
    def modify_file(self, file_type):
        """修改文件"""
        if file_type == "info":
            self.modify_info()
        elif file_type == "chart":
            self.open_chart_search_window()
        elif file_type == "audio":
            self.open_audio_search_window()
        elif file_type == "art":
            self.modify_art()
            
    def modify_info(self):
        """修改信息文件"""
        dialog = ModifyInfoDialog(self.project_info, self)
        if dialog.exec_() == QDialog.Accepted:
            # 更新工程信息
            self.project_info['Level'] = dialog.level_edit.text().strip()
            self.project_info['Composer'] = dialog.composer_edit.text().strip()
            self.project_info['Charter'] = dialog.charter_edit.text().strip()
            update_info_txt(self.project_folder, self.project_info)
            MessageBox("成功", "工程信息已更新！", self).exec_()
            # 刷新窗口
            self.close()
            self.parent.open_project(self.project_name)
            
    def open_chart_search_window(self):
        """打开谱面搜索窗口"""
        dialog = ChartSearchWindow(self.project_folder, self.project_info, self.project_name, self.parent, self)
        dialog.exec_()
        
    def open_audio_search_window(self):
        """打开音频搜索窗口"""
        dialog = AudioSearchWindow(self.project_folder, self.project_info, self.project_name, self.parent, self)
        dialog.exec_()
        
    def modify_art(self):
        """修改曲绘文件"""
        dialog = ModifyArtDialog(self.project_folder, self.project_info, self.project_name, self)
        if dialog.exec_() == QDialog.Accepted:
            # 刷新窗口
            self.close()
            self.parent.open_project(self.project_name)
        
    def delete_file(self, file_type):
        """删除文件"""
        if file_type == "info":
            MessageBox("警告", "不能删除信息文件！", self).exec_()
            return
            
        if not MessageBox("确认", "确定要删除这个文件吗？", self).exec_():
            return
            
        try:
            if file_type == "chart":
                chart_file = self.project_info.get("Chart", "")
                if chart_file:
                    file_path = os.path.join(self.project_folder, chart_file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    self.project_info['Chart'] = ""
                    update_info_txt(self.project_folder, self.project_info)
            elif file_type == "audio":
                for f in os.listdir(self.project_folder):
                    if f.lower().endswith('.wav'):
                        os.remove(os.path.join(self.project_folder, f))
            elif file_type == "art":
                art_file = f"{self.project_info.get('Path', '')}.png"
                if self.project_info.get('Path'):
                    file_path = os.path.join(self.project_folder, art_file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            
            MessageBox("成功", "文件已删除！", self).exec_()
            # 刷新窗口
            self.close()
            self.parent.open_project(self.project_name)
        except Exception as e:
            MessageBox("错误", f"删除文件失败：{str(e)}", self).exec_()
            
    def open_project_folder(self):
        """打开工程文件夹"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.project_folder)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', self.project_folder])
        except Exception as e:
            MessageBox("错误", f"无法打开文件夹：{str(e)}", self).exec_()
            
    def pack_project(self):
        """一键打包工程为zip"""
        try:
            zip_filename = f"{self.project_name}.zip"
            zip_path = os.path.join(self.project_folder, zip_filename)
            
            # 定义要打包的核心文件
            core_files = []
            
            # info.txt
            info_path = os.path.join(self.project_folder, "info.txt")
            if os.path.exists(info_path):
                core_files.append(("info.txt", info_path))
            
            # 谱面文件
            if self.project_info.get("Chart"):
                chart_path = os.path.join(self.project_folder, self.project_info["Chart"])
                if os.path.exists(chart_path):
                    core_files.append((self.project_info["Chart"], chart_path))
            
            # 音频文件
            for f in os.listdir(self.project_folder):
                if f.lower().endswith('.wav'):
                    audio_path = os.path.join(self.project_folder, f)
                    core_files.append((f, audio_path))
                    break
            
            # 曲绘文件
            if self.project_info.get("Path"):
                art_file = f"{self.project_info['Path']}.png"
                art_path = os.path.join(self.project_folder, art_file)
                if os.path.exists(art_path):
                    core_files.append((art_file, art_path))
            
            if not core_files:
                MessageBox("警告", "没有找到可打包的文件！", self).exec_()
                return
            
            # 创建zip文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename, file_path in core_files:
                    zipf.write(file_path, filename)
            
            MessageBox("成功", f"工程已打包为：{zip_filename}", self).exec_()
            
            # 询问是否打开文件夹
            if MessageBox("打开文件夹", "是否打开工程文件夹查看打包结果？", self).exec_():
                if os.name == 'nt':  # Windows
                    os.startfile(self.project_folder)
                elif os.name == 'posix':  # macOS and Linux
                    subprocess.run(['open', self.project_folder])
                    
        except Exception as e:
            MessageBox("错误", f"打包失败：{str(e)}", self).exec_()

class ModifyInfoDialog(QDialog):
    def __init__(self, project_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改工程信息")
        self.setFixedSize(400, 300)
        self.project_info = project_info
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = TitleLabel("修改工程信息")
        layout.addWidget(title_label)
        
        # 难度
        level_label = BodyLabel("难度")
        layout.addWidget(level_label)
        
        self.level_edit = LineEdit()
        self.level_edit.setText(self.project_info.get("Level", ""))
        layout.addWidget(self.level_edit)
        
        # Composer
        composer_label = BodyLabel("Composer")
        layout.addWidget(composer_label)
        
        self.composer_edit = LineEdit()
        self.composer_edit.setText(self.project_info.get("Composer", ""))
        layout.addWidget(self.composer_edit)
        
        # Charter
        charter_label = BodyLabel("Charter")
        layout.addWidget(charter_label)
        
        self.charter_edit = LineEdit()
        self.charter_edit.setText(self.project_info.get("Charter", ""))
        layout.addWidget(self.charter_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = PrimaryPushButton("保存")
        self.save_button.clicked.connect(self.accept)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)

class ChartSearchWindow(QDialog):
    def __init__(self, project_folder, project_info, project_name, main_window, parent=None):
        super().__init__(parent)
        self.project_folder = project_folder
        self.project_info = project_info
        self.project_name = project_name
        self.main_window = main_window
        self.parent = parent
        self.setWindowTitle("谱面搜索")
        self.setFixedSize(800, 700)  # 调整窗口大小，增加高度
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 标题 - 使用较小的字体
        title_label = SubtitleLabel("谱面搜索")
        layout.addWidget(title_label)
        
        # 谱面文件夹选择
        folder_label = BodyLabel("谱面文件夹（TextAsset）")
        layout.addWidget(folder_label)
        
        folder_layout = QHBoxLayout()
        self.folder_edit = LineEdit()
        self.folder_edit.setPlaceholderText("请选择谱面文件夹")
        folder_layout.addWidget(self.folder_edit)
        
        self.browse_button = PushButton("选取")
        self.browse_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.browse_button)
        layout.addLayout(folder_layout)
        
        # 筛选条件
        filter_label = StrongBodyLabel("筛选条件")
        layout.addWidget(filter_label)
        
        filter_layout = QGridLayout()
        
        # 关键词
        keyword_label = BodyLabel("关键词")
        filter_layout.addWidget(keyword_label, 0, 0)
        self.keyword_edit = LineEdit()
        self.keyword_edit.setPlaceholderText("#")
        filter_layout.addWidget(self.keyword_edit, 0, 1)
        
        # 物量
        number_label = BodyLabel("物量")
        filter_layout.addWidget(number_label, 0, 2)
        self.number_edit = LineEdit()
        filter_layout.addWidget(self.number_edit, 0, 3)
        
        # BPM
        bpm_label = BodyLabel("BPM")
        filter_layout.addWidget(bpm_label, 1, 0)
        self.bpm_edit = LineEdit()
        filter_layout.addWidget(self.bpm_edit, 1, 1)
        
        # 音频长度
        length_label = BodyLabel("音频长度")
        filter_layout.addWidget(length_label, 1, 2)
        self.length_edit = LineEdit()
        filter_layout.addWidget(self.length_edit, 1, 3)
        
        # 开始筛选按钮
        self.search_button = PrimaryPushButton("开始筛选")
        self.search_button.clicked.connect(self.search_charts)
        filter_layout.addWidget(self.search_button, 0, 4, 2, 1)
        
        layout.addLayout(filter_layout)
        
        # 曲目预览区域
        preview_group = CardWidget()
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        preview_title = StrongBodyLabel("曲目预览")
        preview_layout.addWidget(preview_title)
        
        # 创建一个水平布局来放置曲绘预览和信息
        preview_h_layout = QHBoxLayout()
        
        # 曲绘预览
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(160, 90)  # 16:9比例
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setText("暂无预览")
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        preview_h_layout.addWidget(self.preview_label)
        
        # 曲目信息
        info_layout = QVBoxLayout()
        self.chart_name_label = BodyLabel("谱面名称: ")
        self.composer_label = BodyLabel("作曲者: ")
        self.charter_label = BodyLabel("谱师: ")
        self.level_label = BodyLabel("难度: ")
        info_layout.addWidget(self.chart_name_label)
        info_layout.addWidget(self.composer_label)
        info_layout.addWidget(self.charter_label)
        info_layout.addWidget(self.level_label)
        preview_h_layout.addLayout(info_layout)
        
        preview_layout.addLayout(preview_h_layout)
        layout.addWidget(preview_group)
        
        # 搜索结果
        result_label = StrongBodyLabel("搜索结果")
        layout.addWidget(result_label)
        
        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 结果表格
        self.result_table = TableWidget()
        self.result_table.setBorderRadius(8)
        self.result_table.setBorderVisible(True)
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(['文件路径', '物量', 'BPM', '谱面时长（秒）', '匹配度'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择整行
        self.result_table.itemSelectionChanged.connect(self.on_item_selected)  # 连接选择事件
        layout.addWidget(self.result_table)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.add_button = PrimaryPushButton("添加到工程")
        self.add_button.clicked.connect(self.add_chart)
        self.add_button.setEnabled(False)
        button_layout.addWidget(self.add_button)
        
        layout.addLayout(button_layout)
        
        # 状态栏
        self.status_label = BodyLabel("就绪")
        layout.addWidget(self.status_label)
        
    def on_item_selected(self):
        """当选择表格中的项目时更新预览"""
        selected_items = self.result_table.selectedItems()
        if not selected_items:
            return
            
        # 获取选中行的文件名
        row = selected_items[0].row()
        chart_filename = self.result_table.item(row, 0).text()
        
        # 更新曲目信息
        self.chart_name_label.setText(f"谱面名称: {chart_filename}")
        self.composer_label.setText(f"作曲者: {self.project_info.get('Composer', '')}")
        self.charter_label.setText(f"谱师: {self.project_info.get('Charter', '')}")
        self.level_label.setText(f"难度: {self.project_info.get('Level', '')}")
        
        # 尝试加载曲绘预览
        self.load_chart_preview(chart_filename)
        
    def load_chart_preview(self, chart_filename):
        """加载曲绘预览"""
        # 从文件名获取路径值（移除.json扩展名）
        path_value = chart_filename.replace(".json", "")
        
        # 构建曲绘文件路径
        art_file = f"{path_value}.png"
        art_path = os.path.join(os.path.dirname(self.folder_edit.text()), art_file)
        
        # 如果在谱面文件夹中找不到，则尝试在工程文件夹中查找
        if not os.path.exists(art_path):
            art_path = os.path.join(self.project_folder, f"{self.project_info.get('Path', '')}.png")
            
        # 如果找到了曲绘文件，则加载并显示
        if os.path.exists(art_path):
            try:
                pixmap = QPixmap(art_path)
                # 缩放图片以适应预览标签
                pixmap = pixmap.scaled(160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pixmap)
            except Exception as e:
                self.preview_label.setText("预览加载失败")
        else:
            self.preview_label.setText("暂无预览")
        
    def select_folder(self):
        """选择谱面文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "打开铺面文件夹", self.folder_edit.text())
        if folder_path:
            self.folder_edit.setText(folder_path)
            
    def search_charts(self):
        """搜索谱面"""
        file_dir = self.folder_edit.text()
        if not os.path.exists(file_dir):
            MessageBox("错误", "路径不存在。", self).exec_()
            return
            
        difficulty = self.keyword_edit.text()
        target_number = self.number_edit.text()
        target_bpm = self.bpm_edit.text()
        target_max_time = self.length_edit.text()
        
        if not target_number and not target_bpm and not target_max_time:
            MessageBox("缺少筛选条件", "请至少填写一个筛选条件！", self).exec_()
            return
            
        # 解析筛选条件
        if not difficulty:
            difficulty = "#"
        keywords = ["#", difficulty]
        
        target_number = int(target_number) if target_number else None
        target_bpm = int(target_bpm) if target_bpm else None
        target_max_time = int(target_max_time) if target_max_time else None
        
        try:
            file_list = os.listdir(file_dir)
            file_count = len(file_list)
            chart_objects_list = []
            
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.status_label.setText("正在分析谱面文件...")
            self.search_button.setEnabled(False)
            self.result_table.setRowCount(0)
            
            # 分析谱面文件
            for i, file in enumerate(file_list):
                # 更新进度条（分析阶段占50%）
                progress = int((i / file_count) * 50)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()  # 更新UI
                
                # 确认是否含有关键词
                skip = False
                for keyword in keywords:
                    if keyword not in file:
                        skip = True
                        break
                if skip:
                    continue
                    
                # 尝试分析铺面文件
                try:
                    chart = analyseJsonChart(os.path.join(file_dir, file))
                    if chart:
                        chart_objects_list.append(chart)
                        self.status_label.setText(f"{i+1}/{file_count}\t分析完成{chart}")
                        QApplication.processEvents()  # 更新UI
                except KeyError as e:
                    self.status_label.setText(f"{i+1}/{file_count}\t分析'{file}'时遇到 KeyError: {str(e)}")
                    QApplication.processEvents()  # 更新UI
                except Exception as e:
                    self.status_label.setText(f"{i+1}/{file_count}\t分析'{file}'时出错: {str(e)}")
                    QApplication.processEvents()  # 更新UI
                    
            if not chart_objects_list:
                self.status_label.setText("未找到匹配的谱面文件")
                self.progress_bar.setVisible(False)
                self.search_button.setEnabled(True)
                return
                
            # 计算匹配度
            self.status_label.setText(f"正在对 {len(chart_objects_list)} 个铺面文件进行匹配...")
            QApplication.processEvents()  # 更新UI
            
            # 重置分数
            for chart in chart_objects_list:
                chart.sortingScore = 0
                
            # 计算匹配度并更新进度
            for i, chart in enumerate(chart_objects_list):
                if target_number is not None:
                    chart.sortingScore += max(0, 10 - abs(target_number - chart.objectNumber))
                if target_bpm is not None:
                    chart.sortingScore += max(0, 10 - 0.2 * abs(target_bpm - chart.bpm))
                if target_max_time is not None:
                    chart.sortingScore += max(0, 10 - 0.2 * abs(target_max_time - chart.audioLength))
                    
                # 更新进度条（匹配阶段占50%）
                progress = int(50 + (i / len(chart_objects_list)) * 50)
                self.progress_bar.setValue(progress)
                QApplication.processEvents()  # 更新UI
                
            # 完成进度条
            self.progress_bar.setValue(100)
            QApplication.processEvents()  # 更新UI
            
            # 进行排序
            sorted_list = sorted(chart_objects_list, key=lambda x: x.sortingScore, reverse=True)[:10]
            
            # 清空现有结果
            self.result_table.setRowCount(0)
            
            # 输出结果
            if len(sorted_list) == 0 or sorted_list[0].sortingScore <= 0:
                self.status_label.setText("匹配完成。未找到任何匹配项目。")
            else:
                self.status_label.setText(f"匹配完成，最佳匹配项为：{sorted_list[0].fileName}")
                for chart in sorted_list:
                    if chart.sortingScore <= 0:
                        continue
                    row = self.result_table.rowCount()
                    self.result_table.insertRow(row)
                    self.result_table.setItem(row, 0, QTableWidgetItem(chart.fileName))
                    self.result_table.setItem(row, 1, QTableWidgetItem(str(chart.objectNumber)))
                    self.result_table.setItem(row, 2, QTableWidgetItem(str(chart.bpm)))
                    self.result_table.setItem(row, 3, QTableWidgetItem(str(chart.audioLength)))
                    self.result_table.setItem(row, 4, QTableWidgetItem(f"{chart.sortingScore / 30:.2%}"))
                    
                # 启用添加按钮
                self.add_button.setEnabled(True)
                
            self.progress_bar.setVisible(False)
            self.search_button.setEnabled(True)
            
        except Exception as e:
            MessageBox("错误", f"搜索失败：{str(e)}", self).exec_()
            self.progress_bar.setVisible(False)
            self.search_button.setEnabled(True)
            
    def add_chart(self):
        """添加谱面到工程"""
        selected_items = self.result_table.selectedItems()
        if not selected_items:
            MessageBox("警告", "请先选择要添加的谱面！", self).exec_()
            return
            
        # 获取选中行的文件名
        row = selected_items[0].row()
        chart_filename = self.result_table.item(row, 0).text()
        
        try:
            # 复制谱面文件到工程文件夹
            source_path = os.path.join(self.folder_edit.text(), chart_filename)
            target_filename = f"{self.project_info['Path']}.json"
            target_path = os.path.join(self.project_folder, target_filename)
            
            shutil.copy2(source_path, target_path)
            
            # 更新工程信息
            self.project_info['Chart'] = target_filename
            update_info_txt(self.project_folder, self.project_info)
            
            MessageBox("成功", f"谱面已添加到工程 '{self.project_name}'！", self).exec_()
            self.accept()  # 关闭对话框
            # 刷新父窗口
            self.parent.close()
            self.main_window.open_project(self.project_name)
            
        except Exception as e:
            MessageBox("错误", f"添加谱面失败：{str(e)}", self).exec_()

class AudioSearchWindow(QDialog):
    def __init__(self, project_folder, project_info, project_name, main_window, parent=None):
        super().__init__(parent)
        self.project_folder = project_folder
        self.project_info = project_info
        self.project_name = project_name
        self.main_window = main_window
        self.parent = parent
        self.setWindowTitle("音频搜索")
        self.setFixedSize(700, 600)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = TitleLabel("音频筛选")
        layout.addWidget(title_label)
        
        # 音频文件夹选择
        folder_label = BodyLabel("音频文件夹（wav）")
        layout.addWidget(folder_label)
        
        folder_layout = QHBoxLayout()
        self.folder_edit = LineEdit()
        self.folder_edit.setPlaceholderText("请选择音频文件夹")
        folder_layout.addWidget(self.folder_edit)
        
        self.browse_button = PushButton("选取")
        self.browse_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.browse_button)
        layout.addLayout(folder_layout)
        
        # 音频时长筛选
        filter_group = CardWidget()
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        
        filter_title = StrongBodyLabel("筛选条件")
        filter_layout.addWidget(filter_title)
        
        duration_layout = QHBoxLayout()
        duration_label = BodyLabel("目标音频时长（秒，精确到小数点后两位）")
        duration_layout.addWidget(duration_label)
        duration_layout.addStretch()
        filter_layout.addLayout(duration_layout)
        
        input_layout = QHBoxLayout()
        self.duration_edit = LineEdit()
        self.duration_edit.setPlaceholderText("请输入目标音频时长")
        input_layout.addWidget(self.duration_edit)
        
        self.search_button = PrimaryPushButton("开始筛选")
        self.search_button.clicked.connect(self.search_audio)
        input_layout.addWidget(self.search_button)
        filter_layout.addLayout(input_layout)
        
        layout.addWidget(filter_group)
        
        # 搜索结果
        result_label = StrongBodyLabel("搜索结果")
        layout.addWidget(result_label)
        
        # 进度条
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 结果表格
        self.result_table = TableWidget()
        self.result_table.setBorderRadius(8)
        self.result_table.setBorderVisible(True)
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(['文件路径', '音频时长（秒）', '匹配度'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.result_table)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.play_button = PushButton("试听")
        self.play_button.clicked.connect(self.play_audio)
        button_layout.addWidget(self.play_button)
        
        self.add_button = PrimaryPushButton("添加到工程")
        self.add_button.clicked.connect(self.add_audio)
        self.add_button.setEnabled(False)
        button_layout.addWidget(self.add_button)
        
        layout.addLayout(button_layout)
        
        # 状态栏
        self.status_label = BodyLabel("就绪")
        layout.addWidget(self.status_label)
        
    def select_folder(self):
        """选择音频文件夹"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择音频文件夹", self.folder_edit.text())
        if folder_path:
            self.folder_edit.setText(folder_path)
            
    def search_audio(self):
        """搜索音频"""
        folder_path = self.folder_edit.text()
        if not folder_path or not os.path.exists(folder_path):
            MessageBox("错误", "请选择有效的音频文件夹！", self).exec_()
            return
            
        target_duration_str = self.duration_edit.text()
        if not target_duration_str:
            MessageBox("错误", "请填写目标音频时长！", self).exec_()
            return
            
        try:
            target_duration = float(target_duration_str)
        except ValueError:
            MessageBox("错误", "音频时长必须是数字！", self).exec_()
            return
            
        # 扫描音频文件
        audio_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.wav')]
        audio_objects_list = []
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在分析音频文件...")
        self.search_button.setEnabled(False)
        self.result_table.setRowCount(0)
        
        # 分析音频文件
        for i, audio_file in enumerate(audio_files):
            # 更新进度条（分析阶段占50%）
            progress = int((i / len(audio_files)) * 50)
            self.progress_bar.setValue(progress)
            QApplication.processEvents()  # 更新UI
            
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
                audio_objects_list.append(audio_obj)
                self.status_label.setText(f"{i+1}/{len(audio_files)}\t分析完成 {audio_file}")
                QApplication.processEvents()  # 更新UI
                
        if not audio_objects_list:
            self.status_label.setText("未找到匹配的音频文件")
            self.progress_bar.setVisible(False)
            self.search_button.setEnabled(True)
            return
            
        # 计算匹配度
        self.status_label.setText(f"正在对 {len(audio_objects_list)} 个音频文件进行匹配...")
        QApplication.processEvents()  # 更新UI
        
        # 重置分数
        for audio_obj in audio_objects_list:
            audio_obj.sortingScore = 0
            
        # 计算匹配度并更新进度
        for i, audio_obj in enumerate(audio_objects_list):
            # 匹配度计算：时长越接近，匹配度越高
            time_diff = abs(target_duration - audio_obj.duration)
            audio_obj.sortingScore = max(0, 10 - time_diff * 2)  # 每差1秒扣2分
            
            # 更新进度条（匹配阶段占50%）
            progress = int(50 + (i / len(audio_objects_list)) * 50)
            self.progress_bar.setValue(progress)
            QApplication.processEvents()  # 更新UI
            
        # 完成进度条
        self.progress_bar.setValue(100)
        QApplication.processEvents()  # 更新UI
        
        # 进行排序
        audio_sorted_list = sorted(audio_objects_list, key=lambda x: x.sortingScore, reverse=True)[:10]
        
        # 清空现有结果
        self.result_table.setRowCount(0)
        
        # 输出结果
        if len(audio_sorted_list) == 0 or audio_sorted_list[0].sortingScore <= 0:
            self.status_label.setText("匹配完成。未找到任何匹配项目。")
        else:
            self.status_label.setText(f"匹配完成，最佳匹配项为：{audio_sorted_list[0].fileName}")
            for audio_obj in audio_sorted_list:
                if audio_obj.sortingScore <= 0:
                    continue
                row = self.result_table.rowCount()
                self.result_table.insertRow(row)
                self.result_table.setItem(row, 0, QTableWidgetItem(audio_obj.fileName))
                self.result_table.setItem(row, 1, QTableWidgetItem(str(audio_obj.duration)))
                self.result_table.setItem(row, 2, QTableWidgetItem(f"{audio_obj.sortingScore / 10:.2%}"))
                
            # 启用添加按钮
            self.add_button.setEnabled(True)
            
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)
        
    def play_audio(self):
        """试听音频"""
        selected_items = self.result_table.selectedItems()
        if not selected_items:
            MessageBox("警告", "请先选择要试听的音频！", self).exec_()
            return
            
        # 获取选中行的文件名
        row = selected_items[0].row()
        audio_filename = self.result_table.item(row, 0).text()
        audio_path = os.path.join(self.folder_edit.text(), audio_filename)
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(audio_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', audio_path])
        except Exception as e:
            MessageBox("错误", f"无法播放音频：{str(e)}", self).exec_()
            
    def add_audio(self):
        """添加音频到工程"""
        selected_items = self.result_table.selectedItems()
        if not selected_items:
            MessageBox("警告", "请先选择要添加的音频！", self).exec_()
            return
            
        # 获取选中行的文件名
        row = selected_items[0].row()
        audio_filename = self.result_table.item(row, 0).text()
        
        try:
            # 删除现有音频文件
            for f in os.listdir(self.project_folder):
                if f.lower().endswith('.wav'):
                    os.remove(os.path.join(self.project_folder, f))
            
            # 复制新文件
            source_path = os.path.join(self.folder_edit.text(), audio_filename)
            shutil.copy2(source_path, self.project_folder)
            
            MessageBox("成功", f"音频已添加到工程 '{self.project_name}'！", self).exec_()
            self.accept()  # 关闭对话框
            # 刷新父窗口
            self.parent.close()
            self.main_window.open_project(self.project_name)
            
        except Exception as e:
            MessageBox("错误", f"添加音频失败：{str(e)}", self).exec_()

class ModifyArtDialog(QDialog):
    def __init__(self, project_folder, project_info, project_name, parent=None):
        super().__init__(parent)
        self.project_folder = project_folder
        self.project_info = project_info
        self.project_name = project_name
        self.parent = parent
        self.setWindowTitle("修改曲绘")
        self.setFixedSize(450, 350)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = TitleLabel("修改曲绘")
        layout.addWidget(title_label)
        
        # 字体选择区域
        font_card = CardWidget()
        font_layout = QVBoxLayout(font_card)
        font_layout.setContentsMargins(15, 15, 15, 15)
        font_layout.setSpacing(10)
        
        font_title = StrongBodyLabel("字体选择")
        font_layout.addWidget(font_title)
        
        # 字体选择控件
        font_select_layout = QHBoxLayout()
        self.font_edit = LineEdit()
        self.font_edit.setPlaceholderText("请选择字体文件")
        font_select_layout.addWidget(self.font_edit)
        
        self.font_button = PushButton("浏览")
        self.font_button.clicked.connect(self.browse_font)
        font_select_layout.addWidget(self.font_button)
        font_layout.addLayout(font_select_layout)
        
        layout.addWidget(font_card)
        
        # 操作按钮区域
        action_card = CardWidget()
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(15, 15, 15, 15)
        action_layout.setSpacing(10)
        
        action_title = StrongBodyLabel("操作选项")
        action_layout.addWidget(action_title)
        
        # 重新生成曲绘按钮
        self.regenerate_button = PrimaryPushButton("重新生成曲绘")
        self.regenerate_button.clicked.connect(self.regenerate_art)
        action_layout.addWidget(self.regenerate_button)
        
        # 选择本地图片替换按钮
        self.replace_button = PushButton("选择本地图片替换")
        self.replace_button.clicked.connect(self.replace_art)
        action_layout.addWidget(self.replace_button)
        
        layout.addWidget(action_card)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = PushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
    def browse_font(self):
        """浏览选择字体文件"""
        font_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择字体文件",
            "",
            "字体文件 (*.ttf *.otf *.ttc);;所有文件 (*.*)"
        )
        if font_path:
            self.font_edit.setText(font_path)
            
    def regenerate_art(self):
        """重新生成曲绘"""
        font_path = self.font_edit.text().strip()
            
        if not font_path:
            MessageBox("警告", "未设置曲绘字体，无法生成曲绘！", self).exec_()
        elif create_chart_art(self.project_folder, self.project_info['Name'], self.project_info['Level'], self.project_info['Path'], font_path):
            MessageBox("成功", "曲绘已重新生成！", self).exec_()
            self.accept()  # 关闭对话框并刷新父窗口
        else:
            MessageBox("错误", "曲绘生成失败！", self).exec_()
            
    def replace_art(self):
        """选择本地图片替换"""
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg);;所有文件 (*.*)"
        )
        
        if image_path:
            try:
                target_filename = f"{self.project_info['Path']}.png"
                target_path = os.path.join(self.project_folder, target_filename)
                shutil.copy2(image_path, target_path)
                
                MessageBox("成功", "曲绘已替换！", self).exec_()
                self.accept()  # 关闭对话框并刷新父窗口
            except Exception as e:
                MessageBox("错误", f"替换曲绘失败：{str(e)}", self).exec_()

def main():
    app = QApplication(sys.argv)
    # 应用主题
    setTheme(Theme.LIGHT)
    
    # 创建并显示主窗口
    main_window = MainWindow()
    # 设置窗口图标
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "icon.ico")
    if os.path.exists(icon_path):
        main_window.setWindowIcon(QIcon(icon_path))
    main_window.show()
    
    sys.exit(app.exec_())

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 PhiChartSearch")
        self.setFixedSize(500, 400)
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = TitleLabel("PhiChartSearch")
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = StrongBodyLabel("版本：v1.0.0")
        layout.addWidget(version_label)
        
        # 技术信息
        tech_info = BodyLabel("基于 Python 语言\nGUI 界面框架：PyQt5 QFluentWidgets")
        layout.addWidget(tech_info)
        
        # 版权声明标题
        copyright_title = StrongBodyLabel("版权声明")
        layout.addWidget(copyright_title)
        
        # 版权声明内容
        copyright_text = "本软件遵循 GPLv3 协议，请遵守开源协议。\n" \
                         "本项目只用于搜索Phigros的音频文件和谱面文件\n" \
                         "程序内不包含任何游戏版权保护版权文件\n" \
                         "请勿传播拆包后文件\n" \
                         "请勿传播搜索后文件"
        copyright_label = BodyLabel(copyright_text)
        layout.addWidget(copyright_label)
        
        # 链接按钮区域
        link_layout = QHBoxLayout()
        
        # GitHub按钮
        self.github_button = PushButton("GitHub")
        self.github_button.clicked.connect(self.open_github)
        link_layout.addWidget(self.github_button)
        
        # 哔哩哔哩按钮
        self.bilibili_button = PushButton("哔哩哔哩")
        self.bilibili_button.clicked.connect(self.open_bilibili)
        link_layout.addWidget(self.bilibili_button)
        
        layout.addLayout(link_layout)
        
        # 关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = PushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def open_github(self):
        """打开GitHub链接"""
        QDesktopServices.openUrl(QUrl("https://github.com/catmcbe/PhiChartSearch"))
        
    def open_bilibili(self):
        """打开哔哩哔哩链接"""
        QDesktopServices.openUrl(QUrl("https://space.bilibili.com/587887115"))

if __name__ == '__main__':
    main()
