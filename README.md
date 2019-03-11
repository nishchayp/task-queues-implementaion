# task-queues-implementaion

## Abstract
Since uploading large data sets handicaps the server to process further requests, I've used Celery to implement task queues with RabbitMQ as the broker so as to allow the uploading of data sets to be an asynchronous task. Each such task is enqueued in the task queue and is assigned a unique `task_id`. This `task_id` could then be used to get the current status of the running task and also to revoke the task if required. It is also made sure that any task performing a write on the database if is revoked then a database rollback must come into action and thus keep the database consistent. This rollback is implemented through the two-phase commit feature of mysql. All these and yet more functionalities are provided to the user through a REST API which has been developed using Flask.

## Technology stack:
- Python
- RabbitMQ(Celery)
- Flask
- SQL

## Demonstration:
- Call deprecated insert endpoint at *‘/dpd_insert/<num>’* where num is an optional parameter to specify the number of rows of random data to be inserted(if not specified num = 100000). Observe that this would handicap the server until the insertion is complete and would not allow the server to service other requests.
- Once completed the result could be observed at *‘/get_data/count’* to get the count of the number of rows in the database table and *‘/delete_all’* could be used to clear the table. Also *‘/get_data’* could be used to query the complete database table but this is not recommended for retrieving a large number of rows as it might slow down the application(postman/browser/etc) being used to call the API with an excess of data.
- Now, call the insert endpoint at *‘/insert/<num>’* where num is an optional parameter to specify the number of rows of random data to be inserted(if not specified num = 100000). Observe unlike the *‘/dpd_insert’* endpoint the insertion using this endpoint is performed asynchronously by abstracting the operation as a task and enqueuing it in the task queue. The server responds almost instantly and is ready to service other requests. Take note of the task_id returned back in response.
- Use *‘/status/<task_id>’* endpoint to get the current status of the task. Optionally use *‘/stop/<task_id>’* to stop the task and perform a revoke along with a rollback. Observe the database table through *‘/get_data/count’*(recommended) or *‘/get_data’* endpoints to find the desired results, i.e. count is increased by the number of entries requested to be inserted if the task was not stopped while it was running otherwise there is no increase in the count of the entries in database table since the write operation is being performed in an all-or-none fashion.

## Endpoints:
- **/** : Presents with a welcome message.
- **/insert** or **/insert/<int:num>** : "Initiates request for insertion into database asynchronously by enqueuing it int0 the task queue. An optional URL parameter could be provided to specify the number of records to be inserted. If not specified the default value of 100000 is used.
- **/dpd_insert** or **/dpd_insert/<int:num>** : This route should be deprecated as it inserts into database synchronously and thus blocking the server. An optional URL parameter could be provided to specify the number of records to be inserted. If not specified the default value of 100000 is used.
- **/stop/<task_id>** : Initiates request to stop the task specified by the task_id. Revokes the task by terminating the task from the task queue meanwhile also performing database rollback.
- **/status/<task_id>** : Gives the status of the task specified by the task_id.
- **/delete_all** : Deletes all the data from the table in database. Used to facilitate testing of the API.
- **/get_data** : Gives all the data from the table in database. Used to facilitate testing of the API.
- **/get_data/count** : Gives count of all the data from the table in database. Used to facilitate testing of the API.

## Caveats and improvements
The code has been presented as a single file flask app due to its concise size and to improve readability. The codebase could and must be refactored and made more modular in a production scenario when it would be interacting with other libraries, modules and services.

Most of the endpoints have been designed to service GET requests since data passed along with the request is minimal and is thus passed as URL parameter rather than POST request. This might have to change is more data needs to be sent along the request.

Docker-compose does not provide for ordering the build of containers in a specific order therefore the app container which needs to connect to the broker might fail in its first attempt to connect but since it employs a persistent reconnect strategy it connects in its subsequent attempts. This feature to build containers in a specific order is against the architecture of docker-compose and thus workarounds such as healthcheck and reconnect strategies are the only way outs and are encouraged in the official documentation [https://docs.docker.com/compose/startup-order/].

Mysql database is presently being used with dummy table and random data. This choice should be assessed when in production depending on the structure and use case of the data being fed to the application.

Celery is being run as a root process and this could be changed to run as a user with appropriate permissions based on the overall architecture of the system.

The database is being accessed through root user and the root password is being passed as an environment variable in the container orchestration process. This should be replaced by the manner secret keys and configuration is handled by the overall system.


## Thoughts on scaling Long-running jobs and potential issues
Task queues and pipelining processes is a potential solution to handle long-running jobs by allowing asynchronous processing of tasks. Most solutions(including RabbitMQ-Celery) comes with a round-robin scheduling strategy out of the box, an appropriate scheduling strategy can make a significant difference while implementing this architecture and thus the best fit for the use case should be researched and implemented. 

Asynchronous request handling has the potential of causing issues when scaled such as problems caused by dependencies, i.e. if tasks are dependent on each other the asynchronous servicing of such tasks may cause deadlocks or inconsistent and unexpected results. Therefore, the design goal of the system should be to keep dependencies to a minimum and if present then to handle them appropriately.

Load balancing and database replication should also be considered while creating a solution that could scale. For instance MongoDB provides with replica sets which could be set up make the database more resilient to outage and also provide load balancing by distributing request to access the database to appropriate replica of the database meanwhile presenting a consistent view of the database to the user (version 4.x now also provides for transactions thus making bulk inserts atomic). Database consistency and resilience is crucial for a data-intensive application.
