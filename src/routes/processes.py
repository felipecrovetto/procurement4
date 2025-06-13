from flask import Blueprint, request, jsonify
from src.models.database import db
from src.models.models import Process
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
processes_bp = Blueprint('processes', __name__)

@processes_bp.route('/', methods=['GET'])
def get_processes():
    """Obtener lista de procesos"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        process_type = request.args.get('process_type', '')
        
        query = Process.query
        
        if search:
            query = query.filter(
                db.or_(
                    Process.process_number.contains(search),
                    Process.title.contains(search),
                    Process.description.contains(search)
                )
            )
        
        if status:
            query = query.filter(Process.status == status)
            
        if process_type:
            query = query.filter(Process.process_type == process_type)
        
        # Ordenar por fecha de creación descendente
        query = query.order_by(Process.created_date.desc())
        
        processes = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'processes': [process.to_dict() for process in processes.items],
            'total': processes.total,
            'pages': processes.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error getting processes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@processes_bp.route('/', methods=['POST'])
def create_process():
    """Crear nuevo proceso"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('process_number'):
            return jsonify({'error': 'El número de proceso es requerido'}), 400
        if not data.get('title'):
            return jsonify({'error': 'El título del proceso es requerido'}), 400
        if not data.get('process_type'):
            return jsonify({'error': 'El tipo de proceso es requerido'}), 400
        
        # Verificar número de proceso único
        existing = Process.query.filter_by(process_number=data['process_number']).first()
        if existing:
            return jsonify({'error': 'Ya existe un proceso con este número'}), 400
        
        # Parsear fechas
        start_date = None
        end_date = None
        
        if data.get('start_date'):
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Formato de fecha de inicio inválido'}), 400
        
        if data.get('end_date'):
            try:
                end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Formato de fecha de fin inválido'}), 400
        
        process = Process(
            process_number=data['process_number'],
            title=data['title'],
            description=data.get('description'),
            process_type=data['process_type'],
            status=data.get('status', 'draft'),
            budget=data.get('budget'),
            start_date=start_date,
            end_date=end_date,
            notes=data.get('notes')
        )
        
        db.session.add(process)
        db.session.commit()
        
        logger.info(f"Process created: {process.process_number}")
        return jsonify(process.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating process: {str(e)}")
        return jsonify({'error': str(e)}), 500

@processes_bp.route('/<int:process_id>', methods=['GET'])
def get_process(process_id):
    """Obtener proceso específico"""
    try:
        process = Process.query.get_or_404(process_id)
        return jsonify(process.to_dict())
    except Exception as e:
        logger.error(f"Error getting process {process_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@processes_bp.route('/<int:process_id>', methods=['PUT'])
def update_process(process_id):
    """Actualizar proceso"""
    try:
        process = Process.query.get_or_404(process_id)
        data = request.get_json()
        
        # Verificar número de proceso único si se cambia
        if data.get('process_number') and data['process_number'] != process.process_number:
            existing = Process.query.filter_by(process_number=data['process_number']).first()
            if existing:
                return jsonify({'error': 'Ya existe un proceso con este número'}), 400
        
        # Parsear fechas si se proporcionan
        if data.get('start_date'):
            try:
                process.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Formato de fecha de inicio inválido'}), 400
        
        if data.get('end_date'):
            try:
                process.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Formato de fecha de fin inválido'}), 400
        
        # Actualizar campos
        process.process_number = data.get('process_number', process.process_number)
        process.title = data.get('title', process.title)
        process.description = data.get('description', process.description)
        process.process_type = data.get('process_type', process.process_type)
        process.status = data.get('status', process.status)
        process.budget = data.get('budget', process.budget)
        process.notes = data.get('notes', process.notes)
        
        db.session.commit()
        
        logger.info(f"Process updated: {process.process_number}")
        return jsonify(process.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating process {process_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@processes_bp.route('/<int:process_id>', methods=['DELETE'])
def delete_process(process_id):
    """Eliminar proceso"""
    try:
        process = Process.query.get_or_404(process_id)
        
        # Verificar si tiene ofertas asociadas
        if process.bids:
            return jsonify({'error': 'No se puede eliminar un proceso con ofertas asociadas'}), 400
        
        db.session.delete(process)
        db.session.commit()
        
        logger.info(f"Process deleted: {process.process_number}")
        return jsonify({'message': 'Proceso eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting process {process_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@processes_bp.route('/stats', methods=['GET'])
def get_process_stats():
    """Obtener estadísticas de procesos"""
    try:
        total = Process.query.count()
        draft = Process.query.filter_by(status='draft').count()
        active = Process.query.filter_by(status='active').count()
        evaluation = Process.query.filter_by(status='evaluation').count()
        completed = Process.query.filter_by(status='completed').count()
        cancelled = Process.query.filter_by(status='cancelled').count()
        
        # Estadísticas por tipo
        simple_purchase = Process.query.filter_by(process_type='simple_purchase').count()
        large_tender = Process.query.filter_by(process_type='large_tender').count()
        
        return jsonify({
            'total': total,
            'by_status': {
                'draft': draft,
                'active': active,
                'evaluation': evaluation,
                'completed': completed,
                'cancelled': cancelled
            },
            'by_type': {
                'simple_purchase': simple_purchase,
                'large_tender': large_tender
            }
        })
    except Exception as e:
        logger.error(f"Error getting process stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@processes_bp.route('/recent', methods=['GET'])
def get_recent_processes():
    """Obtener procesos recientes"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        processes = Process.query.order_by(
            Process.created_date.desc()
        ).limit(limit).all()
        
        return jsonify([process.to_dict() for process in processes])
    except Exception as e:
        logger.error(f"Error getting recent processes: {str(e)}")
        return jsonify({'error': str(e)}), 500

