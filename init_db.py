"""
Script de inicialización de la base de datos
Crea las tablas y datos de ejemplo si es necesario
"""

import os
import sys
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.database import db
from src.models.models import *
from src.models.excel_models import *

def create_sample_data():
    """Crear datos de ejemplo para demostración"""
    try:
        # Verificar si ya existen datos
        if Supplier.query.first() or Process.query.first():
            print("Ya existen datos en la base de datos. Omitiendo creación de datos de ejemplo.")
            return
        
        print("Creando datos de ejemplo...")
        
        # Crear proveedores de ejemplo
        suppliers = [
            Supplier(
                name="Proveedor Tecnológico S.A.",
                contact_person="Juan Pérez",
                email="juan.perez@provtech.com",
                phone="+56912345678",
                address="Av. Providencia 1234, Santiago",
                rut="12.345.678-9",
                status="active",
                notes="Especialista en equipos informáticos"
            ),
            Supplier(
                name="Suministros Industriales Ltda.",
                contact_person="María González",
                email="maria.gonzalez@suministros.cl",
                phone="+56987654321",
                address="Calle Industrial 567, Valparaíso",
                rut="98.765.432-1",
                status="active",
                notes="Proveedor de materiales industriales"
            ),
            Supplier(
                name="Servicios Profesionales SpA",
                contact_person="Carlos Rodríguez",
                email="carlos.rodriguez@servicios.cl",
                phone="+56911223344",
                address="Las Condes 890, Santiago",
                rut="11.222.333-4",
                status="active",
                notes="Consultoría y servicios profesionales"
            )
        ]
        
        for supplier in suppliers:
            db.session.add(supplier)
        
        db.session.commit()
        print(f"Creados {len(suppliers)} proveedores de ejemplo")
        
        # Crear procesos de ejemplo
        processes = [
            Process(
                process_number="LIC-2024-001",
                title="Adquisición de Equipos Informáticos",
                description="Licitación para la compra de computadores y equipos de red para la oficina central",
                process_type="large_tender",
                status="active",
                budget=50000000,
                start_date=datetime.now() - timedelta(days=10),
                end_date=datetime.now() + timedelta(days=20),
                notes="Proceso prioritario para renovación tecnológica"
            ),
            Process(
                process_number="COM-2024-002",
                title="Compra de Material de Oficina",
                description="Adquisición de suministros de oficina para el trimestre",
                process_type="simple_purchase",
                status="evaluation",
                budget=2000000,
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() + timedelta(days=5),
                notes="Compra rutinaria trimestral"
            ),
            Process(
                process_number="LIC-2024-003",
                title="Servicios de Consultoría en Gestión",
                description="Contratación de servicios de consultoría para mejora de procesos",
                process_type="large_tender",
                status="draft",
                budget=30000000,
                start_date=datetime.now() + timedelta(days=5),
                end_date=datetime.now() + timedelta(days=35),
                notes="Proyecto de mejora organizacional"
            )
        ]
        
        for process in processes:
            db.session.add(process)
        
        db.session.commit()
        print(f"Creados {len(processes)} procesos de ejemplo")
        
        # Crear ofertas de ejemplo
        bids = [
            Bid(
                process_id=1,  # LIC-2024-001
                supplier_id=1,  # Proveedor Tecnológico S.A.
                bid_amount=45000000,
                technical_score=4.5,
                commercial_score=4.2,
                total_score=4.35,
                status="submitted",
                notes="Oferta competitiva con buena propuesta técnica"
            ),
            Bid(
                process_id=1,  # LIC-2024-001
                supplier_id=2,  # Suministros Industriales Ltda.
                bid_amount=48000000,
                technical_score=3.8,
                commercial_score=4.0,
                total_score=3.9,
                status="submitted",
                notes="Oferta con precio más alto pero cumple especificaciones"
            ),
            Bid(
                process_id=2,  # COM-2024-002
                supplier_id=2,  # Suministros Industriales Ltda.
                bid_amount=1800000,
                technical_score=4.0,
                commercial_score=4.5,
                total_score=4.25,
                status="evaluated",
                notes="Mejor oferta para material de oficina"
            )
        ]
        
        for bid in bids:
            db.session.add(bid)
        
        db.session.commit()
        print(f"Creadas {len(bids)} ofertas de ejemplo")
        
        # Crear alertas de ejemplo
        alerts = [
            Alert(
                title="Proceso próximo a vencer",
                message="El proceso LIC-2024-001 vence en 5 días",
                alert_type="deadline",
                priority="high",
                status="active",
                process_id=1,
                due_date=datetime.now() + timedelta(days=5)
            ),
            Alert(
                title="Documentos faltantes",
                message="Faltan documentos técnicos en el proceso COM-2024-002",
                alert_type="missing_document",
                priority="medium",
                status="active",
                process_id=2
            )
        ]
        
        for alert in alerts:
            db.session.add(alert)
        
        db.session.commit()
        print(f"Creadas {len(alerts)} alertas de ejemplo")
        
        print("✅ Datos de ejemplo creados exitosamente")
        
    except Exception as e:
        print(f"❌ Error creando datos de ejemplo: {str(e)}")
        db.session.rollback()

def initialize_database():
    """Inicializar la base de datos"""
    try:
        print("Inicializando base de datos...")
        
        # Crear todas las tablas
        db.create_all()
        print("✅ Tablas de base de datos creadas")
        
        # Crear datos de ejemplo
        create_sample_data()
        
        print("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {str(e)}")
        raise

if __name__ == "__main__":
    # Importar la aplicación Flask
    from src.main import app
    
    with app.app_context():
        initialize_database()

