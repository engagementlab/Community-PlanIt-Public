Community Planit Documentation
==============================

__A game about your neighborhood.__

# Overview #
Community PlanIt is written using Python(Django) and JavaScript(jQuery).  It has evolved over the course of the half year development
which has led to some naming inconsistencies which will be noticable immediately.  For example, instances are 1:1 to neighborhoods in
the UI.  Going through Pivotal to see older stories may help shed light on design and development decisions.  This application makes
heavy use of Django model inheritance and nested app folders.

The software was written in an Arch Linux environment and deployed to a Debian 6.0.1 environment.  The only differences encountered
between the two are the process of installing dependancies and getting started.  This README covers installation and getting started
for Debian 6.0.1 as to match the production environment.

The development environment uses Supervisord to manage gunicorn, nginx and memcache if necessary.  Its entirely possible to skip it for
nginx and memcache and leave that to the system daemon handler.  Nginx handles assets and reverse proxy routing to gunicorn.

# Dependancies #
  
Communtiy PlanIt requires certain dependancies before installing and getting started.

## System Dependancies ##

These dependancies are installed through the system package manager or compiled from source.  Its highly recommended to use the system
package manager `aptitude` in the case of Debian.

In most cases the installation of these dependancies will follow the pattern: `sudo apt-get install [package-name]`

* python-setuptools
* rubygems
* nginx
* memcached
* git
* sqlite3
* python-imaging
* mysql-server
* python-mysqldb
* python-memcache
* python-magic

## Python Dependancies ##

In order to install the Python dependancies ensure you have the `python-setuptools` package installed.

In most cases the installation of these dependancies will follow the pattern: `sudo easy_install [package-name]`

* supervisor
* gunicorn
* south
* django_compressor

## Ruby Dependancies ##

The project utilizes SASS for compiling stylesheets.  It must be downloaded from the SASS package via rubygems.

`sudo gem install sass`

## Custom dependancies ##

These dependancies cannot be installed by a package manager for versioning reasons.

### Installing django_gmapsfield ###

    $ git clone https://github.com/bocoup/django_gmapsfield.git
    $ cd django_gmapsfield
    $ sudo python setup.py install

### Installing django v1.2.3 ###

    $ wget http://media.djangoproject.com/releases/1.2/Django-1.2.3.tar.gz
    $ tar zxvf Django-1.2.3.tar.gz
    $ cd Django-1.2.3
    $ sudo python setup.py install

# Configuring Community PlanIt #

## Getting the source ##

Community PlanIt source code is stored in `git` fetch the latest into a local directory such as ~/git/community-planit:
  
    $ git clone git@github.com:bocoup/community-planit.git

## Environment configurations ##

### development.ini ###
You can find a sample development.ini in the /config directory.

__MEDIA_ROOT__: Set this to your assets directory, absolute path not relative.

## nginx.conf ##
You can find a sample nginx.conf in the /config directory.

Copy the config file to /etc/nginx:
    sudo cp nginx.conf /etc/nginx/

Change the line under location /assets to, no trailing slash:
    alias "/path/to/community-planit/assets"

Change the line under location /admin-media to the directory that Django admin assets are on your machine, chances are
if you're using Debian this line will most likely be:
    alias "/usr/local/lib/python2.6/dist-packages/django/contrib/admin/media";

Change the line referring to mimetypes to match your operating system, if you're using Debian this line will most
likely be:
    include     /etc/nginx/mime.types;

## Supervisor ##
You can find a sample supervisord.conf in the /config directory.

Copy the config file to /etc/:
    sudo cp supervisord.conf /etc/

Modify the supervisor script to change the following two lines:
    command=gunicorn_django --workers=2 --bind=127.0.0.1:9090
    directory=/path/to/community-planit/web/

They should be modified to fit your environment, but most likely the defaults will be fine.  Change the directory to
an absolute path that matches your structure.

## Crontab ##
If you want email notifications to go out when missions end, you will need to add the following line for each instance
of Community PlanIt.  Change the /path/to/web to an absolute path to the checked out directory.

    0 0 * * * cd /path/to/web && python manage.py email_notifications

# Getting Started #

The three things needed to work fluently with Community PlanIt are starting supervisor, starting nginx and starting
sass.  You may also want to set your hostfile to have an entry that looks like:

    127.0.0.1   planit.local

## Supervisor ##

    $ sudo supervisord

## Nginx ##
    
    $ sudo /etc/init.d/nginx start

## Sass ##

    $ cd ~/git/community-planit/assets
    $ sass --watch scss:css

Once all these items have been started, navigating to http://planit.local should bring up a fresh instance of
Community PlanIt.

# Deployment #

In order to deploy on an existing server you will most likely need to add a new remote if one does not already exist.

Such as:

    git remote add github git@github.com:bocoup/community-planit.git

Working with the development branch is as simple as:
    
    # Locally
    $ git commit -am "Some commit message"
    $ git push github development

    # Remote
    $ git pull github development
