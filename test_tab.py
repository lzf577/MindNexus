import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt, QEvent
from view import MindMapView
from models import NodeModel
from items import NodeItem

app = QApplication(sys.argv)
view = MindMapView()
view.show()

# Select root item
view.root_item.setSelected(True)

print("Before Tab:", len(view.nodes))
event = QKeyEvent(QEvent.KeyPress, Qt.Key_Tab, Qt.NoModifier, "\t")
view.keyPressEvent(event)
print("After Tab:", len(view.nodes))

# Now test entering text
view.root_item.start_editing()
event2 = QKeyEvent(QEvent.KeyPress, Qt.Key_Tab, Qt.NoModifier, "\t")
view.keyPressEvent(event2)
print("After Tab (editing):", len(view.nodes))

sys.exit(0)
