#!flask/bin/python
from app import app
import pandas as pd

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=9999, debug = True)
