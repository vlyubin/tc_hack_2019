from flask import request, session
from flask import Flask, render_template, jsonify, request, redirect, url_for
from app import app
import datetime
import os, json

@app.route('/login')
def login():
  return render_template('login.html')

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
