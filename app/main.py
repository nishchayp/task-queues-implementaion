from flask import Flask
from flask import jsonify
from flask_celery import make_celery
from celery.task.control import revoke
from celery.result import AsyncResult
from flask_sqlalchemy import SQLAlchemy
import string
from random import choice, randint

app = Flask(__name__)


#################
# Configuration #
#################

app.config['CELERY_BROKER_URL'] = "amqp://broker:5672/"
app.config['CELERY_RESULT_BACKEND'] = "db+mysql+pymysql://root:pw1234@database:3306/celery_tasks"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:pw1234@database:3306/baseline_data"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

celery = make_celery(app)
db = SQLAlchemy(app)


#########
# Model #
#########

class Data(db.Model):
	"""A Model to hold dummy data for purpose of showcasing the functioning of the REST API."""
	id = db.Column('id', db.Integer, primary_key = True)
	field1 = db.Column('field1', db.String(50))
	field2 = db.Column('field2', db.String(50))

	@property
	def serialize(self):
		"""Serializes data and thus enables being passed as valid argument to jsonify()."""
		return {
		'id': self.id,
		'field1': self.field1,
		'field2': self.field2,
		}


####################
# Helper functions #
####################

def get_rand_str():
	"""Generates a random string with length and characters of the string randomly 
	selected from the specified range of length and set of characters provided."""
	min_char = 8
	max_char = 12
	allchar = string.ascii_letters + string.digits
	rand_str = "".join(choice(allchar) for x in range(randint(min_char, max_char)))
	return rand_str


##############################
# Celery(Worker queue) tasks #
##############################

@celery.task(name = 'main.large_insert')
def large_insert(num):
	"""Inserts 'num' rows into the specified database table."""
	try:
		for x in range(0, num):
			field1 = get_rand_str()
			field2 = get_rand_str()
			data_entry = Data(field1 = field1, field2 = field2)

			db.session.add(data_entry)
		db.session.commit()
		app.logger.info('Data successfully inserted into database')
	except:
		db.session.rollback()
		app.logger.info('Rollback successfully, data not inserted into database')

@celery.task(name='main.revoke_and_rollback')
def revoke_and_rollback(task_id):
	"""Initiates request to remove task with the specified task_id from the Celery worker queue.
	The database is also made to rollback any changes made by the task."""
	revoke(task_id, terminate = True)
	app.logger.info('Request to revoke and rollback initiated')


#########################
# API endpoints(routes) #
#########################

@app.route('/')
def index():
	message = 'Implementing task queues using Celery & RabbitMQ'
	return jsonify(
		success = True,
		message = message
		)

@app.route('/insert')
@app.route('/insert/<int:num>')
def insert(num = 100000):
	"""Initiates request for insertion into database asynchronously by enqueuing it int0 the worker queue. 
	An optional URL parameter could be provided to specify the number of records to be inserted. If not specified the default value of 100000 is used."""
	result = large_insert.delay(num)
	message = 'Insertion into database started asynchronously. Use task_id to get task status and/or stop ongoing task'
	return jsonify(
		success = True,
		message = message,
		task_id = result.task_id
		)

@app.route('/dpd_insert')
@app.route('/dpd_insert/<int:num>')
def dpd_insert(num):
	"""This route should be deprecated as it inserts into database synchronously and thus blocking the server. 
	An optional URL parameter could be provided to specify the number of records to be inserted. If not specified the default value of 100000 is used."""
	large_insert(num)
	message = 'Insertion into database completed synchronously while blocking the database server.'
	return jsonify(
		success = True,
		message = message
		)

@app.route('/stop/<task_id>')
def stop(task_id):
	"""Initiates request to stop the task specefied by the task_id. Revokes the task by terminating
	the task from the worker queue meanwhile also performing database rollback."""
	revoke_and_rollback.delay(task_id)
	message = 'Initiated request to revoke task and rollback database. Use task_id to get task status.'
	return jsonify(
		success = True,
		message = message,
		task_id = task_id
		)

@app.route('/status/<task_id>')
def status(task_id):
	"""Gives the status of the task specified by the task_id."""
	result = celery.AsyncResult(task_id)
	return jsonify(
		success = True,
		task_id = task_id,
		status = result.status
		)

@app.route('/delete_all', methods = ['GET', 'DELETE'])
def delete_all():
	"""Deletes all the data from the table in database. Used to facilitate testing of the API."""
	try:
		num_rows_deleted = db.session.query(Data).delete()
		db.session.commit()
		return jsonify(
			success = True,
			message = 'Data table cleared',
			num_rows_deleted = num_rows_deleted
			)
	except:
		db.session.rollback()
		app.logger.error('Error occured while clearing data table')
		return jsonify(
			success = False,
			message = 'Error clearing data table'
			)

@app.route('/get_data')
def get_data():
	"""Gives all the data from the table in database. Used to facilitate testing of the API."""
	count = db.session.query(Data).count()
	data = Data.query.all()
	return jsonify(
		success = True,
		count = count,
		data = [x.serialize for x in data]
		)

@app.route('/get_data/count')
def get_data_count():
	"""Gives count of all the data from the table in database. Used to facilitate testing of the API."""
	count = db.session.query(Data).count()
	return jsonify(
		success = True,
		count = count
		)


if __name__ == '__main__':
	app.run(host='0.0.0.0')
