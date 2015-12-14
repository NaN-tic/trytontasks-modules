#This file is part of trytontasks_modules. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from invoke import task, run

@task
def list():
    'List modules'
    print "List modules and repos"
