from flask import Blueprint, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from src.models.database import db
from src.models.models import Alert, Process
from datetime import datetime, timedelta
import logging
import atexit

logger = logging.getLogger(__name__)
alerts_scheduler_bp = Blueprint('alerts_scheduler', __name__)

# Scheduler global
scheduler = None

def check_process_deadlines():
    """Función para verificar vencimientos de procesos automáticamente"""
    try:
        with db.app.app_context():
            alerts_created = 0
            
            # Verificar procesos que vencen pronto
            warning_days = 7
            warning_date = datetime.utcnow() + timedelta(days=warning_days)
            
            processes_ending_soon = Process.query.filter(
                Process.end_date <= warning_date,
                Process.end_date > datetime.utcnow(),
                Process.status.in_(['active', 'evaluation'])
            ).all()
            
            for process in processes_ending_soon:
                existing_alert = Alert.query.filter_by(
                    process_id=process.id,
                    alert_type='deadline',
                    status='active'
                ).first()
                
                if not existing_alert:
                    days_remaining = (process.end_date - datetime.utcnow()).days
                    
                    alert = Alert(
                        title=f'Proceso próximo a vencer: {process.process_number}',
                        message=f'El proceso "{process.title}" vence en {days_remaining} días ({process.end_date.strftime("%d/%m/%Y")})',
                        alert_type='deadline',
                        priority='high' if days_remaining <= 3 else 'medium',
                        process_id=process.id,
                        due_date=process.end_date
                    )
                    
                    db.session.add(alert)
                    alerts_created += 1
            
            # Verificar procesos vencidos
            expired_processes = Process.query.filter(
                Process.end_date < datetime.utcnow(),
                Process.status.in_(['active', 'evaluation'])
            ).all()
            
            for process in expired_processes:
                existing_alert = Alert.query.filter_by(
                    process_id=process.id,
                    alert_type='process_expired',
                    status='active'
                ).first()
                
                if not existing_alert:
                    alert = Alert(
                        title=f'Proceso vencido: {process.process_number}',
                        message=f'El proceso "{process.title}" venció el {process.end_date.strftime("%d/%m/%Y")} y requiere atención',
                        alert_type='process_expired',
                        priority='critical',
                        process_id=process.id
                    )
                    
                    db.session.add(alert)
                    alerts_created += 1
            
            db.session.commit()
            logger.info(f"Automatic deadline check: {alerts_created} alerts created")
            
    except Exception as e:
        logger.error(f"Error in automatic deadline check: {str(e)}")
        if db.session:
            db.session.rollback()

def init_scheduler(app):
    """Inicializar el scheduler de alertas"""
    global scheduler
    
    if scheduler is None:
        scheduler = BackgroundScheduler()
        
        # Programar verificación diaria a las 9:00 AM
        scheduler.add_job(
            func=check_process_deadlines,
            trigger=CronTrigger(hour=9, minute=0),
            id='deadline_check',
            name='Check process deadlines',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Alert scheduler started")
        
        # Asegurar que el scheduler se cierre al terminar la aplicación
        atexit.register(lambda: scheduler.shutdown())

@alerts_scheduler_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """Obtener estado del scheduler"""
    try:
        global scheduler
        
        if scheduler is None:
            return jsonify({
                'running': False,
                'message': 'Scheduler no inicializado'
            })
        
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return jsonify({
            'running': scheduler.running,
            'jobs': jobs
        })
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_scheduler_bp.route('/run-check', methods=['POST'])
def run_manual_check():
    """Ejecutar verificación manual de vencimientos"""
    try:
        check_process_deadlines()
        return jsonify({'message': 'Verificación manual ejecutada exitosamente'})
    except Exception as e:
        logger.error(f"Error in manual check: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_scheduler_bp.route('/start', methods=['POST'])
def start_scheduler():
    """Iniciar el scheduler"""
    try:
        global scheduler
        
        if scheduler is None:
            from flask import current_app
            init_scheduler(current_app)
            return jsonify({'message': 'Scheduler iniciado exitosamente'})
        elif not scheduler.running:
            scheduler.start()
            return jsonify({'message': 'Scheduler reiniciado exitosamente'})
        else:
            return jsonify({'message': 'Scheduler ya está ejecutándose'})
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_scheduler_bp.route('/stop', methods=['POST'])
def stop_scheduler():
    """Detener el scheduler"""
    try:
        global scheduler
        
        if scheduler and scheduler.running:
            scheduler.shutdown()
            scheduler = None
            return jsonify({'message': 'Scheduler detenido exitosamente'})
        else:
            return jsonify({'message': 'Scheduler no está ejecutándose'})
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        return jsonify({'error': str(e)}), 500

