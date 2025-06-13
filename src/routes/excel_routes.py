import os
import pandas as pd
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from src.models.database import db
from src.models.excel_models import *
from datetime import datetime
import tempfile
import logging

logger = logging.getLogger(__name__)
excel_bp = Blueprint('excel', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_excel_structure(df, table_type):
    """Validar estructura de tabla Excel según el tipo"""
    errors = []
    warnings = []
    
    if table_type == 'process_tracking':
        required_columns = ['Número de Proceso', 'Nombre del Proceso', 'Tipo', 'Estado', 'Presupuesto']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Columna requerida faltante: {col}")
    
    elif table_type == 'technical_evaluation':
        required_columns = ['Número de Proceso', 'Proveedor', 'Criterio', 'Peso (%)', 'Puntuación']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Columna requerida faltante: {col}")
        
        # Validar que los pesos sumen 100%
        if 'Peso (%)' in df.columns:
            total_weight = df['Peso (%)'].sum()
            if abs(total_weight - 100) > 0.1:
                warnings.append(f"Los pesos no suman 100% (suma actual: {total_weight}%)")
    
    elif table_type == 'commercial_comparison':
        required_columns = ['Número de Proceso', 'Descripción del Ítem', 'Proveedor', 'Precio Unitario', 'Precio Total']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Columna requerida faltante: {col}")
    
    elif table_type == 'supplier_evaluation':
        required_columns = ['Proveedor', 'Categoría', 'Criterio', 'Puntuación']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Columna requerida faltante: {col}")
    
    elif table_type == 'savings_analysis':
        required_columns = ['Número de Proceso', 'Categoría', 'Presupuesto Inicial', 'Precio Final']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Columna requerida faltante: {col}")
    
    elif table_type == 'questions_answers':
        required_columns = ['Número de Proceso', 'Pregunta', 'Respuesta']
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Columna requerida faltante: {col}")
    
    return errors, warnings

@excel_bp.route('/upload', methods=['POST'])
def upload_excel():
    """Subir y procesar archivo Excel"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se encontró archivo en la solicitud'}), 400
        
        file = request.files['file']
        table_type = request.form.get('table_type')
        
        if file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de archivo no permitido. Solo se permiten archivos Excel (.xlsx, .xls)'}), 400
        
        if not table_type:
            return jsonify({'error': 'Debe especificar el tipo de tabla'}), 400
        
        # Leer archivo Excel
        try:
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'Error leyendo archivo Excel: {str(e)}'}), 400
        
        # Validar estructura
        errors, warnings = validate_excel_structure(df, table_type)
        
        if errors:
            return jsonify({
                'error': 'Errores de validación encontrados',
                'validation_errors': errors,
                'validation_warnings': warnings
            }), 400
        
        # Procesar datos según el tipo de tabla
        records_created = 0
        
        if table_type == 'process_tracking':
            records_created = process_tracking_data(df)
        elif table_type == 'technical_evaluation':
            records_created = process_technical_evaluation_data(df)
        elif table_type == 'commercial_comparison':
            records_created = process_commercial_comparison_data(df)
        elif table_type == 'supplier_evaluation':
            records_created = process_supplier_evaluation_data(df)
        elif table_type == 'savings_analysis':
            records_created = process_savings_analysis_data(df)
        elif table_type == 'questions_answers':
            records_created = process_questions_answers_data(df)
        else:
            return jsonify({'error': 'Tipo de tabla no soportado'}), 400
        
        return jsonify({
            'message': f'Archivo procesado exitosamente. {records_created} registros creados.',
            'records_created': records_created,
            'validation_warnings': warnings,
            'table_type': table_type
        }), 201
        
    except Exception as e:
        logger.error(f"Error uploading Excel file: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_tracking_data(df):
    """Procesar datos de seguimiento de procesos"""
    records_created = 0
    
    for _, row in df.iterrows():
        try:
            # Parsear fechas
            start_date = None
            end_date = None
            
            if pd.notna(row.get('Fecha de Inicio')):
                start_date = pd.to_datetime(row['Fecha de Inicio'])
            
            if pd.notna(row.get('Fecha de Fin')):
                end_date = pd.to_datetime(row['Fecha de Fin'])
            
            record = ExcelProcessTracking(
                process_number=str(row['Número de Proceso']),
                process_name=str(row['Nombre del Proceso']),
                process_type=str(row.get('Tipo', '')),
                status=str(row.get('Estado', '')),
                budget=float(row['Presupuesto']) if pd.notna(row.get('Presupuesto')) else None,
                start_date=start_date,
                end_date=end_date,
                responsible=str(row.get('Responsable', '')),
                notes=str(row.get('Notas', ''))
            )
            
            db.session.add(record)
            records_created += 1
            
        except Exception as e:
            logger.warning(f"Error processing row: {str(e)}")
            continue
    
    db.session.commit()
    return records_created

def process_technical_evaluation_data(df):
    """Procesar datos de evaluación técnica"""
    records_created = 0
    
    for _, row in df.iterrows():
        try:
            weight = float(row['Peso (%)']) if pd.notna(row.get('Peso (%)')) else 0
            score = float(row['Puntuación']) if pd.notna(row.get('Puntuación')) else 0
            weighted_score = (weight * score) / 100
            
            record = ExcelTechnicalEvaluation(
                process_number=str(row['Número de Proceso']),
                supplier_name=str(row['Proveedor']),
                criterion=str(row['Criterio']),
                weight=weight,
                score=score,
                weighted_score=weighted_score,
                comments=str(row.get('Comentarios', ''))
            )
            
            db.session.add(record)
            records_created += 1
            
        except Exception as e:
            logger.warning(f"Error processing row: {str(e)}")
            continue
    
    db.session.commit()
    return records_created

def process_commercial_comparison_data(df):
    """Procesar datos de comparación comercial"""
    records_created = 0
    
    for _, row in df.iterrows():
        try:
            record = ExcelCommercialComparison(
                process_number=str(row['Número de Proceso']),
                item_description=str(row['Descripción del Ítem']),
                quantity=float(row.get('Cantidad', 0)) if pd.notna(row.get('Cantidad')) else None,
                unit=str(row.get('Unidad', '')),
                supplier_name=str(row['Proveedor']),
                unit_price=float(row['Precio Unitario']) if pd.notna(row.get('Precio Unitario')) else 0,
                total_price=float(row['Precio Total']) if pd.notna(row.get('Precio Total')) else 0,
                delivery_time=str(row.get('Tiempo de Entrega', '')),
                warranty=str(row.get('Garantía', ''))
            )
            
            db.session.add(record)
            records_created += 1
            
        except Exception as e:
            logger.warning(f"Error processing row: {str(e)}")
            continue
    
    db.session.commit()
    return records_created

def process_supplier_evaluation_data(df):
    """Procesar datos de evaluación de proveedores"""
    records_created = 0
    
    for _, row in df.iterrows():
        try:
            score = float(row['Puntuación']) if pd.notna(row.get('Puntuación')) else 0
            max_score = float(row.get('Puntuación Máxima', 5))
            percentage = (score / max_score * 100) if max_score > 0 else 0
            
            evaluation_date = None
            if pd.notna(row.get('Fecha de Evaluación')):
                evaluation_date = pd.to_datetime(row['Fecha de Evaluación'])
            
            record = ExcelSupplierEvaluation(
                supplier_name=str(row['Proveedor']),
                evaluation_category=str(row.get('Categoría', '')),
                criterion=str(row['Criterio']),
                score=score,
                max_score=max_score,
                percentage=percentage,
                comments=str(row.get('Comentarios', '')),
                evaluation_date=evaluation_date
            )
            
            db.session.add(record)
            records_created += 1
            
        except Exception as e:
            logger.warning(f"Error processing row: {str(e)}")
            continue
    
    db.session.commit()
    return records_created

def process_savings_analysis_data(df):
    """Procesar datos de análisis de ahorros"""
    records_created = 0
    
    for _, row in df.iterrows():
        try:
            initial_budget = float(row['Presupuesto Inicial']) if pd.notna(row.get('Presupuesto Inicial')) else 0
            final_price = float(row['Precio Final']) if pd.notna(row.get('Precio Final')) else 0
            savings_amount = initial_budget - final_price
            savings_percentage = (savings_amount / initial_budget * 100) if initial_budget > 0 else 0
            
            record = ExcelSavingsAnalysis(
                process_number=str(row['Número de Proceso']),
                category=str(row.get('Categoría', '')),
                initial_budget=initial_budget,
                final_price=final_price,
                savings_amount=savings_amount,
                savings_percentage=savings_percentage,
                value_added=str(row.get('Valor Agregado', ''))
            )
            
            db.session.add(record)
            records_created += 1
            
        except Exception as e:
            logger.warning(f"Error processing row: {str(e)}")
            continue
    
    db.session.commit()
    return records_created

def process_questions_answers_data(df):
    """Procesar datos de consultas y respuestas"""
    records_created = 0
    
    for _, row in df.iterrows():
        try:
            question_date = None
            answer_date = None
            
            if pd.notna(row.get('Fecha de Pregunta')):
                question_date = pd.to_datetime(row['Fecha de Pregunta'])
            
            if pd.notna(row.get('Fecha de Respuesta')):
                answer_date = pd.to_datetime(row['Fecha de Respuesta'])
            
            status = 'answered' if pd.notna(row.get('Respuesta')) and str(row['Respuesta']).strip() else 'pending'
            
            record = ExcelQuestionsAnswers(
                process_number=str(row['Número de Proceso']),
                question_number=int(row.get('Número de Pregunta', 0)) if pd.notna(row.get('Número de Pregunta')) else None,
                question_date=question_date,
                supplier_name=str(row.get('Proveedor', '')),
                question=str(row['Pregunta']),
                answer=str(row.get('Respuesta', '')),
                answer_date=answer_date,
                status=status
            )
            
            db.session.add(record)
            records_created += 1
            
        except Exception as e:
            logger.warning(f"Error processing row: {str(e)}")
            continue
    
    db.session.commit()
    return records_created

@excel_bp.route('/templates/<table_type>', methods=['GET'])
def download_template(table_type):
    """Descargar plantilla Excel para un tipo de tabla específico"""
    try:
        templates = {
            'process_tracking': {
                'filename': 'plantilla_seguimiento_procesos.xlsx',
                'columns': [
                    'Número de Proceso', 'Nombre del Proceso', 'Tipo', 'Estado',
                    'Presupuesto', 'Fecha de Inicio', 'Fecha de Fin', 'Responsable', 'Notas'
                ]
            },
            'technical_evaluation': {
                'filename': 'plantilla_evaluacion_tecnica.xlsx',
                'columns': [
                    'Número de Proceso', 'Proveedor', 'Criterio', 'Peso (%)',
                    'Puntuación', 'Comentarios'
                ]
            },
            'commercial_comparison': {
                'filename': 'plantilla_comparacion_comercial.xlsx',
                'columns': [
                    'Número de Proceso', 'Descripción del Ítem', 'Cantidad', 'Unidad',
                    'Proveedor', 'Precio Unitario', 'Precio Total', 'Tiempo de Entrega', 'Garantía'
                ]
            },
            'supplier_evaluation': {
                'filename': 'plantilla_evaluacion_proveedores.xlsx',
                'columns': [
                    'Proveedor', 'Categoría', 'Criterio', 'Puntuación',
                    'Puntuación Máxima', 'Comentarios', 'Fecha de Evaluación'
                ]
            },
            'savings_analysis': {
                'filename': 'plantilla_analisis_ahorros.xlsx',
                'columns': [
                    'Número de Proceso', 'Categoría', 'Presupuesto Inicial',
                    'Precio Final', 'Valor Agregado'
                ]
            },
            'questions_answers': {
                'filename': 'plantilla_consultas_respuestas.xlsx',
                'columns': [
                    'Número de Proceso', 'Número de Pregunta', 'Fecha de Pregunta',
                    'Proveedor', 'Pregunta', 'Respuesta', 'Fecha de Respuesta'
                ]
            }
        }
        
        if table_type not in templates:
            return jsonify({'error': 'Tipo de plantilla no soportado'}), 400
        
        template_info = templates[table_type]
        
        # Crear DataFrame vacío con las columnas
        df = pd.DataFrame(columns=template_info['columns'])
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False, sheet_name='Datos')
            tmp_path = tmp.name
        
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=template_info['filename'],
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error downloading template {table_type}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@excel_bp.route('/data/<table_type>', methods=['GET'])
def get_excel_data(table_type):
    """Obtener datos de Excel procesados"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        model_map = {
            'process_tracking': ExcelProcessTracking,
            'technical_evaluation': ExcelTechnicalEvaluation,
            'commercial_comparison': ExcelCommercialComparison,
            'supplier_evaluation': ExcelSupplierEvaluation,
            'savings_analysis': ExcelSavingsAnalysis,
            'questions_answers': ExcelQuestionsAnswers
        }
        
        if table_type not in model_map:
            return jsonify({'error': 'Tipo de tabla no soportado'}), 400
        
        model = model_map[table_type]
        
        query = model.query.order_by(model.upload_date.desc())
        
        data = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'data': [item.to_dict() for item in data.items],
            'total': data.total,
            'pages': data.pages,
            'current_page': page,
            'table_type': table_type
        })
        
    except Exception as e:
        logger.error(f"Error getting Excel data {table_type}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@excel_bp.route('/analysis/<table_type>', methods=['GET'])
def get_excel_analysis(table_type):
    """Obtener análisis de datos de Excel"""
    try:
        if table_type == 'technical_evaluation':
            return get_technical_evaluation_analysis()
        elif table_type == 'commercial_comparison':
            return get_commercial_comparison_analysis()
        elif table_type == 'supplier_evaluation':
            return get_supplier_evaluation_analysis()
        elif table_type == 'savings_analysis':
            return get_savings_analysis_analysis()
        else:
            return jsonify({'error': 'Análisis no disponible para este tipo de tabla'}), 400
            
    except Exception as e:
        logger.error(f"Error getting Excel analysis {table_type}: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_technical_evaluation_analysis():
    """Análisis de evaluación técnica"""
    # Obtener datos agrupados por proveedor
    supplier_scores = db.session.query(
        ExcelTechnicalEvaluation.supplier_name,
        db.func.sum(ExcelTechnicalEvaluation.weighted_score).label('total_score')
    ).group_by(ExcelTechnicalEvaluation.supplier_name).all()
    
    # Obtener criterios más importantes
    top_criteria = db.session.query(
        ExcelTechnicalEvaluation.criterion,
        db.func.avg(ExcelTechnicalEvaluation.weight).label('avg_weight')
    ).group_by(ExcelTechnicalEvaluation.criterion).order_by(
        db.func.avg(ExcelTechnicalEvaluation.weight).desc()
    ).limit(5).all()
    
    return jsonify({
        'supplier_scores': [
            {'supplier': item.supplier_name, 'total_score': float(item.total_score)}
            for item in supplier_scores
        ],
        'top_criteria': [
            {'criterion': item.criterion, 'avg_weight': float(item.avg_weight)}
            for item in top_criteria
        ]
    })

def get_commercial_comparison_analysis():
    """Análisis de comparación comercial"""
    # Obtener mejores ofertas por ítem
    best_offers = db.session.query(
        ExcelCommercialComparison.item_description,
        db.func.min(ExcelCommercialComparison.unit_price).label('best_price'),
        ExcelCommercialComparison.supplier_name
    ).group_by(ExcelCommercialComparison.item_description).all()
    
    # Obtener estadísticas por proveedor
    supplier_stats = db.session.query(
        ExcelCommercialComparison.supplier_name,
        db.func.avg(ExcelCommercialComparison.unit_price).label('avg_price'),
        db.func.count(ExcelCommercialComparison.id).label('item_count')
    ).group_by(ExcelCommercialComparison.supplier_name).all()
    
    return jsonify({
        'best_offers': [
            {
                'item': item.item_description,
                'best_price': float(item.best_price),
                'supplier': item.supplier_name
            }
            for item in best_offers
        ],
        'supplier_stats': [
            {
                'supplier': item.supplier_name,
                'avg_price': float(item.avg_price),
                'item_count': item.item_count
            }
            for item in supplier_stats
        ]
    })

def get_supplier_evaluation_analysis():
    """Análisis de evaluación de proveedores"""
    # Obtener ranking de proveedores
    supplier_ranking = db.session.query(
        ExcelSupplierEvaluation.supplier_name,
        db.func.avg(ExcelSupplierEvaluation.percentage).label('avg_percentage')
    ).group_by(ExcelSupplierEvaluation.supplier_name).order_by(
        db.func.avg(ExcelSupplierEvaluation.percentage).desc()
    ).all()
    
    # Obtener análisis por categoría
    category_analysis = db.session.query(
        ExcelSupplierEvaluation.evaluation_category,
        db.func.avg(ExcelSupplierEvaluation.percentage).label('avg_percentage'),
        db.func.count(ExcelSupplierEvaluation.id).label('evaluation_count')
    ).group_by(ExcelSupplierEvaluation.evaluation_category).all()
    
    return jsonify({
        'supplier_ranking': [
            {'supplier': item.supplier_name, 'avg_percentage': float(item.avg_percentage)}
            for item in supplier_ranking
        ],
        'category_analysis': [
            {
                'category': item.evaluation_category,
                'avg_percentage': float(item.avg_percentage),
                'evaluation_count': item.evaluation_count
            }
            for item in category_analysis
        ]
    })

def get_savings_analysis_analysis():
    """Análisis de ahorros"""
    # Obtener ahorros totales
    total_savings = db.session.query(
        db.func.sum(ExcelSavingsAnalysis.savings_amount).label('total_savings'),
        db.func.avg(ExcelSavingsAnalysis.savings_percentage).label('avg_percentage')
    ).first()
    
    # Obtener ahorros por categoría
    category_savings = db.session.query(
        ExcelSavingsAnalysis.category,
        db.func.sum(ExcelSavingsAnalysis.savings_amount).label('category_savings'),
        db.func.avg(ExcelSavingsAnalysis.savings_percentage).label('avg_percentage')
    ).group_by(ExcelSavingsAnalysis.category).all()
    
    return jsonify({
        'total_savings': {
            'amount': float(total_savings.total_savings) if total_savings.total_savings else 0,
            'avg_percentage': float(total_savings.avg_percentage) if total_savings.avg_percentage else 0
        },
        'category_savings': [
            {
                'category': item.category,
                'savings_amount': float(item.category_savings),
                'avg_percentage': float(item.avg_percentage)
            }
            for item in category_savings
        ]
    })

