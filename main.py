from flask import render_template
from flask import redirect
from flask import request
from flask import Flask
from replit import db
import time


app = Flask(__name__)


@app.route('/')
def home():
  if request.args.get('poll') != None:
    try:
      # check if it's a repeat response
      if db['polls'][request.args.get('poll')]['allow_repeat'] != True:
        if request.headers.get('x-forwarded-for') in db['polls'][request.args.get('poll')]['logged']:
          return redirect(f'/results?id={request.args.get("poll")}', code=302)
          
      return render_template('poll.html', data=db['polls'][request.args.get('poll')])
    except KeyError:
      return render_template('404.html')
  return render_template('index.html')

@app.route('/create', methods=['POST'])
def create():
  title = request.form['title']
  description = request.form['description']
  options = request.form['options'].strip().split(';')
  allow_repeat = request.form['repeat'] in ['1']

  # generate page id
  id = str(abs(hash(str(time.time())+options[0])))
  db['polls'][id] = {
    'title': title,
    'description': description,
    'options': options,
    'responses': {},
    'logged': [],
    'total': 0,
    'allow_repeat': allow_repeat,
    'id': id
  }
  # set responses to 0 for each option
  for option in options:
    db['polls'][id]['responses'][option] = 0

  return redirect(f'/?poll={id}')

@app.route('/response')
def response():
  if request.args.get('poll') != None:
    if request.args.get('option') != None:
      if request.args.get('poll') in db['polls']:
        option = request.args.get('option')
        id = request.args.get('poll')

        # check if it's a repeat response
        # just in case user manually types out as a get request
        print(db['polls'][id]['allow_repeat'])
        if db['polls'][id]['allow_repeat'] != True:
          if request.headers.get('x-forwarded-for') in db['polls'][id]['logged']:
            return redirect(f'/results?id={id}', code=302) 

        # process
        db['polls'][id]['responses'][option] += 1;
        db['polls'][id]['total'] += 1;

        # log down user
        db['polls'][id]['logged'].append(request.headers.get('x-forwarded-for'))
        return redirect(f'/results?id={id}', code=302)
      else:
        return render_template('404.html')
    else:
      return render_template('404.html')
  else:
    return render_template('404.html')

@app.route('/results')
def results():
  # disallow preliminary access to results
  if request.args.get('id') in db['polls']:
    if not request.headers.get('x-forwarded-for') in db['polls'][request.args.get('id')]['logged']:
      # user tried to access results without submission
      return redirect(f'/?poll={request.args.get("id")}', code=302)
    else:
      return render_template('results.html', data=db['polls'][request.args.get('id')])
  return render_template('404.html')


# comment this out after running the first time
db['polls'] = {}
app.run(host='0.0.0.0', port=8080)
