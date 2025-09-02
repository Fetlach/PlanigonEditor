from PySide6.QtWidgets import QApplication, QWidget, QDockWidget, QHBoxLayout, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QPushButton, QGraphicsLineItem, QVBoxLayout, QLineEdit, QLabel
from PySide6.QtGui import QPolygonF, QPen, QBrush
from PySide6.QtCore import Qt, QPointF, Signal, QObject, Slot
import sys
from enum import Enum, auto
from dataclasses import dataclass
from include import planigonData

## --- Editor --- ##

class Mode(Enum):
    EMPTY = auto()
    IDLE = auto()
    POLYGON_SELECTED = auto()
    EDGE_SELECTED = auto()

@dataclass
class EditorState:
    mode: Mode = Mode.EDGE_SELECTED
    selected_polygon = None
    selected_edge = None

## --- UI --- ##

class GraphicsView(QGraphicsView):
    def __init__(self, scene, controller, parent=None):
        super().__init__(scene, parent)
        #self.setRenderHints(self.renderHints() | QPainter.Antialiasing)
        self.controller = controller
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.zoom_factor = 1.15
        self._last_mouse_pos = None
        self._panning = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_X and self.controller.state.mode != Mode.IDLE:
            self.controller.on_deselect_all()
            # maybe clear highlights, remove temporary attach lines, etc.
        elif event.key() == Qt.Key_A:
            self.controller.cycleSelectedPlanigon(-1)
            #print("planigon index: ", self.controller.planigonIdx)
        elif event.key() == Qt.Key_D:
            self.controller.cycleSelectedPlanigon(1)
            #print("planigon index: ", self.controller.planigonIdx)
        elif event.key() == Qt.Key_Q:
            self.controller.cycleSelectedEdge(-1)
            #print("edge index: ", self.controller.edgeIdx)
        elif event.key() == Qt.Key_E:
            self.controller.cycleSelectedEdge(1)
            #print("edge index: ", self.controller.edgeIdx)
        # Accept and create previewed polygon
        elif event.key() == Qt.Key_Enter and self.controller.state.mode == Mode.ATTACHING and self.controller.preview_poly is not None:
            pass
        # Delete selected polygon
        elif event.key() == Qt.Key_Backspace and self.controller.state.mode == Mode.POLYGON_SELECTED:
            pass
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        factor = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
        self.scale(factor, factor)
        #print("scroll called")
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.modifiers() & Qt.AltModifier:
            # Alt + LMB starts panning
            self._last_mouse_pos = event.position()
            self._panning = True
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.RightButton:
            # RMB deselects
            self.controller.on_deselect_all()
            
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position() - self._last_mouse_pos
            #print(f"Mouse delta: {delta.x()}, {delta.y()}")
            self._last_mouse_pos = event.position()

            h_val = self.horizontalScrollBar().value()
            v_val = self.verticalScrollBar().value()
            #print(f"Before scroll: h={h_val}, v={v_val}")

            self.horizontalScrollBar().setValue(h_val - delta.x())
            self.verticalScrollBar().setValue(v_val - delta.y())

            #print(f"After scroll: h={self.horizontalScrollBar().value()}, v={self.verticalScrollBar().value()}\n")
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._panning:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class SelectableEdge(QGraphicsLineItem, QObject):
    edgeSelected = Signal(object)

    def __init__(self, start, end, parent_polygon, size=5, parent=None):
        QGraphicsLineItem.__init__(self, start.x(), start.y(), end.x(), end.y())
        QObject.__init__(self, parent)
        self.parent_polygon = parent_polygon
        self.start = start
        self.end = end
        self.size = size
        self.setPen(QPen(Qt.blue, self.size))
        self.setZValue(10)
        self.setFlag(QGraphicsLineItem.ItemIsSelectable, False)
        self.setAcceptedMouseButtons(Qt.LeftButton)

    def mousePressEvent(self, event):
        #self.setPen(QPen(Qt.red, self.size))  # highlight selection
        #self.parent_polygon.deselect_polygon()
        #self.parent_polygon.removeEdgesExcept(self)
        self.edgeSelected.emit(self)
        #print("edge selected")
        super().mousePressEvent(event)

class SelectablePolygon(QGraphicsPolygonItem, QObject):
    polySelected = Signal(object)

    def __init__(self, polygon, faceRef: planigonData.Face, parent=None):
        QGraphicsPolygonItem.__init__(self, polygon)
        QObject.__init__(self, parent)
        self.face_ref = faceRef
        self.setPen(QPen(Qt.black, 2))
        self.setBrush(QBrush(Qt.lightGray))
        self.setFlag(QGraphicsPolygonItem.ItemIsSelectable, False)
        self.setZValue(0)
        self.setAcceptedMouseButtons(Qt.LeftButton)  # LMB only, handled by view

    def mousePressEvent(self, event):
        self.polySelected.emit(self)
        super().mousePressEvent(event)
    
    def deselect_polygon(self):
        #print("deselected poly")
        self.setBrush(QBrush(Qt.lightGray))
        # Remove selectable edges
        self.setAcceptedMouseButtons(Qt.LeftButton)

class previewPoly(QGraphicsPolygonItem, QObject):
    def __init__(self, polygon, parent=None):
        QGraphicsPolygonItem.__init__(self, polygon)
        QObject.__init__(self, parent)
        self.setPen(QPen(Qt.black, 2))
        self.setBrush(QBrush(Qt.green))
        self.setZValue(0)

class EditorController(QObject):
    # -- Signals -- #
    # - transforms
    transformUpdated = Signal()
    # - previews
    previewRemoved = Signal()
    previewUpdated = Signal(list[planigonData.Vertex])
    # - state changes
    stateChanged = Signal(EditorState)
    diagramUpdated = Signal(planigonData.Diagram)
    # - requests
    bakeTransforms = Signal()

    # -- Preview indexes -- #
    planigonIdx = 0
    edgeIdx = 0
    selected_edge = tuple[planigonData.Vertex, planigonData.Vertex]

    def __init__(self, scene):
        super().__init__()
        self.scene_ref = scene
        self.state = EditorState()
        self.diagram = planigonData.Diagram()
        self.selected_edge = SelectableEdge(QPointF(0,0), QPointF(0,10), None)

    def set_plan_Idx(self, idx: int):
        self.planigonIdx = (idx + len(planigonData.planigons)) % len(planigonData.planigons)
        self.edgeIdx = 0
        print(self.planigonIdx)
        self.updatePreviewPoly()

    def set_edge_Idx(self, idx: int):
        self.edgeIdx = (idx + len(planigonData.planigons[self.planigonIdx].lengths)) % len(planigonData.planigons[self.planigonIdx].lengths)
        self.updatePreviewPoly()

    def set_selected_edge(self, edge: QGraphicsLineItem):
        self.selected_edge = edge

    def removePreviewPoly(self):
        for item in self.scene_ref.items():
            if isinstance(item, previewPoly):
                self.scene_ref.removeItem(item)

    def updatePreviewPoly(self):
        # remove previews
        self.removePreviewPoly()
        if self.state.mode is Mode.EDGE_SELECTED or self.state.mode is Mode.EMPTY:
            points = planigonData.getPlanigonVertices(
                planigonData.Vertex([self.selected_edge.start.x(), self.selected_edge.start.y()]), 
                planigonData.Vertex([self.selected_edge.end.x(), self.selected_edge.end.y()]), 
                self.edgeIdx,
                planigonData.planigons[self.planigonIdx].lengths,
                planigonData.planigons[self.planigonIdx].angles)
            polyPoints = [QPointF(point.pos[0], point.pos[1]) for point in points]
            preview = previewPoly(QPolygonF(polyPoints))
            self.scene_ref.addItem(preview)
    
    def addFace(self):
        if self.state.mode is Mode.EDGE_SELECTED or self.state.mode is Mode.EMPTY:
            self.removePreviewPoly()
            points = planigonData.getPlanigonVertices(
                planigonData.Vertex([self.selected_edge.start.x(), self.selected_edge.start.y()]), 
                planigonData.Vertex([self.selected_edge.end.x(), self.selected_edge.end.y()]), 
                self.edgeIdx,
                planigonData.planigons[self.planigonIdx].lengths,
                planigonData.planigons[self.planigonIdx].angles)
            vert_pos = [point.pos for point in points]
            newFace = self.diagram.add_planigon(vert_pos)
            polyPoints = [QPointF(point.pos[0], point.pos[1]) for point in points]
            newPoly = SelectablePolygon(QPolygonF(polyPoints), newFace)
            self.scene_ref.addItem(newPoly)
            newPoly.polySelected.connect(self.on_polygon_selected)
            self.set_state(
                mode=Mode.IDLE,
                selected_polygon=None,
                selected_edge=None
            )
            self.on_deselect_all()


    def request_update_diagram(self):
        self.diagramUpdated.emit(self.diagram)

    def set_state(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self.state, k, v)
        self.stateChanged.emit(self.state)

    def on_deselect_all(self):
        self.set_state(
            mode=Mode.IDLE,
            selected_polygon=None,
            selected_edge=None
        )
        # remove all edges
        for item in self.scene_ref.items():
            if isinstance(item, SelectableEdge):
                try:
                    item.edgeSelected.disconnect()
                except (TypeError, RuntimeError):
                    pass
                self.scene_ref.removeItem(item)
        
        # remove preview poly
        self.removePreviewPoly()

        # enable all polygons & deselect
        for item in self.scene_ref.items():
            if isinstance(item, SelectablePolygon):
                item.deselect_polygon()
                item.setAcceptedMouseButtons(Qt.LeftButton)

    def on_polygon_selected(self, polygon_item:SelectablePolygon):
        self.set_state(
            mode=Mode.POLYGON_SELECTED,
            selected_polygon=polygon_item,
            selected_edge=None
        )
        # remove all edges
        for item in self.scene_ref.items():
            if isinstance(item, SelectableEdge):
                try:
                    item.edgeSelected.disconnect()
                except (TypeError, RuntimeError):
                    pass
                self.scene_ref.removeItem(item)
                del item

        # disable all polygons
        for item in self.scene_ref.items():
            if isinstance(item, SelectablePolygon) and item != polygon_item:
                item.deselect_polygon()

        # set values for marked polygon
        polygon_item.setAcceptedMouseButtons(Qt.NoButton)
        polygon_item.setBrush(QBrush(Qt.red))

        # create new edges to select
        #print(polygon_item.face_ref)
        for edge in planigonData.iterate(polygon_item.face_ref.edge):
            if edge.twin is None:
                # add selectable edge
                #print("coord:", edge.origin.pos[0], edge.origin.pos[1])
                newEdge = SelectableEdge(
                    QPointF(edge.next.origin.pos[0], edge.next.origin.pos[1]), 
                    QPointF(edge.origin.pos[0], edge.origin.pos[1]), 
                    None, 
                    5)
                newEdge.edgeSelected.connect(self.on_edge_selected)
                self.scene_ref.addItem(newEdge)


    def on_edge_selected(self, edge):
        self.set_state(
            mode=Mode.EDGE_SELECTED,
            selected_edge=edge
        )
        self.selected_edge = edge
        # remove all non-selected edges
        newList = [edge]
        for item in self.scene_ref.items():
            if isinstance(item, SelectableEdge) and item != edge:
                try:
                    item.edgeSelected.disconnect()
                except (TypeError, RuntimeError):
                    pass
                self.scene_ref.removeItem(item)
        edge.setAcceptedMouseButtons(Qt.NoButton)
        # disable all polygons
        for item in self.scene_ref.items():
            if isinstance(item, SelectablePolygon):
                item.setAcceptedMouseButtons(Qt.NoButton)
        # create a planigon preview
        self.updatePreviewPoly()

class IndexSelector(QWidget):
    indexChanged = Signal(int)  # emits new index whenever changed

    def __init__(self, label_text="Index:", start_index=0, max_index=10, parent=None):
        super().__init__(parent)
        self._index = start_index
        self._max_index = max_index

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        self.prev_btn = QPushButton("<")
        self.prev_btn.clicked.connect(self.decrement)
        layout.addWidget(self.prev_btn)

        self.idx_edit = QLineEdit(str(self._index))
        self.idx_edit.setFixedWidth(40)
        self.idx_edit.setAlignment(Qt.AlignCenter)
        self.idx_edit.editingFinished.connect(self.on_text_entered)
        layout.addWidget(self.idx_edit)

        self.next_btn = QPushButton(">")
        self.next_btn.clicked.connect(self.increment)
        layout.addWidget(self.next_btn)

        self._update_buttons()

    @Slot()
    def decrement(self):
        if self._index > 0:
            self._index -= 1
            self.idx_edit.setText(str(self._index))
            self.indexChanged.emit(self._index)
        self._update_buttons()

    @Slot()
    def increment(self):
        if self._index < self._max_index:
            self._index += 1
            self.idx_edit.setText(str(self._index))
            self.indexChanged.emit(self._index)
        self._update_buttons()

    @Slot()
    def on_text_entered(self):
        text = self.idx_edit.text().strip()
        if text.isdigit():
            idx = int(text)
            if 0 <= idx <= self._max_index:
                self._index = idx
                self.indexChanged.emit(self._index)
            else:
                # clamp to bounds
                self._index = max(0, min(idx, self._max_index))
                self.idx_edit.setText(str(self._index))
                self.indexChanged.emit(self._index)
        else:
            # reset to current index if invalid
            self.idx_edit.setText(str(self._index))
        self._update_buttons()

    def setIndex(self, idx: int):
        self._index = max(0, min(idx, self._max_index))
        self.idx_edit.setText(str(self._index))
        self.indexChanged.emit(self._index)
        self._update_buttons()

    def setMaxIndex(self, max_idx: int):
        self._max_index = max_idx
        if self._index > max_idx:
            self.setIndex(max_idx)
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.setEnabled(self._index > 0)
        self.next_btn.setEnabled(self._index < self._max_index)

# ---- Dockable menu panel ----
class MenuPanel(QWidget):
    def __init__(self, controller: EditorController):
        super().__init__()
        self.controller = controller

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Face Name:"))
        self.face_name_input = QLineEdit()
        layout.addWidget(self.face_name_input)

        # Index selectors
        self.planigonIdxSelector = IndexSelector("Planigon Index:", 0, len(planigonData.planigons) - 1, None)
        layout.addWidget(self.planigonIdxSelector)
        self.edgeIdxSelector = IndexSelector("Edge Index:", 0, 100, None)
        layout.addWidget(self.edgeIdxSelector)

        # Controller buttons
        add_face_btn = QPushButton("Add Face")
        add_face_btn.clicked.connect(self.controller.addFace)
        layout.addWidget(add_face_btn)

        self.status_label = QLabel("Ready.")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Connect signals from controller back to UI
        #self.controller.previewUpdated.connect(self.scene.on_preview_updated)
        self.planigonIdxSelector.indexChanged.connect(self.on_planigon_index_changed)
        self.edgeIdxSelector.indexChanged.connect(self.on_edge_index_changed)
        
    def on_edge_index_changed(self, new_idx):
        # tell controller about edge index change
        self.controller.set_edge_Idx(new_idx)

    def on_planigon_index_changed(self, new_idx):
        self.controller.set_plan_Idx(new_idx)

    def on_add_face(self):
        name = self.face_name_input.text().strip()
        if name:
            self.controller.addFace(name)
        else:
            self.status_label.setText("Enter a face name first.")

    def on_face_added(self, name):
        self.status_label.setText(f"Face '{name}' added!")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up graphics scene
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-500, -500, 1000, 1000)  # centered around origin
        #self.scene.addRect(-100, -100, 200, 200, QPen(Qt.blue, 5), QBrush(Qt.red)) # test rect

        # Set up controller
        self.controller = EditorController(self.scene)

        # Set up view
        self.view = GraphicsView(self.scene, self.controller)
        self.setCentralWidget(self.view)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.view.centerOn(0, 0)
        self.view.show()
        
        # Set up menu dock
        print("central:", self.centralWidget().size())
        menu_dock = QDockWidget("Editor Menu", self)
        menu_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        menu_panel = MenuPanel(self.controller)
        menu_dock.setWidget(menu_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, menu_dock)

        self.setWindowTitle("Planigon Editor Prototype")
        self.resize(1000, 600)
        print("central:", self.centralWidget().size())

        # Create bindings

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())