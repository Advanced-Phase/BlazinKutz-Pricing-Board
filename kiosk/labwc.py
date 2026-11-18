from pathlib import Path
import xml.etree.ElementTree as ET

tree = ET.parse("/etc/xdg/labwc/rc.xml")
root = tree.getroot()
namespace = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
if namespace:
    ET.register_namespace("", namespace[1:-1])
keyboard = root.find(namespace + "keyboard")
if keyboard is None:
    keyboard = ET.SubElement(root, namespace + "keyboard")
binding = ET.SubElement(keyboard, namespace + "keybind", key="C-A-w")
ET.SubElement(binding, namespace + "action", name="Execute", command="lxterminal -t 'Wi-Fi setup' -e /opt/blazin-kiosk/wifi-menu")
tree.write("/home/board/.config/labwc/rc.xml", encoding="utf-8")
