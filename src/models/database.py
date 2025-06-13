from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Inicializar la base de datos con la aplicación Flask"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("Base de datos inicializada correctamente")

