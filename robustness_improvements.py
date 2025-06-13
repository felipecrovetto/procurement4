"""
Mejoras de Robustez para el Sistema de Gestión de Compras y Licitaciones
Incluye: Sistema de logging, respaldos automáticos, monitoreo del sistema
"""

import os
import sys
import shutil
import sqlite3
import logging
import zipfile
import psutil
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import json

# Configuración de logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DIR = 'src/logs'
BACKUP_DIR = 'backups'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_RETENTION_DAYS = 30

def setup_logging():
    """Configurar sistema de logging avanzado"""
    # Crear directorio de logs si no existe
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Configurar logger principal
    logger = logging.getLogger('procurement_system')
    logger.setLevel(LOG_LEVEL)
    
    # Evitar duplicar handlers
    if logger.handlers:
        return logger
    
    # Handler para archivo con rotación
    log_file = os.path.join(LOG_DIR, 'procurement_system.log')
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=MAX_LOG_SIZE, 
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(LOG_LEVEL)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Configurar loggers específicos
    setup_specific_loggers()
    
    logger.info("Sistema de logging inicializado correctamente")
    return logger

def setup_specific_loggers():
    """Configurar loggers específicos para diferentes módulos"""
    modules = ['database', 'api', 'excel', 'backup', 'monitoring']
    
    for module in modules:
        module_logger = logging.getLogger(f'procurement_system.{module}')
        module_logger.setLevel(LOG_LEVEL)
        
        # Handler específico para cada módulo
        log_file = os.path.join(LOG_DIR, f'{module}.log')
        handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=3,
            encoding='utf-8'
        )
        handler.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        
        module_logger.addHandler(handler)

class BackupManager:
    """Gestor de respaldos automáticos"""
    
    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.logger = logging.getLogger('procurement_system.backup')
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_database_backup(self):
        """Crear respaldo de la base de datos"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'db_backup_{timestamp}.db'
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Buscar archivo de base de datos
            db_files = ['procurement.db', 'src/procurement.db', 'instance/procurement.db']
            source_db = None
            
            for db_file in db_files:
                if os.path.exists(db_file):
                    source_db = db_file
                    break
            
            if not source_db:
                self.logger.warning("No se encontró archivo de base de datos para respaldar")
                return None
            
            # Crear respaldo
            shutil.copy2(source_db, backup_path)
            
            # Comprimir respaldo
            zip_path = backup_path + '.zip'
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, backup_filename)
            
            # Eliminar archivo sin comprimir
            os.remove(backup_path)
            
            self.logger.info(f"Respaldo de base de datos creado: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"Error creando respaldo de base de datos: {str(e)}")
            return None
    
    def create_files_backup(self):
        """Crear respaldo de archivos subidos"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'files_backup_{timestamp}.zip'
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Directorios a respaldar
            dirs_to_backup = ['src/uploads', 'uploads']
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for backup_dir in dirs_to_backup:
                    if os.path.exists(backup_dir):
                        for root, dirs, files in os.walk(backup_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, os.path.dirname(backup_dir))
                                zipf.write(file_path, arcname)
            
            # Verificar que el archivo no esté vacío
            if os.path.getsize(backup_path) > 0:
                self.logger.info(f"Respaldo de archivos creado: {backup_path}")
                return backup_path
            else:
                os.remove(backup_path)
                self.logger.info("No hay archivos para respaldar")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creando respaldo de archivos: {str(e)}")
            return None
    
    def cleanup_old_backups(self):
        """Limpiar respaldos antiguos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
            deleted_count = 0
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
                        self.logger.info(f"Respaldo antiguo eliminado: {filename}")
            
            if deleted_count > 0:
                self.logger.info(f"Limpieza completada: {deleted_count} respaldos eliminados")
            
        except Exception as e:
            self.logger.error(f"Error en limpieza de respaldos: {str(e)}")
    
    def restore_database(self, backup_path):
        """Restaurar base de datos desde respaldo"""
        try:
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Archivo de respaldo no encontrado: {backup_path}")
            
            # Crear respaldo de seguridad antes de restaurar
            current_backup = self.create_database_backup()
            
            # Extraer y restaurar
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(self.backup_dir)
                
                # Buscar archivo de base de datos extraído
                for filename in zipf.namelist():
                    if filename.endswith('.db'):
                        extracted_path = os.path.join(self.backup_dir, filename)
                        
                        # Restaurar a ubicación principal
                        target_paths = ['procurement.db', 'src/procurement.db']
                        for target in target_paths:
                            if os.path.exists(os.path.dirname(target)) or target == 'procurement.db':
                                shutil.copy2(extracted_path, target)
                                self.logger.info(f"Base de datos restaurada desde: {backup_path}")
                                break
                        
                        # Limpiar archivo temporal
                        os.remove(extracted_path)
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error restaurando base de datos: {str(e)}")
            return False

class SystemMonitor:
    """Monitor del estado del sistema"""
    
    @staticmethod
    def get_system_status():
        """Obtener estado completo del sistema"""
        logger = logging.getLogger('procurement_system.monitoring')
        
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy',
                'checks': {}
            }
            
            # Verificar espacio en disco
            disk_usage = psutil.disk_usage('.')
            disk_free_gb = disk_usage.free / (1024**3)
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            status['checks']['disk_space'] = {
                'status': 'healthy' if disk_free_gb > 1 else 'warning',
                'free_gb': round(disk_free_gb, 2),
                'used_percent': round(disk_percent, 1),
                'message': f'{disk_free_gb:.1f} GB libres ({disk_percent:.1f}% usado)'
            }
            
            # Verificar memoria
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            status['checks']['memory'] = {
                'status': 'healthy' if memory_percent < 80 else 'warning',
                'used_percent': memory_percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'message': f'{memory_percent:.1f}% de memoria en uso'
            }
            
            # Verificar CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            status['checks']['cpu'] = {
                'status': 'healthy' if cpu_percent < 80 else 'warning',
                'usage_percent': cpu_percent,
                'message': f'{cpu_percent:.1f}% de CPU en uso'
            }
            
            # Verificar directorios críticos
            critical_dirs = ['src/uploads', 'src/logs', 'backups']
            dirs_status = []
            
            for directory in critical_dirs:
                if os.path.exists(directory):
                    dirs_status.append(f'{directory}: OK')
                else:
                    dirs_status.append(f'{directory}: FALTANTE')
                    status['overall_status'] = 'warning'
            
            status['checks']['directories'] = {
                'status': 'healthy' if all('OK' in d for d in dirs_status) else 'warning',
                'details': dirs_status
            }
            
            # Verificar base de datos
            db_status = SystemMonitor.check_database_health()
            status['checks']['database'] = db_status
            
            # Determinar estado general
            warning_checks = [check for check in status['checks'].values() 
                            if check['status'] == 'warning']
            error_checks = [check for check in status['checks'].values() 
                          if check['status'] == 'error']
            
            if error_checks:
                status['overall_status'] = 'error'
            elif warning_checks:
                status['overall_status'] = 'warning'
            
            logger.info(f"Verificación de estado completada: {status['overall_status']}")
            return status
            
        except Exception as e:
            logger.error(f"Error en verificación de estado: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def check_database_health():
        """Verificar salud de la base de datos"""
        try:
            # Buscar archivo de base de datos
            db_files = ['procurement.db', 'src/procurement.db', 'instance/procurement.db']
            db_path = None
            
            for db_file in db_files:
                if os.path.exists(db_file):
                    db_path = db_file
                    break
            
            if not db_path:
                return {
                    'status': 'warning',
                    'message': 'Archivo de base de datos no encontrado'
                }
            
            # Verificar integridad
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar que las tablas principales existan
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['suppliers', 'processes', 'bids', 'documents', 'alerts']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                conn.close()
                return {
                    'status': 'error',
                    'message': f'Tablas faltantes: {", ".join(missing_tables)}'
                }
            
            # Verificar integridad de la base de datos
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            conn.close()
            
            if integrity_result == 'ok':
                return {
                    'status': 'healthy',
                    'message': 'Base de datos funcionando correctamente',
                    'tables_count': len(tables)
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Problemas de integridad: {integrity_result}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error verificando base de datos: {str(e)}'
            }

class ErrorHandler:
    """Manejador centralizado de errores"""
    
    def __init__(self):
        self.logger = logging.getLogger('procurement_system.errors')
    
    def log_error(self, error, context=None):
        """Registrar error con contexto"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        self.logger.error(f"Error registrado: {json.dumps(error_info, indent=2)}")
        return error_info
    
    def handle_api_error(self, error, endpoint=None):
        """Manejar errores de API específicamente"""
        context = {
            'endpoint': endpoint,
            'error_category': 'api_error'
        }
        
        return self.log_error(error, context)

def initialize_robustness():
    """Inicializar todas las mejoras de robustez"""
    try:
        # Configurar logging
        logger = setup_logging()
        
        # Crear directorios necesarios
        directories = [LOG_DIR, BACKUP_DIR, 'src/uploads']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # Inicializar componentes
        backup_manager = BackupManager()
        error_handler = ErrorHandler()
        
        logger.info("Sistema de robustez inicializado correctamente")
        
        return {
            'logger': logger,
            'backup_manager': backup_manager,
            'error_handler': error_handler
        }
        
    except Exception as e:
        print(f"Error inicializando sistema de robustez: {str(e)}")
        return None

# Funciones de utilidad para integración con Flask
def create_backup_endpoint(app, backup_manager):
    """Crear endpoint para respaldos manuales"""
    @app.route('/api/system/backup', methods=['POST'])
    def manual_backup():
        try:
            db_backup = backup_manager.create_database_backup()
            files_backup = backup_manager.create_files_backup()
            
            return {
                'success': True,
                'database_backup': db_backup,
                'files_backup': files_backup,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}, 500

def create_monitoring_endpoint(app):
    """Crear endpoint para monitoreo del sistema"""
    @app.route('/api/system/status', methods=['GET'])
    def system_status():
        try:
            status = SystemMonitor.get_system_status()
            return status
        except Exception as e:
            return {'error': str(e)}, 500

# Exportar funciones principales
__all__ = [
    'setup_logging',
    'BackupManager', 
    'SystemMonitor',
    'ErrorHandler',
    'initialize_robustness'
]

