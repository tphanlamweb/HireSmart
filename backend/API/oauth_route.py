from flask import Blueprint, redirect, url_for, current_app, flash
from flask_login import login_user
from .oauth_config import oauth
from .models import User, db
import traceback

oauth_bp = Blueprint("oauth_bp", __name__)

@oauth_bp.route('/login/google')
def google_login():
    try:
        google = oauth.create_client('google')
        redirect_uri = url_for('oauth_bp.google_authorize', _external=True)
        return google.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.error(f"Google login error: {e}")
        current_app.logger.error(traceback.format_exc())
        flash('Unable to connect to Google authentication service.', 'error')
        return redirect(url_for('user.login'))

@oauth_bp.route('/login/google/authorize')
def google_authorize():
    try:
        google = oauth.create_client('google')
        token = google.authorize_access_token()
        
        # Kiểm tra token tồn tại
        if not token:
            current_app.logger.error("No token received from Google")
            flash('Authentication failed.', 'error')
            return redirect(url_for('user.login'))
        
        user_info = token.get('userinfo')
        
        # Kiểm tra user_info tồn tại
        if not user_info:
            current_app.logger.error("No userinfo in token")
            flash('Authentication failed.', 'error')
            return redirect(url_for('user.login'))
        
        email = user_info.get('email')
        
        # Kiểm tra email tồn tại
        if not email:
            current_app.logger.error("No email in user info")
            flash('Authentication failed.', 'error')
            return redirect(url_for('user.login'))

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                user_name=user_info.get('name'),
                provider='google',
                provider_id=user_info.get('sub', user_info.get('id')),  # Sử dụng 'sub' thay vì 'id'
                avatar_url=user_info.get('picture')
            )
            db.session.add(user)
            db.session.commit()

        login_user(user, remember=True)
        flash('Successfully logged in!', 'success')
        return redirect(url_for('views.home'))
        
    except Exception as e:
        current_app.logger.error(f"OAuth authorize error: {e}")
        current_app.logger.error(traceback.format_exc())
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('user.login'))