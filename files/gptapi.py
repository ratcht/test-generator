import openai
import re
import os
import logging
import sys
from files.model import Model
from files.workbook import Workbook, PassageGroup, QuestionGroup
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
rel_path = "files/api-key.txt"
# abs_file_path = os.path.join(script_dir, rel_path)
abs_file_path = resource_path(rel_path)

with open(abs_file_path) as f:
  # authenticate openai
  api_key=f.readline()
  openai.api_key = api_key


def generate_passage_group(model: Model, topic, section_type:SectionType, number_of_questions):
  # generate passage first
  passage_prompt = "Generate a new "+section_type.value+" passage on the topic: "+topic +" with an identical verbal length within each section of prose to the example passage given; aim for a verbal complexity level 20%% harder than the example passage with a Flesch Reading Ease score that is 20%% higher than the example passage, and a Flesch-Kincaid Grade Level that is 20% higher than the example passage. This will ensure that the text is more complex in terms of both readability and grade level. Note the common sentence lengths, sentence structures and formulations of the example passage; note the narrative tone of the given passage, the manner in which any conflicts present themselves within the example passage, as well as the level of detail within the given passage - use and incorporate as many of these details as you can to help you formulate the new passage you are about to generate, which will help you maintain the ACTs standard across tests."
  passage = generate_response(model, passage_prompt)

  # then generate questions
  questions_prompt = "For the following passage, I want you to generate a numbered list of "+str(number_of_questions)+" multiple choice questions that test the same exact skills (question for question) as the ten questions that appear in the example questions below. Make sure all questions are numbered. These questions should test the student on the newly generated passage at a difficulty level equal to or slightly harder than the example questions given. Try to make the wording and constructions of the question stems very close to the example questions given - don't be afraid to repeat primary phrases. Phrase and structure the new questions similarly to the examples. (So when a question asks about lines in the passage, your new question should do the same). When creating the multiple-choice questions, ensure that the wrong answer choices are plausible and strongly constructed. The wrong answer choices should be related to the passage, derived from other parts of the passage, or contain partially correct information. This will ensure that the questions test the reader's comprehensive understanding of the passage. The answers should follow the same structures/presentations as the answers from the corresponding examples given. When generating your new multiple choice questions, please start with the same first number as the example questions. Make sure there are "+str(number_of_questions)+" questions. DO NOT INCLUDE WHICH OPTION IS THE ANSWER WITH THE OUTPUT. The passage that you will generate the questions for is the following: "+passage
  questions = generate_response(model, questions_prompt)


  # then generate answers
  answers_prompt = "For the following questions and passage, generate a set of answers to each one. Write a list of letters that correspond to each multiple choice answer. Make sure there is an answer for each question. The passage: "+passage+".\nThe questions:\n"+questions
  answers = generate_response(model, answers_prompt)
  answers = re.sub(r'\d+. ', '', answers)
  answers = answers.split('\n')

  # Parse questions with regex
  questions_unparsed = re.split(r"\b[0-9]*[0-9]+.", questions)
  if questions_unparsed[0] == '':
    questions_unparsed.pop(0)

  questions_parsed = []
  for i, unparsed in enumerate(questions_unparsed):
    questions_parsed.append(str(i+1)+"."+unparsed)

  # Parse question groups
  question_groups=[]

  print("Questions Length: "+str(len(questions_parsed)))
  print("Answers Length: " + str(len(answers)))
  min_length = min(len(questions_parsed), len(answers))
  questions_parsed = questions_parsed[:min_length]
  answers = answers[:min_length]
  print("\nUpdated:")
  print("Questions Length: "+str(len(questions_parsed)))
  print("Answers Length: " + str(len(answers)))


  for i, question in enumerate(questions_parsed):
    list_split = question.split('\n')
    quest = list_split[0]
    responses = list_split[1:len(list_split)]
    print("Response: ")
    print(responses)
    while responses[len(responses)-1] == '':
      responses.pop(len(responses)-1)
    
    answer_uncut = answers[i]
    answer = answer_uncut[len(answer_uncut)-1]

    question_group = QuestionGroup(quest, responses, answer)
    question_groups.append(question_group)

  print("--------------")
  print("Passage: ")
  print(passage)
  print("--------------")
  print("Questions:")
  print(question_groups)
  print("--------------")
  print("Answers:")
  print(answers)
  print('\n')

  return PassageGroup(passage, question_groups, topic)



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