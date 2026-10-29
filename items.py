from PySide6.QtWidgets import QGraphicsObject, QGraphicsTextItem, QGraphicsPathItem, QGraphicsEllipseItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QPolygonF
from PySide6.QtCore import Qt, QRectF, QPointF
import math

class EditableTextItem(QGraphicsTextItem):
    def __init__(self, text, node_item):
        super().__init__(text, node_item)
        self.node_item = node_item
        self.document().setDocumentMargin(0)
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        if self.textInteractionFlags() == Qt.TextEditorInteraction:
            self.setTextInteractionFlags(Qt.NoTextInteraction)
            new_text = self.toPlainText().strip()
            if not new_text:
                new_text = "新节点"
            if self.node_item:
                self.node_item.update_text(new_text)

class NodeItem(QGraphicsObject):
    def get_theme(self):
        m = self.model
        while m.parent:
            m = m.parent
        return m.style or {}

    def __init__(self, model, view=None):
        super().__init__()
        self.model = model
        self.view = view
        self.edge_items = []
        self.parent_edge = None
        self.relation_edges_out = []
        self.relation_edges_in = []
        
        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemIsMovable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        
        theme = self.get_theme()
        self.natural_width = 120
        self.natural_height = 40
        self.width = 120
        self.height = 40
        self.radius = theme.get("radius", 8)
        
        # Text item
        self.text_item = EditableTextItem(self.model.text, self)
        
        base_font = self.view.current_font if self.view and hasattr(self.view, 'current_font') else QFont("Microsoft YaHei", 10)
        font = QFont(base_font)
        
        if "font_family" in theme:
            font.setFamily(theme["font_family"])
        if "font_size" in theme:
            font.setPointSize(theme["font_size"])
            
        if self.model.is_root():
            if theme.get("root_font_weight") == "bold":
                font.setBold(True)
            if "root_font_size" in theme:
                font.setPointSize(theme["root_font_size"])
        else:
            if theme.get("font_weight") == "bold":
                font.setBold(True)
                
        self.text_item.setFont(font)
        
        text_color = theme.get("root_text_color", theme.get("text_color", "#323232")) if self.model.is_root() else theme.get("text_color", "#323232")
        self.text_item.setDefaultTextColor(QColor(text_color))
        
        doc_width = self.text_item.boundingRect().width()
        doc_height = self.text_item.boundingRect().height()
        self.natural_width = max(120, doc_width + 30)
        self.natural_height = max(40, doc_height + 20)
        self.width = self.natural_width
        self.height = self.natural_height
        
        # Adjust text position
        self._update_text_pos()
        self.text_item.setTextInteractionFlags(Qt.NoTextInteraction)
        
        # Connection points
        self.edge_items = [] # edges where this node is parent
        self.parent_edge = None # edge where this node is child
        
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
        
    def paint(self, painter, option, widget=None):
        rect = self.boundingRect()
        theme = self.get_theme()
        
        # Draw background
        node_bg = theme.get("node_bg", "#fafafa")
        node_border = theme.get("node_border", "#c8c8c8")
        root_bg = theme.get("root_bg", "#dcebff")
        root_border = theme.get("root_border", "#96b4dc")
        
        if self.model.is_root():
            base_bg = root_bg
            base_border = root_border
        else:
            level = self.model.get_level() - 1
            if isinstance(node_bg, list):
                base_bg = node_bg[min(level, len(node_bg) - 1)]
            else:
                base_bg = node_bg
                
            if isinstance(node_border, list):
                base_border = node_border[min(level, len(node_border) - 1)]
            else:
                base_border = node_border

        if self.isSelected():
            pen = QPen(QColor(64, 158, 255), 3)  # 加粗且醒目的蓝色边框表示选中
            brush = QBrush(QColor(base_bg))      # 保留原有背景色，防止白色文字不可见
        else:
            pen = QPen(QColor(base_border), 1)
            brush = QBrush(QColor(base_bg))
                
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRoundedRect(rect, self.radius, self.radius)
        
    def _update_text_pos(self):
        # 居左排版文本
        doc_rect = self.text_item.boundingRect()
        x = 15  # 左侧边距
        y = (self.height - doc_rect.height()) / 2
        self.text_item.setPos(x, y)
        
    def update_text(self, new_text):
        if self.model.text != new_text:
            if self.view and hasattr(self.view, 'push_undo_state'):
                self.view.push_undo_state()
        
        self.model.text = new_text
        self.text_item.setPlainText(new_text)
        self.text_item.document().setDocumentMargin(0)
        
        # Auto resize width based on text
        doc_width = self.text_item.boundingRect().width()
        doc_height = self.text_item.boundingRect().height()
        new_width = max(120, doc_width + 30)
        new_height = max(40, doc_height + 20)
        self.natural_width = new_width
        self.natural_height = new_height
        
        if new_width != self.width or new_height != self.height:
            self.prepareGeometryChange()
            self.width = new_width
            self.height = new_height
            
        self._update_text_pos()
        self.update()
        if self.view:
            self.view.update_layout()
            
    def update_size_for_font(self):
        doc_width = self.text_item.boundingRect().width()
        doc_height = self.text_item.boundingRect().height()
        new_width = max(120, doc_width + 30)
        new_height = max(40, doc_height + 20)
        self.natural_width = new_width
        self.natural_height = new_height
        
        if new_width != self.width or new_height != self.height:
            self.prepareGeometryChange()
            self.width = new_width
            self.height = new_height
            
        self._update_text_pos()
        self.update()
        if self.view:
            self.view.update_layout()
            
    def start_editing(self):
        self.text_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.text_item.setFocus()
        cursor = self.text_item.textCursor()
        from PySide6.QtGui import QTextCursor
        cursor.select(QTextCursor.SelectionType.Document)
        self.text_item.setTextCursor(cursor)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        self.start_editing()
        
    def itemChange(self, change, value):
        if change == QGraphicsObject.ItemPositionHasChanged:
            # Update connected edges
            if self.parent_edge:
                self.parent_edge.update_path()
            for edge in self.edge_items:
                edge.update_path()
            for edge in self.relation_edges_out:
                edge.update_path()
            for edge in self.relation_edges_in:
                edge.update_path()
        return super().itemChange(change, value)
        
    def mousePressEvent(self, event):
        self._drag_start_pos = self.pos()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.flags() & QGraphicsObject.ItemIsMovable:
            delta = event.scenePos() - event.lastScenePos()
            super().mouseMoveEvent(event)
            
            # 将拖拽位移同步到所有子节点，使整棵子树跟随移动
            def move_children(node):
                if not node.view: return
                children = [n for n in node.view.nodes if n.model.parent == node.model]
                for child in children:
                    child.setPos(child.pos() + delta)
                    move_children(child)
                    
            move_children(self)
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if hasattr(self, '_drag_start_pos') and self.pos() != self._drag_start_pos:
            # 如果是根节点被移动了，保存撤销状态，以便保存新的坐标
            if self.model.parent is None and self.view:
                self.view.push_undo_state()
        
    def right_center(self):
        pos = self.scenePos()
        return QPointF(pos.x() + self.width, pos.y() + self.height / 2)
        
    def left_center(self):
        pos = self.scenePos()
        return QPointF(pos.x(), pos.y() + self.height / 2)

    def top_center(self):
        pos = self.scenePos()
        return QPointF(pos.x() + self.width / 2, pos.y())

    def bottom_center(self):
        pos = self.scenePos()
        return QPointF(pos.x() + self.width / 2, pos.y() + self.height)


class EdgeItem(QGraphicsPathItem):
    def __init__(self, parent_node, child_node):
        super().__init__()
        self.parent_node = parent_node
        self.child_node = child_node
        
        self.parent_node.edge_items.append(self)
        self.child_node.parent_edge = self
        
        theme = parent_node.get_theme()
        edge_color = theme.get("edge_color", "#969696")
        edge_width = theme.get("edge_width", 2)
        
        # Appearance
        pen = QPen(QColor(edge_color), edge_width)
        pen.setStyle(Qt.SolidLine)
        self.setPen(pen)
        self.setZValue(-1) # Behind nodes
        
        self.update_path()
        
    def update_path(self):
        theme = self.parent_node.get_theme()
        is_vertical = theme.get("layout") == "vertical"
        
        path = QPainterPath()
        
        if is_vertical:
            start_pt = self.parent_node.bottom_center()
            end_pt = self.child_node.top_center()
            path.moveTo(start_pt)
            ctrl1 = QPointF(start_pt.x(), start_pt.y() + 30)
            ctrl2 = QPointF(end_pt.x(), end_pt.y() - 30)
        else:
            start_pt = self.parent_node.right_center()
            end_pt = self.child_node.left_center()
            path.moveTo(start_pt)
            ctrl1 = QPointF(start_pt.x() + 40, start_pt.y())
            ctrl2 = QPointF(end_pt.x() - 40, end_pt.y())
            
        path.cubicTo(ctrl1, ctrl2, end_pt)
        self.setPath(path)

class ControlHandleItem(QGraphicsEllipseItem):
    def __init__(self, edge_item, is_ctrl1):
        super().__init__(-6, -6, 12, 12)
        self.edge_item = edge_item
        self.is_ctrl1 = is_ctrl1
        self.setBrush(QBrush(QColor("#3b82f6")))
        self.setPen(QPen(Qt.white, 2))
        self.setZValue(10)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.edge_item.update_from_handle(self.is_ctrl1, self.pos())
        return super().itemChange(change, value)
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.edge_item.on_handle_released()

class RelationEdgeItem(QGraphicsPathItem):
    def __init__(self, start_node, end_node, color="#000000", ctrl1_offset=None, ctrl2_offset=None, line_style="dashed", line_width=1):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node
        self.color = color
        self.ctrl1_offset = ctrl1_offset
        self.ctrl2_offset = ctrl2_offset
        self.line_style = line_style
        self.line_width = line_width
        self.setZValue(-2) # 在节点和普通连线之下
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        
        self.pen = QPen(QColor(self.color))
        self.pen.setWidth(self.line_width)
        # self.pen.setStyle(Qt.DashLine) # 可选为虚线，实线更好看
        
        self.arrow_head = QPolygonF()
        self.update_path()
        
    def set_color(self, color):
        self.color = color
        self.update_path()
        self.update()
        
    def set_line_style(self, style):
        self.line_style = style
        self.update_path()
        self.update()
        
    def set_line_width(self, width):
        self.line_width = width
        self.update_path()
        self.update()
        
    def update_handles_visibility(self):
        if self.isSelected():
            if not hasattr(self, 'handle1'):
                self.handle1 = ControlHandleItem(self, True)
                self.handle2 = ControlHandleItem(self, False)
                if self.scene():
                    self.scene().addItem(self.handle1)
                    self.scene().addItem(self.handle2)
        else:
            if hasattr(self, 'handle1'):
                if self.handle1.scene():
                    self.handle1.scene().removeItem(self.handle1)
                if self.handle2.scene():
                    self.handle2.scene().removeItem(self.handle2)
                del self.handle1
                del self.handle2
                
    def update_from_handle(self, is_ctrl1, pos):
        self._updating_from_handle = True
        if is_ctrl1:
            start_pt = self.start_node.sceneBoundingRect().center()
            self.ctrl1_offset = {"dx": pos.x() - start_pt.x(), "dy": pos.y() - start_pt.y()}
        else:
            end_pt = self.end_node.sceneBoundingRect().center()
            self.ctrl2_offset = {"dx": pos.x() - end_pt.x(), "dy": pos.y() - end_pt.y()}
        self.update_path()
        self.update()
        self._updating_from_handle = False
        
    def on_handle_released(self):
        if hasattr(self.start_node, 'view') and self.start_node.view:
            self.start_node.view.update_relation_model(self)
            self.start_node.view.push_undo_state()
            
    def itemChange(self, change, value):
        if change == QGraphicsPathItem.ItemSelectedHasChanged:
            self.update_handles_visibility()
            self.update_path()
            self.update()
        elif change == QGraphicsPathItem.ItemSceneHasChanged:
            if not self.scene() and hasattr(self, 'handle1'):
                if self.handle1.scene():
                    self.handle1.scene().removeItem(self.handle1)
                if self.handle2.scene():
                    self.handle2.scene().removeItem(self.handle2)
                del self.handle1
                del self.handle2
        return super().itemChange(change, value)
        
    def update_path(self):
        start_pt = self.start_node.sceneBoundingRect().center()
        end_pt = self.end_node.sceneBoundingRect().center()
        
        if self.ctrl1_offset is None:
            c1x = start_pt.x() + (end_pt.x() - start_pt.x()) / 3
            c1y = start_pt.y() + (end_pt.y() - start_pt.y()) / 3
        else:
            c1x = start_pt.x() + self.ctrl1_offset.get("dx", 0)
            c1y = start_pt.y() + self.ctrl1_offset.get("dy", 0)
            
        if self.ctrl2_offset is None:
            c2x = start_pt.x() + (end_pt.x() - start_pt.x()) * 2 / 3
            c2y = start_pt.y() + (end_pt.y() - start_pt.y()) * 2 / 3
        else:
            c2x = end_pt.x() + self.ctrl2_offset.get("dx", 0)
            c2y = end_pt.y() + self.ctrl2_offset.get("dy", 0)
            
        self.ctrl1_pos = QPointF(c1x, c1y)
        self.ctrl2_pos = QPointF(c2x, c2y)
        
        path = QPainterPath()
        path.moveTo(start_pt)
        path.cubicTo(self.ctrl1_pos, self.ctrl2_pos, end_pt)
        self.setPath(path)
        
        if self.isSelected():
            self.pen.setWidth(self.line_width + 2)
            self.pen.setColor(QColor("#3b82f6")) # 蓝色高亮表示选中
            if hasattr(self, 'handle1') and self.handle1.scene() and not getattr(self, '_updating_from_handle', False):
                self.handle1.setPos(self.ctrl1_pos)
                self.handle2.setPos(self.ctrl2_pos)
        else:
            self.pen.setWidth(self.line_width)
            self.pen.setColor(QColor(self.color))
            
        if self.line_style == "dashed":
            self.pen.setStyle(Qt.DashLine)
        else:
            self.pen.setStyle(Qt.SolidLine)
            
        self.setPen(self.pen)
        
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        
        start_pt = self.start_node.sceneBoundingRect().center()
        end_pt = self.end_node.sceneBoundingRect().center()
        
        if self.isSelected():
            painter.setPen(QPen(QColor("#3b82f6"), 1, Qt.DashLine))
            painter.drawLine(start_pt, self.ctrl1_pos)
            painter.drawLine(end_pt, self.ctrl2_pos)
            
        dx = end_pt.x() - self.ctrl2_pos.x()
        dy = end_pt.y() - self.ctrl2_pos.y()
        
        if dx == 0 and dy == 0:
            dx = end_pt.x() - start_pt.x()
            dy = end_pt.y() - start_pt.y()
            
        angle = math.atan2(dy, dx)
        
        tangent_len = math.hypot(dx, dy)
        if tangent_len > 0:
            arrow_pt = QPointF(end_pt.x() - (dx/tangent_len)*60, end_pt.y() - (dy/tangent_len)*60)
        else:
            arrow_pt = end_pt
            
        arrow_size = 12
        p1 = arrow_pt - QPointF(math.cos(angle - math.pi/6) * arrow_size, math.sin(angle - math.pi/6) * arrow_size)
        p2 = arrow_pt - QPointF(math.cos(angle + math.pi/6) * arrow_size, math.sin(angle + math.pi/6) * arrow_size)
        
        self.arrow_head.clear()
        self.arrow_head.append(arrow_pt)
        self.arrow_head.append(p1)
        self.arrow_head.append(p2)
        
        if self.isSelected():
            painter.setBrush(QBrush(QColor("#3b82f6")))
        else:
            painter.setBrush(QBrush(QColor(self.color)))
            
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(self.arrow_head)
