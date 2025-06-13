from flask import Blueprint, request, jsonify
from src.models.database import db
from src.models.models import Alert, Process
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/', methods=['GET'])
def get_alerts():
    """Obtener lista de alertas"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', '')
        alert_type = request.args.get('alert_type', '')
        priority = request.args.get('priority', '')
        
        query = Alert.query
        
        if status:
            query = query.filter(Alert.status == status)
        
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        
        if priority:
            query = query.filter(Alert.priority == priority)
        
        # Ordenar por prioridad y fecha de creación
        priority_order = db.case(
            (Alert.priority == 'critical', 1),
            (Alert.priority == 'high', 2),
            (Alert.priority == 'medium', 3),
            (Alert.priority == 'low', 4),
            else_=5
        )
        query = query.order_by(priority_order, Alert.created_date.desc())
        
        alerts = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts.items],
            'total': alerts.total,
            'pages': alerts.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/', methods=['POST'])
def create_alert():
    """Crear nueva alerta"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('title'):
            return jsonify({'error': 'El título de la alerta es requerido'}), 400
        if not data.get('message'):
            return jsonify({'error': 'El mensaje de la alerta es requerido'}), 400
        if not data.get('alert_type'):
            return jsonify({'error': 'El tipo de alerta es requerido'}), 400
        
        # Verificar que el proceso existe si se especifica
        if data.get('process_id'):
            process = Process.query.get(data['process_id'])
            if not process:
                return jsonify({'error': 'El proceso especificado no existe'}), 404
        
        # Parsear fecha de vencimiento si se proporciona
        due_date = None
        if data.get('due_date'):
            try:
                due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Formato de fecha de vencimiento inválido'}), 400
        
        alert = Alert(
            title=data['title'],
            message=data['message'],
            alert_type=data['alert_type'],
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'active'),
            process_id=data.get('process_id'),
            due_date=due_date
        )
        
        db.session.add(alert)
        db.session.commit()
        
        logger.info(f"Alert created: {alert.title}")
        return jsonify(alert.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating alert: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Obtener alerta específica"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        return jsonify(alert.to_dict())
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Actualizar alerta"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        data = request.get_json()
        
        # Actualizar campos
        alert.title = data.get('title', alert.title)
        alert.message = data.get('message', alert.message)
        alert.alert_type = data.get('alert_type', alert.alert_type)
        alert.priority = data.get('priority', alert.priority)
        alert.status = data.get('status', alert.status)
        
        # Actualizar fecha de resolución si el estado cambia a resuelto
        if data.get('status') == 'resolved' and alert.resolved_date is None:
            alert.resolved_date = datetime.utcnow()
        elif data.get('status') != 'resolved':
            alert.resolved_date = None
        
        # Actualizar fecha de vencimiento si se proporciona
        if 'due_date' in data:
            if data['due_date']:
                try:
                    alert.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': 'Formato de fecha de vencimiento inválido'}), 400
            else:
                alert.due_date = None
        
        db.session.commit()
        
        logger.info(f"Alert updated: {alert_id}")
        return jsonify(alert.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating alert {alert_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Eliminar alerta"""
    try:
        alert = Alert.query.get_or_404(alert_id)
        
        db.session.delete(alert)
        db.session.commit()
        
        logger.info(f"Alert deleted: {alert_id}")
        return jsonify({'message': 'Alerta eliminada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting alert {alert_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/stats', methods=['GET'])
def get_alert_stats():
    """Obtener estadísticas de alertas"""
    try:
        total = Alert.query.count()
        active = Alert.query.filter_by(status='active').count()
        dismissed = Alert.query.filter_by(status='dismissed').count()
        resolved = Alert.query.filter_by(status='resolved').count()
        
        # Estadísticas por prioridad
        critical = Alert.query.filter_by(priority='critical', status='active').count()
        high = Alert.query.filter_by(priority='high', status='active').count()
        medium = Alert.query.filter_by(priority='medium', status='active').count()
        low = Alert.query.filter_by(priority='low', status='active').count()
        
        # Estadísticas por tipo
        deadline = Alert.query.filter_by(alert_type='deadline', status='active').count()
        missing_document = Alert.query.filter_by(alert_type='missing_document', status='active').count()
        process_expired = Alert.query.filter_by(alert_type='process_expired', status='active').count()
        
        return jsonify({
            'total': total,
            'by_status': {
                'active': active,
                'dismissed': dismissed,
                'resolved': resolved
            },
            'by_priority': {
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low
            },
            'by_type': {
                'deadline': deadline,
                'missing_document': missing_document,
                'process_expired': process_expired
            }
        })
    except Exception as e:
        logger.error(f"Error getting alert stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/active', methods=['GET'])
def get_active_alerts():
    """Obtener alertas activas"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        # Ordenar por prioridad y fecha de creación
        priority_order = db.case(
            (Alert.priority == 'critical', 1),
            (Alert.priority == 'high', 2),
            (Alert.priority == 'medium', 3),
            (Alert.priority == 'low', 4),
            else_=5
        )
        
        alerts = Alert.query.filter_by(status='active').order_by(
            priority_order, Alert.created_date.desc()
        ).limit(limit).all()
        
        return jsonify([alert.to_dict() for alert in alerts])
    except Exception as e:
        logger.error(f"Error getting active alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/check-deadlines', methods=['POST'])
def check_deadlines():
    """Verificar vencimientos y crear alertas automáticas"""
    try:
        alerts_created = 0
        
        # Verificar procesos que vencen pronto
        warning_days = 7  # Alertar 7 días antes del vencimiento
        warning_date = datetime.utcnow() + timedelta(days=warning_days)
        
        processes_ending_soon = Process.query.filter(
            Process.end_date <= warning_date,
            Process.end_date > datetime.utcnow(),
            Process.status.in_(['active', 'evaluation'])
        ).all()
        
        for process in processes_ending_soon:
            # Verificar si ya existe una alerta para este proceso
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
            # Verificar si ya existe una alerta para este proceso
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
        
        logger.info(f"Deadline check completed: {alerts_created} alerts created")
        return jsonify({
            'message': f'Verificación completada: {alerts_created} alertas creadas',
            'alerts_created': alerts_created
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error checking deadlines: {str(e)}")
        return jsonify({'error': str(e)}), 500

