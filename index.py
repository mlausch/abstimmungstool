#!/usr/bin/python3

import os
import sys
import cgi
import yaml
import pymysql.cursors
from jinja2 import Environment, FileSystemLoader
import pprint
import cgitb
cgitb.enable()

config_path = 'config.yaml'

def is_voted(db, fid, uuid):
    c = db.cursor(pymysql.cursors.DictCursor)
    c.execute('select count(fragen_id) as c from teilgenommen where fragen_id=%s and teilnehmer_id=%s', (fid, uuid))
    return True if c.fetchall()[0]['c'] == 1 else False
    

def get_fragen(db, uuid):
    c = db.cursor(pymysql.cursors.DictCursor)

    c.execute('select id, frage, sichtbar, abgeschlossen from fragen;')
    questions = c.fetchall()

    for q in questions:
        q['voted'] = 1 if is_voted(db, q['id'], uuid) else 0

        c.execute('select id, antwort from antworten where fragen_id=%s', (q['id']))
        answers = c.fetchall()
        q['answers'] = list()
        for answer in answers:
            c.execute('select count(antwort_id) as stimmen from auswertung where fragen_id=%s and antwort_id=%s', (q['id'], answer['id']))
            stimmen = c.fetchall()[0]['stimmen']
            q['answers'].append({'antwort': answer['antwort'], 'stimmen': stimmen, 'id': answer['id']})

    return questions


def vote(db, uuid, vote):
    _,fid,aid = vote.split('_')

    # if question already voted, then do nothing
    if is_voted(db, fid, uuid):
        return

    c = db.cursor(pymysql.cursors.DictCursor)
    c.execute('insert into auswertung (antwort_id, fragen_id) values (%s, %s)', (aid, fid))
    c.execute('insert into teilgenommen (teilnehmer_id, fragen_id) values (%s, %s)', (uuid, fid))
    
    return
    
    
def toggle_flag(db, flag):
    flag, f_id = flag.split('_')
    if flag == 'abgeschlossen':
        query = 'update fragen set abgeschlossen = mod(abgeschlossen+1, 2) where id=%s'
    if flag == 'sichtbar':
        query = 'update fragen set sichtbar = mod(sichtbar+1, 2) where id=%s'
        
    c = db.cursor()
    c.execute(query, (f_id))

def user_exists(db, uuid):
    c = db.cursor(pymysql.cursors.DictCursor)
    c.execute('select count(*) as c from teilnehmer where id=%s', (uuid))
    if c.fetchall()[0]['c'] == 0:
        return False
    else:
        return True

def get_user(db, uuid):
    c = db.cursor(pymysql.cursors.DictCursor)
    c.execute('select name, email from teilnehmer where id=%s', (uuid))

    data = c.fetchone()
    return (data['name'], data['email'])


def main():
    try:
        template_env = Environment(loader=FileSystemLoader('templates'))
        template_env.add_extension('jinja2.ext.loopcontrols')
        
    
        template = template_env.get_template('index.html')
    
        # open db connection
        with open(config_path, 'r') as fh:
            config = yaml.safe_load(fh)
        db = pymysql.connect(host = config['mysql']['host'],
                             user = config['mysql']['user'],
                             password = config['mysql']['pw'],
                             database = config['mysql']['db'],
                             autocommit=True,
                             charset='utf8')
    
        # read formdata
        formdata = cgi.FieldStorage()

        # check uuid
        uuid_error = False
        if 'uuid' not in formdata:
            uuid_error = True
        elif not user_exists(db, formdata['uuid'].value):
            uuid_error = True

        if uuid_error:
            template = template_env.get_template('user_invalid.html')
            page = template.render()
        
        ## uuid ok. ab hier jetzt verarbeiten
        else:
            uuid = formdata['uuid'].value
            name,email = get_user(db, uuid)
    
            # check for answers
            for i in formdata:
                if ('antwort_' in i):
                    vote(db, uuid, i)
                    break
        
            questions=get_fragen(db, uuid)

            page = template.render(questions=questions,name=name, uuid=uuid)
        
    
        #html headers
        print('Content-type: text/html;charset=utf-8;')
        if os.environ['REQUEST_METHOD'] == 'POST':
            print(f'Location: index.py?uuid={uuid}')
            print()
            sys.exit(0)
        print()
        print(page)
    except:
        print('Content-type: text/html;charset=utf-8;')
        print()
        raise


main()
