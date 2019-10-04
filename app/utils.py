from .storage import retrive_all_webpages

TITLE_TO_URL_CACHE = {}

def make_title_to_url_cache():
  if len(TITLE_TO_URL_CACHE) != 0:
    return

  for page in retrive_all_webpages():
    TITLE_TO_URL_CACHE[page[0].split('-')[0]] = page[1]

# TODO: from csv

def get_title_to_url_cahce():
  global TITLE_TO_URL_CACHE
  if len(TITLE_TO_URL_CACHE) == 0:
    make_title_to_url_cache()
  return TITLE_TO_URL_CACHE
