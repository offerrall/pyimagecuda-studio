from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPathItem, QMenu)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainter, QPainterPath, QBrush
import re

from ...nodes.core import EndNode, Node, delete_node, free_nodes
from ...nodes.constraints import get_annotated_params
from ...nodes.global_variables import get_linked_variable, link_to_node

from .cable_widget import CableWidget
from .node import NodeWidget, PortWidget
from ...nodes.node_factory import create_node, get_node_menu_structure
import copy

class NodeGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.preview_callback = None
        self.execute_callback = None
        self.selection_changed_callback = None
        self.delete_callback = None
        
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        self.setScene(self.scene)
        
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.temp_line_pen = QPen(QColor(200, 200, 200), 2, Qt.DashLine)
        
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        self.setBackgroundBrush(QBrush(QColor(40, 40, 40)))
        
        self.node_widgets = {}
        self.cables = []
        self.dragging_cable = None
        self.temp_line = None
        self.nodes: list[Node] = []
        
        self.panning = False
        self.pan_start = QPointF()

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setOptimizationFlags(QGraphicsView.DontAdjustForAntialiasing)

        self.context_menu_pos = QPointF(0, 0)

    def create_init_output_node(self):
        output_node = create_node(EndNode, "Output", self.preview_callback)
        if output_node:
            self.nodes.append(output_node)
            self.add_node(output_node, 600, 70)
            self.rebuild_cables()

    def clear_all(self, create_output_node=True):
        free_nodes(self.nodes)
        self.nodes.clear()
        self.node_widgets.clear()
        self.cables.clear()
        self.scene.clear()
        if create_output_node:
            self.create_init_output_node()

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        
        grid_size = 20
        
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        
        x = left
        while x < rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += grid_size
        
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += grid_size

    def refresh_node_visual(self, node_id: str):
        if node_id in self.node_widgets:
            self.node_widgets[node_id].update_visuals()

    def on_selection_changed(self):
        if self.selection_changed_callback:
            selected_items = self.scene.selectedItems()
            selected_nodes = [item for item in selected_items if isinstance(item, NodeWidget)]
            
            selected_node_ids = [node_widget.node.id for node_widget in selected_nodes]
            self.selection_changed_callback(selected_node_ids)
    
    def auto_execute(self):
        if self.execute_callback:
            self.execute_callback()
    
    def add_node(self, node, x=0, y=0):
        widget = NodeWidget(node, x, y, self)
        self.scene.addItem(widget)
        self.node_widgets[node.id] = widget
        return widget
    
    def rebuild_cables(self):
        for cable in self.cables:
            self.scene.removeItem(cable)
        self.cables.clear()
        
        for node_id, widget in self.node_widgets.items():
            node = widget.node
            
            if hasattr(node, 'connect_to') and node.connect_to:
                target_widget = self.node_widgets.get(node.connect_to.id)
                if target_widget:
                    port_num = getattr(node, 'connect_to_port', 1)
                    cable = CableWidget(node, node.connect_to, 1, port_num)
                    
                    source_port = widget.get_output_port(1)
                    target_port = target_widget.get_input_port(port_num)
                    
                    if source_port and target_port:
                        cable.set_ports(source_port, target_port)
                        self.scene.addItem(cable)
                        self.cables.append(cable)
            
            if hasattr(node, 'connect_to_1') and node.connect_to_1:
                target_widget = self.node_widgets.get(node.connect_to_1.id)
                if target_widget:
                    cable = CableWidget(node, node.connect_to_1, 1, node.connect_to_1_port)
                    
                    source_port = widget.get_output_port(1)
                    target_port = target_widget.get_input_port(node.connect_to_1_port)
                    
                    if source_port and target_port:
                        cable.set_ports(source_port, target_port)
                        self.scene.addItem(cable)
                        self.cables.append(cable)
            
            if hasattr(node, 'connect_to_2') and node.connect_to_2:
                target_widget = self.node_widgets.get(node.connect_to_2.id)
                if target_widget:
                    cable = CableWidget(node, node.connect_to_2, 2, node.connect_to_2_port)
                    
                    source_port = widget.get_output_port(2)
                    target_port = target_widget.get_input_port(node.connect_to_2_port)
                    
                    if source_port and target_port:
                        cable.set_ports(source_port, target_port)
                        self.scene.addItem(cable)
                        self.cables.append(cable)
    
    def update_cables(self):
        for cable in self.cables:
            cable.update_position()
    
    def get_node_init_params(self, source_node, new_name):
        
        params = get_annotated_params(source_node)
        
        init_params = {'name': new_name}
        
        if hasattr(source_node, 'finish_callback'):
            init_params['finish_callback'] = self.preview_callback
        
        for param in params:
            if param.name in ['name', 'id']:
                continue
            
            try:
                value = getattr(source_node, param.name)
                
                if isinstance(value, (list, dict)):
                    value = copy.deepcopy(value)
                elif isinstance(value, tuple):
                    value = tuple(value)
                else:
                    value = value
                
                init_params[param.name] = value
                print(f"[GUI-DUPLICATE] Preparing parameter {param.name} = {value}")
            except Exception as e:
                print(f"[GUI-DUPLICATE] Failed to get parameter {param.name}: {e}")
        
        return init_params

    def duplicate_selected_nodes(self):
        
        selected_items = self.scene.selectedItems()
        selected_nodes = [item for item in selected_items if isinstance(item, NodeWidget)]
        
        if not selected_nodes:
            print("[GUI-DUPLICATE] No nodes selected")
            return
        
        for item in selected_items:
            item.setSelected(False)
        
        offset_x = 50
        offset_y = 50
        
        duplicated_widgets = []
        original_to_duplicate = {}
        
        for node_widget in selected_nodes:
            original_node = node_widget.node
            
            if type(original_node) is EndNode:
                print(f"[GUI-DUPLICATE] Skipping EndNode: {original_node.name}")
                continue
            
            current_pos = node_widget.pos()
            new_x = current_pos.x() + offset_x
            new_y = current_pos.y() + offset_y
            
            base_name = original_node.name
            match = re.match(r'^(.*?)\s*(\d+)$', base_name)
            if match:
                base_name = match.group(1)
            
            unique_name = self.get_unique_name(base_name)
            
            node_class = type(original_node)
            
            init_params = self.get_node_init_params(original_node, unique_name)
            
            new_node = node_class(**init_params)
            
            if new_node is None:
                print(f"[GUI-DUPLICATE] Failed to create node of type {node_class.__name__}")
                continue
            
            self.nodes.append(new_node)
            new_widget = self.add_node(new_node, new_x, new_y)
            
            new_widget.setSelected(True)
            duplicated_widgets.append(new_widget)
            
            original_to_duplicate[original_node.id] = new_node
            
            params = get_annotated_params(original_node)
            for param in params:
                if param.name in ['name', 'id']:
                    continue
                
                linked_var = get_linked_variable(original_node.id, param.name)
                if linked_var:
                    link_to_node(linked_var, new_node.id, param.name)
                    print(f"[GUI-DUPLICATE] Linked variable '{linked_var}' to {new_node.name}.{param.name}")
            
            print(f"[GUI-DUPLICATE] Duplicated {original_node.name} as {new_node.name} at ({new_x}, {new_y})")
        
        for original_id, new_node in original_to_duplicate.items():
            original_node = next((n for n in self.nodes if n.id == original_id), None)
            if not original_node:
                continue
            
            if hasattr(original_node, 'connect_to') and original_node.connect_to:
                if original_node.connect_to.id in original_to_duplicate:
                    target_node = original_to_duplicate[original_node.connect_to.id]
                    target_port = original_node.connect_to_port
                    try:
                        new_node.connect_to_node(target_node, port=target_port)
                        print(f"[GUI-DUPLICATE] Connected {new_node.name} -> {target_node.name} (port {target_port})")
                    except Exception as e:
                        print(f"[GUI-DUPLICATE] Failed to connect: {e}")
            
            if hasattr(original_node, 'connect_to_1') and original_node.connect_to_1:
                if original_node.connect_to_1.id in original_to_duplicate:
                    target_node = original_to_duplicate[original_node.connect_to_1.id]
                    target_port = original_node.connect_to_1_port
                    try:
                        new_node.connect_to_node(target_node, port=1, target_port=target_port)
                        print(f"[GUI-DUPLICATE] Connected {new_node.name} port 1 -> {target_node.name} (port {target_port})")
                    except Exception as e:
                        print(f"[GUI-DUPLICATE] Failed to connect port 1: {e}")
            
            if hasattr(original_node, 'connect_to_2') and original_node.connect_to_2:
                if original_node.connect_to_2.id in original_to_duplicate:
                    target_node = original_to_duplicate[original_node.connect_to_2.id]
                    target_port = original_node.connect_to_2_port
                    try:
                        new_node.connect_to_node(target_node, port=2, target_port=target_port)
                        print(f"[GUI-DUPLICATE] Connected {new_node.name} port 2 -> {target_node.name} (port {target_port})")
                    except Exception as e:
                        print(f"[GUI-DUPLICATE] Failed to connect port 2: {e}")
        
        if duplicated_widgets:
            self.rebuild_cables()
            print(f"[GUI-DUPLICATE] Successfully duplicated {len(duplicated_widgets)} node(s)")
    
    def delete_selected_items(self):
        selected_items = self.scene.selectedItems()
        
        selected_cables = [item for item in selected_items if isinstance(item, CableWidget)]
        selected_nodes = [item for item in selected_items if isinstance(item, NodeWidget)]
        
        deleted_node_ids = []
        
        for cable in selected_cables:
            source_node = cable.source_node
            
            if hasattr(source_node, 'connect_to_1'):
                if cable.source_port_num == 1:
                    source_node.disconnect_node(port=1)
                else:
                    source_node.disconnect_node(port=2)
            else:
                source_node.disconnect_node()
            
            self.scene.removeItem(cable)
            self.cables.remove(cable)
        
        for node_widget in selected_nodes:
            node = node_widget.node

            if type(node) is EndNode:
                continue
            
            deleted_node_ids.append(node.id)
            
            delete_node(node)
            
            if node in self.nodes:
                self.nodes.remove(node)
            
            if node.id in self.node_widgets:
                del self.node_widgets[node.id]
            
            self.scene.removeItem(node_widget)
        
        if selected_nodes or selected_cables:
            self.rebuild_cables()
            self.auto_execute()
            
            if deleted_node_ids and self.delete_callback:
                self.delete_callback(deleted_node_ids)
    
    def create_node_at_position(self, node_class, name, pos):
        unique_name = self.get_unique_name(name)
        node = create_node(node_class, unique_name, self.preview_callback)
        
        if node is None:
            return
        
        self.nodes.append(node)
        self.add_node(node, pos.x(), pos.y())
    
    def show_context_menu(self, pos):
        menu = QMenu()
        menu_structure = get_node_menu_structure()

        for category, items in menu_structure.items():
            if isinstance(items, dict):
                submenu = menu.addMenu(category)
                for item_name, node_class in items.items():
                    submenu.addAction(item_name).triggered.connect(
                        lambda checked, nc=node_class, n=item_name: 
                        self.create_node_at_position(nc, n, self.context_menu_pos)
                    )
            else:
                menu.addAction(category).triggered.connect(
                    lambda checked, nc=items, n=category: 
                    self.create_node_at_position(nc, n, self.context_menu_pos)
                )
        
        menu.exec(pos)
    
    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        old_pos = self.mapToScene(event.position().toPoint())
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        self.scale(zoom_factor, zoom_factor)
        
        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
    
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        
        if event.button() == Qt.MiddleButton:
            self.panning = True
            self.pan_start = event.pos()
            self.setDragMode(QGraphicsView.NoDrag)
            return
        
        if event.button() == Qt.RightButton:
            self.context_menu_pos = self.mapToScene(event.pos())
            self.show_context_menu(event.globalPosition().toPoint())
            return
        
        if event.button() == Qt.LeftButton and isinstance(item, PortWidget) and not item.is_input:
            source_node = item.node_widget.node
            port_number = item.port_number
            
            if hasattr(source_node, 'connect_to_1'):
                if port_number == 1 and source_node.connect_to_1:
                    source_node.disconnect_node(port=1)
                    self.rebuild_cables()
                    self.auto_execute()
                elif port_number == 2 and source_node.connect_to_2:
                    source_node.disconnect_node(port=2)
                    self.rebuild_cables()
                    self.auto_execute()
            else:
                if source_node.connect_to:
                    source_node.disconnect_node()
                    self.rebuild_cables()
                    self.auto_execute()
            
            self.dragging_cable = {
                'source_widget': item.node_widget,
                'source_port': item,
                'port_number': port_number
            }
            
            start = item.get_center()
            end = self.mapToScene(event.pos())
            
            path = QPainterPath(start)
            dx = end.x() - start.x()
            ctrl_offset = abs(dx) * 0.5
            if ctrl_offset < 50:
                ctrl_offset = 50
            
            ctrl1 = QPointF(start.x() + ctrl_offset, start.y())
            ctrl2 = QPointF(end.x() - ctrl_offset, end.y())
            path.cubicTo(ctrl1, ctrl2, end)
            
            self.temp_line = QGraphicsPathItem(path)
            self.temp_line.setPen(self.temp_line_pen)
            self.scene.addItem(self.temp_line)
            
            self.setDragMode(QGraphicsView.NoDrag)
            return
        
        if event.button() == Qt.LeftButton and isinstance(item, PortWidget) and item.is_input:
            target_node = item.node_widget.node
            input_port_number = item.port_number
            
            source_node = None
            source_port_number = 1
            
            if hasattr(target_node, 'node_connected_1'):
                if input_port_number == 1 and target_node.node_connected_1:
                    source_node = target_node.node_connected_1
                elif input_port_number == 2 and target_node.node_connected_2:
                    source_node = target_node.node_connected_2
            elif hasattr(target_node, 'node_connected') and target_node.node_connected:
                source_node = target_node.node_connected
            
            if source_node:
                if hasattr(source_node, 'connect_to_1'):
                    if source_node.connect_to_1 == target_node and source_node.connect_to_1_port == input_port_number:
                        source_port_number = 1
                        source_node.disconnect_node(port=1)
                    elif source_node.connect_to_2 == target_node and source_node.connect_to_2_port == input_port_number:
                        source_port_number = 2
                        source_node.disconnect_node(port=2)
                else:
                    source_port_number = 1
                    source_node.disconnect_node()
                
                self.rebuild_cables()
                self.auto_execute()
                
                source_widget = self.node_widgets.get(source_node.id)
                if source_widget:
                    source_port = source_widget.get_output_port(source_port_number)
                    
                    if source_port:
                        self.dragging_cable = {
                            'source_widget': source_widget,
                            'source_port': source_port,
                            'port_number': source_port_number
                        }
                        
                        start = source_port.get_center()
                        end = self.mapToScene(event.pos())
                        
                        path = QPainterPath(start)
                        dx = end.x() - start.x()
                        ctrl_offset = abs(dx) * 0.5
                        if ctrl_offset < 50:
                            ctrl_offset = 50
                        
                        ctrl1 = QPointF(start.x() + ctrl_offset, start.y())
                        ctrl2 = QPointF(end.x() - ctrl_offset, end.y())
                        path.cubicTo(ctrl1, ctrl2, end)
                        
                        self.temp_line = QGraphicsPathItem(path)
                        self.temp_line.setPen(self.temp_line_pen)
                        self.scene.addItem(self.temp_line)
                        
                        self.setDragMode(QGraphicsView.NoDrag)
                        return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.panning:
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return
        
        if self.dragging_cable and self.temp_line:
            start = self.dragging_cable['source_port'].get_center()
            end = self.mapToScene(event.pos())
            
            path = QPainterPath(start)
            dx = end.x() - start.x()
            ctrl_offset = abs(dx) * 0.5
            if ctrl_offset < 50:
                ctrl_offset = 50
            
            ctrl1 = QPointF(start.x() + ctrl_offset, start.y())
            ctrl2 = QPointF(end.x() - ctrl_offset, end.y())
            path.cubicTo(ctrl1, ctrl2, end)
            
            self.temp_line.setPath(path)
            return
        
        super().mouseMoveEvent(event)

    def get_unique_name(self, base_name):
        existing_names = {node.name for node in self.nodes}
        
        if base_name not in existing_names:
            return base_name
        
        counter = 2
        while f"{base_name} {counter}" in existing_names:
            counter += 1
        
        return f"{base_name} {counter}"

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self.panning:
            self.panning = False
            self.setDragMode(QGraphicsView.RubberBandDrag)
            return
        
        if self.dragging_cable:
            if self.temp_line:
                self.scene.removeItem(self.temp_line)
                self.temp_line = None
            
            item = self.itemAt(event.pos())
            
            if isinstance(item, PortWidget) and item.is_input:
                source_widget = self.dragging_cable['source_widget']
                target_widget = item.node_widget
                port_number = item.port_number
                
                source_node = source_widget.node
                target_node = target_widget.node
                
                if hasattr(target_node, 'node_connected_1'):
                    if port_number == 1 and target_node.node_connected_1:
                        old_source = target_node.node_connected_1
                        if hasattr(old_source, 'connect_to_1'):
                            if old_source.connect_to_1 == target_node:
                                old_source.disconnect_node(port=1)
                            elif old_source.connect_to_2 == target_node:
                                old_source.disconnect_node(port=2)
                        else:
                            old_source.disconnect_node()
                    elif port_number == 2 and target_node.node_connected_2:
                        old_source = target_node.node_connected_2
                        if hasattr(old_source, 'connect_to_1'):
                            if old_source.connect_to_1 == target_node:
                                old_source.disconnect_node(port=1)
                            elif old_source.connect_to_2 == target_node:
                                old_source.disconnect_node(port=2)
                        else:
                            old_source.disconnect_node()
                else:
                    if target_node.node_connected:
                        old_source = target_node.node_connected
                        if hasattr(old_source, 'connect_to_1'):
                            if old_source.connect_to_1 == target_node:
                                old_source.disconnect_node(port=1)
                            elif old_source.connect_to_2 == target_node:
                                old_source.disconnect_node(port=2)
                        else:
                            old_source.disconnect_node()
                
                try:
                    if hasattr(source_node, 'connect_to_1'):
                        source_node.connect_to_node(
                            target_node,
                            port=self.dragging_cable['port_number'],
                            target_port=port_number
                        )
                    else:
                        source_node.connect_to_node(target_node, port=port_number)
                    
                    self.rebuild_cables()
                    self.auto_execute()
                    
                except ValueError as e:
                    pass
            
            self.dragging_cable = None
            self.setDragMode(QGraphicsView.RubberBandDrag)
            return
        
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selected_items()
        elif event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
            self.duplicate_selected_nodes()
        else:
            super().keyPressEvent(event)