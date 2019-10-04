import pandas as pd

from ast import literal_eval

from cdqa.utils.filters import filter_paragraphs
from cdqa.utils.download import download_model, download_bnpp_data
from cdqa.pipeline.cdqa_sklearn import QAPipeline

from flask import Flask, request
app = Flask(__name__)

df = pd.read_csv('data/mayo.csv',converters={'paragraphs': literal_eval})
df = filter_paragraphs(df)
cdqa_pipeline = QAPipeline(reader='models/bert_qa_vGPU-sklearn.joblib', retriever="tfidf")
cdqa_pipeline = cdqa_pipeline.to("cuda")
cdqa_pipeline.fit_retriever(df)


def answer_mayo_query(query):
  prediction = cdqa_pipeline.predict(query)
  return prediction

def answer_wellness_query(query):
  prediction = cdqa_pipeline.predict(query)
  return prediction

@app.route('/', methods=['POST'])
def answer():
  data = request.get_json()

  if data['source'] == 'mayo':
    return json.dumps(answer_mayo_query(data['query']))

  if data['source'] == 'wellness':
    return json.dumps(answer_wellness_query(data['query']))

  raise Exception()

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80, threaded=False)
