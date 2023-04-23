from files.section import SectionType, ComplexEncoder
from files.workbook import QuestionGroup, parse_question_group
import json

class Model:
  def __init__(self, title, section_type: SectionType, text, sample_question_groups: list):
    self.title = title
    self.section_type = section_type
    self.text = text
    self.sample_question_groups = sample_question_groups

  def jsonify(self):
    return dict(title = self.title, section_type = self.section_type, text = self.text, question_groups = self.sample_question_groups)
  
def save_models(models, file_path):
  with open(file_path, "w") as json_file:
    json_file.write(json.dumps(models, cls=ComplexEncoder))


def load_models(file_path):
  models = []
  with open(file_path) as _file:
    json_data = json.load(_file)
    
    for model in json_data:
      section_type = SectionType(model["section_type"])

      # parse question groups:
      sample_question_groups = []
      for question_group in model["question_groups"]:
        sample_question_groups.append(parse_question_group(question_group))

      model_to_add = Model(model['title'], section_type, model['text'], sample_question_groups)
      models.append(model_to_add)

  return models