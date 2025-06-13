import os
import sys
import os
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, session
from flask_cors import CORS
from src.models.database import db
from src.models.models import *
from src.models.excel_models import *
from src.routes.suppliers import suppliers_bp
from src.routes.processes import processes_bp
from src.routes.documents import documents_bp
from src.routes.bids import bids_bp
from src.routes.alerts import alerts_bp
from src.routes.reports import reports_bp
from src.routes.alerts_scheduler import alerts_scheduler_bp
from src.routes.excel_routes import excel_bp
from src.routes.auth import auth_bp, login_required

# Configuración de logging básico
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('procurement_system')

# Robustness setup (opcional)
try:
    from robustness_improvements import setup_logging, SystemMonitor, BackupManager
    logger = setup_logging()
    ROBUSTNESS_ENABLED = True
except ImportError:
    ROBUSTNESS_ENABLED = False
    logger.warning("Robustness improvements not available")

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'procurement_secret_key_2024_enhanced')

# Configuración de base de datos
# Para Heroku, usar DATABASE_URL si está disponible, sino usar SQLite local
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Heroku PostgreSQL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Desarrollo local con SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///procurement.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Crear carpeta de uploads si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# CORS - Permitir todas las origins para compatibilidad con Heroku
CORS(app, origins="*")

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
app.register_blueprint(processes_bp, url_prefix='/api/processes')
app.register_blueprint(documents_bp, url_prefix='/api/documents')
app.register_blueprint(bids_bp, url_prefix='/api/bids')
app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(alerts_scheduler_bp, url_prefix='/api/alerts-scheduler')
app.register_blueprint(excel_bp, url_prefix='/api/excel')

# Importar y registrar el nuevo blueprint de evaluación
from src.routes.evaluation import evaluation_bp
app.register_blueprint(evaluation_bp, url_prefix='/api/evaluation')

# Importar y registrar el nuevo blueprint de exportación
from src.routes.export import export_bp
app.register_blueprint(export_bp, url_prefix='/api/export')

# Importar y registrar el nuevo blueprint de calendario
from src.routes.calendar import calendar_bp
app.register_blueprint(calendar_bp, url_prefix='/api/calendar')

# Inicializar DB
db.init_app(app)

# Inicializar backups si aplica
if ROBUSTNESS_ENABLED:
    try:
        backup_manager = BackupManager()
    except Exception as e:
        logger.warning(f"Backup manager initialization failed: {e}")

@app.route('/health')
def health_check():
    try:
        if ROBUSTNESS_ENABLED:
            status = SystemMonitor.get_system_status()
            return jsonify(status), 200 if status['overall_status'] == 'healthy' else 503
        else:
            return jsonify({'status': 'ok', 'message': 'Basic health check passed'}), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/system/backup', methods=['POST'])
def create_backup():
    try:
        if not ROBUSTNESS_ENABLED:
            return jsonify({'success': False, 'message': 'Backup functionality not available'}), 503

        db_backup = backup_manager.create_database_backup()
        files_backup = backup_manager.create_files_backup()
        logger.info(f"Backup created successfully: DB={db_backup}, Files={files_backup}")

        return jsonify({
            'success': True,
            'message': 'Backup creado exitosamente',
            'database_backup': db_backup,
            'files_backup': files_backup
        })
    except Exception as e:
        logger.error(f"Backup creation failed: {str(e)}")
        return jsonify({'success': False, 'message': f'Error creando backup: {str(e)}'}), 500

@app.route('/api/system/status')
def system_status():
    try:
        if ROBUSTNESS_ENABLED:
            status = SystemMonitor.get_system_status()
        else:
            status = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'basic',
                'message': 'Sistema funcionando en modo básico'
            }
        return jsonify(status)
    except Exception as e:
        logger.error(f"System status check failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {error}")
    return jsonify({'error': 'Recurso no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    return jsonify({'error': 'Error interno del servidor'}), 500

@app.errorhandler(413)
def file_too_large(error):
    logger.warning(f"File too large: {error}")
    return jsonify({'error': 'Archivo muy grande. Máximo 16MB permitido'}), 413

# Inicialización de la base de datos
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")

        if ROBUSTNESS_ENABLED:
            try:
                status = SystemMonitor.get_system_status()
                if status['overall_status'] != 'healthy':
                    logger.warning(f"System health issues detected: {status}")
                backup_manager.cleanup_old_backups()
            except Exception as e:
                logger.warning(f"Robustness checks failed: {e}")
    except Exception as e:
        logger.error(f"Application initialization failed: {str(e)}")
        raise

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Servir archivos estáticos y SPA routing"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    # Verificar autenticación para rutas protegidas
    if path == '' or path == 'index.html':
        # Verificar si el usuario está autenticado
        if not session.get('authenticated'):
            # Servir página de login
            login_path = os.path.join(static_folder_path, 'login.html')
            if os.path.exists(login_path):
                return send_from_directory(static_folder_path, 'login.html')
            else:
                return "Login page not found", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        # Si está autenticado, servir index.html, sino login.html
        if session.get('authenticated'):
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404
        else:
            login_path = os.path.join(static_folder_path, 'login.html')
            if os.path.exists(login_path):
                return send_from_directory(static_folder_path, 'login.html')
            else:
                return "Login page not found", 404

if __name__ == '__main__':
    try:
        logger.info("Starting Procurement Management System...")
        # Para desarrollo local
        app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=False)
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise

