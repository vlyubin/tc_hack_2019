from flask import request, session
from flask import Flask, render_template, jsonify, request, redirect, url_for, make_response
from app import app
import datetime
import os, json
import plotly
import plotly.graph_objs as go
import pandas as pd
import json
import urllib
import urllib.request
import urllib.parse
import requests
from .utils import get_title_to_url_cahce

ML_SERVER_URL = 'http://ec2-34-209-226-198.us-west-2.compute.amazonaws.com:5000'

@app.route('/symptom')
def symptom(symtoms):
  """Takes a list of symptoms and returns a sorted list of top 5 diseases"""

  df = pd.read_excel('data/raw_data.xlsx')
    
  df = df.fillna(method='ffill')
  df["match"] = 0

  for i in symtoms:
      df["match"] += df["Symptom"].apply(lambda x: (str.lower(i) in str.lower(x))*1)

  return df.groupby("Disease")[["match", "Count of Disease Occurrence"]].sum().sort_values(["match", "Count of Disease Occurrence"], ascending = False).reset_index().head(10)

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/logout')
def logout():
  resp = make_response(redirect('/'))
  resp.set_cookie('logged_id', 'no')
  return resp 

@app.route('/login')
def login():
  return render_template('login.html')

@app.route('/search', methods=['POST'])
def search():
  info = request.get_json(force=True)
  data = {
    'source': 'mayo',
    'query': info['query']
  }

  url = ML_SERVER_URL + '?' + urllib.parse.urlencode(data) 
  response = requests.post(url=url) 
  print(response.json())

  rv = response.json()
  for entry in rv:
    entry[3] = get_title_to_url_cahce()[entry[1].split('-')[0]]

  return json.dumps(rv)

@app.route('/login_handler')
def login_handler():
  resp = make_response(redirect('/my-info'))
  resp.set_cookie('logged_id', 'yes')
  return resp 

@app.route('/self-diagnosis')
def sd():
  return render_template('self_diagnose.html')

@app.route('/staying-healthy')
def sh():
  return render_template('stay_healthy.html')

@app.route('/disease-info')
def di():
  return render_template('stay_healthy.html')

@app.route('/my-info')
def claims():
  if request.cookies.get('logged_id', None) != 'yes':
      return render_template('unathenticated.html')

  return render_template('claims.html')

@app.route('/base')
def base():
  return render_template('base.html')

#################################
# Error handlers
#################################

@app.errorhandler(404)
def page_not_found(e):
  return err404()

@app.errorhandler(500)
def page_not_found(e):
  return err500()

def err404():
  return render_template('404.html'), 404

def err500():
  return render_template('500.html'), 500
