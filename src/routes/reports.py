from flask import Blueprint, request, jsonify, send_file
from src.models.database import db
from src.models.models import Process, Supplier, Bid, Document, Alert
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os
import tempfile
import logging

logger = logging.getLogger(__name__)
reports_bp = Blueprint('reports', __name__)

# Configurar matplotlib para usar backend no interactivo
plt.switch_backend('Agg')
sns.set_style("whitegrid")

@reports_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    """Obtener datos para el dashboard principal"""
    try:
        # Contadores principales
        total_processes = Process.query.count()
        total_suppliers = Supplier.query.count()
        total_bids = Bid.query.count()
        active_alerts = Alert.query.filter_by(status='active').count()
        
        # Distribución de procesos por estado
        process_status_data = db.session.query(
            Process.status,
            db.func.count(Process.id).label('count')
        ).group_by(Process.status).all()
        
        # Distribución de procesos por tipo
        process_type_data = db.session.query(
            Process.process_type,
            db.func.count(Process.id).label('count')
        ).group_by(Process.process_type).all()
        
        # Procesos recientes
        recent_processes = Process.query.order_by(
            Process.created_date.desc()
        ).limit(5).all()
        
        # Alertas activas por prioridad
        alert_priority_data = db.session.query(
            Alert.priority,
            db.func.count(Alert.id).label('count')
        ).filter_by(status='active').group_by(Alert.priority).all()
        
        # Tendencias mensuales (últimos 6 meses)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        monthly_trends = db.session.query(
            db.func.strftime('%Y-%m', Process.created_date).label('month'),
            db.func.count(Process.id).label('count')
        ).filter(
            Process.created_date >= six_months_ago
        ).group_by(
            db.func.strftime('%Y-%m', Process.created_date)
        ).order_by('month').all()
        
        # Ahorro estimado (precio referencia vs adjudicado)
        savings_data = db.session.query(
            Process.id,
            Process.title,
            Process.budget,
            db.func.min(Bid.bid_amount).label('lowest_bid')
        ).join(Bid, Process.id == Bid.process_id)\
         .filter(Process.budget.isnot(None), Bid.bid_amount.isnot(None))\
         .group_by(Process.id, Process.title, Process.budget).all()
        
        total_savings = 0
        savings_by_process = []
        for item in savings_data:
            if item.budget and item.lowest_bid:
                saving = item.budget - item.lowest_bid
                savings_percentage = (saving / item.budget) * 100 if item.budget > 0 else 0
                total_savings += saving
                savings_by_process.append({
                    'process_id': item.id,
                    'process_title': item.title,
                    'budget': item.budget,
                    'lowest_bid': item.lowest_bid,
                    'saving': saving,
                    'savings_percentage': savings_percentage
                })
        
        # Top 5 proveedores por número de procesos
        top_suppliers = db.session.query(
            Supplier.id,
            Supplier.name,
            db.func.count(Bid.id).label('bid_count'),
            db.func.count(db.case((Bid.status == 'awarded', 1))).label('awarded_count')
        ).join(Bid, Supplier.id == Bid.supplier_id)\
         .group_by(Supplier.id, Supplier.name)\
         .order_by(db.func.count(Bid.id).desc())\
         .limit(5).all()
        
        return jsonify({
            'counters': {
                'total_processes': total_processes,
                'total_suppliers': total_suppliers,
                'total_bids': total_bids,
                'active_alerts': active_alerts,
                'total_savings': total_savings
            },
            'process_status_distribution': [
                {'status': item.status, 'count': item.count}
                for item in process_status_data
            ],
            'process_type_distribution': [
                {'type': item.process_type, 'count': item.count}
                for item in process_type_data
            ],
            'recent_processes': [process.to_dict() for process in recent_processes],
            'alert_priority_distribution': [
                {'priority': item.priority, 'count': item.count}
                for item in alert_priority_data
            ],
            'monthly_trends': [
                {'month': item.month, 'count': item.count}
                for item in monthly_trends
            ],
            'savings_data': {
                'total_savings': total_savings,
                'savings_by_process': savings_by_process
            },
            'top_suppliers': [
                {
                    'supplier_id': item.id,
                    'supplier_name': item.name,
                    'bid_count': item.bid_count,
                    'awarded_count': item.awarded_count,
                    'success_rate': (item.awarded_count / item.bid_count * 100) if item.bid_count > 0 else 0
                }
                for item in top_suppliers
            ]
        })
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/process/<int:process_id>/analysis', methods=['GET'])
def get_process_analysis(process_id):
    """Obtener análisis detallado de un proceso"""
    try:
        process = Process.query.get_or_404(process_id)
        bids = Bid.query.filter_by(process_id=process_id).all()
        
        if not bids:
            return jsonify({
                'process': process.to_dict(),
                'analysis': {
                    'message': 'No hay ofertas para analizar'
                }
            })
        
        # Análisis de ofertas
        bid_amounts = [bid.bid_amount for bid in bids if bid.bid_amount]
        technical_scores = [bid.technical_score for bid in bids if bid.technical_score]
        commercial_scores = [bid.commercial_score for bid in bids if bid.commercial_score]
        
        analysis = {
            'total_bids': len(bids),
            'financial_analysis': {},
            'technical_analysis': {},
            'commercial_analysis': {}
        }
        
        if bid_amounts:
            analysis['financial_analysis'] = {
                'average_amount': sum(bid_amounts) / len(bid_amounts),
                'lowest_bid': min(bid_amounts),
                'highest_bid': max(bid_amounts),
                'savings_vs_budget': process.budget - min(bid_amounts) if process.budget else None,
                'savings_percentage': ((process.budget - min(bid_amounts)) / process.budget * 100) if process.budget else None
            }
        
        if technical_scores:
            analysis['technical_analysis'] = {
                'average_score': sum(technical_scores) / len(technical_scores),
                'highest_score': max(technical_scores),
                'lowest_score': min(technical_scores)
            }
        
        if commercial_scores:
            analysis['commercial_analysis'] = {
                'average_score': sum(commercial_scores) / len(commercial_scores),
                'highest_score': max(commercial_scores),
                'lowest_score': min(commercial_scores)
            }
        
        return jsonify({
            'process': process.to_dict(),
            'bids': [bid.to_dict() for bid in bids],
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Error getting process analysis {process_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/supplier/<int:supplier_id>/performance', methods=['GET'])
def get_supplier_performance(supplier_id):
    """Obtener análisis de rendimiento de un proveedor"""
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        bids = Bid.query.filter_by(supplier_id=supplier_id).all()
        
        if not bids:
            return jsonify({
                'supplier': supplier.to_dict(),
                'performance': {
                    'message': 'No hay ofertas para analizar'
                }
            })
        
        # Análisis de rendimiento
        total_bids = len(bids)
        awarded_bids = len([bid for bid in bids if bid.status == 'awarded'])
        rejected_bids = len([bid for bid in bids if bid.status == 'rejected'])
        
        technical_scores = [bid.technical_score for bid in bids if bid.technical_score]
        commercial_scores = [bid.commercial_score for bid in bids if bid.commercial_score]
        bid_amounts = [bid.bid_amount for bid in bids if bid.bid_amount]
        
        performance = {
            'participation_stats': {
                'total_bids': total_bids,
                'awarded_bids': awarded_bids,
                'rejected_bids': rejected_bids,
                'success_rate': (awarded_bids / total_bids * 100) if total_bids > 0 else 0
            },
            'scoring_stats': {},
            'financial_stats': {}
        }
        
        if technical_scores:
            performance['scoring_stats']['technical'] = {
                'average': sum(technical_scores) / len(technical_scores),
                'best': max(technical_scores),
                'worst': min(technical_scores)
            }
        
        if commercial_scores:
            performance['scoring_stats']['commercial'] = {
                'average': sum(commercial_scores) / len(commercial_scores),
                'best': max(commercial_scores),
                'worst': min(commercial_scores)
            }
        
        if bid_amounts:
            performance['financial_stats'] = {
                'average_bid': sum(bid_amounts) / len(bid_amounts),
                'lowest_bid': min(bid_amounts),
                'highest_bid': max(bid_amounts)
            }
        
        return jsonify({
            'supplier': supplier.to_dict(),
            'bids': [bid.to_dict() for bid in bids],
            'performance': performance
        })
    except Exception as e:
        logger.error(f"Error getting supplier performance {supplier_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/export/suppliers', methods=['GET'])
def export_suppliers():
    """Exportar lista de proveedores a Excel"""
    try:
        suppliers = Supplier.query.all()
        
        # Crear DataFrame
        data = []
        for supplier in suppliers:
            data.append({
                'ID': supplier.id,
                'Nombre': supplier.name,
                'Persona de Contacto': supplier.contact_person,
                'Email': supplier.email,
                'Teléfono': supplier.phone,
                'Dirección': supplier.address,
                'RUT': supplier.rut,
                'Estado': supplier.status,
                'Fecha de Registro': supplier.registration_date.strftime('%d/%m/%Y') if supplier.registration_date else '',
                'Notas': supplier.notes
            })
        
        df = pd.DataFrame(data)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False, sheet_name='Proveedores')
            tmp_path = tmp.name
        
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=f'proveedores_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting suppliers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/export/processes', methods=['GET'])
def export_processes():
    """Exportar lista de procesos a Excel"""
    try:
        processes = Process.query.all()
        
        # Crear DataFrame
        data = []
        for process in processes:
            data.append({
                'ID': process.id,
                'Número de Proceso': process.process_number,
                'Título': process.title,
                'Descripción': process.description,
                'Tipo': process.process_type,
                'Estado': process.status,
                'Presupuesto': process.budget,
                'Fecha de Inicio': process.start_date.strftime('%d/%m/%Y') if process.start_date else '',
                'Fecha de Fin': process.end_date.strftime('%d/%m/%Y') if process.end_date else '',
                'Fecha de Creación': process.created_date.strftime('%d/%m/%Y') if process.created_date else '',
                'Notas': process.notes
            })
        
        df = pd.DataFrame(data)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            df.to_excel(tmp.name, index=False, sheet_name='Procesos')
            tmp_path = tmp.name
        
        return send_file(
            tmp_path,
            as_attachment=True,
            download_name=f'procesos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"Error exporting processes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/chart/process-trends', methods=['GET'])
def get_process_trends_chart():
    """Generar gráfico de tendencias de procesos"""
    try:
        # Obtener datos de los últimos 12 meses
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        monthly_data = db.session.query(
            db.func.strftime('%Y-%m', Process.created_date).label('month'),
            db.func.count(Process.id).label('count')
        ).filter(
            Process.created_date >= twelve_months_ago
        ).group_by(
            db.func.strftime('%Y-%m', Process.created_date)
        ).order_by('month').all()
        
        if not monthly_data:
            return jsonify({'error': 'No hay datos suficientes para generar el gráfico'}), 400
        
        # Crear gráfico
        months = [item.month for item in monthly_data]
        counts = [item.count for item in monthly_data]
        
        plt.figure(figsize=(12, 6))
        plt.plot(months, counts, marker='o', linewidth=2, markersize=6)
        plt.title('Tendencia de Procesos Creados por Mes', fontsize=16, fontweight='bold')
        plt.xlabel('Mes', fontsize=12)
        plt.ylabel('Número de Procesos', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Convertir a base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return jsonify({
            'chart_data': f'data:image/png;base64,{img_base64}',
            'data': [{'month': item.month, 'count': item.count} for item in monthly_data]
        })
    except Exception as e:
        logger.error(f"Error generating process trends chart: {str(e)}")
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/chart/bid-comparison/<int:process_id>', methods=['GET'])
def get_bid_comparison_chart(process_id):
    """Generar gráfico de comparación de ofertas"""
    try:
        process = Process.query.get_or_404(process_id)
        bids = Bid.query.filter_by(process_id=process_id).all()
        
        if not bids:
            return jsonify({'error': 'No hay ofertas para comparar'}), 400
        
        # Filtrar ofertas con montos válidos
        valid_bids = [bid for bid in bids if bid.bid_amount and bid.supplier]
        
        if not valid_bids:
            return jsonify({'error': 'No hay ofertas con montos válidos'}), 400
        
        # Crear gráfico
        suppliers = [bid.supplier.name for bid in valid_bids]
        amounts = [bid.bid_amount for bid in valid_bids]
        
        plt.figure(figsize=(12, 8))
        bars = plt.bar(suppliers, amounts, color='skyblue', edgecolor='navy', alpha=0.7)
        
        # Agregar valores en las barras
        for bar, amount in zip(bars, amounts):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(amounts)*0.01,
                    f'${amount:,.0f}', ha='center', va='bottom', fontweight='bold')
        
        plt.title(f'Comparación de Ofertas - {process.title}', fontsize=16, fontweight='bold')
        plt.xlabel('Proveedores', fontsize=12)
        plt.ylabel('Monto de Oferta', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        # Convertir a base64
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return jsonify({
            'chart_data': f'data:image/png;base64,{img_base64}',
            'process': process.to_dict(),
            'bids_data': [
                {'supplier': bid.supplier.name, 'amount': bid.bid_amount}
                for bid in valid_bids
            ]
        })
    except Exception as e:
        logger.error(f"Error generating bid comparison chart: {str(e)}")
        return jsonify({'error': str(e)}), 500

