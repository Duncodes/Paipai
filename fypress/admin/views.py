# -*- coding: UTF-8 -*-
from flask import Blueprint, session, request, redirect, url_for, render_template, flash, jsonify, make_response, g
from flask.views import MethodView
from flask.ext.babel import lazy_gettext as gettext
from fypress.user import level_required, login_required, User, UserEditForm, UserAddForm, UserEditFormAdmin
from fypress.folder import FolderForm, Folder
from fypress.media import Media
from fypress.post import Post
from fypress.admin.static import messages
from fypress.admin.forms import GeneralSettingsForm, SocialSettingsForm
from fypress.admin.models import Option
from fypress.utils import get_redirect_target, Paginator
from fypress.local import _fypress_
from fypress import __version__

import json

admin  = Blueprint('admin', __name__,  url_prefix='/admin')
config = _fypress_.config

@admin.context_processor
def inject_options():
    from fypress.utils.mysql.sql import FyMySQL
    return dict(options=g.options, queries=FyMySQL._instance.queries, version=__version__, debug=config.DEBUG, flask_config=config)

@admin.before_request
def before_request():
    from fypress.user import User
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

    from fypress.admin import Option
    g.options = Option.auto_load()


@admin.after_request
def clear_cache(response):
    from fypress.public.decorators import cache
    cache.clear()
    return response

@admin.route('/')
@login_required
def root():
    return render_template('admin/index.html', title='Admin')

"""
    Errors & Utils
"""
@admin.route('/back')
def back():
    return redirect(get_redirect_target())

def handle_404():
    return render_template('admin/404.html', title=gettext('Error: 404')), 404

def handle_403():
    return render_template('admin/403.html', title=gettext('Error: 403')), 403

"""
    Settings
"""
@admin.route('/settings/all', methods=['POST', 'GET'])
@level_required(4)
def settings_general():
    form = GeneralSettingsForm(obj=Option.get_settings())

    if form.validate_on_submit():
        for data in form.data:
            Option.update(data, form.data[data])
        from fypress.public.views import reset_options
        reset_options()
        return redirect(url_for('admin.settings_general'))
        
    return render_template('admin/settings_general.html', form=form, title=gettext('General - Settings'))

@admin.route('/settings/social', methods=['POST', 'GET'])
@level_required(4)
def settings_social():
    form = SocialSettingsForm(obj=Option.get_settings('social'))

    if form.validate_on_submit():
        for data in form.data:
            Option.update(data, form.data[data])
        from fypress.public.views import reset_options
        reset_options()
        return redirect(url_for('admin.settings_social'))

    return render_template('admin/settings_social.html', form=form, title=gettext('Social - Settings'))


@admin.route('/settings/design', methods=['POST', 'GET'])
def settings_design():
    options = Option.get_settings('design')
    if request.form:
        for data in request.form:
            Option.update(data, request.form[data])
        from fypress.public.views import reset_options
        reset_options()

        return redirect(url_for('admin.settings_design'))

    return render_template('admin/settings_design.html', design=options, title=gettext('Design - Settings'))

@admin.route('/settings/reading')
def settings_reading():
    return render_template('admin/blank.html')

'''
    Comments
'''
@admin.route('/comments')
@admin.route('/comments/all')
@level_required(4)
def comments():
    return render_template('admin/blank.html')

"""
    Posts & Pages
"""
@admin.route('/pages')
@admin.route('/pages/all')
@level_required(1)
def pages():
    return posts(True)

@admin.route('/pages/edit', methods=['POST', 'GET'])
@admin.route('/pages/new', methods=['POST', 'GET'])
@level_required(1)
def pages_add():
    return posts_add(True)

@admin.route('/posts')
@admin.route('/posts/all')
@level_required(1)
def posts(page=False):
    numbers = Post.count_by_status(page)
    if not request.args.get('filter'):
        if page:
            query = Post.query.where(' _table_.post_status IN ("draft", "published") AND _table_.post_type="page"').order_by('created')
        else:
            query = Post.query.where(' _table_.post_status IN ("draft", "published") AND _table_.post_type="post"').order_by('created')
    else:
        if page:
            query   = Post.query.filter(status=request.args.get('filter'), type='page').order_by('created')
        else:
            query   = Post.query.filter(status=request.args.get('filter'), type='post').order_by('created')

    if page:
        title = gettext('Page')
    else:
        title = gettext('Posts')

    paginator = Paginator(
        query    = query,
        page     = request.args.get('page')
    )

    if page: urls = 'admin.pages'
    else: urls = 'admin.posts'

    return render_template('admin/posts.html', pages=paginator.links, title=title, posts=paginator.items, numbers=numbers, filter=request.args.get('filter'), page=page, urls=urls)

@admin.route('/posts/delete')
@level_required(4)
def posts_delete():
    post = Post.query.get(request.args.get('id'))
    if post:
        Post.delete(post)
        flash(messages['deleted']+' ('+str(post)+')')
        return redirect(get_redirect_target())
    else:
        return handle_404()

@admin.route('/posts/move')
@level_required(1)
def posts_move():
    post = Post.query.get(request.args.get('id'))
    if post:
        post.move(request.args.get('status'))
        flash(messages['moved']+' to '+request.args.get('status')+' ('+str(post)+')')
        return redirect(get_redirect_target())
    else:
        return handle_404()

@admin.route('/posts/edit', methods=['POST', 'GET'])
@admin.route('/posts/new', methods=['POST', 'GET'])
@level_required(1)
def posts_add(page=False):
    post = Post()

    if page: urls = 'admin.pages'
    else: urls = 'admin.posts'

    if request.args.get('edit'):
        post = Post.query.get(request.args.get('edit'))
        if post:
            if post.parent:
                return redirect(url_for(urls+'_add', edit=post.parent))
            if request.form:
                post_id = Post.update(request.form, post)
                flash(messages['updated']+' ('+str(post)+')')
                return redirect(url_for(urls+'_add', edit=post_id))
        else:
            return handle_404()
    else:
        if request.form:
            post_id = Post.create(request.form)
            flash(messages['added']+' ('+str(post)+')')
            return redirect(url_for(urls+'_add', edit=post_id))

    folders = Folder.get_all()

    if page:
        title = gettext('New - Page')
    else:
        title = gettext('New - Post')


    return render_template('admin/posts_new.html', folders=folders, post=post, title=title, page=page, urls=urls)

"""
    Medias
"""
@admin.route('/medias')
@admin.route('/medias/all')
@level_required(1)
def medias():
    if not request.args.get('filter'):
        query = Media.query.select_all(array=True).order_by('modified')
    else:
        query = Media.query.filter(type=request.args.get('filter')).order_by('modified')

    paginator = Paginator(
        query    = query,
        page     = request.args.get('page'),
        per_page = 12
    )
    return render_template('admin/medias.html',  medias=paginator.items, pages=paginator.links, title=gettext('Library - Medias'))

@admin.route('/medias/add/web')
@level_required(1)
def medias_web():
    return render_template('admin/medias_web.html',  title=gettext('Add from Web - Medias'))

@admin.route('/medias/add/upload')
@level_required(1)
def medias_upload():
    return render_template('admin/medias_upload.html',  title=gettext('Medias'))


"""
    Folders
"""
@admin.route('/folders', methods=['POST', 'GET'])
@admin.route('/folders/all', methods=['POST', 'GET'])
@level_required(3)
def folders():
    folders = Folder.get_all(True)
    folder  = None

    if request.args.get('edit') and request.args.get('edit') != 1:
        folder = Folder.query.get(request.args.get('edit'))
        form = FolderForm(obj=folder)
        if form.validate_on_submit():
            form.populate_obj(folder)
            folder.modified = 'NOW()'
            Folder.query.update(folder)
            flash(messages['updated']+' ('+str(folder)+')')
            return redirect(url_for('admin.folders'))
    else:
        form = FolderForm()
        if form.validate_on_submit():
            Folder.add(form)
            flash(messages['added']+' ('+str(folder)+')')
            return redirect(url_for('admin.folders'))

    return render_template('admin/folders.html', folders=folders, folder=folder, title=gettext('Categories'), form=form)


"""
    Users
"""
@admin.route('/users')
@admin.route('/users/all')
@level_required(4)
def users():
    paginator = Paginator(
        query    = User.query.select_all(array=True),
        page     = request.args.get('page')
    )
    return render_template('admin/users.html', title=gettext('Users'), users=paginator.items, pages=paginator.links)

@admin.route('/users/edit', methods=['POST', 'GET'])
@level_required(0)
def users_edit(id_user=None):
    if not id_user:
        id_user = request.args.get('id')

    user = User.query.get(id_user)
    if g.user.status == 4:
        form = UserEditFormAdmin(obj=user)
    else:
        form = UserEditForm(obj=user)

    if form.validate_on_submit():
        status = user.status
        form.populate_obj(user)
        
        # don't allow to change status unless admin.
        if g.user.status != 4:
            user.status = status

        if g.user.status == 4 or g.user.id == user.id:
            User.query.update(user)
            flash(messages['updated']+' ('+str(user)+')')

        if g.user.status == 4:
            return redirect(url_for('admin.users'))
        else:
            return redirect(url_for('admin.users_me'))

    return render_template('admin/users_edit.html', title=gettext('Edit - User'), user=user, form=form)

@admin.route('/users/new', methods=['POST', 'GET'])
@level_required(4)
def users_new():
    form = UserAddForm(request.form)

    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)
        user.registered = 'NOW()'
        User.query.add(user)
        flash(messages['added']+' ('+str(user)+')')
        return redirect(url_for('admin.users'))

    return render_template('admin/users_new.html', title=gettext('New - User'),  form=form)

@admin.route('/users/me', methods=['POST', 'GET'])
@login_required
def users_me():
    return users_edit(session.get('user_id'))


"""
    POST
"""
@admin.route('/medias/upload', methods=['POST'])
@level_required(1)
def post_media():
    return Media.upload(request.files['qqfile'], request.form)


@admin.route('/medias/upload/<uuid>', methods=['POST'])
@level_required(1)
def post_media_delete():
    try:
        #handle_delete(uuid)
        return jsonify(success=True), 200
    except Exception, e:
        return jsonify(success=False, error=e.message), 400

"""
    AJAX
"""
@admin.route('/medias/get')
@level_required(1)
def ajax_get_media():
    media = Media.query.get(request.args.get('id').replace('media_', ''))
    result = {}
    result['name'] = media.name
    result['icon'] = media.icon
    result['guid'] = media.guid
    if media.type == 'image':
        result['var'] = media.data['var']
    if media.type == 'oembed':
        result['html'] = media.html
        
    return jsonify(data=result)

@admin.route('/medias/oembed/add', methods=['POST'])
@level_required(1)
def ajax_oembed_add():
    return Media.add_oembed(request.form)
    
@admin.route('/medias/oembed', methods=['POST'])
@level_required(1)
def ajax_oembed():
    data = request.form.get('data')
    return Media.add_from_web(data)

@admin.route('/folders/update', methods=['POST'])
@level_required(3)
def ajax_folders():
    data = json.loads(request.form.get('data'))
    Folder.update_all(data)
    return ''
