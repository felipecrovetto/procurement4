import os
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from src.models.database import db
from src.models.models import Document, Process, Supplier
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
documents_bp = Blueprint('documents', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@documents_bp.route('/', methods=['GET'])
def get_documents():
    """Obtener lista de documentos"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        process_id = request.args.get('process_id', type=int)
        supplier_id = request.args.get('supplier_id', type=int)
        document_type = request.args.get('document_type', '')
        
        query = Document.query
        
        if process_id:
            query = query.filter(Document.process_id == process_id)
        
        if supplier_id:
            query = query.filter(Document.supplier_id == supplier_id)
        
        if document_type:
            query = query.filter(Document.document_type == document_type)
        
        # Ordenar por fecha de subida descendente
        query = query.order_by(Document.upload_date.desc())
        
        documents = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents.items],
            'total': documents.total,
            'pages': documents.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/upload', methods=['POST'])
def upload_document():
    """Subir nuevo documento"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró archivo en la solicitud'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido'}), 400
        
        # Obtener datos del formulario
        process_id = request.form.get('process_id', type=int)
        supplier_id = request.form.get('supplier_id', type=int)
        document_type = request.form.get('document_type', '')
        description = request.form.get('description', '')
        
        # Validar que al menos uno de process_id o supplier_id esté presente
        if not process_id and not supplier_id:
            return jsonify({'error': 'Debe especificar un proceso o proveedor'}), 400
        
        # Verificar que el proceso existe si se especifica
        if process_id:
            process = Process.query.get(process_id)
            if not process:
                return jsonify({'error': 'El proceso especificado no existe'}), 404
        
        # Verificar que el proveedor existe si se especifica
        if supplier_id:
            supplier = Supplier.query.get(supplier_id)
            if not supplier:
                return jsonify({'error': 'El proveedor especificado no existe'}), 404
        
        # Generar nombre de archivo seguro
        original_filename = file.filename
        filename = secure_filename(original_filename)
        
        # Agregar timestamp para evitar conflictos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        # Crear directorio si no existe
        upload_folder = request.current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        # Guardar archivo
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Obtener información del archivo
        file_size = os.path.getsize(file_path)
        file_type = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        
        # Crear registro en base de datos
        document = Document(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            document_type=document_type,
            process_id=process_id,
            supplier_id=supplier_id,
            description=description
        )
        
        db.session.add(document)
        db.session.commit()
        
        logger.info(f"Document uploaded: {original_filename}")
        return jsonify(document.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<int:document_id>', methods=['GET'])
def get_document(document_id):
    """Obtener información de documento específico"""
    try:
        document = Document.query.get_or_404(document_id)
        return jsonify(document.to_dict())
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<int:document_id>/download', methods=['GET'])
def download_document(document_id):
    """Descargar documento"""
    try:
        document = Document.query.get_or_404(document_id)
        
        if not os.path.exists(document.file_path):
            return jsonify({'error': 'Archivo no encontrado en el sistema'}), 404
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.original_filename
        )
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<int:document_id>', methods=['PUT'])
def update_document(document_id):
    """Actualizar información de documento"""
    try:
        document = Document.query.get_or_404(document_id)
        data = request.get_json()
        
        # Actualizar campos editables
        document.document_type = data.get('document_type', document.document_type)
        document.description = data.get('description', document.description)
        
        # Actualizar asociaciones si se proporcionan
        if 'process_id' in data:
            if data['process_id']:
                process = Process.query.get(data['process_id'])
                if not process:
                    return jsonify({'error': 'El proceso especificado no existe'}), 404
            document.process_id = data['process_id']
        
        if 'supplier_id' in data:
            if data['supplier_id']:
                supplier = Supplier.query.get(data['supplier_id'])
                if not supplier:
                    return jsonify({'error': 'El proveedor especificado no existe'}), 404
            document.supplier_id = data['supplier_id']
        
        db.session.commit()
        
        logger.info(f"Document updated: {document_id}")
        return jsonify(document.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating document {document_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Eliminar documento"""
    try:
        document = Document.query.get_or_404(document_id)
        
        # Eliminar archivo físico
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Eliminar registro de base de datos
        db.session.delete(document)
        db.session.commit()
        
        logger.info(f"Document deleted: {document_id}")
        return jsonify({'message': 'Documento eliminado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@documents_bp.route('/stats', methods=['GET'])
def get_document_stats():
    """Obtener estadísticas de documentos"""
    try:
        total = Document.query.count()
        
        # Estadísticas por tipo
        tender_specs = Document.query.filter_by(document_type='tender_specs').count()
        technical_proposal = Document.query.filter_by(document_type='technical_proposal').count()
        commercial_proposal = Document.query.filter_by(document_type='commercial_proposal').count()
        contract = Document.query.filter_by(document_type='contract').count()
        other = total - (tender_specs + technical_proposal + commercial_proposal + contract)
        
        # Tamaño total de archivos
        total_size = db.session.query(db.func.sum(Document.file_size)).scalar() or 0
        
        return jsonify({
            'total': total,
            'by_type': {
                'tender_specs': tender_specs,
                'technical_proposal': technical_proposal,
                'commercial_proposal': commercial_proposal,
                'contract': contract,
                'other': other
            },
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        })
    except Exception as e:
        logger.error(f"Error getting document stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

