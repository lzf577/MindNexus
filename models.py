import uuid
import xml.etree.ElementTree as ET

class NodeModel:
    def __init__(self, text="新节点", parent=None, style=None):
        self.id = str(uuid.uuid4())
        self.text = text
        self.parent = parent
        self.style = style or {}
        self.relations = [] # Store IDs of target relation nodes
        self.children = []
        if self.parent is not None:
            self.parent.add_child(self)
            
    def add_child(self, child_node):
        if child_node not in self.children:
            self.children.append(child_node)
            child_node.parent = self
            
    def remove_child(self, child_node):
        if child_node in self.children:
            self.children.remove(child_node)
            child_node.parent = None
            
    def is_root(self):
        return self.parent is None
        
    def get_level(self):
        level = 0
        current = self
        while current.parent:
            level += 1
            current = current.parent
        return level

    def remove_from_parent(self):
        if self.parent:
            self.parent.remove_child(self)

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "style": self.style,
            "relations": self.relations,
            "children": [child.to_dict() for child in self.children]
        }
        
    @classmethod
    def from_dict(cls, data, parent=None):
        node = cls(text=data.get("text", "新节点"), parent=parent)
        node.id = data.get("id", str(uuid.uuid4()))
        node.style = data.get("style", {})
        node.relations = data.get("relations", [])
        for child_data in data.get("children", []):
            cls.from_dict(child_data, parent=node)
        return node
        
    def to_markdown(self, indent=0):
        lines = []
        prefix = "  " * indent + "- "
        lines.append(f"{prefix}{self.text}")
        for child in self.children:
            lines.extend(child.to_markdown(indent + 1))
        return lines
        
    def to_xml(self, parent_element=None):
        if parent_element is None:
            elem = ET.Element("Node")
        else:
            elem = ET.SubElement(parent_element, "Node")
        elem.set("id", self.id)
        elem.set("text", self.text)
        for child in self.children:
            child.to_xml(elem)
        return elem
