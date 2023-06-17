import openai
import re
import os
import logging
import sys
from files.model import Model
from files.workbook import Workbook, PassageGroup, QuestionGroup, PromptGroup
from files.section import SectionType

alphabet="abcdefghijklmnopqrstuvwxyz"

def resource_path(relative_path):
  """ Get absolute path to resource, works for dev and for PyInstaller """
  try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")
  return os.path.join(base_path, relative_path)


script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
rel_path = "api-key.txt"
abs_file_path = os.path.join(script_dir,rel_path)
# abs_file_path = resource_path(rel_path)
print(abs_file_path)

with open(abs_file_path) as f:
  # authenticate openai
  api_key=f.readline()
  openai.api_key = api_key


def generate_passage_group(model: Model, topic, section_type:SectionType, number_of_questions, prompt_group: PromptGroup):
  # generate passage first
  passage_prompt = prompt_group.passage_prompt
  passage_prompt = passage_prompt.replace("[section_value]", section_type.value)
  passage_prompt = passage_prompt.replace("[topic]", topic)
  print("-----Loading Passage-------")
  passage = generate_response(model, passage_prompt)

  # then generate questions
  questions_prompt = prompt_group.question_prompt
  questions_prompt = questions_prompt.replace("[num_questions]", str(number_of_questions))
  questions_prompt = questions_prompt.replace("[topic]", topic)
  print("\n-----Loading Questions-------")
  questions_prompt = questions_prompt.replace("[passage]", passage)
  questions = generate_response(model, questions_prompt)


  # then generate answers
  answers_prompt = prompt_group.answer_prompt
  answers_prompt = answers_prompt.replace("[passage]", passage)
  answers_prompt = answers_prompt.replace("[questions]", questions)
  print("-----Loading Answers-------")
  answers = generate_response(model, answers_prompt)

  return PassageGroup(passage, questions, answers, topic)

def generate_response(model, content):
  print("Waiting for GPT")

  # Prepare model for AI
  questions = ""
  answers = ""
  for question_group in model.sample_question_groups:
    questions += (question_group.question+"\n") # add question to string
    answers += str(question_group.answer)+"\n"
    # add in responses
    for i, response in enumerate(question_group.responses):
      questions+=response

  response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You have been named the Chief Question Writer for the next ACT test. Your primary objectives are not only to maintain the high quality standards required of a standardized test (by making sure each test examines students on the same concepts in the same ways), but to make the questions and passages rigorous yet extremely fascinating to precocious high schoolers."},
        {"role": "user", "content": "Below is an example of a "+ model.section_type.value+ " type passage from the ACT "+model.section_type.value+" section. I want you to read through the entire passage and answer the questions that follow it. I will include the answers to the questions at the very bottom so you can confirm your understanding of the passage and questions is on the same page. Ask any clarifying questions if you are uncertain of how the text is presented/formatted, but you do not need to list back the answers for the given passage. Also note the number of words contained in the prose of the passage, just to yourself. This will be important for your next assignment. "+model.text + "\nQuestions:\n"+questions+"\nAnswers:\n"+answers},
        {"role": "assistant", "content": "Understood."},
        {"role": "user", "content": content}
      ]
  )
  return response['choices'][0]['message']['content']