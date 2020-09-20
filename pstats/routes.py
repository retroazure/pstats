from flask import request, Flask, render_template, url_for, flash, redirect
from pstats import app, db, bcrypt
from pstats.models import User, Post
from pstats.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flask_login import login_user, current_user, logout_user, login_required
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
import secrets
import os
from PIL import Image

posts = [
    {
        'author': 'Juliano Martins',
        'title': 'Publicação 1',
        'content': 'Conteúdo',
        'date_posted': '20 de Abril de 2019'
    }
]

def scraping():

    url = 'https://www.basketball-reference.com/leagues/NBA_2019_totals.html' 

    html = urlopen(url)

    soup = BeautifulSoup(html,'html.parser')

    header = [th.getText() for th in soup.findAll('tr')[0].findAll('th')]
    header = header[1:]


    rows = soup.findAll('tr')
    rows = rows[1:]

    player_stats = [[td.getText() for td in rows[i].findAll('td')] for i in range(len(rows))]

    stats = pd.DataFrame(player_stats, columns=header)

    stats = stats.dropna(how='all')
    
    stats.to_csv(r'C:\Users\tomas\Desktop\Data.csv', index=False)

    print(header)

    print(stats.head(10))

    player = []
    team = []
    dataList = []


    for index, row in stats.iterrows():
        player_list = [row.Player]
        player.append(player_list)
    
    for index, row in stats.iterrows():
        team_list = [row.Tm]
        team.append(team_list)

    for index, row in stats.iterrows():
        mylist = [row.Player, row.Tm]
        dataList.append(mylist)
scraping()

@app.route("/")
@app.route("/home")
def home():

    return render_template('home.html')

@app.route("/table")
def tables():
    df = pd.read_csv("C:\\Users\\tomas\\Desktop\\Data.csv")
    
    return render_template('table.html', data=df.to_html(index=False), posts=posts)

@app.route("/about")
def about():
    return render_template('about.html', title='Sobre')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('A sua conta foi criada com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Inicio de sessão inválido. Verifique o seu Email e Password ', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/")
@app.route("/posts")
def publicacoes():
    return render_template('posts.html', title='Publicacões', posts=posts)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/pics', picture_fn)
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path)


    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()


    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.username.data
        db.session.commit()
        flash('A sua conta foi atualizada!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='pics/' + current_user.image_file)
    return render_template('account.html', title='Conta', image_file=image_file,
    form=form)