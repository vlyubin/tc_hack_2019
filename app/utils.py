import pandas as pd
from .storage import retrive_all_webpages

TITLE_TO_URL_CACHE = {}

def make_title_to_url_cache():
  if len(TITLE_TO_URL_CACHE) != 0:
    return

  print('make_title_to_url_cache')

  for page in retrive_all_webpages():
    TITLE_TO_URL_CACHE[page[0].split('-')[0]] = page[1]

  print('Cache made!')

def make_title_to_url_cache2():
  z = pd.read_csv('data/mayo.csv')
  for index, row in z.iterrows():
    #print(row['title'], row['url'])
    TITLE_TO_URL_CACHE[row['title'].split('-')[0]] = row['url']

def get_title_to_url_cahce():
  global TITLE_TO_URL_CACHE
  if len(TITLE_TO_URL_CACHE) == 0:
    make_title_to_url_cache()
  return TITLE_TO_URL_CACHE

df = pd.read_excel('data/raw_data.xlsx')
df = df.fillna(method='ffill')
df['Disease'] = df.Disease.apply(lambda x: str(x).split('_')[1])
df['Symptom'] = df.Symptom.apply(lambda x: str(x).split('_')[1])
df['Disease'] = df.Disease.apply(lambda x: str(x).split('^')[0])

make_title_to_url_cache2()
