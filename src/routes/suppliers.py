from flask import Blueprint, request, jsonify
from src.models.database import db
from src.models.models import Supplier
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/', methods=['GET'])
def get_suppliers():
    """Obtener lista de proveedores"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        
        query = Supplier.query
        
        if search:
            query = query.filter(
                db.or_(
                    Supplier.name.contains(search),
                    Supplier.contact_person.contains(search),
                    Supplier.email.contains(search),
                    Supplier.rut.contains(search)
                )
            )
        
        if status:
            query = query.filter(Supplier.status == status)
        
        suppliers = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'suppliers': [supplier.to_dict() for supplier in suppliers.items],
            'total': suppliers.total,
            'pages': suppliers.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error getting suppliers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suppliers_bp.route('/', methods=['POST'])
def create_supplier():
    """Crear nuevo proveedor"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('name'):
            return jsonify({'error': 'El nombre del proveedor es requerido'}), 400
        
        # Verificar RUT único si se proporciona
        if data.get('rut'):
            existing = Supplier.query.filter_by(rut=data['rut']).first()
            if existing:
                return jsonify({'error': 'Ya existe un proveedor con este RUT'}), 400
        
        supplier = Supplier(
            name=data['name'],
            contact_person=data.get('contact_person'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            rut=data.get('rut'),
            status=data.get('status', 'active'),
            notes=data.get('notes')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        logger.info(f"Supplier created: {supplier.name}")
        return jsonify(supplier.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating supplier: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """Obtener proveedor específico"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify(supplier.to_dict())
    except Exception as e:
        logger.error(f"Error getting supplier {supplier_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Actualizar proveedor"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        data = request.get_json()
        
        # Verificar RUT único si se cambia
        if data.get('rut') and data['rut'] != supplier.rut:
            existing = Supplier.query.filter_by(rut=data['rut']).first()
            if existing:
                return jsonify({'error': 'Ya existe un proveedor con este RUT'}), 400
        
        # Actualizar campos
        supplier.name = data.get('name', supplier.name)
        supplier.contact_person = data.get('contact_person', supplier.contact_person)
        supplier.email = data.get('email', supplier.email)
        supplier.phone = data.get('phone', supplier.phone)
        supplier.address = data.get('address', supplier.address)
        supplier.rut = data.get('rut', supplier.rut)
        supplier.status = data.get('status', supplier.status)
        supplier.notes = data.get('notes', supplier.notes)
        
        db.session.commit()
        
        logger.info(f"Supplier updated: {supplier.name}")
        return jsonify(supplier.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating supplier {supplier_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suppliers_bp.route('/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """Eliminar proveedor"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        
        # Verificar si tiene ofertas asociadas
        if supplier.bids:
            return jsonify({'error': 'No se puede eliminar un proveedor con ofertas asociadas'}), 400
        
        db.session.delete(supplier)
        db.session.commit()
        
        logger.info(f"Supplier deleted: {supplier.name}")
        return jsonify({'message': 'Proveedor eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting supplier {supplier_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@suppliers_bp.route('/stats', methods=['GET'])
def get_supplier_stats():
    """Obtener estadísticas de proveedores"""
    try:
        total = Supplier.query.count()
        active = Supplier.query.filter_by(status='active').count()
        inactive = Supplier.query.filter_by(status='inactive').count()
        blacklisted = Supplier.query.filter_by(status='blacklisted').count()
        
        return jsonify({
            'total': total,
            'active': active,
            'inactive': inactive,
            'blacklisted': blacklisted
        })
    except Exception as e:
        logger.error(f"Error getting supplier stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

