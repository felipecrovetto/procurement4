from flask import Blueprint, request, jsonify
from src.models.database import db
from src.models.models import Process, Bid, EvaluationCriteria, BidEvaluation, BidRanking, Supplier
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
evaluation_bp = Blueprint('evaluation', __name__)

@evaluation_bp.route('/criteria/<int:process_id>', methods=['GET'])
def get_evaluation_criteria(process_id):
    """Obtener criterios de evaluación para un proceso"""
    try:
        criteria = EvaluationCriteria.query.filter_by(process_id=process_id).all()
        return jsonify([criterion.to_dict() for criterion in criteria])
    except Exception as e:
        logger.error(f"Error getting evaluation criteria: {str(e)}")
        return jsonify({'error': str(e)}), 500

@evaluation_bp.route('/criteria', methods=['POST'])
def create_evaluation_criteria():
    """Crear criterios de evaluación para un proceso"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['process_id', 'name', 'weight', 'criteria_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # Verificar que el proceso existe
        process = Process.query.get(data['process_id'])
        if not process:
            return jsonify({'error': 'Proceso no encontrado'}), 404
        
        # Verificar que el peso total no exceda 100%
        existing_criteria = EvaluationCriteria.query.filter_by(process_id=data['process_id']).all()
        total_weight = sum(c.weight for c in existing_criteria) + data['weight']
        if total_weight > 100:
            return jsonify({'error': 'El peso total de los criterios no puede exceder 100%'}), 400
        
        criteria = EvaluationCriteria(
            process_id=data['process_id'],
            name=data['name'],
            description=data.get('description'),
            weight=data['weight'],
            criteria_type=data['criteria_type'],
            max_score=data.get('max_score', 100.0)
        )
        
        db.session.add(criteria)
        db.session.commit()
        
        return jsonify(criteria.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating evaluation criteria: {str(e)}")
        return jsonify({'error': str(e)}), 500

@evaluation_bp.route('/criteria/<int:criteria_id>', methods=['PUT'])
def update_evaluation_criteria(criteria_id):
    """Actualizar criterio de evaluación"""
    try:
        criteria = EvaluationCriteria.query.get_or_404(criteria_id)
        data = request.get_json()
        
        # Verificar peso total si se actualiza el peso
        if 'weight' in data:
            existing_criteria = EvaluationCriteria.query.filter_by(
                process_id=criteria.process_id
            ).filter(EvaluationCriteria.id != criteria_id).all()
            total_weight = sum(c.weight for c in existing_criteria) + data['weight']
            if total_weight > 100:
                return jsonify({'error': 'El peso total de los criterios no puede exceder 100%'}), 400
        
        # Actualizar campos
        for field in ['name', 'description', 'weight', 'criteria_type', 'max_score']:
            if field in data:
                setattr(criteria, field, data[field])
        
        db.session.commit()
        return jsonify(criteria.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating evaluation criteria: {str(e)}")
        return jsonify({'error': str(e)}), 500

@evaluation_bp.route('/criteria/<int:criteria_id>', methods=['DELETE'])
def delete_evaluation_criteria(criteria_id):
    """Eliminar criterio de evaluación"""
    try:
        criteria = EvaluationCriteria.query.get_or_404(criteria_id)
        
        # Verificar si hay evaluaciones asociadas
        evaluations = BidEvaluation.query.filter_by(criteria_id=criteria_id).count()
        if evaluations > 0:
            return jsonify({'error': 'No se puede eliminar el criterio porque tiene evaluaciones asociadas'}), 400
        
        db.session.delete(criteria)
        db.session.commit()
        
        return jsonify({'message': 'Criterio eliminado exitosamente'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting evaluation criteria: {str(e)}")
        return jsonify({'error': str(e)}), 500

@evaluation_bp.route('/evaluate', methods=['POST'])
def evaluate_bid():
    """Evaluar una oferta según los criterios establecidos"""
    try:
        data = request.get_json()
        bid_id = data.get('bid_id')
        evaluations = data.get('evaluations', [])
        evaluator = data.get('evaluator', 'Sistema')
        
        bid = Bid.query.get_or_404(bid_id)
        
        # Eliminar evaluaciones existentes para esta oferta
        BidEvaluation.query.filter_by(bid_id=bid_id).delete()
        
        # Crear nuevas evaluaciones
        for eval_data in evaluations:
            evaluation = BidEvaluation(
                bid_id=bid_id,
                criteria_id=eval_data['criteria_id'],
                score=eval_data['score'],
                comments=eval_data.get('comments'),
                evaluator=evaluator
            )
            db.session.add(evaluation)
        
        # Calcular puntaje total ponderado
        total_score = calculate_weighted_score(bid_id)
        
        # Actualizar la oferta con el puntaje total
        bid.total_score = total_score
        bid.status = 'evaluated'
        bid.evaluation_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Evaluación completada exitosamente',
            'total_score': total_score,
            'bid': bid.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error evaluating bid: {str(e)}")
        return jsonify({'error': str(e)}), 500

@evaluation_bp.route('/ranking/<int:process_id>', methods=['GET'])
def get_bid_ranking(process_id):
    """Obtener ranking de ofertas para un proceso"""
    try:
        rankings = BidRanking.query.filter_by(process_id=process_id)\
                                  .order_by(BidRanking.ranking_position).all()
        
        if not rankings:
            # Generar ranking si no existe
            generate_bid_ranking(process_id)
            rankings = BidRanking.query.filter_by(process_id=process_id)\
                                      .order_by(BidRanking.ranking_position).all()
        
        return jsonify([ranking.to_dict() for ranking in rankings])
    except Exception as e:
        logger.error(f"Error getting bid ranking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@evaluation_bp.route('/ranking/<int:process_id>/generate', methods=['POST'])
def generate_ranking(process_id):
    """Generar ranking de ofertas para un proceso"""
    try:
        result = generate_bid_ranking(process_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error generating ranking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@evaluation_bp.route('/bid/<int:bid_id>/evaluations', methods=['GET'])
def get_bid_evaluations(bid_id):
    """Obtener evaluaciones detalladas de una oferta"""
    try:
        evaluations = BidEvaluation.query.filter_by(bid_id=bid_id).all()
        return jsonify([evaluation.to_dict() for evaluation in evaluations])
    except Exception as e:
        logger.error(f"Error getting bid evaluations: {str(e)}")
        return jsonify({'error': str(e)}), 500

def calculate_weighted_score(bid_id):
    """Calcular puntaje total ponderado de una oferta"""
    try:
        bid = Bid.query.get(bid_id)
        if not bid:
            return 0
        
        evaluations = db.session.query(
            BidEvaluation.score,
            EvaluationCriteria.weight
        ).join(EvaluationCriteria)\
         .filter(BidEvaluation.bid_id == bid_id).all()
        
        if not evaluations:
            return 0
        
        weighted_sum = sum(eval.score * (eval.weight / 100) for eval in evaluations)
        return round(weighted_sum, 2)
    except Exception as e:
        logger.error(f"Error calculating weighted score: {str(e)}")
        return 0

def generate_bid_ranking(process_id):
    """Generar ranking completo de ofertas para un proceso"""
    try:
        # Eliminar ranking existente
        BidRanking.query.filter_by(process_id=process_id).delete()
        
        # Obtener todas las ofertas evaluadas del proceso
        bids = Bid.query.filter_by(process_id=process_id)\
                       .filter(Bid.status == 'evaluated').all()
        
        if not bids:
            return {'message': 'No hay ofertas evaluadas para generar ranking'}
        
        # Calcular puntajes por categoría y total para cada oferta
        bid_scores = []
        for bid in bids:
            evaluations = db.session.query(
                BidEvaluation.score,
                EvaluationCriteria.weight,
                EvaluationCriteria.criteria_type
            ).join(EvaluationCriteria)\
             .filter(BidEvaluation.bid_id == bid.id).all()
            
            technical_score = 0
            commercial_score = 0
            financial_score = 0
            total_weighted_score = 0
            
            for eval in evaluations:
                weighted_score = eval.score * (eval.weight / 100)
                total_weighted_score += weighted_score
                
                if eval.criteria_type == 'technical':
                    technical_score += weighted_score
                elif eval.criteria_type == 'commercial':
                    commercial_score += weighted_score
                elif eval.criteria_type == 'financial':
                    financial_score += weighted_score
            
            bid_scores.append({
                'bid': bid,
                'technical_score': round(technical_score, 2),
                'commercial_score': round(commercial_score, 2),
                'financial_score': round(financial_score, 2),
                'total_score': round(total_weighted_score, 2)
            })
        
        # Ordenar por puntaje total (descendente)
        bid_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Crear registros de ranking
        for position, bid_data in enumerate(bid_scores, 1):
            recommendation = 'award' if position == 1 else 'reject'
            if position <= 3:  # Top 3 como candidatos
                recommendation = 'award' if position == 1 else 'conditional'
            
            ranking = BidRanking(
                process_id=process_id,
                bid_id=bid_data['bid'].id,
                technical_score=bid_data['technical_score'],
                commercial_score=bid_data['commercial_score'],
                financial_score=bid_data['financial_score'],
                weighted_total_score=bid_data['total_score'],
                ranking_position=position,
                recommendation=recommendation,
                justification=f"Posición {position} con puntaje total de {bid_data['total_score']}"
            )
            db.session.add(ranking)
        
        db.session.commit()
        
        return {
            'message': 'Ranking generado exitosamente',
            'total_bids': len(bid_scores),
            'rankings': [ranking.to_dict() for ranking in 
                        BidRanking.query.filter_by(process_id=process_id)
                                       .order_by(BidRanking.ranking_position).all()]
        }
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating bid ranking: {str(e)}")
        raise e

