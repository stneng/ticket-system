from flask import Flask, request, render_template, session, redirect, url_for
from executable import Executable
import requests

app = Flask("web")
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.jinja_env.auto_reload = True

core = Executable('../core/core.exe')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if session.get('username') is None:
            return redirect(url_for('login', f='index'))
        else:
            return render_template('index.html', ses=session)
    else:
        if request.json['op'] == 0:
            ret = core.exec(
                ['query_transfer', '-s', request.json['from'], '-t', request.json['to'], '-d', request.json['date'],
                 '-p', request.json['sorting']])
            return {'e': 0, 'tot': int(ret[0]), 'result': ret[1:]}
        elif request.json['op'] == 1:
            ret = core.exec(
                ['query_ticket', '-s', request.json['from'], '-t', request.json['to'], '-d', request.json['date'], '-p',
                 request.json['sorting']])
            return {'e': 0, 'tot': int(ret[0]), 'result': ret[1:]}
        elif request.json['op'] == 2:
            if session.get('username') is None:
                return {'e': -1, 'msg': 'User is not logged in.'}
            ret = core.exec(
                ['buy_ticket', '-u', session.get('username'), '-i', request.json['trainID'], '-d', request.json['date'],
                 '-n', str(request.json['count']), '-f', request.json['from'], '-t', request.json['to'], '-q',
                 str(request.json['wait']).lower()])
            if ret[0] == '-1':
                return {'e': -1, 'msg': 'Buy ticket failed.'}
            elif ret[0] == 'queue':
                return {'e': 0, 'op': 1}
            else:
                return {'e': 0, 'op': 0, 'tot': ret[0]}
        else:
            return {'e': -100, 'msg': 'Unrecognized request.'}


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('username') is None:
            return render_template('login.html', f=request.args.get('f', 'index'))
        else:
            return redirect(url_for(request.args.get('f', 'index')))
    else:
        if request.json['op'] == 0:
            ret = core.exec(['login', '-u', request.json['username'], '-p', request.json['password']])
            if int(ret[0]):
                return {'e': -1}
            else:
                r = requests.post('http://127.0.0.1:8000/check.php', {'username': request.json['username']}).json()
                if r['e'] == 0:
                    session['username'] = request.json['username']
                    return {'e': 0}
                else:
                    session['username2'] = request.json['username']
                    return {'e': 1}
        elif request.json['op'] == 1:
            ret = core.exec(['add_user', '-c', 'root', '-u', request.json['username'], '-p', request.json['password'],
                             '-n', request.json['name'], '-m', request.json['email'], '-g', '1'])
            return {'e': int(ret[0])}
        elif request.json['op'] == 2:
            if session.get('username') is None:
                return {'e': -1, 'msg': 'User is not logged in.'}
            ret = core.exec(['logout', '-u', session.get('username')])
            session.pop('username')
            return {'e': int(ret[0])}
        elif request.json['op'] == 3:
            r = requests.post('http://127.0.0.1:8000/sendcode.php', {'phone': request.json['phone']})
            return r.text
        elif request.json['op'] == 4:
            r = requests.post('http://127.0.0.1:8000/login.php',
                              {'phone': request.json['phone'], 'code': request.json['code']}).json()
            if r['e'] == 0:
                session['username'] = r['username']
                return {'e': 0}
            else:
                return {'e': -1}
        else:
            return {'e': -100, 'msg': 'Unrecognized request.'}


@app.route('/phoneverify', methods=['GET', 'POST'])
def phoneverify():
    if request.method == 'GET':
        if session.get('username2') is None:
            return redirect(url_for('index', f='index'))
        else:
            return render_template('phoneverify.html', ses=session)
    else:
        if request.json['op'] == 0:
            r = requests.post('http://127.0.0.1:8000/sendcode.php', {'phone': request.json['phone']})
            return r.text
        elif request.json['op'] == 1:
            r = requests.post('http://127.0.0.1:8000/phoneverify.php',
                              {'phone': request.json['phone'], 'code': request.json['code'],
                               'username': session['username2']}).json()
            if r['e'] == 0:
                session['username'] = session['username2']
                session.pop('username2')
                return {'e': 0}
            else:
                return {'e': -1}
        else:
            return {'e': -100, 'msg': 'Unrecognized request.'}


@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if request.method == 'GET':
        if session.get('username') is None:
            return redirect(url_for('login', f='manage'))
        else:
            return render_template('manage.html', ses=session)
    else:
        if request.json['op'] == 0:
            ret = core.exec(['query_profile', '-c', session['username'], '-u', request.json['username']])
            if ret[0] == '-1':
                return {'e': -1}
            return {'e': 0, 'info': ret[0]}
        elif request.json['op'] == 1:
            ret = core.exec(
                ['add_user', '-c', session['username'], '-u', request.json['username'], '-p', request.json['password'],
                 '-n', request.json['name'], '-m', request.json['email'], '-g', request.json['privilege']])
            return {'e': int(ret[0])}
        elif request.json['op'] == 2:
            args = ['modify_profile', '-c', session['username'], '-u', request.json['username']]
            args.extend(['-p', request.json['password']] if request.json['password'] != '' else [])
            args.extend(['-n', request.json['name']] if request.json['name'] != '' else [])
            args.extend(['-m', request.json['email']] if request.json['email'] != '' else [])
            args.extend(['-g', request.json['privilege']] if request.json['privilege'] != '' else [])
            ret = core.exec(args)
            if ret[0] == '-1':
                return {'e': -1}
            return {'e': 0, 'info': ret[0]}


@app.route('/exec', methods=['POST'])
def execute():
    data = request.json
    if data:
        tmp = core.exec([data['cmd']])
        return {'result': tmp}


@app.route('/tmp')
def tmp():
    return render_template('tmp.html', f="index")


if __name__ == '__main__':
    app.run()
