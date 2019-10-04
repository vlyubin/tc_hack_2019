#!flask/bin/python
from app import app
import pandas as pd
import Levenshtein


@app.route('/symptom')
def symptom(symtoms):
	"""Takes a list of symptoms and returns a sorted list of top 5 diseases"""

	df = pd.read_excel('raw_data.xlsx')
# 	df[] = s.split(' ', 1)[1]
    
	df = df.fillna(method='ffill')
	df["match"] = 0

	for i in symtoms:
	    df["match"] += df["Symptom"].apply(lambda x: (str.lower(i) in str.lower(x))*1)

	return df.groupby("Disease")[["match", "Count of Disease Occurrence"]].sum().sort_values(["match", "Count of Disease Occurrence"], ascending = False).reset_index().head(10)
# 	return df.sort_values("lev_ratio_match", ascending = False).head(20)


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=9999, debug = True)

