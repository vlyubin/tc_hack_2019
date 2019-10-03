from flask import request, session
from flask import Flask, render_template, jsonify, request, redirect, url_for
from app import app
import datetime
import os, json

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/logout')
def logout():
  # TODO: Remove login cookie
  return redirect('/')

@app.route('/login')
def login():
  return render_template('login.html')

@app.route('/self-diagnosis')
def sd():
  return render_template('self_diagnose.html')

@app.route('/staying-healthy')
def sh():
  return render_template('stay_healthy.html')

@app.route('/my-info')
def claims():
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
