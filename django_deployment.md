## Login to your server via ssh

`$ ssh root@server-ip-address`

## Initial Server Setup:

1. Create a new user and set the password:

   $ adduser ubuntu

2. Grant Administrative Privileges:

   $ usermod -aG sudo ubuntu

3. Now allow openssh so that you can connect via ssh:

   $ ufw allow OpenSSH
   $ ufw enable

4. Copy sshkeys to new user:

   $rsync --archive --chown=ubuntu:ubuntu ~/.ssh /home/ubuntu

5. Now you can login via ssh like the following and run a command with administrative privileges

   $ ssh ubuntu@server-ip-address
   $ sudo yourcommand

## Deployment Part I [SSH + Setup Environment]:

### Setup Github/Gitlab SSH:

1.  Generate SSH key in your server.

    $ ssh-keygen -t rsa -b 4096 -C "mygithubemail@gmail.com"

2.  Now print the newly generated SSH key in terminal, and copy this by selecting from terminal.

    $ cat ~/.ssh/id_rsa.pub

3.  Login to your Github / Gitlab accounnt open the SSH key options from the settings. You can try out the follwoing:

    i) Github - https://github.com/settings/keys

    ii) Gitlab - https://gitlab.com/-/profile/keys

4.  Now click on new SSH key option and paste the copied public ssh key into the "Key" text box area of the website.

5.  Now click on the create / add key button to successfully creating the SSH key..

6.  From now on, you can clone your repositories from server.

### Pull your Django project into server and perform initial Django setup.

1.  Open your repository and click on Code Clone section and copy the SSH url.

2.  Clone the project repository into server.

    $ git clone git@github.com:farid/testproject.git

3.  Get inside the project directory.

    $ cd testproject

4.  Install necessary packages in the server.

    $ sudo apt update
    $ sudo apt install python3-venv python3-dev libpq-dev postgresql postgresql-contrib nginx curl libxml2-dev libxslt-dev build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev curl software-properties-common

    NB: You might need to install other software dependencies according to your project.

5.  Create and activate virtual environment.

    $ python3 -m venv venv
    $ source venv/bin/activate

6.  Install the required dependencies of the project.

    (venv) $ pip install gunicorn psycopg2-binary wheel
    (venv) $ pip install -r requirements.txt

7.  Now create Postgresql database for production server.

    (venv) $ sudo -u postgres psql
    postgres=# CREATE DATABASE testproject;
    postgres=# CREATE USER testuser WITH PASSWORD 'testpassword';
    postgres=# ALTER ROLE testuser SET client_encoding TO 'utf8';
    postgres=# ALTER ROLE testuser SET default_transaction_isolation TO 'read committed';
    postgres=# ALTER ROLE testuser SET timezone TO 'UTC';
    postgres=# GRANT ALL PRIVILEGES ON DATABASE testproject TO testuser;
    postgres=# \q

8.  Now you can update your Production Database settings in the following approach:

    . . .

    DATABASES = {
    'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'testproject',
    'USER': 'testuser',
    'PASSWORD': 'testpassword',
    'HOST': 'localhost',
    'PORT': 5432,
    }
    }

    . . .

9.  Update the `ALLOWED_HOSTS` variable in your `settings.py` file by adding your IP address there.

    ...

    ALLOWED_HOSTS = ['localhost', 'your-server-ip-addres',]
    ...

10. Now migrate the initial databse schema to our PostgreSQL database.

    (venv) $ python manage.py migrate

11. Run the command to collect all of the static content in to the directory location. You will have to confirm the operation. The static files will then be placed in a directory called static within your project directory. The static files will be saved into the folder which is mentioned in STATIC_ROOT (in the settings.py file)

    (venv) $ python manage.py collectstatic

12. Create an exception for port 8000.

    (venv) $ sudo ufw allow 8000

13. Now try to run the server on port 8000 of your server.

    (venv) $ python manage.py runserver 0:8000

14. In your web browser, visit your server’s domain name or IP address followed by :8000:

    (venv) $ http://server_domain_or_IP:8000

15. Let's try to run the project via `Gunicorn`. Try to locate where the `wsgi.py` file is located, and use the following structure: `[foldername of that location].wsgi`

    (venv) $ cd ~/testproject
    (venv) $ gunicorn --bind 0.0.0.0:8000 testproject.wsgi

16. You can repeat step (12) to check running project via gunicorn is working or not.
17. Now you can deactivate the virtual environment.

    (venv) $ deactivate

## Deployment Part II [Gunicorn + Nginx]:

### Setup Gunicorn

1. Create Gunicorn socket.

   $ sudo nano /etc/systemd/system/gunicorn.socket

2. Now place the following content to there.

   [Unit]
   Description=gunicorn socket

   [Socket]
   ListenStream=/run/gunicorn.sock

   [Install]
   WantedBy=sockets.target

3. Create Gunicorn service.

   $ sudo nano /etc/systemd/system/gunicorn.service

4. Now place the following content there.

   [Unit]
   Description=gunicorn daemon
   Requires=gunicorn.socket
   After=network.target

   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/home/ubuntu/testproject
   ExecStart=/home/ubuntu/testproject/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    testproject.wsgi:application

   [Install]
   WantedBy=multi-user.target

5. Start and enable gunicorn socket. Which will create a socket file at `/run/gunicorn.sock`.

   $ sudo systemctl start gunicorn.socket
   $ sudo systemctl enable gunicorn.socket

6. Now you can check the status of your gunicorn.socket.

   $ sudo systemctl status gunicorn.socket

7. Check for the existence of the `gunicorn.sock` file within the `/run` directory:

   $ file /run/gunicorn.sock

8. If the systemctl status command indicated that an error occurred or if you do not find the gunicorn.sock file in the directory, it’s an indication that the Gunicorn socket was not able to be created correctly. Check the Gunicorn socket’s logs by typing:

   $ sudo journalctl -u gunicorn.socket

   Take another look at your /etc/systemd/system/gunicorn.socket file to fix any problems before continuing.

9. Now try the following commands to sync the changes of gunicorn and restart gunicorn.

   $ sudo systemctl daemon-reload
   $ sudo systemctl restart gunicorn

### Setup Nginx

1.  Create a file inside `sites-available` directory of `nginx`.

    $ sudo nano /etc/nginx/sites-available/testproject

2.  Now copy the following content and place into that file.

    server {
    listen 80;
    server_name server_domain_or_IP; # such as: 121.21.21.65 dev.mywebsite.com

        location = /favicon.ico { access_log off; log_not_found off; }
        location /static/ {
            alias /home/ubuntu/testproject/static/;
        }
        location /media/ {
            alias /home/ubuntu/testproject/media/;
        }

        location / {
            include proxy_params;
            proxy_pass http://unix:/run/gunicorn.sock;
        }

    }

3.  Now enable the file by linking it to the `sites-enabled` directory.

    $ sudo ln -s /etc/nginx/sites-available/testproject /etc/nginx/sites-enabled

4.  Test your Nginx configuration for syntax errors.

    $ sudo nginx -t

5.  If no errors are reported, go ahead and restart Nginx by typing:

    $ sudo systemctl restart nginx

6.  Finally, you need to open up your firewall to normal traffic on port 80. Since you no longer need access to the development server, you can remove the rule to open port 8000 as well:

    $ sudo ufw delete allow 8000
    $ sudo ufw allow 'Nginx Full'

7.  Now open your browser and try to visit following URL:

    http://your-server-ip-address

8.  You supposed to see your Django project up and running...

For troubleshooting the deployment server checkout [https://google.com] [here]..

## Deployment Part III [Celery + Redis + Supervisor]:

1. Install `supervisor`, which will run our background tasks.

   $ sudo apt install supervisor

2. Install `redis-server` if you are using `redis` as your broker:

   $ sudo apt install redis-server

3. Install `rabbitmq-server` if you are using `rabbitmq` as your broker:

   $ sudo apt install rabbitmq-server

4. Now we need to add the supervisor config files at `/etc/supervisor/conf.d`:

   $ sudo nano /etc/supervisor/conf.d/celery_worker.conf

5. Now paste the following content there: (Make sure change the project directory accoring to yours)

   ; ==================================
   ; celery worker supervisor example
   ; ==================================

   ; the name of your supervisord program
   [program:celeryworker]

   ; Set full path to celery program if using virtualenv
   command=/home/ubuntu/testproject/venv/bin/celery -A testproject worker --loglevel=INFO

   ; The directory to your Django project
   directory=/home/ubuntu/testproject

   ; If supervisord is run as the root user, switch users to this UNIX user account
   ; before doing any processing.
   user=ubuntu

   ; Supervisor will start as many instances of this program as named by numprocs
   numprocs=1

   ; Put process stdout output in this file
   stdout_logfile=/var/log/celery/celery_worker.log

   ; Put process stderr output in this file
   stderr_logfile=/var/log/celery/celery_worker.log

   ; If true, this program will start automatically when supervisord is started
   autostart=true

   ; May be one of false, unexpected, or true. If false, the process will never
   ; be autorestarted. If unexpected, the process will be restart when the program
   ; exits with an exit code that is not one of the exit codes associated with this
   ; process’ configuration (see exitcodes). If true, the process will be
   ; unconditionally restarted when it exits, without regard to its exit code.
   autorestart=true

   ; The total number of seconds which the program needs to stay running after
   ; a startup to consider the start successful.
   startsecs=10

   ; Need to wait for currently executing tasks to finish at shutdown.
   ; Increase this if you have very long running tasks.
   stopwaitsecs = 600

   ; When resorting to send SIGKILL to the program to terminate it
   ; send SIGKILL to its whole process group instead,
   ; taking care of its children as well.
   killasgroup=true

   ; if your broker is supervised, set its priority higher
   ; so it starts first
   priority=998

6. Now open another config file to setup Celery Beat (Scheduler):

   $ sudo nano /etc/supervisor/conf.d/celery_beat.conf

7. Then, paste the following contents there: (Make sure change the project directory accoring to yours)

   ; ================================
   ; celery beat supervisor example
   ; ================================

   ; the name of your supervisord program
   [program:celerybeat]

   ; Set full path to celery program if using virtualenv
   command=/home/ubuntu/testproject/venv/bin/celery -A testproject beat --loglevel=INFO

   ; The directory to your Django project
   directory=/home/ubuntu/testproject

   ; If supervisord is run as the root user, switch users to this UNIX user account
   ; before doing any processing.
   user=ubuntu

   ; Supervisor will start as many instances of this program as named by numprocs
   numprocs=1

   ; Put process stdout output in this file
   stdout_logfile=/var/log/celery/celery_beat.log

   ; Put process stderr output in this file
   stderr_logfile=/var/log/celery/celery_beat.log

   ; If true, this program will start automatically when supervisord is started
   autostart=true

   ; May be one of false, unexpected, or true. If false, the process will never
   ; be autorestarted. If unexpected, the process will be restart when the program
   ; exits with an exit code that is not one of the exit codes associated with this
   ; process’ configuration (see exitcodes). If true, the process will be
   ; unconditionally restarted when it exits, without regard to its exit code.
   autorestart=true

   ; The total number of seconds which the program needs to stay running after
   ; a startup to consider the start successful.
   startsecs=10

   ; if your broker is supervised, set its priority higher
   ; so it starts first
   priority=999

8. Now, create the celery directory in the Log folder by following command:

   $ sudo mkdir /var/log/celery

9. Now run the following commands update sync supervisor with the configurations file that we wrote just now:

   $ sudo supervisorctl reread
   $ sudo supervisorctl update

10. Now restart the services with the following command: (You need to run those following commands, if you ever change your code in `tasks.py` file, or any code related to background tasks):

    $ sudo supervisorctl restart all

11. To checkout the log of celery worker, you need to run the following command:

    $ sudo tail -F /var/log/celery/celery_worker.log

12. To checkout the log of celery beat (scheduler), you need to run the following command:

    $ sudo tail -F /var/log/celery/celery_beat.log

13. To see the status of the services, run the following commands:

    $ sudo supervisorctl status celeryworker
    $ sudo supervisorctl status celerybeat

14. Dramatiq worker setup:

```
  $ sudo nano /etc/supervisor/conf.d/dramatiq_worker.conf
```

```
  ; the name of your supervisord program
  [program:dramatiq_worker]

  ; Set full path to celery program if using virtualenv
  command=/home/lengo/backend_booking/.venv/bin/python3 /home/lengo/backend_booking/manage.py rundramatiq
  directory=/home/lengo/backend_booking

  ; The directory to your Django project
  directory=/home/lengo/backend_booking

  ; If supervisord is run as the root user, switch users to this UNIX user account
  ; before doing any processing.
  user=lengo

  ; Supervisor will start as many instances of this program as named by numprocs
  numprocs=1

  ; Put process stdout output in this file
  stdout_logfile=/var/log/dramatiq_worker.out.log

  ; Put process stderr output in this file
  stderr_logfile=/var/log/dramatiq_worker.err.log

  ; If true, this program will start automatically when supervisord is started
  autostart=true

  ; May be one of false, unexpected, or true. If false, the process will never
  ; be autorestarted. If unexpected, the process will be restart when the program
  ; exits with an exit code that is not one of the exit codes associated with this
  ; process’ configuration (see exitcodes). If true, the process will be
  ; unconditionally restarted when it exits, without regard to its exit code.
  autorestart=true

  ; The total number of seconds which the program needs to stay running after
  ; a startup to consider the start successful.
  startsecs=10

  ; Need to wait for currently executing tasks to finish at shutdown.
  ; Increase this if you have very long running tasks.
  stopwaitsecs = 600

  ; When resorting to send SIGKILL to the program to terminate it
  ; send SIGKILL to its whole process group instead,
  ; taking care of its children as well.
  killasgroup=true

  ; if your broker is supervised, set its priority higher
  ; so it starts first
  priority=998

```

```
  $ sudo supervisorctl reread
  $ sudo supervisorctl update
  $ sudo supervisorctl restart all

  # Check logs
  $ sudo tail -F /var/log/dramatiq_worker.out.log
  $ sudo tail -F /var/log/dramatiq_worker.err.log

  $ sudo supervisorctl status dramatiq_worker
```

## Deployment Part IV [Domain Setup + SSL Certificate (Let's Encrypt)]:

Let's add SSL certificate in our domain by using **Let's Encrypt**

1. Firstly, try to connect your domain with your server's ip address. Try the following URL to learn how to do that.

   https://www.123-reg.co.uk/support/domains/how-do-i-point-my-domain-name-to-an-ip-address/

2. Let's place the domain name in the nginx config file. Open the config file:

   $ sudo nano /etc/nginx/sites-available/testproject

3. Now put your domain name in the `server_name` section in the following line: (You can remove your IP address in this case)

   ...
   server_name mydomain.com www.mydomain.com;
   ...

4. Add the domain name in the `ALLOWED_HOSTS`, which is located in the settings.py file.

   ...
   ALLOWED_HOSTS = ['IP_ADDRESS', 'mydomain.com', 'www.mydomain.com']
   ...

5. After making the changes, run the following commands:

   $ sudo nginx -t
   $ sudo systemctl reload nginx
   $ sudo ufw allow 'Nginx Full'

6. Now, install necessary the following packages.

   $ sudo snap install --classic certbot

7. Obtaing an SSL certificate for your domain:

   $ sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

   - Put your email address
   - Type "Y"
   - Type "Y"

8. Holla!!, if your open your domain in the browser you will able to see, the SSL certificate is added, and your domain is running with `https://`.

9. Let's see if we have the renewal system of SSL certificate is active or not.

   $ sudo systemctl status snap.certbot.renew.service

10. You will be able to see "Active: inactive (dead)" in the status section. To add auto renewal system run the following command:

    $ sudo certbot renew --dry-run

11. Congratulations, all simulated renewals succeeded..

# "Please hit on ☆ and make it ★, if you like this tutorial.."
