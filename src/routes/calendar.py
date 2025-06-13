from flask import Blueprint, request, jsonify
from src.models.database import db
from src.models.models import Process, Bid, Supplier, Document, Alert
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
calendar_bp = Blueprint('calendar', __name__)

class ProcessMilestone:
    """Clase para representar hitos de procesos"""
    def __init__(self, process_id, process_number, title, milestone_type, date, status='upcoming', description=None):
        self.process_id = process_id
        self.process_number = process_number
        self.title = title
        self.milestone_type = milestone_type
        self.date = date
        self.status = status
        self.description = description
    
    def to_dict(self):
        return {
            'id': f"{self.process_id}_{self.milestone_type}",
            'process_id': self.process_id,
            'process_number': self.process_number,
            'title': self.title,
            'milestone_type': self.milestone_type,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'description': self.description
        }
    
    def to_fullcalendar_event(self):
        """Convertir a formato de evento de FullCalendar"""
        color_map = {
            'start': '#0d6efd',      # primary
            'end': '#dc3545',        # danger
            'award': '#198754',      # success
            'delivery': '#ffc107',   # warning
            'evaluation': '#0dcaf0', # info
            'other': '#6c757d'       # secondary
        }
        
        # Determinar si está vencido
        if self.date:
            # Convertir self.date a date si es datetime
            milestone_date = self.date.date() if hasattr(self.date, 'date') else self.date
            is_overdue = milestone_date < datetime.now().date() and self.status != 'completed'
        else:
            is_overdue = False
        
        return {
            'id': self.to_dict()['id'],
            'title': f"{self.process_number} - {self.get_milestone_label()}",
            'start': self.date.isoformat() if self.date else None,
            'backgroundColor': '#dc3545' if is_overdue else color_map.get(self.milestone_type, color_map['other']),
            'borderColor': '#dc3545' if is_overdue else color_map.get(self.milestone_type, color_map['other']),
            'textColor': '#ffffff',
            'extendedProps': {
                'process_id': self.process_id,
                'process_number': self.process_number,
                'milestone_type': self.milestone_type,
                'status': self.status,
                'description': self.description,
                'is_overdue': is_overdue
            }
        }
    
    def get_milestone_label(self):
        """Obtener etiqueta del hito"""
        labels = {
            'start': 'Inicio',
            'end': 'Fin',
            'award': 'Adjudicación',
            'delivery': 'Entrega',
            'evaluation': 'Evaluación',
            'other': 'Otro'
        }
        return labels.get(self.milestone_type, 'Hito')

@calendar_bp.route('/milestones', methods=['GET'])
def get_milestones():
    """Obtener todos los hitos de procesos"""
    try:
        # Parámetros de filtro
        process_id = request.args.get('process_id')
        milestone_type = request.args.get('milestone_type')
        status = request.args.get('status')
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        # Obtener procesos
        query = Process.query
        if process_id:
            query = query.filter(Process.id == process_id)
        
        processes = query.all()
        milestones = []
        
        for process in processes:
            # Generar hitos automáticamente basados en fechas del proceso
            process_milestones = generate_process_milestones(process)
            
            # Aplicar filtros
            for milestone in process_milestones:
                # Filtro por tipo de hito
                if milestone_type and milestone.milestone_type != milestone_type:
                    continue
                
                # Filtro por estado
                if status:
                    if status == 'upcoming' and milestone.status != 'upcoming':
                        continue
                    elif status == 'overdue' and milestone.status != 'overdue':
                        continue
                    elif status == 'completed' and milestone.status != 'completed':
                        continue
                
                # Filtro por rango de fechas
                if start_date and milestone.date:
                    try:
                        start_dt = datetime.fromisoformat(start_date).date()
                        if milestone.date < start_dt:
                            continue
                    except:
                        pass
                
                if end_date and milestone.date:
                    try:
                        end_dt = datetime.fromisoformat(end_date).date()
                        if milestone.date > end_dt:
                            continue
                    except:
                        pass
                
                milestones.append(milestone)
        
        return jsonify([milestone.to_dict() for milestone in milestones])
    
    except Exception as e:
        logger.error(f"Error getting milestones: {str(e)}")
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/events', methods=['GET'])
def get_calendar_events():
    """Obtener eventos para FullCalendar"""
    try:
        # Parámetros de FullCalendar
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        # Filtros adicionales
        process_id = request.args.get('process_id')
        milestone_type = request.args.get('milestone_type')
        status = request.args.get('status')
        
        # Obtener procesos
        query = Process.query
        if process_id:
            query = query.filter(Process.id == process_id)
        
        processes = query.all()
        events = []
        
        for process in processes:
            # Generar hitos del proceso
            process_milestones = generate_process_milestones(process)
            
            for milestone in process_milestones:
                # Aplicar filtros
                if milestone_type and milestone.milestone_type != milestone_type:
                    continue
                
                if status:
                    if status == 'upcoming' and milestone.status != 'upcoming':
                        continue
                    elif status == 'overdue' and milestone.status != 'overdue':
                        continue
                    elif status == 'completed' and milestone.status != 'completed':
                        continue
                
                # Filtro por rango de fechas de FullCalendar
                if start_date and milestone.date:
                    try:
                        start_dt = datetime.fromisoformat(start_date).date()
                        if milestone.date < start_dt:
                            continue
                    except:
                        pass
                
                if end_date and milestone.date:
                    try:
                        end_dt = datetime.fromisoformat(end_date).date()
                        if milestone.date > end_dt:
                            continue
                    except:
                        pass
                
                events.append(milestone.to_fullcalendar_event())
        
        return jsonify(events)
    
    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/upcoming', methods=['GET'])
def get_upcoming_milestones():
    """Obtener hitos próximos (próximos 7 días)"""
    try:
        days_ahead = int(request.args.get('days', 7))
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        processes = Process.query.all()
        upcoming = []
        
        for process in processes:
            milestones = generate_process_milestones(process)
            for milestone in milestones:
                if (milestone.date and 
                    today <= milestone.date <= future_date and 
                    milestone.status == 'upcoming'):
                    upcoming.append(milestone)
        
        # Ordenar por fecha
        upcoming.sort(key=lambda x: x.date)
        
        return jsonify([milestone.to_dict() for milestone in upcoming])
    
    except Exception as e:
        logger.error(f"Error getting upcoming milestones: {str(e)}")
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/overdue', methods=['GET'])
def get_overdue_milestones():
    """Obtener hitos vencidos"""
    try:
        today = datetime.now().date()
        
        processes = Process.query.all()
        overdue = []
        
        for process in processes:
            milestones = generate_process_milestones(process)
            for milestone in milestones:
                if (milestone.date and 
                    milestone.date < today and 
                    milestone.status != 'completed'):
                    milestone.status = 'overdue'
                    overdue.append(milestone)
        
        # Ordenar por fecha (más antiguos primero)
        overdue.sort(key=lambda x: x.date)
        
        return jsonify([milestone.to_dict() for milestone in overdue])
    
    except Exception as e:
        logger.error(f"Error getting overdue milestones: {str(e)}")
        return jsonify({'error': str(e)}), 500

@calendar_bp.route('/stats', methods=['GET'])
def get_calendar_stats():
    """Obtener estadísticas del calendario"""
    try:
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        
        processes = Process.query.all()
        
        upcoming_count = 0
        overdue_count = 0
        total_milestones = 0
        
        for process in processes:
            milestones = generate_process_milestones(process)
            total_milestones += len(milestones)
            
            for milestone in milestones:
                if milestone.date:
                    if today <= milestone.date <= next_week and milestone.status == 'upcoming':
                        upcoming_count += 1
                    elif milestone.date < today and milestone.status != 'completed':
                        overdue_count += 1
        
        return jsonify({
            'upcoming_count': upcoming_count,
            'overdue_count': overdue_count,
            'total_milestones': total_milestones
        })
    
    except Exception as e:
        logger.error(f"Error getting calendar stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_process_milestones(process):
    """Generar hitos automáticamente para un proceso"""
    milestones = []
    today = datetime.now().date()
    
    # Determinar estado basado en el estado del proceso
    def get_milestone_status(milestone_date, process_status):
        if not milestone_date:
            return 'upcoming'
        
        # Convertir milestone_date a date si es datetime
        if hasattr(milestone_date, 'date'):
            milestone_date = milestone_date.date()
        
        if process_status in ['completed', 'cancelled']:
            return 'completed'
        elif milestone_date < today:
            return 'overdue'
        else:
            return 'upcoming'
    
    # Hito de inicio
    if process.start_date:
        milestones.append(ProcessMilestone(
            process_id=process.id,
            process_number=process.process_number,
            title=process.title,
            milestone_type='start',
            date=process.start_date,
            status=get_milestone_status(process.start_date, process.status),
            description=f"Inicio del proceso {process.process_number}"
        ))
    
    # Hito de fin
    if process.end_date:
        milestones.append(ProcessMilestone(
            process_id=process.id,
            process_number=process.process_number,
            title=process.title,
            milestone_type='end',
            date=process.end_date,
            status=get_milestone_status(process.end_date, process.status),
            description=f"Fin del proceso {process.process_number}"
        ))
    
    # Hito de evaluación (estimado a la mitad del proceso)
    if process.start_date and process.end_date:
        evaluation_date = process.start_date + (process.end_date - process.start_date) / 2
        milestones.append(ProcessMilestone(
            process_id=process.id,
            process_number=process.process_number,
            title=process.title,
            milestone_type='evaluation',
            date=evaluation_date,
            status=get_milestone_status(evaluation_date, process.status),
            description=f"Evaluación de ofertas - {process.process_number}"
        ))
    
    # Hito de adjudicación (estimado 5 días después del fin)
    if process.end_date:
        award_date = process.end_date + timedelta(days=5)
        milestones.append(ProcessMilestone(
            process_id=process.id,
            process_number=process.process_number,
            title=process.title,
            milestone_type='award',
            date=award_date,
            status=get_milestone_status(award_date, process.status),
            description=f"Adjudicación del proceso {process.process_number}"
        ))
    
    # Hito de entrega (estimado 30 días después de adjudicación)
    if process.end_date:
        delivery_date = process.end_date + timedelta(days=35)
        milestones.append(ProcessMilestone(
            process_id=process.id,
            process_number=process.process_number,
            title=process.title,
            milestone_type='delivery',
            date=delivery_date,
            status=get_milestone_status(delivery_date, process.status),
            description=f"Entrega estimada - {process.process_number}"
        ))
    
    return milestones

