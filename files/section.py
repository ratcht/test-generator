from enum import Enum
import json
from files.workbook import Workbook, parse_workbook

class SectionType(str, Enum):
  READING="Reading"
  GRAMMAR="Grammar"
  SCIENCE="Science"


class Section:
  def __init__(self, section_type: SectionType):
    self.section_type=section_type

    self.workbooks = []
  
  def add_workbook(self, workbook):
    self.workbooks.append(workbook)

  def jsonify(self):
    return dict(section_type = self.section_type, workbooks = self.workbooks)
  


class ComplexEncoder(json.JSONEncoder):
  def default(self, obj):
    if hasattr(obj,'jsonify'):
      return obj.jsonify()
    else:
      return json.JSONEncoder.default(self, obj)


def save_sections(sections, file_path):
  with open(file_path, "w") as json_file:
    json_file.write(json.dumps(sections, cls=ComplexEncoder))


def load_sections(file_path):
  sections = {}
  with open(file_path) as _file:
    json_data = json.load(_file)
    
    for section in json_data:
      section_type = SectionType(section["section_type"])
      print(section_type)
      print(section_type.value)
      section_to_add = Section(section_type)
      for workbook in section['workbooks']:
        section_to_add.add_workbook(parse_workbook(workbook))
      sections[section_type.value] = section_to_add

    # init sections if json is empty
    if len(sections) < 3:
      sections = {}
      for section_type in SectionType:
        section_to_add = Section(section_type)
        sections[section_type.value] = section_to_add
  return sections