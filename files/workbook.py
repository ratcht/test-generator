class QuestionGroup:
  def __init__(self, question: str, responses: list, answer: str):
    self.question = question
    self.responses = responses
    self.answer = answer

  def jsonify(self):
    return dict(question = self.question, responses = self.responses, answer = self.answer)

class PassageGroup:
  def __init__(self, passage: str, question_groups: list, topic: str):
    self.passage = passage
    self.question_groups = question_groups
    self.topic = topic
  
  def jsonify(self):
    return dict(passage = self.passage, question_groups = self.question_groups, topic = self.topic)


class Workbook:
  def __init__(self, passage_groups: list):
    self.passage_groups = passage_groups

  def jsonify(self):
    return dict(passage_groups = self.passage_groups)


def parse_question_group(json_obj):
  question_group_to_add = QuestionGroup(json_obj["question"], json_obj["responses"], json_obj["answer"])
  return question_group_to_add

def parse_passage_group(json_obj):
  # PassageGroup
  # Contains "passage" : str
  # Contains "question_groups" : list
  question_groups = []
  for question_group in json_obj["question_groups"]:
    question_group_to_add = QuestionGroup(parse_question_group(question_group))
    question_groups.append(question_group_to_add)
  
  passage_group_to_add = PassageGroup(json_obj["passage"], question_groups)
  return passage_group_to_add



def parse_workbook(json_obj):

  # Workbook:
  #   -> PassageGroup
  #     -> List of Question Groups
  #       -> Each QuestionGroup
  #           -> Question
  #           -> Responses
  #           -> Answer

  passage_groups = []
  for passage_group in json_obj["passage_groups"]:
    passage_groups.append(parse_passage_group(passage_group))

  workbook = Workbook(passage_groups)
  return workbook
  