from flask import Flask, render_template, request
from markupsafe import escape
app = Flask(__name__)

@app.route('/home')
@app.route('/')
@app.route('/index')
def hello():
    return '<h1>Hello World!</h1><img src="http://helloflask.com/totoro.gif">'

@app.route('/user/<name>')
def user_page(name):
    return f'User {escape(name)}'









