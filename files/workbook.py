import json

class PromptGroup:
  def __init__(self, passage_prompt, question_prompt, answer_prompt):
    self.passage_prompt = passage_prompt
    self.question_prompt=question_prompt
    self.answer_prompt = answer_prompt
    
  def toJSON(self):
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2)

  def jsonify(self):
    return dict(passage_prompt = self.passage_prompt, question_prompt = self.question_prompt, answer_prompt = self.answer_prompt)


def parse_prompts(json_obj):
  prompts=[]
  for prompts in json_obj:
    prompt_to_add = PromptGroup(json_obj["passage_prompt"], json_obj["question_prompt"], json_obj["answer_prompt"])
    prompts.append(prompt_to_add)

  return prompts


def load_prompts(file_path):
  prompts = []
  with open(file_path) as _file:
    json_data = json.load(_file)
    
    for prompt_group in json_data:
      prompts.append(PromptGroup(prompt_group["passage_prompt"], prompt_group["question_prompt"], prompt_group["answer_prompt"]))
  return prompts

class ComplexEncoder(json.JSONEncoder):
  def default(self, obj):
    if hasattr(obj,'jsonify'):
      return obj.jsonify()
    else:
      return json.JSONEncoder.default(self, obj)
    
def save_prompts(prompts, file_path):
  with open(file_path, "w") as json_file:
    json_file.write(json.dumps(prompts, cls=ComplexEncoder))
  

class QuestionGroup:
  def __init__(self, question: str, responses: list, answer: str):
    self.question = question
    self.responses = responses
    self.answer = answer

  def jsonify(self):
    return dict(question = self.question, responses = self.responses, answer = self.answer)

class PassageGroup:
  def __init__(self, passage: str, questions: str, answers: str, topic: str):
    self.passage = passage
    self.questions= questions
    self.answers = answers
    self.topic = topic
  
  def jsonify(self):
    return dict(passage = self.passage, questions = self.questions, answers=self.answers, topic = self.topic)


class Workbook:
  def __init__(self, title, passage_groups: list):
    self.title = title
    self.passage_groups = passage_groups

  def jsonify(self):
    return dict(title = self.title, passage_groups = self.passage_groups)


def parse_question_group(json_obj):
  question_group_to_add = QuestionGroup(json_obj["question"], json_obj["responses"], json_obj["answer"])
  return question_group_to_add

def parse_passage_group(json_obj):
  # PassageGroup
  # Contains "passage" : str
  # Contains "question_groups" : list
  
  passage_group_to_add = PassageGroup(json_obj["passage"], json_obj["questions"], json_obj["answers"], json_obj["topic"])
  return passage_group_to_add



def parse_workbook(json_obj):

  # Workbook:
  #   -> Title
  #   -> PassageGroup
  #     -> List of Question Groups
  #       -> Each QuestionGroup
  #           -> Question
  #           -> Responses
  #           -> Answer

  passage_groups = []
  for passage_group in json_obj["passage_groups"]:
    passage_groups.append(parse_passage_group(passage_group))

  workbook = Workbook(json_obj["title"], passage_groups)
  return workbook
  