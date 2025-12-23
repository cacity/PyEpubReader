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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer, QUrl
from PyQt6.QtGui import QIcon, QFont, QFontDatabase, QTextCursor, QTextBlockFormat, QFontMetrics
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

        self.import_font_button = QPushButton("导入字体", self)
        self.import_font_button.clicked.connect(self.import_font)
        self.import_font_button.setIcon(QIcon("./icon/icons8-opened-folder-240.png"))
        hbox1.addWidget(self.import_font_button)

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
        self.margin_value = initial_margin

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
        self.last_state_file = os.path.join(script_dir, "book", "last_state.json")
        self.settings_file = os.path.join(script_dir, "book", "reader_settings.json")
        self.fonts_dir = os.path.join(script_dir, "book", "fonts")
        self.imported_font_files = []

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
        self.table_widget.verticalHeader().setVisible(False)
        ####
        self.table_widget.setHorizontalHeaderLabels([ "章节"])
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

        # 设置 QTextBrowser 的字体
        self.font = QFont("Microsoft YaHei", 14)
        self.text_browser.setFont(self.font)

        self.is_eye_protection_mode_active = False
        self.load_settings()
        self.apply_font_size()
        self.apply_text_browser_style()

        # 自动搜索并添加书籍到下拉列表
        self.populate_books_combo()

    def apply_text_browser_style(self):
        background = "#DCEBDD" if self.is_eye_protection_mode_active else "#FFFFFF"
        foreground = "#1A3D14" if self.is_eye_protection_mode_active else "#000000"
        self.text_browser.setStyleSheet(
            f"QTextBrowser {{ padding: {self.margin_value}px; background-color: {background}; color: {foreground}; }}"
        )

    def closeEvent(self, event):
        self.save_last_state()
        self.save_settings()
        super().closeEvent(event)

    def load_settings(self):
        try:
            if not os.path.exists(self.settings_file):
                return
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f) or {}

            self.margin_value = int(data.get("margin_value", self.margin_value))
            self.line_spacing = int(data.get("line_spacing", self.line_spacing))
            self.paragraph_spacing = int(data.get("paragraph_spacing", self.paragraph_spacing))
            self.is_eye_protection_mode_active = bool(data.get("eye_protection", self.is_eye_protection_mode_active))

            font_size = data.get("font_size")
            if isinstance(font_size, int) and font_size > 0:
                self.font_size = font_size

            imported = data.get("imported_fonts") or []
            if isinstance(imported, list):
                self.imported_font_files = [str(p) for p in imported if p]

            for rel_path in self.imported_font_files:
                abs_path = os.path.join(script_dir, rel_path)
                if os.path.exists(abs_path):
                    QFontDatabase.addApplicationFont(abs_path)

            font_family = data.get("font_family")
            if isinstance(font_family, str) and font_family.strip():
                self.font = QFont(font_family.strip())

            self.margin_slider.setValue(self.margin_value)
            self.line_spacing_slider.setValue(self.line_spacing)
            self.paragraph_spacing_slider.setValue(self.paragraph_spacing)
        except Exception:
            return

    def save_settings(self):
        try:
            book_dir = os.path.join(script_dir, "book")
            if not os.path.exists(book_dir):
                os.makedirs(book_dir)

            data = {
                "margin_value": int(self.margin_value),
                "line_spacing": int(self.line_spacing),
                "paragraph_spacing": int(self.paragraph_spacing),
                "eye_protection": bool(self.is_eye_protection_mode_active),
                "font_family": self.font.family() if hasattr(self, "font") else "",
                "font_size": int(self.font_size),
                "imported_fonts": list(self.imported_font_files),
            }
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def save_last_state(self):
        try:
            if not os.path.exists(os.path.join(script_dir, "book")):
                os.makedirs(os.path.join(script_dir, "book"))

            book = self.file_combo.currentText().strip() if self.file_combo.currentText() else ""
            document_item = self.table_widget.currentItem()
            document = document_item.text().strip() if document_item else ""
            position = int(self.get_current_position())

            if not book:
                return

            state = {"book": book, "document": document, "position": position}
            with open(self.last_state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False)
        except Exception:
            # 关闭时不打断退出流程
            pass

    def load_last_state(self):
        try:
            if not os.path.exists(self.last_state_file):
                return None
            with open(self.last_state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def restore_last_state(self):
        state = self.load_last_state()
        if not state:
            return False

        book = (state.get("book") or "").strip()
        document = (state.get("document") or "").strip()
        position = state.get("position")
        try:
            position = int(position)
        except Exception:
            position = 0

        if not book:
            return False

        index = self.file_combo.findText(book)
        if index < 0:
            return False

        old_block = self.file_combo.blockSignals(True)
        try:
            self.file_combo.setCurrentIndex(index)
        finally:
            self.file_combo.blockSignals(old_block)

        self.auto_load_book(book)

        target_item = None
        if document:
            for row in range(self.table_widget.rowCount()):
                item = self.table_widget.item(row, 0)
                if item and item.text() == document:
                    target_item = item
                    self.table_widget.setCurrentCell(row, 0)
                    self.table_widget.selectRow(row)
                    break

        if target_item is None:
            self.load_and_render_first_file()
            target_item = self.table_widget.currentItem() or (self.table_widget.item(0, 0) if self.table_widget.rowCount() > 0 else None)
        else:
            self.render_selected_file(target_item)

        if target_item is None:
            return True

        def apply_scroll():
            scrollbar = self.text_browser.verticalScrollBar()
            scrollbar.setValue(position)

        QTimer.singleShot(0, apply_scroll)
        QTimer.singleShot(100, apply_scroll)
        return True

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
        self.margin_value = value
        self.apply_text_browser_style()

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
        ll = len(self.toggle_sidebar_button.text())
        if self.splitter.sizes()[0] > 0:
            # 隐藏左边栏
            self.splitter.setSizes([0, 1])

            print(ll)
            if ll > 1 :
                self.toggle_sidebar_button.setText("显示边栏")
            if ll == 0:
                self.toggle_sidebar_button.setText("")
        else:
            # 显示左边栏
            #self.splitter.setSizes([1, 1])
            self.splitter.setSizes([int(self.width() * 1 / 12), int(self.width() * 11 / 12)])
            if ll > 1:
                self.toggle_sidebar_button.setText("隐藏边栏")
            if ll == 0:
                self.toggle_sidebar_button.setText("")
    def set_eye_protection_mode(self):
        """设置护眼配色模式"""
        self.is_eye_protection_mode_active = True
        self.apply_text_browser_style()
        #self.render_selected_file()


    def select_and_apply_font(self):
        self.font, ok = QFontDialog.getFont(self.text_browser.font(), self)
        if ok:
            if self.font.pointSize() and self.font.pointSize() > 0:
                self.font_size = self.font.pointSize()
            self.apply_font_size()
            self.render_selected_file()

    def import_font(self):
        font_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入字体文件",
            "",
            "Font Files (*.ttf *.otf *.ttc);;All Files (*)",
        )
        if not font_path:
            return

        try:
            os.makedirs(self.fonts_dir, exist_ok=True)
            font_filename = os.path.basename(font_path)
            target_path = os.path.join(self.fonts_dir, font_filename)
            if not os.path.exists(target_path):
                shutil.copy2(font_path, target_path)

            font_id = QFontDatabase.addApplicationFont(target_path)
            if font_id < 0:
                self.status_bar.showMessage("字体导入失败：不支持的字体文件")
                return

            families = QFontDatabase.applicationFontFamilies(font_id)
            if not families:
                self.status_bar.showMessage("字体导入失败：未识别到字体族名")
                return

            rel_path = os.path.relpath(target_path, start=script_dir)
            if rel_path not in self.imported_font_files:
                self.imported_font_files.append(rel_path)

            self.font = QFont(families[0])
            self.apply_font_size()
            self.render_selected_file()
            self.status_bar.showMessage(f"已导入字体：{families[0]}")
        except Exception:
            self.status_bar.showMessage("字体导入失败")
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

        # 创建 book/书名 目录（不存在则创建）
        if not os.path.exists("book"):
            os.makedirs("book")

        # 如果书籍目录不存在或为空，则从epub直接解压（epub本质是zip）
        needs_extract = (not os.path.exists(book_path)) or (os.path.isdir(book_path) and not os.listdir(book_path))
        if needs_extract:
            os.makedirs(book_path, exist_ok=True)
            with zipfile.ZipFile(self.epub_file_path, 'r') as epub_zip:
                epub_zip.extractall(book_path)

        # 后续渲染统一使用解压目录作为“书籍路径”
        self.epub_file_path = os.path.join("book", epub_folder)

        # 将“书名目录”加入书籍下拉框（避免混入html子目录路径）
        old_block = self.file_combo.blockSignals(True)
        try:
            if self.file_combo.findText(epub_folder) < 0:
                self.file_combo.addItem(epub_folder)
            self.file_combo.setCurrentText(epub_folder)
        finally:
            self.file_combo.blockSignals(old_block)

        # 搜索包含html/xhtml的目录并渲染
        folders = self.search_folders_with_html(book_path)
        if not folders:
            self.status_bar.showMessage("未找到可渲染的章节目录（html/xhtml文件不足）")
            return
        self.html_path_name = folders[0]

        self.update_file_list()
        self.load_and_render_first_file()

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
            item = self.table_widget.currentItem()
            if item is None and self.table_widget.rowCount() > 0:
                item = self.table_widget.item(0, 0)
            if item is None:
                return

        # 获取双击或选中的文件名
        selected_file_name = item.text()
        #print(selected_file_name)
        # 构建文件的完整路径
        epub_file = os.path.basename(self.epub_file_path)
        epub_folder = os.path.splitext(epub_file)[0]

        selected_file_path = os.path.join(self.html_path_name, selected_file_name)
        if not os.path.exists(selected_file_path):
            return

        html_base_dir = os.path.dirname(os.path.abspath(selected_file_path))
        self.text_browser.document().setBaseUrl(QUrl.fromLocalFile(html_base_dir + os.sep))

        # 读取选定文件的内容
        with open(selected_file_path, "r", encoding="utf-8-sig") as file:
            file_content = file.read()

        soup = BeautifulSoup(file_content, "html.parser")

        # Qt 的 QTextBrowser 不会加载 <link rel="stylesheet"> 的外部CSS：这里把它们读入并内联到 <style>
        css_chunks = []
        for link in soup.find_all("link"):
            rel = link.get("rel") or []
            rel_values = [v.lower() for v in (rel if isinstance(rel, list) else [rel])]
            if "stylesheet" not in rel_values:
                continue
            href = link.get("href")
            if not href:
                continue
            css_path = os.path.normpath(os.path.join(html_base_dir, href))
            if os.path.exists(css_path):
                try:
                    with open(css_path, "r", encoding="utf-8-sig") as css_file:
                        css_chunks.append(css_file.read())
                except Exception:
                    pass
            link.decompose()

        # 兜底样式（图片自适应）
        css_chunks.append(
            f"""
            img {{ max-width: 100%; height: auto; }}
            """
        )

        # 强制覆盖书籍自带 font-family，确保“选择字体/导入字体”可见
        selected_family = self.text_browser.font().family()
        if selected_family:
            safe_family = selected_family.replace("\\", "\\\\").replace("\"", "\\\"")
            css_chunks.append(f'body, div, p, span {{ font-family: "{safe_family}" !important; }}')

        head = soup.head
        if head is None:
            head = soup.new_tag("head")
            if soup.html:
                soup.html.insert(0, head)
            else:
                soup.insert(0, head)

        existing_style = head.find("style", attrs={"id": "pye-reader-style"})
        if existing_style:
            existing_style.string = "\n".join(css_chunks)
        else:
            style_tag = soup.new_tag("style", id="pye-reader-style")
            style_tag.string = "\n".join(css_chunks)
            head.append(style_tag)

        self.text_browser.setHtml(str(soup))
        self.text_browser.document().setDefaultFont(self.text_browser.font())
        self.apply_document_formatting()

    def apply_document_formatting(self):
        doc = self.text_browser.document()
        cursor = QTextCursor(doc)
        cursor.beginEditBlock()

        metrics = QFontMetrics(self.text_browser.font())
        min_line_height = metrics.lineSpacing()
        line_height = max(min_line_height, int(self.line_spacing))
        indent_px = metrics.horizontalAdvance("中") * 2

        block = doc.firstBlock()
        while block.isValid():
            text = block.text()
            if text.strip():
                cursor.setPosition(block.position())
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)

                fmt = cursor.blockFormat()
                fmt.setBottomMargin(float(self.paragraph_spacing))
                fmt.setLineHeight(float(line_height), int(QTextBlockFormat.LineHeightTypes.FixedHeight.value))
                if fmt.alignment() & Qt.AlignmentFlag.AlignHCenter:
                    fmt.setTextIndent(0.0)
                else:
                    fmt.setTextIndent(float(indent_px))

                cursor.setBlockFormat(fmt)
            block = block.next()

        cursor.endEditBlock()

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
            new_name = re.sub(r'(?<=[^\d])(\d)(?=[^\d]|$)', r'0\g<1>', filename)

            # 如果新旧文件名不同，则重命名文件
            if new_name != filename:
                os.rename(os.path.join(self.html_path_name, filename),
                          os.path.join(self.html_path_name, new_name))
        all_files = os.listdir(self.html_path_name)
        xhtml_files1 = [file for file in all_files if file.endswith('.html') or file.endswith('.xhtml')]
        xhtml_files1.sort()
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
            self.import_font_button.setText("")
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
            self.import_font_button.setText("导入字体")


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
        font = QFont(self.font)
        font.setPointSize(self.font_size)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.text_browser.setFont(font)

        # 保持护眼/页边距等样式
        self.apply_text_browser_style()
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
        if not os.path.exists(book_dir):
            return

        book_names = set()
        for entry in os.listdir(book_dir):
            full_path = os.path.join(book_dir, entry)
            if os.path.isdir(full_path):
                book_names.add(entry)
                continue

            entry_lower = entry.lower()
            if entry_lower.endswith((".epub", ".zip")):
                book_names.add(os.path.splitext(entry)[0])

        old_block = self.file_combo.blockSignals(True)
        try:
            self.file_combo.clear()
            for name in sorted(book_names):
                self.file_combo.addItem(name)
        finally:
            self.file_combo.blockSignals(old_block)

        if self.file_combo.count() > 0:
            if not self.restore_last_state():
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
        book_dir = os.path.join(script_dir, "book")
        extracted_dir = os.path.join(book_dir, book_name)
        extracted_rel = os.path.join("book", book_name)

        # 如果未解压（或目录为空），尝试从 book/<书名>.epub 或 book/<书名>.zip 解压
        needs_extract = (not os.path.exists(extracted_dir)) or (os.path.isdir(extracted_dir) and not os.listdir(extracted_dir))
        if needs_extract:
            source_path = None
            for ext in (".epub", ".zip"):
                candidate = os.path.join(book_dir, f"{book_name}{ext}")
                if os.path.exists(candidate):
                    source_path = candidate
                    break

            if not source_path:
                self.status_bar.showMessage(f"未找到书籍：{book_name}（缺少解压目录或同名 .epub/.zip）")
                return

            os.makedirs(extracted_dir, exist_ok=True)
            with zipfile.ZipFile(source_path, 'r') as epub_zip:
                epub_zip.extractall(extracted_dir)

        self.epub_file_path = extracted_rel
        folders = self.search_folders_with_html(extracted_rel)
        if not folders:
            self.status_bar.showMessage("未找到可渲染的章节目录（html/xhtml文件不足）")
            return

        self.html_path_name = folders[0]
        self.update_file_list()

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
