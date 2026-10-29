import sys
import os
import json
import xml.etree.ElementTree as ET
import logging
from logging.handlers import RotatingFileHandler
import datetime

# 初始化日志记录器
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_filename = os.path.join(LOG_DIR, f"mindnexus_{datetime.datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_filename, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox, 
                                 QMenuBar, QColorDialog, QDialog, QVBoxLayout, QHBoxLayout, 
                                 QLabel, QLineEdit, QPushButton, QFormLayout, QProgressDialog, QComboBox)
from PySide6.QtGui import QAction, QPageSize, QPainter, QImage, QIcon, QPageLayout
from PySide6.QtCore import QSizeF, Qt, QRectF, QMarginsF, QThread, Signal, QEvent
from PySide6.QtPrintSupport import QPrinter
from view import MindMapView
from models import NodeModel
from template_data import TEMPLATE_LIST, get_templates
from import_engine import extract_mindmap_from_image, extract_mindmap_from_pdf, extract_mindmap_from_text

def get_resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和 PyInstaller 打包环境"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

SETTINGS_FILE = "settings.json"

def load_settings():
    default_settings = {
        "api_key": "",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-2.5-pro",
        "last_dir": ""
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    default_settings.update(data)
                return default_settings
        except:
            pass
    return default_settings

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("大模型 API 设置")
        self.setMinimumWidth(400)
        
        self.settings = load_settings()
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.api_key_input = QLineEdit(self.settings.get("api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.base_url_input = QLineEdit(self.settings.get("base_url", "https://generativelanguage.googleapis.com/v1beta/openai/"))
        
        self.model_input = QComboBox()
        self.model_input.setEditable(True)
        self.model_input.addItems([
            "gemini-2.5-flash", 
            "gemini-2.5-flash-lite",
            "gemini-3-flash", 
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-robotics-er-1.6-preview"
        ])
        self.model_input.setCurrentText(self.settings.get("model", "gemini-2.5-flash"))
        
        form_layout.addRow("API Key:", self.api_key_input)
        form_layout.addRow("Base URL:", self.base_url_input)
        form_layout.addRow("模型名称:", self.model_input)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def get_settings(self):
        new_settings = dict(self.settings)
        new_settings["api_key"] = self.api_key_input.text().strip()
        new_settings["base_url"] = self.base_url_input.text().strip()
        new_settings["model"] = self.model_input.currentText().strip()
        return new_settings

class ImportWorker(QThread):
    finished_signal = Signal(dict)
    error_signal = Signal(str)
    
    def __init__(self, file_path, import_type, settings):
        super().__init__()
        self.file_path = file_path
        self.import_type = import_type
        self.settings = settings
        
    def run(self):
        try:
            if self.import_type == "image":
                data = extract_mindmap_from_image(
                    self.file_path, 
                    self.settings["api_key"], 
                    self.settings["base_url"], 
                    self.settings["model"]
                )
            elif self.import_type == "text":
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                data = extract_mindmap_from_text(
                    text_content, 
                    self.settings["api_key"], 
                    self.settings["base_url"], 
                    self.settings["model"]
                )
            else:
                data = extract_mindmap_from_pdf(
                    self.file_path, 
                    self.settings["api_key"], 
                    self.settings["base_url"], 
                    self.settings["model"]
                )
            self.finished_signal.emit(data)
        except Exception as e:
            self.error_signal.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mind Nexus 思维导图 v2.0.1")
        app_icon = QIcon()
        for icon_name in ["logo.ico", "logo.png"]:
            icon_path = get_resource_path(icon_name)
            if os.path.exists(icon_path):
                app_icon.addFile(icon_path)
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
        self.resize(1000, 700)
        
        self.settings = load_settings()
        self.mindmap_view = MindMapView(self)
        self.setCentralWidget(self.mindmap_view)
        
        self.current_filepath = None
        self.is_modified = False
        self.mindmap_view.data_modified.connect(self.set_modified)
        
        self.setAcceptDrops(True)
        self.mindmap_view.setAcceptDrops(True)
        self.mindmap_view.viewport().setAcceptDrops(True)
        self.mindmap_view.installEventFilter(self)
        self.mindmap_view.viewport().installEventFilter(self)
        
        self._create_menu()
        
    def get_last_dir(self):
        last_dir = self.settings.get("last_dir", "")
        if last_dir and os.path.isdir(last_dir):
            return last_dir
        if self.current_filepath and os.path.isdir(os.path.dirname(self.current_filepath)):
            return os.path.dirname(self.current_filepath)
        user_home = os.path.expanduser("~")
        if os.path.isdir(user_home):
            return user_home
        return os.path.abspath(os.path.dirname(__file__))

    def update_last_dir(self, filepath):
        if not filepath:
            return
        if os.path.isdir(filepath):
            dir_path = filepath
        else:
            dir_path = os.path.dirname(os.path.abspath(filepath))
            
        if os.path.isdir(dir_path):
            self.settings["last_dir"] = dir_path
            save_settings(self.settings)

    def _classify_file(self, filepath):
        if not filepath:
            return "unknown"
        _, ext = os.path.splitext(filepath.lower())
        image_exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        pdf_exts = {".pdf"}
        text_exts = {
            ".txt", ".md", ".py", ".c", ".cpp", ".cc", ".h", ".hpp",
            ".html", ".htm", ".css", ".js", ".ts", ".jsx", ".tsx",
            ".yaml", ".yml", ".xml", ".ini", ".conf", ".sql", ".sh",
            ".bat", ".java", ".go", ".rs", ".csv", ".log"
        }
        if ext == ".mnx":
            return "mnx"
        elif ext == ".json":
            return "json"
        elif ext in image_exts:
            return "image"
        elif ext in pdf_exts:
            return "pdf"
        elif ext in text_exts:
            return "text"
        return "unknown"
        
    def set_modified(self):
        if not self.is_modified:
            self.is_modified = True
            self.setWindowTitle(self.windowTitle() + " *")
        
    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        
        new_action = QAction("新建", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        import_image_action = QAction("导入图片 (AI)...", self)
        import_image_action.triggered.connect(self.import_image)
        file_menu.addAction(import_image_action)
        
        import_pdf_action = QAction("导入 PDF (AI)...", self)
        import_pdf_action.triggered.connect(self.import_pdf)
        file_menu.addAction(import_pdf_action)
        
        import_text_action = QAction("导入文本 (AI)...", self)
        import_text_action.triggered.connect(self.import_text)
        file_menu.addAction(import_text_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("设置 API...", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_file)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 新建模板菜单
        template_menu = menubar.addMenu("模板")
        
        new_template_menu = template_menu.addMenu("从模板新建...")
        
        for text, key in TEMPLATE_LIST:
            sub_menu = new_template_menu.addMenu(text)
            
            action_h = QAction("从左到右", self)
            action_h.triggered.connect(lambda checked=False, k=key: self.load_template(k, "horizontal"))
            sub_menu.addAction(action_h)
            
            action_v = QAction("从上而下", self)
            action_v.triggered.connect(lambda checked=False, k=key: self.load_template(k, "vertical"))
            sub_menu.addAction(action_v)
            
        template_menu.addSeparator()
        
        change_template_menu = template_menu.addMenu("当前样式改为模板...")
        
        for text, key in TEMPLATE_LIST:
            sub_menu = change_template_menu.addMenu(text)
            
            action_h = QAction("从左到右", self)
            action_h.triggered.connect(lambda checked=False, k=key: self.mindmap_view.apply_template_style(k, "horizontal"))
            sub_menu.addAction(action_h)
            
            action_v = QAction("从上而下", self)
            action_v.triggered.connect(lambda checked=False, k=key: self.mindmap_view.apply_template_style(k, "vertical"))
            sub_menu.addAction(action_v)
            
        # 字体菜单
        from PySide6.QtWidgets import QFontDialog
        from PySide6.QtGui import QFont
        font_menu = menubar.addMenu("字体")
        
        def apply_preset_font(family):
            font = QFont(family, self.mindmap_view.current_font.pointSize())
            font.setBold(self.mindmap_view.current_font.bold())
            font.setItalic(self.mindmap_view.current_font.italic())
            self.mindmap_view.set_font(font)
            
        preset_fonts = [
            ("微软雅黑 (默认)", "Microsoft YaHei"),
            ("宋体", "SimSun"),
            ("黑体", "SimHei"),
            ("楷体", "KaiTi"),
            ("Arial", "Arial")
        ]
        
        for name, family in preset_fonts:
            action = QAction(name, self)
            action.triggered.connect(lambda checked=False, f=family: apply_preset_font(f))
            font_menu.addAction(action)
            
        font_menu.addSeparator()
        
        def set_font():
            ok, font = QFontDialog.getFont(self.mindmap_view.current_font, self, "选择自定义字体")
            if ok:
                self.mindmap_view.set_font(font)
                
        font_action = QAction("自定义...", self)
        font_action.triggered.connect(set_font)
        font_menu.addAction(font_action)
        
        # 关联线颜色菜单
        relation_color_menu = menubar.addMenu("连线颜色")
        
        def set_relation_color(color):
            self.mindmap_view.current_relation_color = color
            self.mindmap_view.change_selected_relation_color(color)
            
        color_black = QAction("黑色 (默认)", self)
        color_black.triggered.connect(lambda: set_relation_color("#000000"))
        relation_color_menu.addAction(color_black)
            
        color_yellow = QAction("黄色", self)
        color_yellow.triggered.connect(lambda: set_relation_color("#eab308"))
        relation_color_menu.addAction(color_yellow)
        
        color_red = QAction("红色", self)
        color_red.triggered.connect(lambda: set_relation_color("#ef4444"))
        relation_color_menu.addAction(color_red)
        
        color_blue = QAction("蓝色", self)
        color_blue.triggered.connect(lambda: set_relation_color("#3b82f6"))
        relation_color_menu.addAction(color_blue)
        
        color_green = QAction("绿色", self)
        color_green.triggered.connect(lambda: set_relation_color("#22c55e"))
        relation_color_menu.addAction(color_green)
        
        relation_color_menu.addSeparator()
        
        def custom_color():
            color = QColorDialog.getColor(initial=self.mindmap_view.current_relation_color, parent=self, title="选择关联线颜色")
            if color.isValid():
                set_relation_color(color.name())
                
        color_custom = QAction("自定义...", self)
        color_custom.triggered.connect(custom_color)
        relation_color_menu.addAction(color_custom)
        
        # 连线风格菜单
        relation_style_menu = menubar.addMenu("连线风格")
        
        def set_relation_style(style):
            self.mindmap_view.current_relation_style = style
            self.mindmap_view.change_selected_relation_style(style)
            
        style_solid = QAction("实线", self)
        style_solid.triggered.connect(lambda: set_relation_style("solid"))
        relation_style_menu.addAction(style_solid)
        
        style_dashed = QAction("虚线 (默认)", self)
        style_dashed.triggered.connect(lambda: set_relation_style("dashed"))
        relation_style_menu.addAction(style_dashed)
        
        relation_style_menu.addSeparator()
        
        def set_relation_width(w):
            self.mindmap_view.current_relation_width = w
            self.mindmap_view.change_selected_relation_width(w)
            
        width_thin = QAction("细 (1px - 默认)", self)
        width_thin.triggered.connect(lambda: set_relation_width(1))
        relation_style_menu.addAction(width_thin)
        
        width_medium = QAction("中 (3px)", self)
        width_medium.triggered.connect(lambda: set_relation_width(3))
        relation_style_menu.addAction(width_medium)
        
        width_thick = QAction("粗 (5px)", self)
        width_thick.triggered.connect(lambda: set_relation_width(5))
        relation_style_menu.addAction(width_thick)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
    def show_about_dialog(self):
        about_text = (
            "<h2>Mind Nexus</h2>"
            "<p><b>版本：</b> 2.0.1</p>"
            "<p><b>核心功能：</b></p>"
            "<ul>"
            "<li>支持从图片、PDF文档以及纯文本智能（AI）一键生成思维导图</li>"
            "<li>支持新建多种模板的思维导图及排版样式调整</li>"
            "<li>丰富的自定义功能（字体、连线颜色、连线粗细等）</li>"
            "<li>一键导出为 PDF、PNG、JPG 格式的高清图片</li>"
            "</ul>"
            "<p>感谢您的使用！</p>"
        )
        QMessageBox.about(self, "关于 Mind Nexus", about_text)
        
    def load_template(self, template_name, layout_direction="horizontal"):
        templates = get_templates()
        
        if template_name in templates:
            data = templates[template_name]
            # Ensure style dictionary exists
            if "style" not in data:
                data["style"] = {}
            # Apply the selected layout direction
            data["style"]["layout"] = layout_direction
            
            root_model = NodeModel.from_dict(data)
            self.mindmap_view.load_from_model(root_model)
            self.current_filepath = None
            
            # Format window title
            direction_text = "从左到右" if layout_direction == "horizontal" else "从上而下"
            self.setWindowTitle(f"Mind Nexus v2.0.1 - 新建思维导图 ({data['text']}模板 - {direction_text})")
            self.is_modified = False

    def new_file(self):
        data = {
            "text": "中心主题",
            "children": []
        }
        root_model = NodeModel.from_dict(data)
        self.mindmap_view.load_from_model(root_model)
        self.current_filepath = None
        self.setWindowTitle("Mind Nexus v2.0.1 - 新建思维导图")
        self.is_modified = False

    def load_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.mindmap_view.clear_all()
            if isinstance(data, list):
                for item in data:
                    root_model = NodeModel.from_dict(item)
                    pos_x = item.get("_pos", {}).get("x", 0)
                    pos_y = item.get("_pos", {}).get("y", 0)
                    self.mindmap_view.add_root_model(root_model, pos_x, pos_y)
            else:
                root_model = NodeModel.from_dict(data)
                self.mindmap_view.add_root_model(root_model, 0, 0)
                
            self.mindmap_view.update_layout()
            self.current_filepath = filepath
            self.update_last_dir(filepath)
            self.setWindowTitle(f"Mind Nexus v2.0.1 - {filepath}")
            self.is_modified = False
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败:\n{e}")

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "打开文件", self.get_last_dir(), "Mind Nexus 文件 (*.mnx);;JSON 文件 (*.json)"
        )
        if not filepath: return
        self.update_last_dir(filepath)
        self.load_file(filepath)
            
    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            save_settings(new_settings)
            self.settings = load_settings()
            QMessageBox.information(self, "提示", "设置已保存")
            
    def check_api_key(self):
        self.settings = load_settings()
        if not self.settings.get("api_key"):
            QMessageBox.warning(self, "提示", "请先在“文件”->“设置 API...”中配置大模型 API Key。")
            self.open_settings()
            self.settings = load_settings()
            if not self.settings.get("api_key"):
                return False
        return True
        
    def import_image(self):
        if not self.check_api_key(): return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入图片", self.get_last_dir(), "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not filepath: return
        self.update_last_dir(filepath)
        self._start_import_worker(filepath, "image")
        
    def import_pdf(self):
        if not self.check_api_key(): return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入 PDF", self.get_last_dir(), "PDF 文件 (*.pdf)"
        )
        if not filepath: return
        self.update_last_dir(filepath)
        self._start_import_worker(filepath, "pdf")
        
    def import_text(self):
        if not self.check_api_key(): return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入文本", self.get_last_dir(), 
            "文本文件 (*.txt *.md *.json *.py *.c *.cpp *.h *.html *.css *.js *.yaml *.yml *.ini *.conf)"
        )
        if not filepath: return
        self.update_last_dir(filepath)
        self._start_import_worker(filepath, "text")
        
    def _start_import_worker(self, filepath, import_type):
        self.progress_dialog = QProgressDialog("正在请求 AI 分析文档，请稍候...", "取消", 0, 0, self)
        self.progress_dialog.setWindowTitle("AI 导入")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
        self.settings = load_settings()
        self.import_worker = ImportWorker(filepath, import_type, self.settings)
        self.import_worker.finished_signal.connect(self._on_import_finished)
        self.import_worker.error_signal.connect(self._on_import_error)
        self.progress_dialog.canceled.connect(self.import_worker.terminate)
        self.import_worker.start()
        
    def _on_import_finished(self, data):
        self.progress_dialog.close()
        try:
            self.mindmap_view.clear_all()
            root_model = NodeModel.from_dict(data)
            self.mindmap_view.add_root_model(root_model, 0, 0)
            self.mindmap_view.update_layout()
            self.current_filepath = None
            self.setWindowTitle("Mind Nexus v2.0.1 - 新建思维导图 (AI 导入)")
            self.is_modified = True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解析导入的数据失败:\n{e}")
            
    def _on_import_error(self, error_msg):
        self.progress_dialog.close()
        QMessageBox.critical(self, "导入失败", f"AI 处理失败:\n{error_msg}")
        
    def save_file(self):
        if self.current_filepath:
            self._save_to(self.current_filepath, ".mnx")
        else:
            self.save_as_file()
            
    def save_as_file(self):
        default_dir = self.get_last_dir()
        if self.current_filepath:
            default_path = self.current_filepath
        else:
            default_path = os.path.join(default_dir, "思维导图.mnx")
            
        filepath, filter_str = QFileDialog.getSaveFileName(
            self, "另存为", default_path, 
            "Mind Nexus 文件 (*.mnx);;JSON 文件 (*.json);;XML 文件 (*.xml);;Markdown 文件 (*.md)"
        )
        if not filepath: return
        
        if "(*.mnx)" in filter_str:
            ext = ".mnx"
            self.current_filepath = filepath
            self.setWindowTitle(f"Mind Nexus v2.0.1 - {filepath}")
        elif "(*.json)" in filter_str:
            ext = ".json"
        elif "(*.xml)" in filter_str:
            ext = ".xml"
        elif "(*.md)" in filter_str:
            ext = ".md"
        else:
            ext = ".mnx"
            
        if not filepath.endswith(ext):
            filepath += ext
            
        self.update_last_dir(filepath)
        self._save_to(filepath, ext)
        
    def _save_to(self, filepath, ext):
        try:
            root_nodes = [node for node in self.mindmap_view.nodes if node.model.parent is None]
            if ext in [".mnx", ".json"]:
                data = []
                for node in root_nodes:
                    node_data = node.model.to_dict()
                    node_data["_pos"] = {"x": node.pos().x(), "y": node.pos().y()}
                    data.append(node_data)
                        
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif ext == ".xml":
                root_elem = ET.Element("Mindmap")
                for node in root_nodes:
                    root_elem.append(node.model.to_xml())
                tree = ET.ElementTree(root_elem)
                ET.indent(tree, space="  ", level=0)
                tree.write(filepath, encoding='utf-8', xml_declaration=True)
            elif ext == ".md":
                md_lines = []
                for node in root_nodes:
                    md_lines.extend(node.model.to_markdown())
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("\n".join(md_lines))
                    
            self.update_last_dir(filepath)
            QMessageBox.information(self, "成功", f"文件已保存至：\n{filepath}")
            self.is_modified = False
            title = self.windowTitle()
            if title.endswith(" *"):
                self.setWindowTitle(title[:-2])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败:\n{e}")
            
    def export_file(self):
        scene = self.mindmap_view.scene
        if not scene.items():
            QMessageBox.warning(self, "警告", "当前画布为空，无法导出。")
            return
            
        from PySide6.QtWidgets import QInputDialog
        formats = ["PNG 图片 (*.png)", "JPG 图片 (*.jpg)", "PDF 文件 (*.pdf)"]
        format_str, ok = QInputDialog.getItem(self, "选择导出格式", "请选择你要导出的格式:", formats, 2, False)
        if not ok or not format_str:
            return
            
        default_path = os.path.join(self.get_last_dir(), "未命名")
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出", default_path, format_str
        )
        if not filepath: return
        self.update_last_dir(filepath)
        
        rect = scene.itemsBoundingRect()
        margin = 50
        rect.adjust(-margin, -margin, margin, margin)
        
        try:
            if "(*.pdf)" in format_str:
                if not filepath.endswith(".pdf"): filepath += ".pdf"
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filepath)
                
                size = QSizeF(rect.width(), rect.height())
                page_size = QPageSize(size, QPageSize.Point)
                printer.setPageSize(page_size)
                printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Point)
                
                painter = QPainter(printer)
                painter.setRenderHint(QPainter.Antialiasing)
                
                target_rect = QRectF(printer.pageLayout().paintRectPixels(printer.resolution()))
                scene.render(painter, target=target_rect, source=rect)
                painter.end()
            else:
                is_png = "(*.png)" in format_str
                if is_png and not filepath.endswith(".png"): filepath += ".png"
                if not is_png and not filepath.endswith(".jpg"): filepath += ".jpg"
                
                image = QImage(int(rect.width()), int(rect.height()), QImage.Format_ARGB32)
                
                if is_png:
                    image.fill(Qt.transparent)
                else:
                    image.fill(Qt.white)
                    
                painter = QPainter(image)
                painter.setRenderHint(QPainter.Antialiasing)
                
                target_rect = QRectF(0, 0, image.width(), image.height())
                scene.render(painter, target=target_rect, source=rect)
                painter.end()
                
                image.save(filepath)
                
            QMessageBox.information(self, "成功", f"导出成功：\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败:\n{e}")

    def eventFilter(self, watched, event):
        if watched in (self.mindmap_view, self.mindmap_view.viewport()):
            if event.type() == QEvent.DragEnter:
                self.dragEnterEvent(event)
                return event.isAccepted()
            elif event.type() == QEvent.DragMove:
                self.dragMoveEvent(event)
                return event.isAccepted()
            elif event.type() == QEvent.Drop:
                self.dropEvent(event)
                return event.isAccepted()
        return super().eventFilter(watched, event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                filepath = urls[0].toLocalFile()
                if filepath:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                filepath = urls[0].toLocalFile()
                if filepath:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if filepath:
                event.acceptProposedAction()
                self.handle_dropped_file(filepath)
                return
        event.ignore()

    def handle_dropped_file(self, filepath):
        if not filepath or not os.path.isfile(filepath):
            return
            
        category = self._classify_file(filepath)
        
        # 1. 检查当前导图是否有未保存修改
        if self.is_modified:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('保存更改')
            msg_box.setText('当前思维导图已修改，是否在载入新文件前先保存？')
            msg_box.setIcon(QMessageBox.Question)
            
            save_btn = msg_box.addButton('保存', QMessageBox.AcceptRole)
            discard_btn = msg_box.addButton('不保存', QMessageBox.DestructiveRole)
            cancel_btn = msg_box.addButton('取消', QMessageBox.RejectRole)
            
            msg_box.exec()
            
            if msg_box.clickedButton() == save_btn:
                self.save_file()
                if self.is_modified:
                    return
            elif msg_box.clickedButton() == cancel_btn:
                return

        # 2. 根据识别类型自动分流
        if category == "mnx":
            self.load_file(filepath)
        elif category == "json":
            is_native_map = False
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content_json = json.load(f)
                if isinstance(content_json, dict) and ("children" in content_json or "text" in content_json):
                    is_native_map = True
                elif isinstance(content_json, list) and len(content_json) > 0 and isinstance(content_json[0], dict) and ("children" in content_json[0] or "text" in content_json[0]):
                    is_native_map = True
            except Exception:
                pass
                
            if is_native_map:
                self.load_file(filepath)
            else:
                if not self.check_api_key(): return
                self.update_last_dir(filepath)
                self._start_import_worker(filepath, "text")
        elif category == "image":
            if not self.check_api_key(): return
            self.update_last_dir(filepath)
            self._start_import_worker(filepath, "image")
        elif category == "pdf":
            if not self.check_api_key(): return
            self.update_last_dir(filepath)
            self._start_import_worker(filepath, "pdf")
        elif category == "text":
            if not self.check_api_key(): return
            self.update_last_dir(filepath)
            self._start_import_worker(filepath, "text")
        else:
            # 探测未知后缀文件是否为文本
            is_text = False
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    f.read(1024)
                is_text = True
            except Exception:
                pass
                
            if is_text:
                if not self.check_api_key(): return
                self.update_last_dir(filepath)
                self._start_import_worker(filepath, "text")
            else:
                QMessageBox.warning(
                    self,
                    "不支持的文件格式",
                    f"未能自动识别该文件类型：\n{os.path.basename(filepath)}\n\n支持拖入的文件包括：\n- 思维导图工程文件 (*.mnx, *.json)\n- 图像文件 (*.png, *.jpg, *.jpeg, *.bmp, *.webp)\n- 便携文档 (*.pdf)\n- 纯文本与源码文件 (*.txt, *.md, *.py 等)"
                )

    def closeEvent(self, event):
        if self.is_modified:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('保存更改')
            msg_box.setText('文件已修改，退出前要保存吗？')
            msg_box.setIcon(QMessageBox.Question)
            
            save_btn = msg_box.addButton('保存', QMessageBox.AcceptRole)
            discard_btn = msg_box.addButton('不保存', QMessageBox.DestructiveRole)
            cancel_btn = msg_box.addButton('取消', QMessageBox.RejectRole)
            
            msg_box.exec()
            
            if msg_box.clickedButton() == save_btn:
                self.save_file()
                if self.is_modified:
                    event.ignore()
                else:
                    event.accept()
            elif msg_box.clickedButton() == discard_btn:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MindNexus.SmartMindMap.Platform.v2")
        except Exception:
            pass

    app = QApplication(sys.argv)
    
    app_icon = QIcon()
    for icon_name in ["logo.ico", "logo.png"]:
        icon_path = get_resource_path(icon_name)
        if os.path.exists(icon_path):
            app_icon.addFile(icon_path)
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f2f5;
        }
    """)
    
    logging.info("MindNexus Application Started")
    window = MainWindow()
    window.show()
    exit_code = app.exec()
    logging.info(f"MindNexus Application Exited with code {exit_code}")
    sys.exit(exit_code)
