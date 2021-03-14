# NSS
Federated NSS is an framework for machine learning
and other computations on decentralized data. NSS has been 
developed to facilitate experimentation with 
Federated Learning (FL), a subspace learning approach to machine 
learning where a shared global model is trained across many 
participating clients that
keep their training data locally.

## Usage
1. First make sure that mysql is installed on your server.
```shell
service mysqld status 
```
will check the sql service even though the service is running fine 
and you can log into the MySQL prompt using mysql -uroot -p and start executing queries 
without any problems.

2. Configure the settings.py for the database in 
   NSS-Backend/DATASET/DATASET/settings.py. 
   A dictionary containing the settings for 
   all databases to be used with Django. It is a nested dictionary 
   whose contents map a database alias to a dictionary containing the options for an individual database.