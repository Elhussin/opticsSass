
### install venv
```bash
sudo apt install python3.12-venv
python3 -m venv venv
source venv/bin/activate
```



### install django
`python3 -m pip install Django`

### create project
`django-admin startproject <project_name>`

### run server
`python3 manage.py runserver`

### create app
`python3 manage.py startapp <app_name>`

### install requirements
```bash
pip install -r requirements.txt
```

### install postgresql
```bash
sudo apt install postgresql postgresql-contrib
```


### create user
```bash
sudo -u postgres psql
CREATE USER <username> WITH PASSWORD '<password>';
```

### check status
```bash
sudo systemctl status postgresql
```

### Switch to PostgreSQL user
```bash
sudo -i -u postgres
psql  # to enter the PostgreSQL command line interface
```

### enable postgresql
```bash
sudo systemctl enable postgresql
```

### create database
```bash
sudo -u postgres psql
CREATE DATABASE optics;
CREATE USER taha WITH ENCRYPTED PASSWORD '3112';

ALTER ROLE taha SET client_encoding TO 'utf8';
ALTER ROLE taha SET default_transaction_isolation TO 'read committed';
ALTER ROLE taha SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE optics TO taha;
\q
```
