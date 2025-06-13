from datetime import datetime
from src.models.database import db

class Supplier(db.Model):
    """Modelo para proveedores"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    rut = db.Column(db.String(20), unique=True)
    status = db.Column(db.String(20), default='active')  # active, inactive, blacklisted
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relaciones
    bids = db.relationship('Bid', backref='supplier', lazy=True)
    documents = db.relationship('Document', backref='supplier', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'rut': self.rut,
            'status': self.status,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'notes': self.notes
        }

class Process(db.Model):
    """Modelo para procesos de compra/licitación"""
    __tablename__ = 'processes'
    
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    process_type = db.Column(db.String(50), nullable=False)  # simple_purchase, large_tender
    status = db.Column(db.String(20), default='draft')  # draft, active, evaluation, completed, cancelled
    budget = db.Column(db.Float)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relaciones
    bids = db.relationship('Bid', backref='process', lazy=True)
    documents = db.relationship('Document', backref='process', lazy=True)
    alerts = db.relationship('Alert', backref='process', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_number': self.process_number,
            'title': self.title,
            'description': self.description,
            'process_type': self.process_type,
            'status': self.status,
            'budget': self.budget,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'notes': self.notes
        }

class Bid(db.Model):
    """Modelo para ofertas/propuestas"""
    __tablename__ = 'bids'
    
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    bid_amount = db.Column(db.Float)
    technical_score = db.Column(db.Float)
    commercial_score = db.Column(db.Float)
    total_score = db.Column(db.Float)
    status = db.Column(db.String(20), default='submitted')  # submitted, evaluated, awarded, rejected
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    evaluation_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_id': self.process_id,
            'supplier_id': self.supplier_id,
            'bid_amount': self.bid_amount,
            'technical_score': self.technical_score,
            'commercial_score': self.commercial_score,
            'total_score': self.total_score,
            'status': self.status,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'notes': self.notes,
            'supplier_name': self.supplier.name if self.supplier else None,
            'process_title': self.process.title if self.process else None
        }

class Document(db.Model):
    """Modelo para documentos"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    document_type = db.Column(db.String(50))  # tender_specs, technical_proposal, commercial_proposal, contract
    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'document_type': self.document_type,
            'process_id': self.process_id,
            'supplier_id': self.supplier_id,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'description': self.description,
            'process_title': self.process.title if self.process else None,
            'supplier_name': self.supplier.name if self.supplier else None
        }

class Alert(db.Model):
    """Modelo para alertas del sistema"""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # deadline, missing_document, process_expired
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='active')  # active, dismissed, resolved
    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    resolved_date = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'alert_type': self.alert_type,
            'priority': self.priority,
            'status': self.status,
            'process_id': self.process_id,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'resolved_date': self.resolved_date.isoformat() if self.resolved_date else None,
            'process_title': self.process.title if self.process else None
        }


class EvaluationCriteria(db.Model):
    """Modelo para criterios de evaluación"""
    __tablename__ = 'evaluation_criteria'
    
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    weight = db.Column(db.Float, nullable=False)  # Peso del criterio (0-100)
    criteria_type = db.Column(db.String(50), nullable=False)  # technical, commercial, financial
    max_score = db.Column(db.Float, default=100.0)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    evaluations = db.relationship('BidEvaluation', backref='criteria', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_id': self.process_id,
            'name': self.name,
            'description': self.description,
            'weight': self.weight,
            'criteria_type': self.criteria_type,
            'max_score': self.max_score,
            'created_date': self.created_date.isoformat() if self.created_date else None
        }

class BidEvaluation(db.Model):
    """Modelo para evaluaciones detalladas de ofertas"""
    __tablename__ = 'bid_evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    bid_id = db.Column(db.Integer, db.ForeignKey('bids.id'), nullable=False)
    criteria_id = db.Column(db.Integer, db.ForeignKey('evaluation_criteria.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)  # Puntaje obtenido
    comments = db.Column(db.Text)
    evaluator = db.Column(db.String(100))
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    bid = db.relationship('Bid', backref='evaluations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'bid_id': self.bid_id,
            'criteria_id': self.criteria_id,
            'score': self.score,
            'comments': self.comments,
            'evaluator': self.evaluator,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'criteria_name': self.criteria.name if self.criteria else None,
            'criteria_weight': self.criteria.weight if self.criteria else None,
            'criteria_type': self.criteria.criteria_type if self.criteria else None
        }

class BidRanking(db.Model):
    """Modelo para ranking final de ofertas"""
    __tablename__ = 'bid_rankings'
    
    id = db.Column(db.Integer, primary_key=True)
    process_id = db.Column(db.Integer, db.ForeignKey('processes.id'), nullable=False)
    bid_id = db.Column(db.Integer, db.ForeignKey('bids.id'), nullable=False)
    technical_score = db.Column(db.Float)
    commercial_score = db.Column(db.Float)
    financial_score = db.Column(db.Float)
    weighted_total_score = db.Column(db.Float, nullable=False)
    ranking_position = db.Column(db.Integer, nullable=False)
    recommendation = db.Column(db.String(50))  # award, reject, conditional
    justification = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    bid = db.relationship('Bid', backref='ranking')
    process = db.relationship('Process', backref='rankings')
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_id': self.process_id,
            'bid_id': self.bid_id,
            'technical_score': self.technical_score,
            'commercial_score': self.commercial_score,
            'financial_score': self.financial_score,
            'weighted_total_score': self.weighted_total_score,
            'ranking_position': self.ranking_position,
            'recommendation': self.recommendation,
            'justification': self.justification,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'supplier_name': self.bid.supplier.name if self.bid and self.bid.supplier else None,
            'bid_amount': self.bid.bid_amount if self.bid else None
        }

