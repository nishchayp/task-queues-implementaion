CREATE DATABASE IF NOT EXISTS celery_tasks;
CREATE DATABASE IF NOT EXISTS baseline_data;
USE baseline_data;
CREATE TABLE IF NOT EXISTS data(
	id INTEGER PRIMARY KEY AUTO_INCREMENT,
	field1 VARCHAR(50),
	field2 VARCHAR(50)
);