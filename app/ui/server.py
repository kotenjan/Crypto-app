from typing import overload
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from ui.parser import Parser

# what type of data do display in chart - overview or predictions
overview = True
app = Flask(__name__)
CORS(app)
parser = Parser()

@app.route('/data/')
def predictions(success=True, message=''):
	return jsonify({
		'data': parser.get_predicted_intervals(),
		'success': success,
		'message': message,
	})

@app.route('/add/')
def add():
	name = request.args.get('name', default=None, type=str)
	symbol = request.args.get('symbol', default=None, type=str)
	response = parser.add_name(name, symbol)
	if response:
		return predictions(False, response)
	return predictions()

@app.route('/remove/')
def remove():
	name = request.args.get('name', default=None, type=str)
	parser.remove_name(name)
	parser.remove_table(name)
	return predictions()

@app.route('/mode/')
def change_mode():
	global overview
	overview = not overview
	limit = request.args.get('limit', default=100, type=int)
	if overview:
		data = parser.build_dataset(limit)
	else:
		data = parser.get_comparation_chart(limit)
	return jsonify(data)

@app.route('/chart/')
def chart():
	global overview
	limit = request.args.get('limit', default=100, type=int)
	if overview:
		data = parser.build_dataset(limit)
	else:
		data = parser.get_comparation_chart(limit)
	return jsonify(data)

@app.route('/')
def get_view():
	return render_template('index.html')

def start():
	app.run(host='0.0.0.0')
