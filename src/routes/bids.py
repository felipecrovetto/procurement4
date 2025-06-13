from flask import Blueprint, request, jsonify
from src.models.database import db
from src.models.models import Bid, Process, Supplier
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
bids_bp = Blueprint('bids', __name__)

@bids_bp.route('/', methods=['GET'])
def get_bids():
    """Obtener lista de ofertas"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        process_id = request.args.get('process_id', type=int)
        supplier_id = request.args.get('supplier_id', type=int)
        status = request.args.get('status', '')
        
        query = Bid.query
        
        if process_id:
            query = query.filter(Bid.process_id == process_id)
        
        if supplier_id:
            query = query.filter(Bid.supplier_id == supplier_id)
        
        if status:
            query = query.filter(Bid.status == status)
        
        # Ordenar por fecha de envío descendente
        query = query.order_by(Bid.submission_date.desc())
        
        bids = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'bids': [bid.to_dict() for bid in bids.items],
            'total': bids.total,
            'pages': bids.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error getting bids: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bids_bp.route('/', methods=['POST'])
def create_bid():
    """Crear nueva oferta"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('process_id'):
            return jsonify({'error': 'El ID del proceso es requerido'}), 400
        if not data.get('supplier_id'):
            return jsonify({'error': 'El ID del proveedor es requerido'}), 400
        
        # Verificar que el proceso existe
        process = Process.query.get(data['process_id'])
        if not process:
            return jsonify({'error': 'El proceso especificado no existe'}), 404
        
        # Verificar que el proveedor existe
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({'error': 'El proveedor especificado no existe'}), 404
        
        # Verificar que no existe ya una oferta del mismo proveedor para el mismo proceso
        existing = Bid.query.filter_by(
            process_id=data['process_id'],
            supplier_id=data['supplier_id']
        ).first()
        if existing:
            return jsonify({'error': 'Ya existe una oferta de este proveedor para este proceso'}), 400
        
        bid = Bid(
            process_id=data['process_id'],
            supplier_id=data['supplier_id'],
            bid_amount=data.get('bid_amount'),
            technical_score=data.get('technical_score'),
            commercial_score=data.get('commercial_score'),
            total_score=data.get('total_score'),
            status=data.get('status', 'submitted'),
            notes=data.get('notes')
        )
        
        # Calcular score total si se proporcionan scores individuales
        if bid.technical_score is not None and bid.commercial_score is not None:
            bid.total_score = (bid.technical_score + bid.commercial_score) / 2
        
        db.session.add(bid)
        db.session.commit()
        
        logger.info(f"Bid created: Process {process.process_number}, Supplier {supplier.name}")
        return jsonify(bid.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating bid: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bids_bp.route('/<int:bid_id>', methods=['GET'])
def get_bid(bid_id):
    """Obtener oferta específica"""
    try:
        bid = Bid.query.get_or_404(bid_id)
        return jsonify(bid.to_dict())
    except Exception as e:
        logger.error(f"Error getting bid {bid_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bids_bp.route('/<int:bid_id>', methods=['PUT'])
def update_bid(bid_id):
    """Actualizar oferta"""
    try:
        bid = Bid.query.get_or_404(bid_id)
        data = request.get_json()
        
        # Actualizar campos
        bid.bid_amount = data.get('bid_amount', bid.bid_amount)
        bid.technical_score = data.get('technical_score', bid.technical_score)
        bid.commercial_score = data.get('commercial_score', bid.commercial_score)
        bid.total_score = data.get('total_score', bid.total_score)
        bid.status = data.get('status', bid.status)
        bid.notes = data.get('notes', bid.notes)
        
        # Actualizar fecha de evaluación si el estado cambia a evaluado
        if data.get('status') == 'evaluated' and bid.evaluation_date is None:
            bid.evaluation_date = datetime.utcnow()
        
        # Recalcular score total si se actualizan scores individuales
        if bid.technical_score is not None and bid.commercial_score is not None:
            bid.total_score = (bid.technical_score + bid.commercial_score) / 2
        
        db.session.commit()
        
        logger.info(f"Bid updated: {bid_id}")
        return jsonify(bid.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating bid {bid_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bids_bp.route('/<int:bid_id>', methods=['DELETE'])
def delete_bid(bid_id):
    """Eliminar oferta"""
    try:
        bid = Bid.query.get_or_404(bid_id)
        
        db.session.delete(bid)
        db.session.commit()
        
        logger.info(f"Bid deleted: {bid_id}")
        return jsonify({'message': 'Oferta eliminada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting bid {bid_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bids_bp.route('/stats', methods=['GET'])
def get_bid_stats():
    """Obtener estadísticas de ofertas"""
    try:
        total = Bid.query.count()
        submitted = Bid.query.filter_by(status='submitted').count()
        evaluated = Bid.query.filter_by(status='evaluated').count()
        awarded = Bid.query.filter_by(status='awarded').count()
        rejected = Bid.query.filter_by(status='rejected').count()
        
        return jsonify({
            'total': total,
            'submitted': submitted,
            'evaluated': evaluated,
            'awarded': awarded,
            'rejected': rejected
        })
    except Exception as e:
        logger.error(f"Error getting bid stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bids_bp.route('/process/<int:process_id>/comparison', methods=['GET'])
def get_process_bid_comparison(process_id):
    """Obtener comparación de ofertas para un proceso"""
    try:
        process = Process.query.get_or_404(process_id)
        bids = Bid.query.filter_by(process_id=process_id).all()
        
        comparison_data = {
            'process': process.to_dict(),
            'bids': [bid.to_dict() for bid in bids],
            'summary': {
                'total_bids': len(bids),
                'average_amount': sum(bid.bid_amount for bid in bids if bid.bid_amount) / len(bids) if bids else 0,
                'lowest_bid': min(bid.bid_amount for bid in bids if bid.bid_amount) if bids else 0,
                'highest_bid': max(bid.bid_amount for bid in bids if bid.bid_amount) if bids else 0
            }
        }
        
        return jsonify(comparison_data)
    except Exception as e:
        logger.error(f"Error getting bid comparison for process {process_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

