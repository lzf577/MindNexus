from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QShortcut, QKeySequence
from models import NodeModel
from items import NodeItem, EdgeItem, EditableTextItem

class MindMapView(QGraphicsView):
    data_modified = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # 赋予一个极大的场景范围，以便通过修改滚动条来实现无限制拖拽
        self.setSceneRect(-10000, -10000, 20000, 20000)
        
        self.nodes = [] # List of NodeItems
        self.edges = []
        self.relation_edges = []
        
        self.undo_stack = [] # Stack for undo states
        
        self.root_item = None
        self._dragging = False
        self._last_mouse_pos = None
        
        self.current_relation_color = "#000000" # Default black
        self.current_relation_style = "dashed"
        self.current_relation_width = 1
        self._drawing_relation_start_node = None
        self._temp_relation_line = None
        
        from PySide6.QtGui import QFont
        self.current_font = QFont("Microsoft YaHei", 10)
        
        self.init_center_node()
        self.setup_shortcuts()
        
    def set_font(self, font):
        self.push_undo_state()
        self.current_font = font
        for node in self.nodes:
            node.text_item.setFont(font)
            node.update_size_for_font()
        self.update_layout()

    def setup_shortcuts(self):
        self.shortcut_tab = QShortcut(QKeySequence(Qt.Key_Tab), self)
        self.shortcut_tab.setContext(Qt.WindowShortcut)
        self.shortcut_tab.activated.connect(self.handle_tab)
        
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.shortcut_enter.setContext(Qt.WindowShortcut)
        self.shortcut_enter.activated.connect(self.handle_enter)
        
        self.shortcut_enter2 = QShortcut(QKeySequence(Qt.Key_Enter), self)
        self.shortcut_enter2.setContext(Qt.WindowShortcut)
        self.shortcut_enter2.activated.connect(self.handle_enter)
        
        self.shortcut_esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.shortcut_esc.setContext(Qt.WindowShortcut)
        self.shortcut_esc.activated.connect(self.handle_escape)

        self.shortcut_copy = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_C), self)
        self.shortcut_copy.setContext(Qt.WindowShortcut)
        self.shortcut_copy.activated.connect(self.handle_copy)

        self.shortcut_cut = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_X), self)
        self.shortcut_cut.setContext(Qt.WindowShortcut)
        self.shortcut_cut.activated.connect(self.handle_cut)

        self.shortcut_paste = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_V), self)
        self.shortcut_paste.setContext(Qt.WindowShortcut)
        self.shortcut_paste.activated.connect(self.handle_paste)

        self.shortcut_undo = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_Z), self)
        self.shortcut_undo.setContext(Qt.WindowShortcut)
        self.shortcut_undo.activated.connect(self.handle_undo)

        self.shortcut_select_all = QShortcut(QKeySequence(Qt.CTRL | Qt.Key_A), self)
        self.shortcut_select_all.setContext(Qt.WindowShortcut)
        self.shortcut_select_all.activated.connect(self.handle_select_all)

    def get_editing_item(self):
        for node in self.nodes:
            if node.text_item.hasFocus():
                return node
        return None

    def push_undo_state(self):
        self.data_modified.emit()
        # 记录所有根节点的状态以及它们的位置
        state = []
        for node in self.nodes:
            if node.model.parent is None:
                node_data = node.model.to_dict()
                node_data["_pos"] = {"x": node.pos().x(), "y": node.pos().y()}
                state.append(node_data)
        self.undo_stack.append(state)
        if len(self.undo_stack) > 50: # Limit stack size
            self.undo_stack.pop(0)

    def handle_select_all(self):
        if self.get_editing_item():
            return
            
        for node in self.nodes:
            node.setSelected(True)

    def handle_undo(self):
        # Do not undo if user is currently editing text
        if self.get_editing_item():
            return
            
        if not self.undo_stack:
            return
            
        previous_state = self.undo_stack.pop()
        from models import NodeModel
        
        self.clear_all()
        # previous_state is a list of root node dicts
        for data in previous_state:
            old_model = NodeModel.from_dict(data)
            pos_x = data.get("_pos", {}).get("x", 0)
            pos_y = data.get("_pos", {}).get("y", 0)
            self.add_root_model(old_model, pos_x, pos_y)
            
        self.draw_relations()
        self.update_layout()

    def handle_copy(self):
        # Do not copy node if user is currently editing text (let text copy happen)
        if self.get_editing_item():
            return
            
        selected_nodes = [n for n in self.nodes if n.isSelected()]
        if not selected_nodes:
            return
            
        import json
        from PySide6.QtWidgets import QApplication
        
        node_item = selected_nodes[0]
        data = node_item.model.to_dict()
        clipboard = QApplication.clipboard()
        clipboard.setText(json.dumps(data))

    def handle_cut(self):
        # Do not cut node if user is currently editing text (let text cut happen)
        if self.get_editing_item():
            return
            
        selected_nodes = [n for n in self.nodes if n.isSelected()]
        if not selected_nodes:
            return
            
        node_item = selected_nodes[0]
        if node_item == self.root_item or node_item.model.parent is None:
            # 根节点不允许剪切删除
            return
            
        import json
        from PySide6.QtWidgets import QApplication
        
        # 将选中节点及其子树导出为结构化数据并写入系统剪贴板
        data = node_item.model.to_dict()
        clipboard = QApplication.clipboard()
        clipboard.setText(json.dumps(data))
        
        # 记录父节点引用，便于后续焦点智能聚焦
        parent_model = node_item.model.parent
        parent_ui = next((n for n in self.nodes if n.model == parent_model), None)
        
        # 压入撤销历史栈并从画布与模型拓扑中安全移除
        self.push_undo_state()
        self.delete_node(node_item, skip_undo=True)
        self.data_modified.emit()
        
        # 自动选中父节点，便于用户立即按Ctrl+V转移黏贴至新分支
        if parent_ui and parent_ui in self.nodes:
            self.scene.clearSelection()
            parent_ui.setSelected(True)

    def handle_paste(self):
        # Do not paste node if user is currently editing text (let text paste happen)
        if self.get_editing_item():
            return
            
        from PySide6.QtWidgets import QApplication
        import json
        
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            return
            
        data = None
        try:
            parsed_data = json.loads(text)
            if isinstance(parsed_data, dict) and ("text" in parsed_data or "id" in parsed_data):
                data = parsed_data
        except Exception:
            pass
            
        selected_nodes = [n for n in self.nodes if n.isSelected()]
        parent_item = selected_nodes[0] if selected_nodes else self.root_item
        
        if data is None:
            self.push_undo_state()
            self.add_node(parent_item, text=text, skip_undo=True)
            return
            
        self.push_undo_state()
        
        from models import NodeModel
        
        # We need to assign new UUIDs to the pasted models so they don't conflict
        def recreate_model(data, parent):
            new_node = NodeModel(text=data.get("text", "新节点"), parent=parent)
            new_node.style = data.get("style", {})
            for child_data in data.get("children", []):
                recreate_model(child_data, new_node)
            return new_node
            
        new_model = recreate_model(data, parent_item.model)
        
        # Build UI tree for the pasted model
        def build_ui_tree(model, parent_ui):
            ui_node = NodeItem(model, self)
            self.scene.addItem(ui_node)
            self.nodes.append(ui_node)
            
            edge = EdgeItem(parent_ui, ui_node)
            self.scene.addItem(edge)
            self.edges.append(edge)
            
            # Temporary position
            ui_node.setPos(parent_ui.pos().x() + 150, parent_ui.pos().y())
            
            for child_model in model.children:
                build_ui_tree(child_model, ui_node)
                
            return ui_node
            
        new_root_ui = build_ui_tree(new_model, parent_item)
        
        self.update_layout()
        self.scene.clearSelection()
        new_root_ui.setSelected(True)

    def handle_tab(self):
        editing_item = self.get_editing_item()
        selected_nodes = [n for n in self.nodes if n.isSelected()]
        
        if editing_item:
            editing_item.text_item.clearFocus()
            self.setFocus()
            self.add_node(editing_item)
        elif selected_nodes:
            self.add_node(selected_nodes[0])

    def handle_enter(self):
        editing_item = self.get_editing_item()
        selected_nodes = [n for n in self.nodes if n.isSelected()]
        
        current_item = None
        if editing_item:
            editing_item.text_item.clearFocus()
            self.setFocus()
            current_item = editing_item
        elif selected_nodes:
            current_item = selected_nodes[0]
            
        if current_item and current_item != self.root_item:
            parent_item = next(n for n in self.nodes if n.model == current_item.model.parent)
            self.add_node(parent_item)

    def handle_escape(self):
        editing_item = self.get_editing_item()
        if editing_item:
            editing_item.text_item.clearFocus()
            self.setFocus()
            editing_item.setSelected(True)

    def init_center_node(self):
        model = NodeModel("中心主题")
        self.root_item = NodeItem(model, self)
        self.scene.addItem(self.root_item)
        self.nodes.append(self.root_item)
        
        # Center in scene
        self.root_item.setPos(0, 0)
        self.root_item.setSelected(True)
        self.update_layout()
        
    def clear_all(self):
        self.scene.clear()
        self.nodes.clear()
        self.edges.clear()
        self.relation_edges.clear()
        self.root_item = None
        
    def add_root_model(self, root_model, x=0, y=0):
        root_item = NodeItem(root_model, self)
        self.scene.addItem(root_item)
        self.nodes.append(root_item)
        root_item.setPos(x, y)
        
        # 默认将第一个添加的根节点作为 self.root_item（为了兼容原有部分逻辑）
        if self.root_item is None:
            self.root_item = root_item
            
        def build_ui_tree(parent_item):
            for child_model in parent_item.model.children:
                child_item = NodeItem(child_model, self)
                self.scene.addItem(child_item)
                self.nodes.append(child_item)
                
                edge = EdgeItem(parent_item, child_item)
                self.scene.addItem(edge)
                self.edges.append(edge)
                
                build_ui_tree(child_item)
                
        build_ui_tree(root_item)
        return root_item

    def load_from_model(self, root_model):
        self.clear_all()
        root_item = self.add_root_model(root_model, 0, 0)
        root_item.setSelected(True)
        self.draw_relations()
        self.update_layout()
        
    def add_floating_node(self, scene_pos):
        self.push_undo_state()
        from models import NodeModel
        
        # 创建新的独立根节点
        new_model = NodeModel("新节点", parent=None)
        # 尝试继承当前主根节点的样式
        if self.root_item:
            new_model.style = dict(self.root_item.model.style)
            
        new_item = self.add_root_model(new_model, scene_pos.x(), scene_pos.y())
        new_item.setPos(scene_pos.x() - new_item.width / 2, scene_pos.y() - new_item.height / 2)
        
        self.scene.clearSelection()
        new_item.setSelected(True)
        new_item.start_editing()
        self.update_layout()
        
    def update_relation_model(self, rel_edge):
        start_node = rel_edge.start_node
        end_node = rel_edge.end_node
        
        for idx, relation in enumerate(start_node.model.relations):
            target_id = relation if isinstance(relation, str) else relation.get("target")
            if target_id == end_node.model.id:
                if isinstance(relation, str):
                    relation = {"target": target_id, "color": rel_edge.color}
                    start_node.model.relations[idx] = relation
                    
                relation["ctrl1_offset"] = rel_edge.ctrl1_offset
                relation["ctrl2_offset"] = rel_edge.ctrl2_offset
                relation["style"] = rel_edge.line_style
                relation["width"] = rel_edge.line_width
                break
                
    def change_selected_relation_style(self, style):
        from items import RelationEdgeItem
        selected_relations = [item for item in self.scene.selectedItems() if isinstance(item, RelationEdgeItem)]
        if not selected_relations: return
        self.push_undo_state()
        for item in selected_relations:
            item.set_line_style(style)
            self.update_relation_model(item)
            
    def change_selected_relation_width(self, width):
        from items import RelationEdgeItem
        selected_relations = [item for item in self.scene.selectedItems() if isinstance(item, RelationEdgeItem)]
        if not selected_relations: return
        self.push_undo_state()
        for item in selected_relations:
            item.set_line_width(width)
            self.update_relation_model(item)
                
    def change_selected_relation_color(self, color):
        from items import RelationEdgeItem
        selected_relations = [item for item in self.scene.selectedItems() if isinstance(item, RelationEdgeItem)]
        if not selected_relations:
            return
            
        self.push_undo_state()
        
        for item in selected_relations:
            item.set_color(color)
            
            # Update model
            start_node = item.start_node
            end_node = item.end_node
            
            for idx, relation in enumerate(start_node.model.relations):
                target_id = relation if isinstance(relation, str) else relation.get("target")
                if target_id == end_node.model.id:
                    if isinstance(relation, str):
                        start_node.model.relations[idx] = {"target": target_id, "color": color}
                    else:
                        relation["color"] = color
                    break
        
    def draw_relations(self):
        for edge in self.relation_edges:
            if edge.scene() == self.scene:
                self.scene.removeItem(edge)
        self.relation_edges.clear()
        for node in self.nodes:
            node.relation_edges_out.clear()
            node.relation_edges_in.clear()
            
        from items import RelationEdgeItem
        for node in self.nodes:
            for relation in node.model.relations:
                target_id = relation if isinstance(relation, str) else relation.get("target")
                color = "#000000" if isinstance(relation, str) else relation.get("color", "#000000")
                ctrl1_offset = None if isinstance(relation, str) else relation.get("ctrl1_offset")
                ctrl2_offset = None if isinstance(relation, str) else relation.get("ctrl2_offset")
                line_style = "solid" if isinstance(relation, str) else relation.get("style", "solid")
                line_width = 3 if isinstance(relation, str) else relation.get("width", 3)
                
                target_node = next((n for n in self.nodes if n.model.id == target_id), None)
                if target_node:
                    rel_edge = RelationEdgeItem(
                        node, target_node, 
                        color=color, 
                        ctrl1_offset=ctrl1_offset, 
                        ctrl2_offset=ctrl2_offset,
                        line_style=line_style,
                        line_width=line_width
                    )
                    self.scene.addItem(rel_edge)
                    self.relation_edges.append(rel_edge)
                    node.relation_edges_out.append(rel_edge)
                    target_node.relation_edges_in.append(rel_edge)
        
    def focusNextPrevChild(self, next):
        # Prevent Qt from intercepting Tab key for focus switching
        return False
        
    def add_node(self, parent_item, text="新节点", skip_undo=False):
        if not skip_undo:
            self.push_undo_state()
            
        new_model = NodeModel(text, parent_item.model)
        new_item = NodeItem(new_model, self)
        self.scene.addItem(new_item)
        self.nodes.append(new_item)
        
        edge = EdgeItem(parent_item, new_item)
        self.scene.addItem(edge)
        self.edges.append(edge)
        
        # Initial position near parent
        new_item.setPos(parent_item.pos().x() + 150, parent_item.pos().y())
        
        self.update_layout()
        
        # Select newly created node
        self.scene.clearSelection()
        new_item.setSelected(True)
        
    def delete_node(self, node_item, skip_undo=False):
        if node_item == self.root_item:
            return # Can't delete root
            
        if not skip_undo:
            self.push_undo_state()
            
        # Delete children recursively
        children_items = [n for n in self.nodes if n.model.parent == node_item.model]
        for child in children_items:
            self.delete_node(child, skip_undo=True)
            
        # Remove edges
        if node_item.parent_edge:
            self.scene.removeItem(node_item.parent_edge)
            if node_item.parent_edge in self.edges:
                self.edges.remove(node_item.parent_edge)
                
        # Remove from parent's edges list
        parent_item = next((n for n in self.nodes if n.model == node_item.model.parent), None)
        if parent_item and node_item.parent_edge in parent_item.edge_items:
            parent_item.edge_items.remove(node_item.parent_edge)
            
        # Remove node
        node_item.model.remove_from_parent()
        self.scene.removeItem(node_item)
        self.nodes.remove(node_item)
        
        self.update_layout()
        
    def keyPressEvent(self, event):
        selected_nodes = [n for n in self.nodes if n.isSelected()]
        
        is_editing = self.get_editing_item() is not None
            
        # If currently editing, let the text item handle all other keys
        if is_editing:
            super().keyPressEvent(event)
            return
            
        # Handle Delete/Backspace (delete node or relation)
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            from items import RelationEdgeItem
            selected_relations = [item for item in self.scene.selectedItems() if isinstance(item, RelationEdgeItem)]
            
            if selected_nodes or selected_relations:
                self.push_undo_state()
                
                for rel in selected_relations:
                    self.scene.removeItem(rel)
                    if rel in self.relation_edges:
                        self.relation_edges.remove(rel)
                    if rel in rel.start_node.relation_edges_out:
                        rel.start_node.relation_edges_out.remove(rel)
                    if rel in rel.end_node.relation_edges_in:
                        rel.end_node.relation_edges_in.remove(rel)
                        
                    for idx, relation in enumerate(rel.start_node.model.relations):
                        target_id = relation if isinstance(relation, str) else relation.get("target")
                        if target_id == rel.end_node.model.id:
                            del rel.start_node.model.relations[idx]
                            break
                            
                for item in selected_nodes:
                    self.delete_node(item, skip_undo=True)
                    
                event.accept()
                return
                
        # If not editing and typing a printable character, start editing
        text = event.text()
        if text and text.isprintable() and not (event.modifiers() & (Qt.ControlModifier | Qt.AltModifier | Qt.MetaModifier)):
            if event.key() != Qt.Key_Space:
                if selected_nodes:
                    current_item = selected_nodes[0]
                    current_item.start_editing()
                    # Forward the event so the text item gets the typed character
                    super().keyPressEvent(event)
                    return
                    
        super().keyPressEvent(event)
        
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.ControlModifier:
            # Zoom
            factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)
            
    def mousePressEvent(self, event: QMouseEvent):
        # 判断是否点击在节点上
        item = self.itemAt(event.pos())
        on_node = None
        if item:
            for node in self.nodes:
                if item == node or item == node.text_item or item is node or item is node.text_item:
                    on_node = node
                    break
                    
        if event.button() == Qt.MiddleButton or (event.button() == Qt.RightButton and not on_node):
            self._dragging = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.RightButton and on_node:
            self._drawing_relation_start_node = on_node
            from PySide6.QtWidgets import QGraphicsLineItem
            from PySide6.QtGui import QPen, QColor
            self._temp_relation_line = QGraphicsLineItem()
            pen = QPen(QColor(self.current_relation_color))
            pen.setWidth(self.current_relation_width)
            if self.current_relation_style == "dashed":
                pen.setStyle(Qt.DashLine)
            else:
                pen.setStyle(Qt.SolidLine)
            self._temp_relation_line.setPen(pen)
            self._temp_relation_line.setZValue(10)
            
            start_pos = on_node.sceneBoundingRect().center()
            self._temp_relation_line.setLine(start_pos.x(), start_pos.y(), start_pos.x(), start_pos.y())
            self.scene.addItem(self._temp_relation_line)
            event.accept()
        else:
            # Handle click outside to commit text changes and allow RightButton for context menu
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()
            
            # Pan view
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        elif self._drawing_relation_start_node and self._temp_relation_line:
            start_pos = self._drawing_relation_start_node.sceneBoundingRect().center()
            end_pos = self.mapToScene(event.pos())
            self._temp_relation_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        elif self._drawing_relation_start_node:
            start_node = self._drawing_relation_start_node
            self._drawing_relation_start_node = None
            
            if self._temp_relation_line:
                self.scene.removeItem(self._temp_relation_line)
                self._temp_relation_line = None
                
            item = self.itemAt(event.pos())
            end_node = None
            if item:
                for node in self.nodes:
                    if item == node or item == node.text_item or item is node or item is node.text_item:
                        end_node = node
                        break
                        
            if end_node and end_node != start_node:
                # Add relation
                existing = [r for r in start_node.model.relations if (r if isinstance(r, str) else r.get("target")) == end_node.model.id]
                if not existing:
                    self.push_undo_state()
                    start_node.model.relations.append({
                        "target": end_node.model.id, 
                        "color": self.current_relation_color,
                        "style": self.current_relation_style,
                        "width": self.current_relation_width
                    })
                    from items import RelationEdgeItem
                    rel_edge = RelationEdgeItem(
                        start_node, end_node, 
                        color=self.current_relation_color,
                        line_style=self.current_relation_style,
                        line_width=self.current_relation_width
                    )
                    self.scene.addItem(rel_edge)
                    self.relation_edges.append(rel_edge)
                    start_node.relation_edges_out.append(rel_edge)
                    end_node.relation_edges_in.append(rel_edge)
                event.accept()
            else:
                # 只是右键单击，没有拖拽产生连接，则调起右键菜单
                self.contextMenuEvent(event)
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            on_node = False
            if item:
                for node in self.nodes:
                    if item == node or item == node.text_item or item is node or item is node.text_item:
                        on_node = True
                        break
            
            # 如果在空白处双击左键
            if not on_node:
                scene_pos = self.mapToScene(event.pos())
                self.add_floating_node(scene_pos)
                event.accept()
                return
                
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        # 确定鼠标下方的元素
        item = self.itemAt(event.pos())
        node_item = None
        
        if item:
            # 遍历寻找对应的 NodeItem，避免 PySide6 包装类型丢失问题
            for node in self.nodes:
                if item == node or item == node.text_item or item is node or item is node.text_item:
                    node_item = node
                    break
                    
        # 如果点击在空白处，不显示菜单，直接返回（交由右键拖拽处理）
        if not node_item:
            return
        
        # 如果右键点击到了节点，则先选中它
        self.scene.clearSelection()
        node_item.setSelected(True)
            
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        
        menu = QMenu(self)
        
        action_new = QAction("新建", self)
        action_new.triggered.connect(self.handle_tab)
        
        action_copy = QAction("复制", self)
        action_copy.triggered.connect(self.handle_copy)
        
        action_cut = QAction("剪切", self)
        action_cut.triggered.connect(self.handle_cut)
        
        action_paste = QAction("黏贴", self)
        action_paste.triggered.connect(self.handle_paste)
        
        action_undo = QAction("撤销", self)
        action_undo.triggered.connect(self.handle_undo)
        
        menu.addAction(action_new)
        menu.addAction(action_copy)
        menu.addAction(action_cut)
        menu.addAction(action_paste)
        menu.addAction(action_undo)
        
        menu.exec(event.globalPos())
            
    def apply_template_style(self, template_key, layout_direction):
        from template_data import get_templates
        from PySide6.QtGui import QColor, QPen
        from PySide6.QtCore import Qt
        
        templates = get_templates()
        if template_key not in templates: return
        
        style = templates[template_key].get("style", {}).copy()
        style["layout"] = layout_direction
        
        self.push_undo_state()
        
        # 将样式赋给所有根节点
        for node in self.nodes:
            if node.model.parent is None:
                node.model.style = style
                
        # 更新所有节点的字体颜色、圆角并重绘
        for node in self.nodes:
            theme = node.get_theme()
            text_color = theme.get("root_text_color", theme.get("text_color", "#323232")) if node.model.is_root() else theme.get("text_color", "#323232")
            node.text_item.setDefaultTextColor(QColor(text_color))
            node.radius = theme.get("radius", 8)
            node.update()
            
        # 更新所有常规连线
        for edge in self.edges:
            theme = edge.parent_node.get_theme()
            edge_color = theme.get("edge_color", "#969696")
            edge_width = theme.get("edge_width", 2)
            pen = QPen(QColor(edge_color), edge_width)
            pen.setStyle(Qt.SolidLine)
            edge.setPen(pen)
            edge.update_path()
            edge.update()
            
        # 更新窗口标题
        parent_window = self.parentWidget()
        if hasattr(parent_window, "setWindowTitle") and hasattr(parent_window, "current_filepath"):
            filepath = parent_window.current_filepath
            direction_text = "从左到右" if layout_direction == "horizontal" else "从上而下"
            template_text = templates[template_key].get("text", "")
            if filepath:
                parent_window.setWindowTitle(f"Mind Nexus v2.0.1 - {filepath} ({template_text}模板 - {direction_text})")
            else:
                parent_window.setWindowTitle(f"Mind Nexus v2.0.1 - 新建思维导图 ({template_text}模板 - {direction_text})")
            
        self.update_layout()
        
    def update_layout(self):
        if not self.root_item:
            return
            
        # 按层级（level）对节点进行分组并统一尺寸
        levels = {}
        for node in self.nodes:
            level = node.model.get_level()
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
            
        for level, nodes_in_level in levels.items():
            if not nodes_in_level:
                continue
            max_w = max(n.natural_width for n in nodes_in_level)
            max_h = max(n.natural_height for n in nodes_in_level)
            for n in nodes_in_level:
                if n.width != max_w or n.height != max_h:
                    n.prepareGeometryChange()
                    n.width = max_w
                    n.height = max_h
                    n._update_text_pos()
                    n.update()
                    
        theme = self.root_item.get_theme()
        is_vertical = theme.get("layout") == "vertical"
            
        H_SPACING = 80 if not is_vertical else 40
        V_SPACING = 20 if not is_vertical else 60
        
        def calculate_tree_size(node_item):
            children = [n for n in self.nodes if n.model.parent == node_item.model]
            if not children:
                return node_item.width if is_vertical else node_item.height
                
            if is_vertical:
                total_width = sum(calculate_tree_size(c) for c in children) + (len(children) - 1) * H_SPACING
                return max(node_item.width, total_width)
            else:
                total_height = sum(calculate_tree_size(c) for c in children) + (len(children) - 1) * V_SPACING
                return max(node_item.height, total_height)
                
        def layout_node(node_item, x, y):
            node_item.setPos(x, y)
            children = [n for n in self.nodes if n.model.parent == node_item.model]
            if not children:
                return
                
            if is_vertical:
                children_total_width = sum(calculate_tree_size(c) for c in children) + (len(children) - 1) * H_SPACING
                current_x = x - children_total_width / 2 + node_item.width / 2
                base_child_y = y + node_item.height + V_SPACING
                max_child_h = max(c.height for c in children) if children else 0
                
                for child in children:
                    child_w = calculate_tree_size(child)
                    child_x = current_x + child_w / 2 - child.width / 2
                    child_y = base_child_y + (max_child_h - child.height) / 2
                    layout_node(child, child_x, child_y)
                    current_x += child_w + H_SPACING
            else:
                children_total_height = sum(calculate_tree_size(c) for c in children) + (len(children) - 1) * V_SPACING
                current_y = y - children_total_height / 2 + node_item.height / 2
                
                base_child_x = x + node_item.width + H_SPACING
                max_child_w = max(c.width for c in children) if children else 0
                
                for child in children:
                    child_h = calculate_tree_size(child)
                    child_y = current_y + child_h / 2 - child.height / 2
                    child_x = base_child_x + (max_child_w - child.width) / 2
                    layout_node(child, child_x, child_y)
                    current_y += child_h + V_SPACING
                
        # Layout all root nodes (floating nodes) starting from their current position
        for node in self.nodes:
            if node.model.parent is None:
                # For the main root_item, we force it to 0,0, for others keep their current position
                if node == self.root_item:
                    layout_node(node, 0, 0)
                else:
                    layout_node(node, node.pos().x(), node.pos().y())
