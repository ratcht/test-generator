import json
import os
from flask import Flask, redirect, url_for, render_template, request
import sys
from files.section import Section, SectionType, load_sections, save_sections
from files.model import Model, save_models, load_models
from files.workbook import Workbook, QuestionGroup, load_prompts, save_prompts, parse_prompts, PromptGroup
from files.gptapi import generate_passage_group
from files.upload import create_document


app = Flask(__name__)

class ComplexEncoder(json.JSONEncoder):
  def default(self, obj):
    if hasattr(obj,'jsonify'):
      return obj.jsonify()
    else:
      return json.JSONEncoder.default(self, obj)
    
# Load Sections

def resource_path(relative_path):
  """ Get absolute path to resource, works for dev and for PyInstaller """
  try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")

  return os.path.join(base_path, relative_path)


script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
rel_path_sections = "files/text/saved-sections.json"
rel_path_models = "files/text/saved-models.json"
rel_path_prompts = "files/text/saved-prompts.json"

#saved_sections_path = os.path.join(script_dir, rel_path_sections)
#saved_models_path = os.path.join(script_dir, rel_path_models)

saved_sections_path = os.path.join(script_dir, rel_path_sections)
saved_models_path = os.path.join(script_dir,rel_path_models)
saved_prompts_path = os.path.join(script_dir,rel_path_prompts)



sections = load_sections(saved_sections_path)
models = load_models(saved_models_path)
prompts = load_prompts(saved_prompts_path)

print("Sections: ")
print(sections)
print("\nModels:")
print(models)

@app.route("/", methods=["GET"])
def index():
  
  return render_template("index.html")


@app.route("/section", methods=["GET"])
def section():
  section_type_value=request.args.get('section_type')
  section = sections[section_type_value]

  return render_template("test-section.html", section=section)


@app.route("/create/workbook", methods=["GET", "POST"])
def create_workbook():
  if request.method == "GET":
    section_type_value=request.args.get('section_type')
    section = sections[section_type_value]

    # filter models
    filtered_models = []

    for model in models:
      if model.section_type.value == section_type_value:
        filtered_models.append(model)

    return render_template("create-workbook.html", models=filtered_models, section=section, prompts=prompts, prompts_json=json.dumps(prompts, cls=ComplexEncoder))
  
  title=request.form['title']
  section_type_value=request.form['section_type']
  section = sections[section_type_value]
  passages_count = int(request.form['passages-count'])
  questions_per_passage = int(request.form['questions-per-passage'])
  model = models[int(request.form['chosen-model'])]
  topics_list = request.form['topic-list'].split('\r\n')

  passage_prompt = request.form['passage-prompt']
  question_prompt = request.form['question-prompt']
  answer_prompt = request.form['answer-prompt']
  prompt_group = PromptGroup(passage_prompt, question_prompt, answer_prompt)

  passage_groups = []
  for i in range(passages_count):
    topic = topics_list[i] if i < len(topics_list) else topics_list[len(topics_list)-1]
    print("\n######_Generating Passage "+str(i)+"_###########")
    passage_group = generate_passage_group(model, topic, SectionType(section_type_value), questions_per_passage, prompt_group)
    passage_groups.append(passage_group)

  workbook = Workbook(title, passage_groups)

  section.add_workbook(workbook)
  workbook_index = len(section.workbooks)-1


  save_sections(sections, saved_sections_path)

  return redirect(url_for('view_workbook', section_type=section_type_value, workbook_index=workbook_index)) 

@app.route("/save/prompts", methods=["POST"])
def save_post_prompts():
  print("Here!")
  body = request.get_json()
  passage_prompt=body['passage_prompt']
  question_prompt=body['question_prompt']
  answer_prompt=body['answer_prompt']

  new_prompt_group = PromptGroup(passage_prompt, question_prompt, answer_prompt)
  prompts.append(new_prompt_group)

  section_type_value=str(body['section_type'])

  save_prompts(prompts, saved_prompts_path)

  return redirect(url_for('create_workbook', section_type=section_type_value))


@app.route("/upload/workbook", methods=["POST"])
def upload_workbook():
  workbook_index=int(request.form['workbook_index'])
  section_type_value=request.form['section_type']
  section = sections[section_type_value]
  workbook = section.workbooks[workbook_index]

  print('\n\n')
  create_document(workbook)
  return redirect(url_for('index')) 

  
@app.route("/delete/workbook", methods=["GET"])
def delete_workbook():

  workbook_index=int(request.args.get('workbook_index'))
  section_type_value=request.args.get('section_type')
  sections[section_type_value].workbooks.pop(workbook_index)
  save_sections(sections, saved_sections_path)
  return redirect(url_for('index')) 

@app.route("/view/workbook", methods=["GET", "POST"])
def view_workbook():
  print("Viewing Workbook")
  if request.method == "GET":
    section_type_value=request.args.get('section_type')
    workbook_index=int(request.args.get('workbook_index'))

    section = sections[section_type_value]
    workbook = section.workbooks[workbook_index]

    return render_template("view-workbook.html", section = section, workbook = workbook, workbook_index = workbook_index)


@app.route("/model/view", methods=["POST"])
def models_list():
  #section_type_value=request.args.get('section_type')
  section_type_value=request.form['section-type']

  #print("models count:" + str(len(models)))
    # filter models
  filtered_models = []
  filtered_indices = []
  for i, model in enumerate(models):
    print (model.section_type.value)
    if model.section_type.value == section_type_value:
      filtered_models.append(model)
      filtered_indices.append(i)
        
  return render_template("models.html", models=filtered_models, section_type=section_type_value, indices=filtered_indices)
  
@app.route("/model/create", methods=["POST"])
def create_page_model():
  section_type_value=request.form['section-type']
  question_length = 10
  
  if section_type_value == "Grammar":
    question_length = 15

  return render_template("create-model.html", section_type=section_type_value, question_length = question_length)



@app.route("/model/add", methods=["POST"])
def create_model():
  title = request.form['title']
  section = SectionType(request.form['section-type'])
  text = request.form['model-text']

  # Get Question List
  question_groups=[]
  number_of_questions = int(request.form['number-of-questions'])
  print(number_of_questions)

  
  answers = request.form['answers'].split(' ')

  for i, answer in enumerate(answers):
    question = request.form['question'+str(i)]
    responses = request.form['responses'+str(i)].split('\r\n')
    question_groups.append(QuestionGroup(question, responses, answer))


  models.append(Model(title, section, text, question_groups))


  save_models(models, saved_models_path)
  print("Model Created + Saved!")

  return redirect(url_for('section', section_type=section.value))

@app.route("/model/delete", methods=["GET"])
def delete_model():
  # fix later
  model_index=int(request.args.get('model_index'))
  models.pop(model_index)
  save_models(models, saved_models_path)
  return redirect(url_for('index'))



@app.route("/model/edit", methods=["GET", "POST"])
def update_model():
  model_index=int(request.args.get('model_index'))
  if request.method == "GET":
    return render_template("edit-model.html", model=models[model_index])
  
  title = request.form['title']
  section = SectionType(request.form['section-type'])
  text = request.form['model-text']

  # Get Question List
  question_groups=[]
  number_of_questions = int(request.form['number-of-questions'])
  print(number_of_questions)

  
  answers = request.form['answers'].split(' ')

  for i, answer in enumerate(answers):
    question = request.form['question'+str(i)]
    responses = request.form['responses'+str(i)].removesuffix('\r\n').split('\r\n')
    question_groups.append(QuestionGroup(question, responses, answer))


  models.append(Model(title, section, text, question_groups))


  save_models(models, saved_models_path)
  print("Model Created + Saved!")

  return redirect(url_for('section', section_type=section.value))


if __name__ == "__main__":
  # webbrowser.open('http://127.0.0.1:8000')  # Go to example.com
  app.run(port=8000)
