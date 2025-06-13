from flask import Blueprint, request, jsonify, session
from functools import wraps
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

# Credenciales hardcodeadas
VALID_CREDENTIALS = {
    'username': 'procurement',
    'password': 'procurement'
}

def login_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint de inicio de sesión"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if (username == VALID_CREDENTIALS['username'] and 
            password == VALID_CREDENTIALS['password']):
            session['authenticated'] = True
            session['username'] = username
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': username
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Credenciales inválidas'
            }), 401
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Endpoint de cierre de sesión"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logout successful'
    })

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Verificar estado de autenticación"""
    return jsonify({
        'authenticated': session.get('authenticated', False),
        'username': session.get('username', None)
    })

