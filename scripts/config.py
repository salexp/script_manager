import os
from lxml import etree, objectify


class CmdConfig(object):
    def __init__(self, command, file_name, force_new=False):
        self.command = command
        self.file_name = file_name

        if os.path.isfile(file_name) and not force_new:
            tree = objectify.parse(file_name)
            root = tree.getroot()
        else:
            root = objectify.Element('Config')

        self.root = root
        self.save()
        self._init = True

    def __setattr__(self, key, value):
        if not getattr(self, '_init', False) or key == '_init':
            super(CmdConfig, self).__setattr__(key, value)
        else:
            el = objectify.SubElement(self.root, key)
            el._setText(str(value))

    def add_element(self, key, value, attrib={}):
        el = objectify.SubElement(self.root, key)
        el._setText(str(value))
        for k, v in attrib.items():
            el.attrib[k] = str(v)

    def reset(self, children=[]):
        self._init = False
        self.root = objectify.Element('Config')
        for child in children:
            el = objectify.SubElement(self.root, child)

        self.save()
        self._init = True

    def save(self):
        with open(self.file_name, 'w') as f:
            et = etree.ElementTree(self.root)
            et.write(f, encoding='UTF-8', method='xml', pretty_print=True, xml_declaration=True)
