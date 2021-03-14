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

2. Configure the three settings.py for the database in 
   NSS-Backend/DATASET/DATASET/settings.py, NSS-Backend/MATRIX/MATRIX/settings.py 
   and NSS-Backend/NSS/NSS/settings.py.
   A dictionary containing the settings for 
   all databases to be used with Django.
   Following connection parameters will be required.
   
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mydatabase',
        'USER': 'mydatabaseuser',
        'PASSWORD': 'mypassword',
        'HOST': '172.18.112.69',
        'PORT': '3306',
        }
}
```
Then execute migrations
```shell
cd NSS-Backend/NSS/
python manage.py makemigrations
python manage.py migrate
```

3. Run three backend services with different ports.
```shell
cd NSS-Backend/DATASET/
python manage.py runserver 127.0.0.1:23333
```

```shell
cd NSS-Backend/NSS/
python manage.py runserver 127.0.0.1:23334
```

```shell
cd NSS-Backend/MATRIX/
python manage.py runserver 127.0.0.1:23335
```
