import json
import os
from flask import Flask, redirect, url_for, render_template, request
import sys
from files.section import Section, SectionType, load_sections, save_sections
from files.model import Model, save_models, load_models
from files.workbook import Workbook, QuestionGroup
from files.gptapi import generate_passage_group


app = Flask(__name__)

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
# abs_file_path = os.path.join(script_dir, rel_path)
saved_sections_path = os.path.join(rel_path_sections)
saved_models_path = os.path.join(rel_path_models)


sections = load_sections(saved_sections_path)
models = load_models(saved_models_path)

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
    return render_template("create-workbook.html", models=models, section=section)
  
  
  section_type_value=request.form['section_type']
  section = sections[section_type_value]
  passages_count = int(request.form['passages-count'])
  questions_per_passage = int(request.form['questions-per-passage'])
  model = models[int(request.form['chosen-model'])]
  topics_list = request.form['topic-list'].split('\r\n')

  passage_groups = []
  for i in range(passages_count):
    topic = topics_list[i] if i < len(topics_list) else topics_list[len(topics_list)-1]
    print("\n######_Generating Passage "+str(i)+"_###########")
    passage_group = generate_passage_group(model, topic, SectionType(section_type_value), questions_per_passage)
    passage_groups.append(passage_group)

  workbook = Workbook(passage_groups)

  section.add_workbook(workbook)
  workbook_index = len(section.workbooks)-1

  save_sections(sections, saved_sections_path)

  return redirect(url_for('view_workbook', section_type=section_type_value, workbook_index=workbook_index)) 


@app.route("/upload/workbook", methods=["POST"])
def upload_workbook():
  workbook=request.form['workbook']
  section_type_value=request.form['section_type']
  section = sections[section_type_value]
  print('\n\n')
  print(workbook)
  return redirect(url_for('section', section=section)) 


  
  

@app.route("/view/workbook", methods=["GET", "POST"])
def view_workbook():
  if request.method == "GET":
    section_type_value=request.args.get('section_type')
    workbook_index=int(request.args.get('workbook_index'))

    section = sections[section_type_value]
    workbook = section.workbooks[workbook_index]

    return render_template("view-workbook.html", section = section, workbook = workbook)


@app.route("/model", methods=["GET", "POST"])
def models_list():
  print("models count:" + str(len(models)))
  return render_template("models.html", models=models)
  
@app.route("/model/create", methods=["GET", "POST"])
def create_model():
  if request.method == "GET":
    return render_template("create-model.html")

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
  return redirect(url_for('models_list'))

@app.route("/model/delete", methods=["GET"])
def delete_model():
  model_index=int(request.args.get('model_index'))
  models.pop(model_index)
  save_models(models, saved_models_path)
  return redirect(url_for('models_list')) 



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
    responses = request.form['responses'+str(i)].split('\r\n')
    question_groups.append(QuestionGroup(question, responses, answer))


  models.append(Model(title, section, text, question_groups))


  save_models(models, saved_models_path)
  print("Model Created + Saved!")
  return redirect(url_for('models_list'))


if __name__ == "__main__":
  # webbrowser.open('http://127.0.0.1:8000')  # Go to example.com
  app.run(port=8000)
