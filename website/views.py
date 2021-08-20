import os
import secrets
from PIL import Image
from flask import Blueprint, render_template, request, flash, jsonify, url_for, redirect
from flask_login import login_required, current_user
from .models import Note, User, Post
from . import db, create_app
import json
import os.path



views = Blueprint('views', __name__)

def save_picture(picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(picture.filename)
    picture_fn = random_hex + f_ext
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    picture_path = os.path.join(ROOT_DIR, 'static/images', picture_fn)

    output_size = (125, 125)
    i = Image.open(picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@views.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    image_file = url_for('static', filename='images/' + current_user.image_file)

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        picture = request.files.get('picture')

        if (len(username) > 0) or (len(email) > 0) or picture:
            if len(username) > 0:
                if username != current_user.username:
                    user_username = User.query.filter_by(username=username).first()
                    if user_username:
                        flash('Username already exists', category='error')
                    elif len(username) < 3:
                        flash('Username must be greater than 2 characters', category='error')
                    else:
                        current_user.username = username

            if len(email) > 0:
                if email != current_user.email:
                    user_email = User.query.filter_by(email=email).first()
                    if user_email:
                        flash('Email already exists', category='error')
                    elif len(email) < 4:
                        flash('Email must be greater than 3 characters.', category='error')
                    else:
                        current_user.email = email

            if picture.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                picture_file = save_picture(picture)
                current_user.image_file = picture_file
            else:
                flash('Picture must be .png, .jpg, or .jpeg', category='error')

            db.session.commit()
            flash('Your account information has been updated', category='success')
            return redirect(url_for('views.account'))

        else:
            flash('Information has not been changed', category='error')

    return render_template("account.html", user=current_user, image_file=image_file)

@views.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    image_file = url_for('static', filename='images/' + current_user.image_file)

    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added', category='success')


    return render_template("notes.html", user=current_user, image_file=image_file)

@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date.desc()).paginate(page=page, per_page=5)

    return render_template("home.html", posts=posts, user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

@views.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        if len(title) < 1:
            flash('Title is too short', category='error')
        elif len(content) < 1:
            flash('Content is too short', category='error')
        else:
            post = Post(title=title, content=content, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Your post has been created.', category='success')
            
            return redirect(url_for('views.home'))

    return render_template('new_post.html', legend='New Post', user=current_user)

@views.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)

    return render_template('post.html', title=post.title, post=post, user=current_user)

@views.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        abort(403)

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        if len(title) < 1:
            flash('Title is too short', category='error')
        elif len(content) < 1:
            flash('Content is too short', category='error')
        else:
            post.title = title
            post.content = content
            db.session.commit()
            flash('Your post has been updated.', category='success')
            
            return redirect(url_for('views.post', post_id=post.id))
    
    elif request.method == 'GET':
        title = post.title
        content = post.content

    return render_template('new_post.html', legend='Update Post', user=current_user)

@views.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted.', 'success')

    return redirect(url_for('views.home'))

@views.route("/user/<string:username>")
@login_required
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    filter_user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=filter_user)\
        .order_by(Post.date.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=current_user, filter_user=filter_user )