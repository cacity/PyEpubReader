# *-----------------------------------------------*
# *-----------------------------------------------*
# * Copyright @ 2020-2023 by gaofeng 1.92@163.com *
# * All rights reserved 2023.12.20                 *
# *-----------------------------------------------*
#
import os
import sys
import re
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, \
    QWidget, QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser, QFileDialog, QProgressBar, QComboBox, \
    QFontDialog, QSlider, QDialog, QListWidget, QStatusBar
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QFont
import zipfile
import asyncio
from bs4 import BeautifulSoup
import edge_tts
import shutil
import json

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)


class EpubReader(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("EPUB 阅读器")
        self.setWindowIcon(QIcon("./icon/icons8-book-96.png"))
        self.resize(1600, 1000)

        # 初始化行间距和段间距
        self.line_spacing = 20  # 示例值
        self.paragraph_spacing = 10  # 示例值

        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 创建 hbox1
        hbox1 = QHBoxLayout()
        main_layout.addLayout(hbox1)
        hbox2 = QHBoxLayout()
        main_layout.addLayout(hbox2)
        hbox3 = QHBoxLayout()
        main_layout.addLayout(hbox3)

        # 添加 QLabel
        label = QLabel("选择文件:")
        hbox1.addWidget(label)

        # 添加 QLineEdit
        self.file_edit = QLineEdit()
        hbox1.addWidget(self.file_edit)
        # 修改QLineEdit为QComboBox
        self.file_combo = QComboBox()
        hbox1.addWidget(self.file_combo)
        self.file_combo.setMinimumWidth(50)
        self.file_combo.currentIndexChanged.connect(self.on_combo_changed)

        #main_layout.addWidget(self.status_bar)
        self.Voice = QComboBox()
        voices = [
            "zh-CN-XiaoxiaoNeural",
            "zh-CN-XiaoyiNeural",
            "zh-CN-YunjianNeural",
            "zh-CN-YunxiNeural",
            "zh-CN-YunxiaNeural",
            "zh-CN-YunyangNeural",
            "zh-CN-liaoning-XiaobeiNeural",
            "zh-CN-shaanxi-XiaoniNeural",
            "zh-HK-HiuGaaiNeural",
            "zh-HK-HiuMaanNeural",
            "zh-HK-WanLungNeural",
            "zh-TW-HsiaoChenNeural",
            "zh-TW-HsiaoYuNeural",
            "zh-TW-YunJheNeural",
            "zu-ZA-ThandoNeural",
            "zu-ZA-ThembaNeural",
            "zh-TW-HsiaoChenNeural",
            "zh-TW-HsiaoYuNeural",
            "zh-TW-YunJheNeural",
            "zu-ZA-ThandoNeural",
            "zu-ZA-ThembaNeural"
        ]
        self.Voice.addItems(voices)
        self.Voice.setCurrentIndex(3)
        self.Voice.setMinimumWidth(50)
        hbox1.addWidget(self.Voice)

        # 添加 QPushButton - 打开文件
        self.open_button = QPushButton("打开文件")
        self.open_button.clicked.connect(self.open_file)
        self.open_button.setIcon(QIcon("./icon/icons8-打开文件夹-240.png"))
        hbox1.addWidget(self.open_button)

        self.font_button = QPushButton("选择字体", self)
        self.font_button.clicked.connect(self.select_and_apply_font)
        self.font_button.setIcon(QIcon("./icon/icons8-font-96.png"))
        hbox1.addWidget(self.font_button)

        self.eye_protection_button = QPushButton("护眼模式", self)
        self.eye_protection_button.clicked.connect(self.set_eye_protection_mode)
        self.eye_protection_button.setIcon(QIcon("./icon/icons8-眼睛-96.png"))
        hbox1.addWidget(self.eye_protection_button)

        # 创建显示/隐藏左边栏的按钮
        self.toggle_sidebar_button = QPushButton("隐藏边栏", self)
        self.toggle_sidebar_button.clicked.connect(self.toggle_sidebar)
        self.toggle_sidebar_button.setIcon(QIcon("./icon/icons8-add-bookmark-240.png"))
        hbox1.addWidget(self.toggle_sidebar_button)



        # 创建增大字号按钮并绑定事件
        self.increase_font_button = QPushButton("增大字号")
        self.increase_font_button.clicked.connect(self.increase_font_size)
        self.increase_font_button.setIcon(QIcon("./icon/icons8-加大字体-96.png"))
        hbox1.addWidget(self.increase_font_button)

        # 创建减小字号按钮并绑定事件
        self.decrease_font_button = QPushButton("减小字号")
        self.decrease_font_button.clicked.connect(self.decrease_font_size)
        self.decrease_font_button.setIcon(QIcon("./icon/icons8-减小字体-96.png"))
        hbox1.addWidget(self.decrease_font_button)

        # 添加 QPushButton - 语音播放
        self.play_voice_button = QPushButton("电子书转音频")
        self.play_voice_button.clicked.connect(self.play_voice)
        self.play_voice_button.setIcon(QIcon("./icon/icons8-connect-240.png"))
        hbox1.addWidget(self.play_voice_button)
        # 添加停止转音频的按钮
        self.stop_button = QPushButton("停止转音频", self)
        self.stop_button.clicked.connect(self.stop_conversion)
        self.stop_button.setIcon(QIcon("./icon/icons8-stop-64.png"))
        hbox1.addWidget(self.stop_button)

        # 添加全屏模式按钮
        fullscreen_icon = QIcon("./icon/icons8-checkmark-240.png")  # 替换为实际图标路径
        self.fullscreen_button = QPushButton("全屏模式", self)
        self.fullscreen_button.setIcon(fullscreen_icon)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        hbox1.addWidget(self.fullscreen_button)

        # 初始化页边距、行间距和段间距的值
        initial_margin = 10
        initial_line_spacing = 20
        initial_paragraph_spacing = 10

        # 添加页边距调节标签和滑动条
        self.margin_label = QLabel(f"页边距: {initial_margin}")
        hbox3.addWidget(self.margin_label)
        self.margin_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.margin_slider.setMinimum(0)
        self.margin_slider.setMaximum(50)
        self.margin_slider.setValue(initial_margin)
        self.margin_slider.valueChanged.connect(self.update_margin)
        hbox3.addWidget(self.margin_slider)

        # 添加行间距调节标签和滑动条
        self.line_spacing_label = QLabel(f"行间距: {initial_line_spacing}")
        hbox3.addWidget(self.line_spacing_label)
        self.line_spacing_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.line_spacing_slider.setMinimum(0)
        self.line_spacing_slider.setMaximum(50)
        self.line_spacing_slider.setValue(initial_line_spacing)
        self.line_spacing_slider.valueChanged.connect(self.update_line_spacing)
        hbox3.addWidget(self.line_spacing_slider)

        # 添加段间距调节标签和滑动条
        self.paragraph_spacing_label = QLabel(f"段间距: {initial_paragraph_spacing}")
        hbox3.addWidget(self.paragraph_spacing_label)
        self.paragraph_spacing_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.paragraph_spacing_slider.setMinimum(0)
        self.paragraph_spacing_slider.setMaximum(50)
        self.paragraph_spacing_slider.setValue(initial_paragraph_spacing)
        self.paragraph_spacing_slider.valueChanged.connect(self.update_paragraph_spacing)
        hbox3.addWidget(self.paragraph_spacing_slider)

        # 添加收藏按钮
        favorite_button = QPushButton("收藏", self)
        favorite_button.clicked.connect(self.add_to_favorites)
        hbox3.addWidget(favorite_button)

        # 初始化收藏文件路径
        self.favorites_file = os.path.join(script_dir, "book", "favorites.txt")

        # 添加查看收藏按钮
        view_favorites_button = QPushButton("查看收藏", self)
        view_favorites_button.clicked.connect(self.show_favorites)
        hbox3.addWidget(view_favorites_button)

        # 进度条初始化
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hbox2.addWidget(self.progress_bar)
        # 创建 QSplitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        self.status_bar = QStatusBar()
        # 限制状态栏的最大高度
        self.status_bar.setMaximumHeight(20)
        # 使用样式表微调状态栏的外观（可选）
        self.status_bar.setStyleSheet("QStatusBar { font-size: 10pt; }")
        main_layout.addWidget(self.status_bar)

        # 创建 QTableWidget
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(1)
        ####
        self.table_widget.setHorizontalHeaderLabels([ "文件名"])
        # 连接文件列表的双击事件到渲染函数
        self.table_widget.itemDoubleClicked.connect(self.render_selected_file)
        self.splitter.addWidget(self.table_widget)

        # 创建 QTextBrowser
        self.text_browser = QTextBrowser()
        self.splitter.addWidget(self.text_browser)

        # 初始化 EPUB 文件路径
        self.epub_file_path = None
        # self.resizeEvent(None)
        # 初始化字体大小
        self.font_size = 14
        # 初始化句子列表和当前句子的索引
        self.sentences = []
        self.current_sentence_index = -1

        self.tts = None
        self.output = 'output.mp3'
        self.rate = '+30%'
        self.volume = '+0%'

        self.stop_conversion_flag = False
        self.html_path_name = []  # 保存一个html文件的路径
        self.thread = None

        # 自动搜索并添加书籍到下拉列表
        self.populate_books_combo()
        # 设置 QTextBrowser 的字体
        #self.font = QFont("Arial", 14)
        self.font = QFont("Microsoft YaHei", 14)
        self.text_browser.setFont(self.font)

        self.is_eye_protection_mode_active = False

    def get_current_position(self):
        # 获取 QTextBrowser 滚动条的当前位置
        vertical_scrollbar = self.text_browser.verticalScrollBar()
        position = vertical_scrollbar.value()
        max_position = vertical_scrollbar.maximum()

        # 计算当前位置的百分比
        position_percentage = (position / max_position) if max_position != 0 else 0

        '''return {
            "position": position,
            "position_percentage": position_percentage
        }'''
        return position

    def go_to_position(self, position_info):
        # 根据保存的位置信息滚动到指定位置
        if "position" in position_info:
            vertical_scrollbar = self.text_browser.verticalScrollBar()
            vertical_scrollbar.setValue(position_info["position"])
    def show_favorites(self):
        # 加载收藏信息
        favorites = self.load_favorites()

        # 显示收藏对话框
        dialog = FavoritesDialog(favorites, self)
        # 连接信号到槽函数
        dialog.open_favorite_signal.connect(self.open_favorite)
        dialog.exec()

    def open_favorite(self, favorite_info):
        # 实现打开收藏项的操作
        print(favorite_info)
        book_name = favorite_info['book']
        document_name = favorite_info['document']
        position = int(favorite_info['position'])
        # 选中书名列表中的特定书籍
        index = self.file_combo.findText(book_name)
        if index >= 0:
            self.file_combo.setCurrentIndex(index)
            self.auto_load_book(book_name)
        self.auto_load_book(book_name)
        # 然后找到对应的文档
        for row in range(self.table_widget.rowCount()):
            if self.table_widget.item(row, 0).text() == document_name:
                self.table_widget.selectRow(row)
                self.render_selected_file(self.table_widget.item(row, 0))
                break

        # 如果需要，可以将视图滚动到指定位置
        #self.text_browser.scrollToPosition(position)  # 需要实现scrollToPosition方法
        scrollbar = self.text_browser.verticalScrollBar()
        scrollbar.setValue(position)
        #self.scroll_to_percentage(position)
        print(f"打开收藏项: {favorite_info}")

    def scroll_to_percentage(self, percentage):
        # 确保百分比是有效的值
        if 0 <= float(percentage) <= 1:
            # 获取QTextBrowser的垂直滚动条
            scrollbar = self.text_browser.verticalScrollBar()
            print(scrollbar.maximum())
            print(scrollbar.minimum())
            # 计算滚动条应该到达的位置
            position =scrollbar.minimum() +  (scrollbar.maximum() - scrollbar.minimum()) * float(percentage) #scrollbar.minimum() + (scrollbar.maximum() - scrollbar.minimum()) * float(percentage) #scrollbar.minimum() +
            # 设置滚动条的位置
            scrollbar.setValue(position)
    def load_favorites(self):
        # 加载收藏信息的方法
        favorites = []
        try:
            with open(self.favorites_file, "r") as file:
                for line in file:
                    favorites.append(json.loads(line.strip()))
                    #print(favorites)
        except FileNotFoundError:
            print("收藏文件未找到")
        return favorites

    def add_to_favorites(self):
        # 获取当前位置信息
        current_book = self.file_combo.currentText()
        current_document = self.table_widget.currentItem().text()
        current_position = self.get_current_position()
        print(current_position)
        favorite_info = {
            "book": current_book,
            "document": current_document,
            "position": current_position
        }

        # 将收藏信息保存到文件
        '''with open(self.favorites_file, "a") as file:
            file.write(json.dumps(favorite_info) + "\n")'''
        # 将收藏信息作为JSON对象保存
        with open(self.favorites_file, "a") as file:
            json.dump(favorite_info, file)
            file.write("\n")  # 添加换行符以分隔记录

        print("已添加到收藏")
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_button.setText("全屏模式")
        else:
            self.showFullScreen()
            self.fullscreen_button.setText("退出全屏")
    def update_margin(self, value):
        self.margin_label.setText(f"页边距: {value}")
        style_sheet = f"""
        QTextBrowser {{
            padding: {value}px;
        }}
        """
        self.text_browser.setStyleSheet(style_sheet)

    def update_line_spacing(self, value):
        self.line_spacing_label.setText(f"行间距: {value}")
        self.line_spacing = value
        self.render_selected_file()

    # 更新段间距的方法
    def update_paragraph_spacing(self, value):
        self.paragraph_spacing_label.setText(f"段间距: {value}")
        self.paragraph_spacing = value
        self.render_selected_file()
    def toggle_sidebar(self):
        # 检查左边栏当前是否可见
        if self.splitter.sizes()[0] > 0:
            # 隐藏左边栏
            self.splitter.setSizes([0, 1])
            self.toggle_sidebar_button.setText("显示边栏")
        else:
            # 显示左边栏
            #self.splitter.setSizes([1, 1])
            self.splitter.setSizes([int(self.width() * 1 / 12), int(self.width() * 11 / 12)])
            self.toggle_sidebar_button.setText("隐藏边栏")
    def set_eye_protection_mode(self):
        """设置护眼配色模式"""
        self.is_eye_protection_mode_active = True
        style_sheet = """
        QTextBrowser {
            background-color: #DCEBDD;  # 柔和的绿色背景
            color: #1A3D14;            # 深绿色字体
        }
        """
        #self.text_browser.setStyleSheet(style_sheet)
        self.text_browser.setStyleSheet("color: #1A3D14; background-color: #DCEBDD;")
        #self.render_selected_file()


    def select_and_apply_font(self):
        self.font, ok = QFontDialog.getFont()
        if ok:
            self.text_browser.setFont(self.font)
            self.apply_font_size()
    def on_combo_changed(self, index):
        book_name = self.file_combo.currentText()
        # 根据选定的书名来加载和渲染内容
        # 例如，您可以调用一个加载书籍的方法：
        #self.load_and_render_book(book_name)
        self.auto_load_book(book_name)
        self.load_and_render_first_file()
    def open_file(self):

        file_path, _ = QFileDialog.getOpenFileName(self, "选择EPUB文件", "", "EPUB Files (*.epub)")

        if file_path:
            self.file_edit.setText(file_path)
            self.epub_file_path = file_path
            #print(file_path)

        self.unzip_file()

    def unzip_file(self):
        if not self.epub_file_path:
            return

        # 获取 EPUB 文件的基本信息
        epub_file = os.path.basename(self.epub_file_path)
        # 在book下建立的 书名文件夹 如： 白鹿原
        epub_folder = os.path.splitext(epub_file)[0]

        book_path = os.path.join("book", epub_folder)  ##书名目录

        # 检查目标目录是否已存在
        if not os.path.exists(book_path):
            # 创建 book 目录
            if not os.path.exists("book"):
                os.makedirs("book")

            # 复制 EPUB 文件到 book 目录
            shutil.copy2(self.epub_file_path, os.path.join("book", epub_file))

            # 将 EPUB 文件扩展名更改为 .zip
            zip_file = os.path.splitext(epub_file)[0] + ".zip"
            zip_file_path = os.path.join("book", zip_file)
            os.rename(os.path.join("book", epub_file), zip_file_path)

            # 解压缩 EPUB 文件
            with zipfile.ZipFile(zip_file_path, 'r') as epub_zip:
                epub_zip.extractall(book_path)

            # 更新 QTableWidget 中的文件列表
        # 搜索目录并添加到QComboBox中
        folders = self.search_folders_with_html(book_path)
        for folder in folders:
            self.file_combo.addItem(folder)
        self.html_path_name = folders[0]

        self.update_file_list()
        # 渲染 EPUB 文件中的第一个 .xhtml 文件
        self.render_selected_file()

    def search_folders_with_html(self, start_path):
        """搜索包含大于3个.html或.xhtml文件的目录"""
        valid_folders = []

        for root, _, files in os.walk(start_path):
            count = sum(1 for file in files if file.endswith(('.html', '.xhtml')))
            if count > 3:
                valid_folders.append(root)

        return valid_folders

    def render_selected_file(self, item=None):
        if item is None:
            return

        # 获取双击或选中的文件名
        selected_file_name = item.text()
        #print(selected_file_name)
        # 构建文件的完整路径
        epub_file = os.path.basename(self.epub_file_path)
        epub_folder = os.path.splitext(epub_file)[0]

        selected_file_path0 = self.html_path_name + '/' + selected_file_name
        print(self.html_path_name)
        selected_file_path = './' + re.sub(r'\\', '/', selected_file_path0)

        # 获取样式表的完整路径
        stylesheet_path0 = "./book/" + epub_folder + "/EPUB/"
        if os.path.exists(stylesheet_path0):
            stylesheet_path = "./book/" + epub_folder + "/EPUB/stylesheet.css"
            page_styles = "./book/" + epub_folder + "/EPUB/page_styles.css"
        else:
            stylesheet_path = "./book/" + epub_folder + "/stylesheet.css"
            page_styles = "./book/" + epub_folder + "/page_styles.css"
        if os.path.exists(selected_file_path):
            # 读取选定文件的内容
            print(selected_file_path)
            with open(selected_file_path, "r", encoding="utf-8") as file:
                file_content = file.read()
                # 添加 CSS 样式来使图片自适应宽度
                img_style = "<style>img{max-width: 100%; height: auto;}</style>"
                combined_style = f"""
                        <style>
                            img {{
                                max-width: 100%;
                                height: auto;
                            }}
                            p {{
                                line-height: {self.line_spacing}px;
                                margin-bottom: {self.paragraph_spacing}px;
                            }}
                        </style>
                        """

                file_content = combined_style + file_content
                style_tag = f"<style>{stylesheet_path}</style>"
                # 将样式内容添加到HTML头部
                file_content = file_content.replace('href="../../stylesheet.css', f'href="{stylesheet_path}')
                file_content = file_content.replace('href="../../page_styles.css', f'href="{page_styles}')

                # 修复相对图片路径
                image_base_path = os.path.join("book", epub_folder, "EPUB", "images")
                file_content = file_content.replace('src="../images/', f'src="{image_base_path}/')
                # 在右侧渲染修复后的内容
                self.text_browser.setHtml(file_content)

    def update_file_list(self):
        if self.epub_file_path is not None:
            epub_file = os.path.basename(self.epub_file_path)
            # ... 其余代码 ...
        # 更新 QTableWidget 中的文件列表
        if not os.path.exists("book"):
            return

        epub_file = os.path.basename(self.epub_file_path)
        epub_folder = os.path.splitext(epub_file)[0]

        all_files = os.listdir(self.html_path_name)

        xhtml_files = [file for file in all_files if file.endswith('.html') or file.endswith('.xhtml')]
        # 遍历文件列表
        for filename in xhtml_files:
            # 使用正则表达式查找文件名中的单独数字
            new_name = re.sub(r'(?<=[^\d])(\d)(?=[^\d]|$)', '0\g<1>', filename)

            # 如果新旧文件名不同，则重命名文件
            if new_name != filename:
                os.rename(os.path.join(self.html_path_name, filename),
                          os.path.join(self.html_path_name, new_name))
        xhtml_files1 = [file for file in all_files if file.endswith('.html') or file.endswith('.xhtml')]
        self.table_widget.setRowCount(len(xhtml_files1))

        for index, xhtml_file in enumerate(xhtml_files1):
            #self.table_widget.setItem(index, 0, QTableWidgetItem(str(index + 1)))
            self.table_widget.setItem(index, 0, QTableWidgetItem(xhtml_file))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "table_widget") and hasattr(self, "text_browser"):
            # 这里您可以设置您希望的比例
            self.splitter.setSizes([int(self.width() * 1 / 12), int(self.width() * 11 / 12)])
        self.render_selected_file()
        self.update_buttons_on_resize()
        current_width = self.width()
        self.status_bar.showMessage(f"当前窗口宽度：{current_width}")
        super().resizeEvent(event)  # 确保调用基类的 resizeEvent

    def update_buttons_on_resize(self):
        # 设定一个宽度阈值，当窗口宽度小于这个值时，隐藏文字
        width_threshold = 1200  # 可以根据需要调整这个值

        # 获取当前窗口宽度
        current_width = self.width()
        #self.status_bar.showMessage(f"当前窗口宽度：{current_width}")
        # 根据窗口宽度决定是否显示按钮文本
        if current_width < width_threshold:
            # 窗口宽度小于阈值，只显示图标
            self.open_button.setText("")
            self.eye_protection_button.setText("")
            self.toggle_sidebar_button.setText("")
            self.increase_font_button.setText("")
            self.decrease_font_button.setText("")
            self.play_voice_button.setText("")
            self.fullscreen_button.setText("")
            self.stop_button.setText("")
            self.font_button.setText("")
        else:
            # 窗口宽度大于或等于阈值，显示图标和文本
            self.open_button.setText("打开文件")
            self.eye_protection_button.setText("护眼模式")
            self.toggle_sidebar_button.setText("隐藏边栏")
            self.increase_font_button.setText("增大字号")
            self.decrease_font_button.setText("减小字号")
            self.play_voice_button.setText("电子书转音频")
            self.fullscreen_button.setText("全屏模式")
            self.stop_button.setText("停止转音频")
            self.font_button.setText("选择字体")


    def increase_font_size(self):
        """增大字号函数"""
        self.font_size += 1
        self.apply_font_size()
        self.render_selected_file()

    def decrease_font_size(self):
        """减小字号函数"""
        self.font_size -= 1
        self.apply_font_size()
        self.render_selected_file()

    def apply_font_size(self):
        """应用字体大小到 QTextBrowser"""
        #self.text_browser.setStyleSheet(f"font-size: {self.font_size}px;")
        """应用字体大小到 QTextBrowser"""
        font = QFont()
        font.setPointSize(self.font_size)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.text_browser.setFont(self.font)

        self.text_browser.setFont(font)

        # 保持护眼模式的样式
        if self.is_eye_protection_mode_active:
            self.set_eye_protection_mode()
        else:
            # 如果还需要设置额外的样式，可以使用 setStyleSheet
            # 例如，设置字体颜色、对齐方式等
            additional_style = """
                        color: #000000;  # 字体颜色
                        text-align: justify;  # 文字对齐方式
                        """
            self.text_browser.setStyleSheet(additional_style)
        '''additional_style = """
            color: #000000;  # 字体颜色
            text-align: justify;  # 文字对齐方式
            """
        self.text_browser.setStyleSheet(additional_style)'''

    def play_voice(self):
        self.convert_all_to_mp3()


    def convert_all_to_mp3(self):

        self.thread = QThread()  # 创建新线程
        self.worker = AudioConversionWorker(self.html_path_name, self.Voice.currentText(), self.rate, self.volume)
        self.worker.moveToThread(self.thread)  # 将工作类移到新线程

        self.worker.conversion_progress.connect(self.update_progress)  # 连接信号
        self.thread.started.connect(self.worker.run_conversion)  # 启动线程
        self.thread.start()  # 开始线程

    def stop_conversion(self):
        print("停止已点击！")

        if self.thread and self.thread.isRunning():
            self.worker.stop_conversion_flag = True
            self.thread.quit()
            self.thread.wait()

    def update_progress(self, value):
        """更新进度条的值"""
        self.progress_bar.setValue(value)

    def populate_books_combo(self):
        book_dir = os.path.join(script_dir, "book")
        if os.path.exists(book_dir):
            for book_name in os.listdir(book_dir):
                book_path = os.path.join(book_dir, book_name)
                if os.path.isdir(book_path):
                    self.file_combo.addItem(book_name)

            # 如果有书籍，自动加载第一本
            if self.file_combo.count() > 0:
                self.file_combo.setCurrentIndex(0)
                self.auto_load_book(self.file_combo.currentText())
        self.load_and_render_first_file()

    def load_and_render_first_file(self):
        '''if self.table_widget.rowCount() > 0:
            self.render_selected_file(self.table_widget.item(0, 1))'''
        if self.table_widget.rowCount() > 0:
            first_item = self.table_widget.item(0, 0)
            print("渲染文件：", first_item.text())  # 调试信息
            self.render_selected_file(first_item)
    def auto_load_book(self, book_name):
        # 设置 epub 文件路径
        self.epub_file_path = os.path.join(script_dir, "book", book_name)
        #book_path = os.path.join(script_dir, "book", book_name)
        book_path = os.path.relpath(os.path.join(script_dir, "book", book_name), start=os.curdir)
        folders = self.search_folders_with_html(book_path)
        print(folders)
        if folders:
            self.html_path_name = folders[0]
            self.update_file_list()
            self.render_selected_file()

class FavoritesDialog(QDialog):
    # 定义一个信号，传递收藏项的信息
    open_favorite_signal = pyqtSignal(dict)
    def __init__(self, favorites, parent=None):
        super().__init__(parent)
        self.setWindowTitle("收藏列表")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        for favorite in favorites:
            self.list_widget.addItem(f"{favorite['book']} - {favorite['document']} - {favorite['position']}")

        self.open_button = QPushButton("打开选中项")
        self.open_button.clicked.connect(self.open_selected_favorite)
        layout.addWidget(self.open_button)
    def open_selected_favorite(self):
        selected_item = self.list_widget.currentItem()
        if selected_item:
            favorite_info = self.get_favorite_info(selected_item.text())
            self.open_favorite_signal.emit(favorite_info)
            self.hide()  # 隐藏对话框

    def get_favorite_info(self, item_text):
        # 假设 item_text 的格式是 "书名 - 文档名 - 位置"
        parts = item_text.split(" - ")
        if len(parts) == 3:
            return {
                "book": parts[0],
                "document": parts[1],
                "position": parts[2]
            }
        else:
            return {}

class AudioConversionWorker(QObject):
    conversion_progress = pyqtSignal(int)

    def __init__(self, html_folder_path, voice, rate, volume):
        super().__init__()
        self.html_folder_path = html_folder_path
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.stop_conversion_flag = False

    def run_conversion(self):
        # if not self.stop_conversion_flag :
        # html_files = [f for f in os.listdir(self.html_folder_path) if f.endswith(('.html', '.xhtml'))]
        # 和上面这句意思相同
        html_files = []
        for f in os.listdir(self.html_folder_path):
            if f.endswith(('.html', '.xhtml')):
                html_files.append(f)
        total_items = len(html_files)

        for i, file_name in enumerate(html_files):
            if self.stop_conversion_flag:
                print("已停止转换！")
                break

            full_file_path = os.path.join(self.html_folder_path, file_name)
            # path = "D:\\work\\pythonProject\\book\\白鹿原\\OPS"
            parts = full_file_path.split("\\")  # 使用反斜杠分割字符串

            # 找到 'book' 并获取其后的第一个字符串
            if 'book' in parts:
                book_index = parts.index('book')
                if book_index + 1 < len(parts):
                    book_name = parts[book_index + 1]

            parent_directory = os.path.dirname(os.path.dirname(full_file_path))
            # 连接路径和文件夹名
            mp3_folder_path = os.path.join(parent_directory, book_name)
            if not os.path.exists(mp3_folder_path):
                os.makedirs(mp3_folder_path)

            with open(full_file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                # 使用BeautifulSoup提取文本内容
                soup = BeautifulSoup(file_content, 'html.parser')
                text1 = soup.get_text()
                text = text1.encode('utf-8', 'ignore').decode('utf-8')
                # 移除空行和多余的空格
                text = re.sub(r'\s+', ' ', text)
                if text =='' :
                    break


                text_to_convert = text

                base_name = os.path.splitext(file_name)[0]
                # 使用正则表达式提取数字
                numbers = re.findall(r'\d+', base_name)
                numbers_str = ''.join(numbers)
                mp3_output_filename = os.path.join(mp3_folder_path, book_name + '-' + numbers_str + ".mp3")

                asyncio.run(self.save_text_to_mp3(text_to_convert, mp3_output_filename))

            progress = (i + 1) / total_items * 100
            self.conversion_progress.emit(int(progress))

        self.conversion_progress.emit(100)  # 完成

    async def save_text_to_mp3(self, text, output_filename):
        """使用edge_tts将文本转换为mp3并保存"""
        self.tts = edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate, volume=self.volume)
        await self.tts.save(output_filename)


def main():
    app = QApplication(sys.argv)
    window = EpubReader()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
