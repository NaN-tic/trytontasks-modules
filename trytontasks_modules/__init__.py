#This file is part of trytontasks_modules. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import ConfigParser
import os
import hgapi
from invoke import task, run
from blessings import Terminal
from trytontasks_scm import hg_clone

t = Terminal()

def read_config_file(config_file=None, type='repos', unstable=True):
    assert type in ('repos', 'servers', 'patches', 'all'), "Invalid 'type' param"

    Config = ConfigParser.ConfigParser()
    if config_file is not None:
        Config.readfp(open('./config/'+config_file))
    else:
        for r, d, f in os.walk("./config"):
            for files in f:
                if not files.endswith(".cfg"):
                    continue
                if not unstable and files.endswith("-unstable.cfg"):
                    continue
                if 'templates' in r:
                    continue
                Config.readfp(open(os.path.join(r, files)))

    if type == 'all':
        return Config
    for section in Config.sections():
        is_patch = (Config.has_option(section, 'patch')
                and Config.getboolean(section, 'patch'))
        is_server = (Config.has_option(section, 'server')
                and Config.get(section, 'server'))
        if type == 'repos' and (is_patch or is_server):
            Config.remove_section(section)
        elif type == 'patches' and not is_patch:
            Config.remove_section(section)
        elif type == 'servers' and not is_server:
            Config.remove_section(section)
    return Config

@task
def info(config=None):
    'Info config modules'
    Config = read_config_file(config)
    modules = Config.sections()
    modules.sort()

    total = len(modules)
    print t.bold(str(total) + ' modules')

    for module in modules:
        print t.green(module)+' %s %s %s %s' % (
            Config.get(module, 'repo'),
            Config.get(module, 'url'),
            Config.get(module, 'path'),
            Config.get(module, 'branch'),
            )

@task
def config(repo=None, branch='default', update=False):
    'Clone/Update config repo'
    config = "./config"
    if update:
        repo = hgapi.Repo(config)
        repo.hg_pull()
        repo.hg_update(branch)
        print t.green("Updated ") + t.bold('./config')
    else:
        if not repo:
            print t.bold_red('Select a reposotory to clone')
            return
        hg_clone(repo, path=config, branch=branch)
