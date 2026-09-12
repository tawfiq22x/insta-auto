import xml.etree.ElementTree as ET
xml_str = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
    <node index="0" text="GET STARTED" resource-id="com.instagram.android:id/btn" class="android.widget.Button" bounds="[0,0][100,100]" content-desc="" checked="false" clickable="true" enabled="true" focusable="true" focused="false" long-clickable="false" password="false" scrollable="false" selected="false" boundsInParent="[0,0][100,100]" boundsInScreen="[0,0][100,100]" />
</hierarchy>"""

xml_str_lower = xml_str.lower()
try:
    root = ET.fromstring(xml_str_lower)
    print("Success!")
    for node in root.iter('node'):
        print("Found node:", node.attrib.get('text'))
except Exception as e:
    print("Error:", e)
