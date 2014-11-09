# New Django Project

### Local Environment Setup

1. Make sure you have `virtualenvwrapper` installed. If not, Google it and install.
    1. Run <code>mkvirtualenv {{ project-name }} --python=`which python3`</code>
    1. Make `~/Envs/{{ project-name }}/bin/postactivate` look like this:

    ```sh
    #!/bin/bash
    # This hook is run after this virtualenv is activated.
    cd ~/Sites/{{ project-name }}/web/
    pip install -r ../requirements/dev.txt
    ./manage migrate
    ./manage.py runserver 0.0.0.0:8000
    ```
1. In a fresh window, execute `workon {{ project-name }}`.

### Make a database!
1. From within your `web/` directory, execute: `./manage.py migrate`. This will create a local SQLite database. You may delete that database and start from scratch with this command at any time.
    1. After creating a fresh database, you will likely be prompted to install yourself as a superuser. If not, execute `./manage.py createsuperuser`.
