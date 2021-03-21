#!/usr/bin/python3

import os
import sys
import cgi
import yaml
import pymysql.cursors
from jinja2 import Environment, FileSystemLoader
import pprint
import uuid as uuidgen
import smtplib
import cgitb
cgitb.enable()

config_path = 'config.yaml'

def send_mail(template_env, email_conf, user):
    template = template_env.get_template('email.txt')
    msg = template.render(sender = email_conf['sender'], sender_name = email_conf['sender_name'], user = user).encode('utf-8') 

    try:
        server = smtplib.SMTP(email_conf['mailserver'])
        server.sendmail(email_conf['sender'], user['email'], msg)
        server.quit()
    except Exception:
        pass


def get_fragen(db):
    c = db.cursor(pymysql.cursors.DictCursor)

    c.execute('select id, frage, sichtbar, abgeschlossen from fragen;')
    questions = c.fetchall()

    for q in questions:
        c.execute('select id, antwort from antworten where fragen_id=%s', (q['id']))
        answers = c.fetchall()
        q['answers'] = list()
        for answer in answers:
            c.execute('select count(antwort_id) as stimmen from auswertung where fragen_id=%s and antwort_id=%s', (q['id'], answer['id']))
            stimmen = c.fetchall()[0]['stimmen']
            q['answers'].append({'antwort': answer['antwort'], 'stimmen': stimmen})

    return questions

def add_question(db, formdata):
    question = formdata['frage'].value
    answers = list(map(str.strip, formdata['antworten'].value.split('\n')))

    c = db.cursor()
    c.execute('insert into fragen (frage) values (%s)', (question))

    f_id = c.lastrowid

    for answer in answers:
        if len(answer) == 0: 
            continue
        c.execute('insert into antworten (fragen_id, antwort) values (%s, %s)', (f_id, answer))

def add_users(db, formdata, template_env, email_config):
    userdata = list(map(str.strip, formdata['user'].value.split('\n')))
    
    for user in userdata:
        if len(user) == 0:
            continue
        full_name, email = user.split(';')
        last_name, name = full_name.split(',')
        full_name = name.strip() + ' ' + last_name.strip()
        uuid = uuidgen.uuid4()

        c = db.cursor(pymysql.cursors.DictCursor)
        c.execute('select count(*) as c from teilnehmer where name=%s', (full_name))
        if c.fetchall()[0]['c'] == 0:
            c.execute('insert into teilnehmer (id, name, email) values (%s, %s, %s)', (uuid, full_name, email.strip()))
            send_mail(template_env, email_config, {'name': full_name, 'email': email.strip(), 'id': uuid})



def toggle_flag(db, flag):
    flag, f_id = flag.split('_')
    if flag == 'abgeschlossen':
        query = 'update fragen set abgeschlossen = mod(abgeschlossen+1, 2) where id=%s'
    if flag == 'sichtbar':
        query = 'update fragen set sichtbar = mod(sichtbar+1, 2) where id=%s'
        
    c = db.cursor()
    c.execute(query, (f_id))

def get_users(db):
    c = db.cursor(pymysql.cursors.DictCursor)
    c.execute('select name, email, id from teilnehmer')

    return c.fetchall()

def get_user(db, uuid):
    c = db.cursor(pymysql.cursors.DictCursor)
    c.execute('select name, email, id from teilnehmer where id=%s', (uuid))

    return c.fetchall()[0]


def main():
    template_env = Environment(loader=FileSystemLoader('templates'))

    template = template_env.get_template('moderator.html')

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
   
    # if requested add some new data
    if "add" in formdata:
        add_question(db, formdata)
    if "adduser" in formdata:
        add_users(db, formdata, template_env, config['email'])

    # check for toggle
    for i in formdata:
        if ('sichtbar' in i) or ('abgeschlossen' in i):
            toggle_flag(db, i)

    # check for sendmail
    for i in formdata:
        if 'sendmail_' in i:
            _,uuid = i.split('_')
            user = get_user(db, uuid)
            send_mail(template_env, config['email'], user)

    questions=get_fragen(db)
    users = get_users(db)


    #html headers
    print('Content-type: text/html;charset=utf-8;')
    if os.environ['REQUEST_METHOD'] == 'POST':
        print('Location: moderator.py')
        print()
        sys.exit(0)
    print()
    print(template.render(questions=questions, users=users))

if __name__ == '__main__':
    main()
