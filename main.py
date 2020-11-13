from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
import math

with open("config.json", "r") as config:
    params = json.load(config)["params"]

local_server = True
app = Flask(__name__)

app.secret_key = "SECRET-KEY"
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail_user"],
    MAIL_PASSWORD=params["gmail_password"]
)

mail = Mail(app)


if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)


class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@ app.route("/")
@ app.route("/home")
def home():
    posts = Posts.query.filter_by().all()
    last_page = math.ceil(len(posts)/int(params["no_of_posts"]))
    page = request.args.get("page")

    if (not str(page).isnumeric()):
        page = 1

    page = int(page)
    posts = posts[(page-1)*int(params["no_of_posts"]):(page-1)*int(params["no_of_posts"]) + int(params["no_of_posts"])]
    
    if page == 1:
        prev_page = "#"
        next_page = "/?page="+str(page+1)

    elif page == last_page:
        prev_page = "/?page="+str(page-1)
        next_page = "#"

    else:
        prev_page = "/?page="+str(page-1)
        next_page = "/?page="+str(page+1)


    return render_template("index.html", params=params, posts=posts, prev_page=prev_page, next_page=next_page)


@ app.route("/about")
def about():
    return render_template("about.html", params=params)


@ app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    posts = Posts.query.all()
    if "user" in session and session["user"] == params["admin_user"]:
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method == "POST":
        username = request.form.get('uname')
        userpass = request.form.get('pass')

        if username == params["admin_user"] and userpass == params["admin_password"]:
            # set session variable
            session["user"] = username
            return render_template("dashboard.html", params=params, posts=posts)

    else:
        return render_template("sign_in.html", params=params)


@ app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name, phone_num=phone,
                         message=message, email=email, date=datetime.now())

        db.session.add(entry)
        db.session.commit()

        mail.send_message(f"New Message from {name}", sender=email, recipients=[
                          params["gmail_user"]], body=message+"\n"+phone)

    return render_template("contact.html", params=params)


@ app.route("/new-post", methods=["GET", "POST"])
def new_post():
    if "user" in session and session["user"] == params["admin_user"]:
        if request.method == "POST":
            box_title = request.form.get("title")
            tag_line = request.form.get("tag_line")
            slug = request.form.get("slug")
            content = request.form.get("content")
            date = datetime.now()

            post = Posts(title=box_title, tagline=tag_line,
                         slug=slug, content=content, date=date)

            db.session.add(post)
            db.session.commit()

        return render_template("new_post.html", params=params)


@ app.route("/post/<string:post_slug>", methods=['GET'])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)


@ app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if "user" in session and session["user"] == params["admin_user"]:
        if request.method == "POST":
            box_title = request.form.get("title")
            tag_line = request.form.get("tag_line")
            slug = request.form.get("slug")
            content = request.form.get("content")
            date = datetime.now()

            post = Posts.query.filter_by(sno=sno).first()

            post.title = box_title
            post.tagline = tag_line
            post.slug = slug
            post.content = content
            post.date = date

            db.session.commit()

            return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post=post)
    else:
        return redirect("/dashboard")


@ app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashboard")


@ app.route("/delete/<string:sno>")
def delete(sno):
    if "user" in session and session["user"] == params["admin_user"]:
        post = Posts.query.filter_by(sno=sno).first()

        db.session.delete(post)
        db.session.commit()

        return redirect("/dashboard")



app.run(debug=True)
