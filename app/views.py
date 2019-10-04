from flask import request, session
from flask import Flask, render_template, jsonify, request, redirect, url_for
from app import app
import datetime
import os, json
import plotly
import plotly.graph_objs as go
import pandas as pd
import json

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
  data = pd.read_csv("data/two_user_claims.csv")
  print(data)
  claims_df_mem = data[data.members_id == "96d55072fb0560d1"]


  claims_df_mem['event_date'] = claims_df_mem.event_date.apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ"))

  claims_df_mem.sort_values('event_date', inplace = True)


  start = claims_df_mem.event_date.iloc[0]
  end = claims_df_mem.event_date.iloc[-1]
  date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days)]

  df = pd.DataFrame(data={'event_date': date_generated})

  temp_df = df.merge(claims_df_mem[['event_date', 'net_paid_amt']], how = 'left', on = 'event_date')

  temp_df['cum_net_paid_amt'] = temp_df.net_paid_amt.fillna(0).cumsum()


  # fig = go.Figure()
  # fig.add_trace(go.Scatter(
  #                 x=temp_df['event_date'],
  #                 y=temp_df['cum_net_paid_amt'],
  #                 name="Ammount Spent so far",
  #                 line_color='deepskyblue',
  #                 opacity=0.8))
  # return render_template(fig.show())


  graphs = [
    dict(
      data=[
        dict(
          x=temp_df['event_date'],
          y=temp_df['cum_net_paid_amt'],
          type='scatter'
        ),
      ],
      layout=dict(
        title='first graph'
      )
    )

    # dict(
    #   data=[
    #     dict(
    #       x=ts.index,  # Can use the pandas data structures directly
    #       y=ts
    #     )
    #   ]
    # )
  ]

  # Add "ids" to each of the graphs to pass up to the client
  # for templating
  ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

  # Convert the figures to JSON
  # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
  # objects to their JSON equivalents
  graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

  return render_template('claims.html',
               ids=ids,
               data_x=list(map(str, list(temp_df['event_date']))),
               data_y=list(temp_df['cum_net_paid_amt']))




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
