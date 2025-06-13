from datetime import datetime
from src.models.database import db

class ExcelProcessTracking(db.Model):
    """Modelo para seguimiento de procesos desde Excel"""
    __tablename__ = 'excel_process_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), nullable=False)
    process_name = db.Column(db.String(200), nullable=False)
    process_type = db.Column(db.String(50))
    status = db.Column(db.String(50))
    budget = db.Column(db.Float)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    responsible = db.Column(db.String(100))
    notes = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_number': self.process_number,
            'process_name': self.process_name,
            'process_type': self.process_type,
            'status': self.status,
            'budget': self.budget,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'responsible': self.responsible,
            'notes': self.notes,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

class ExcelTechnicalEvaluation(db.Model):
    """Modelo para evaluación técnica desde Excel"""
    __tablename__ = 'excel_technical_evaluation'
    
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), nullable=False)
    supplier_name = db.Column(db.String(200), nullable=False)
    criterion = db.Column(db.String(200), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    score = db.Column(db.Float, nullable=False)
    weighted_score = db.Column(db.Float)
    comments = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_number': self.process_number,
            'supplier_name': self.supplier_name,
            'criterion': self.criterion,
            'weight': self.weight,
            'score': self.score,
            'weighted_score': self.weighted_score,
            'comments': self.comments,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

class ExcelCommercialComparison(db.Model):
    """Modelo para comparación comercial desde Excel"""
    __tablename__ = 'excel_commercial_comparison'
    
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), nullable=False)
    item_description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float)
    unit = db.Column(db.String(50))
    supplier_name = db.Column(db.String(200), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    delivery_time = db.Column(db.String(100))
    warranty = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_number': self.process_number,
            'item_description': self.item_description,
            'quantity': self.quantity,
            'unit': self.unit,
            'supplier_name': self.supplier_name,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'delivery_time': self.delivery_time,
            'warranty': self.warranty,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

class ExcelSupplierEvaluation(db.Model):
    """Modelo para evaluación de proveedores desde Excel"""
    __tablename__ = 'excel_supplier_evaluation'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(200), nullable=False)
    evaluation_category = db.Column(db.String(100), nullable=False)
    criterion = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, default=5.0)
    percentage = db.Column(db.Float)
    comments = db.Column(db.Text)
    evaluation_date = db.Column(db.DateTime)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'supplier_name': self.supplier_name,
            'evaluation_category': self.evaluation_category,
            'criterion': self.criterion,
            'score': self.score,
            'max_score': self.max_score,
            'percentage': self.percentage,
            'comments': self.comments,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

class ExcelSavingsAnalysis(db.Model):
    """Modelo para análisis de ahorros desde Excel"""
    __tablename__ = 'excel_savings_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    initial_budget = db.Column(db.Float, nullable=False)
    final_price = db.Column(db.Float, nullable=False)
    savings_amount = db.Column(db.Float, nullable=False)
    savings_percentage = db.Column(db.Float, nullable=False)
    value_added = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_number': self.process_number,
            'category': self.category,
            'initial_budget': self.initial_budget,
            'final_price': self.final_price,
            'savings_amount': self.savings_amount,
            'savings_percentage': self.savings_percentage,
            'value_added': self.value_added,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

class ExcelQuestionsAnswers(db.Model):
    """Modelo para consultas y respuestas desde Excel"""
    __tablename__ = 'excel_questions_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    process_number = db.Column(db.String(50), nullable=False)
    question_number = db.Column(db.Integer)
    question_date = db.Column(db.DateTime)
    supplier_name = db.Column(db.String(200))
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    answer_date = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='pending')  # pending, answered, closed
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'process_number': self.process_number,
            'question_number': self.question_number,
            'question_date': self.question_date.isoformat() if self.question_date else None,
            'supplier_name': self.supplier_name,
            'question': self.question,
            'answer': self.answer,
            'answer_date': self.answer_date.isoformat() if self.answer_date else None,
            'status': self.status,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None
        }

