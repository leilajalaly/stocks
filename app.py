from alpha_vantage.timeseries import TimeSeries
from flask import Flask, jsonify, request
from flask_cqlalchemy import CQLAlchemy

#Flask setup
app = Flask(__name__)
app.config['CASSANDRA_HOSTS'] = ['cassandra']
app.config['CASSANDRA_KEYSPACE'] = "stocks"
app.config['CQLENG_ALLOW_SCHEMA_MANAGEMENT'] = True
db = CQLAlchemy(app)

class Equity(db.Model):
    equity_name = db.columns.Text(primary_key=True,required=True)
    equity_timestamp = db.columns.List(db.columns.Text,required=False)
    equity_open = db.columns.List(db.columns.Text,required=False)
    equity_high = db.columns.List(db.columns.Text,required=False)
    equity_low = db.columns.List(db.columns.Text,required=False)
    equity_close = db.columns.List(db.columns.Text,required=False)
    equity_volume = db.columns.List(db.columns.Text,required=False)
db.sync_db()


@app.route('/', methods = ['GET'])
def get_all_equity_names():
	q = Equity.all()
	count = len(q)
	name=[]
	for i in range(count):
		name.append(q[i]['equity_name'])
	return jsonify(name)

@app.route('/<name>', methods = ['GET'])
def get_data_by_name(name):
	q = Equity.all()
	count = len(q)
	names=[]
	for i in range(count):
		names.append(q[i]['equity_name'])
	if name in names:
		named_records = dict(Equity.get(equity_name=name))
		return jsonify(named_records), 200
	else:
		return jsonify({'error':'equity name not found!'}), 404


@app.route('/', methods=['POST'])
def create_records():

	if not request.json or not 'name' in request.json:
		return jsonify({'error':'the new record needs to have an equity name'}), 400
	name_input = {'name': request.json['name']}
	equity = name_input['name']

	#Initialize external API Alphavantage
	ts = TimeSeries(key='10LJJQ5BQXUED1VF')
	data = ts.get_daily(equity)

	#Extract dates to list
	dates = data[0].keys()
	timestamp=list(dates)

	#Extract quotes

	open_quote=[]
	for i in dates:
		open_quote.append(data[0][i]['1. open'])

	high_quote=[]
	for i in dates:
		high_quote.append(data[0][i]['2. high'])

	low_quote=[]
	for i in dates:
		low_quote.append(data[0][i]['3. low'])

	close_quote=[]
	for i in dates:
		close_quote.append(data[0][i]['4. close'])

	volume=[]
	for i in dates:
		volume.append(data[0][i]['5. volume'])

	#Add data to db

	Equity.create(equity_name=equity,equity_timestamp=timestamp,equity_open=open_quote,equity_high=high_quote,equity_low=low_quote,equity_close=close_quote,equity_volume=volume)

	return jsonify({'message': 'created: /{}'.format(equity)}), 201


if __name__ == '__main__':
    app.run('0.0.0.0',port=8080)