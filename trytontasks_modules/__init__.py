#This file is part of trytontasks_modules. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import ConfigParser
import os
import sys
from datetime import date
import hgapi
from invoke import task, run
from blessings import Terminal
from multiprocessing import Process
from trytontasks_scm import hg_clone

t = Terminal()
MAX_PROCESSES = 25

def wait_processes(processes, maximum=MAX_PROCESSES, exit_code=None):
    i = 0
    while len(processes) > maximum:
        if i >= len(processes):
            i = 0
        p = processes[i]
        p.join(0.1)
        if p.is_alive():
            i += 1
        else:
            if exit_code is not None:
                exit_code.append(processes[i].exitcode)
            del processes[i]

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


def increase_module_version(module, path, version):
    '''
    Increase version of module
    Cred: http://hg.tryton.org/tryton-tools/file/5f31cfd7e596/increase_version
    '''
    path_repo = os.path.join(path, module)
    if not os.path.exists(path_repo):
        print >> sys.stderr, t.red("Missing repositori:") + t.bold(path_repo)
        return

    cfg_file = os.path.join(path_repo, 'tryton.cfg')
    if not os.path.exists(path_repo):
        print >> sys.stderr, t.red("Missing tryton.cfg file:") + t.bold(
            cfg_file)
        return

    def increase(line):
        if line.startswith('version='):
            return 'version=%s\n' % version
        return line

    cwd = os.getcwd()
    os.chdir(path_repo)

    content = ''
    filename = 'tryton.cfg'
    with open(filename) as fp:
        for line in fp:
            content += increase(line)
    with open(filename, 'w') as fp:
        fp.write(content)
    today = date.today().strftime('%Y-%m-%d')
    content = 'Version %s - %s\n' % (version, today)
    filename = 'CHANGELOG'
    try:
        with open(filename) as fp:
            for line in fp:
                content += line
    except IOError:
        pass
    with open(filename, 'w') as fp:
        fp.write(content)

    os.chdir(cwd)

@task()
def increase_version(version, config=None, unstable=True, clean=False):
    '''
    Modifies all tryton.cfg files in order to set version to <version>
    '''
    if not version:
        print >> sys.stderr, t.red("Missing required version parameter")
        return
    Config = read_config_file(config, unstable=unstable)
    processes = []
    p = None
    for section in Config.sections():
        path = Config.get(section, 'path')
        p = Process(target=increase_module_version, args=(section, path,
                version))
        p.start()
        processes.append(p)
        wait_processes(processes)
    wait_processes(processes, 0)
