# Sistema de Gestión de Compras y Licitaciones

## Descripción

Sistema web completo para la gestión de procesos de compra y licitaciones, desarrollado con Flask y optimizado para despliegue en Heroku.

## Características Principales

- **Gestión Integral de Procesos**: Administración completa de procesos de compra simples y licitaciones grandes
- **Gestión de Proveedores**: Base de datos completa con evaluación y seguimiento
- **Sistema de Ofertas**: Gestión y comparación de propuestas técnicas y comerciales
- **Gestión Documental**: Repositorio centralizado con control de versiones
- **Sistema de Alertas**: Notificaciones automáticas de vencimientos y eventos importantes
- **Análisis con Excel**: Integración completa para carga y análisis de datos
- **Reportes Avanzados**: Dashboard interactivo con gráficos y métricas
- **Sistema de Respaldos**: Backup automático de datos y archivos

## Tecnologías Utilizadas

- **Backend**: Flask 3.1.1 con SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (Heroku)
- **Gráficos**: Chart.js
- **Análisis**: Pandas, Matplotlib, Seaborn
- **Despliegue**: Heroku con Gunicorn

## Estructura del Proyecto

```
procurement_app/
├── src/
│   ├── main.py                 # Aplicación principal
│   ├── models/
│   │   ├── database.py         # Configuración de base de datos
│   │   ├── models.py           # Modelos principales
│   │   └── excel_models.py     # Modelos para datos Excel
│   ├── routes/
│   │   ├── suppliers.py        # API de proveedores
│   │   ├── processes.py        # API de procesos
│   │   ├── documents.py        # API de documentos
│   │   ├── bids.py            # API de ofertas
│   │   ├── alerts.py          # API de alertas
│   │   ├── reports.py         # API de reportes
│   │   ├── alerts_scheduler.py # Sistema de alertas automáticas
│   │   └── excel_routes.py    # API para Excel
│   ├── static/
│   │   ├── index.html         # Interfaz principal
│   │   ├── style.css          # Estilos personalizados
│   │   └── app.js            # Lógica del frontend
│   ├── uploads/               # Documentos cargados
│   └── logs/                  # Archivos de log
├── backups/                   # Respaldos automáticos
├── robustness_improvements.py # Mejoras de robustez
├── requirements.txt           # Dependencias
├── Procfile                   # Configuración Heroku
├── .python-version           # Versión de Python
└── README.md                 # Este archivo
```

## Instalación Local

### Requisitos
- Python 3.11+
- 4 GB RAM mínimo
- 2 GB espacio en disco

### Pasos

1. **Clonar o extraer el proyecto**
   ```bash
   cd procurement_app
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar la aplicación**
   ```bash
   cd src
   python main.py
   ```

5. **Acceder al sistema**
   - Abrir navegador en `http://localhost:5000`

## Despliegue en Heroku

### Preparación

1. **Instalar Heroku CLI**
   - Descargar desde https://devcenter.heroku.com/articles/heroku-cli

2. **Inicializar repositorio Git**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

### Despliegue

1. **Crear aplicación en Heroku**
   ```bash
   heroku create nombre-de-tu-app
   ```

2. **Configurar base de datos PostgreSQL**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. **Configurar variables de entorno**
   ```bash
   heroku config:set SECRET_KEY=tu_clave_secreta_aqui
   ```

4. **Desplegar aplicación**
   ```bash
   git push heroku main
   ```

5. **Inicializar base de datos**
   ```bash
   heroku run python src/main.py
   ```

### Variables de Entorno para Heroku

- `SECRET_KEY`: Clave secreta para Flask
- `DATABASE_URL`: URL de PostgreSQL (automática)

## Funcionalidades Principales

### Dashboard
- Contadores de procesos, proveedores, ofertas y alertas
- Gráficos de distribución por estado y tipo
- Lista de procesos recientes
- Panel de alertas activas

### Gestión de Procesos
- Creación y edición de procesos
- Tipos: Compra Simple y Licitación Grande
- Estados: Borrador, Activo, Evaluación, Completado, Cancelado
- Filtros y búsqueda avanzada
- Exportación a Excel

### Gestión de Proveedores
- Registro completo de información
- Estados: Activo, Inactivo, Lista Negra
- Historial de participación
- Evaluación de desempeño
- Exportación a Excel

### Sistema de Ofertas
- Registro de propuestas técnicas y comerciales
- Puntuación y evaluación
- Comparación automática
- Estados de seguimiento

### Gestión de Documentos
- Carga de archivos múltiples formatos
- Categorización automática
- Asociación con procesos y proveedores
- Descarga segura

### Sistema de Alertas
- Verificación automática de vencimientos
- Alertas de documentos faltantes
- Notificaciones por prioridad
- Gestión de estados

### Análisis con Excel
- Carga de tablas especializadas
- Validación automática de datos
- Plantillas descargables
- Análisis y visualización

### Reportes
- Análisis de tendencias
- Comparación de ofertas
- Evaluación de proveedores
- Gráficos interactivos

## API Endpoints

### Procesos
- `GET /api/processes` - Listar procesos
- `POST /api/processes` - Crear proceso
- `GET /api/processes/{id}` - Obtener proceso
- `PUT /api/processes/{id}` - Actualizar proceso
- `DELETE /api/processes/{id}` - Eliminar proceso

### Proveedores
- `GET /api/suppliers` - Listar proveedores
- `POST /api/suppliers` - Crear proveedor
- `GET /api/suppliers/{id}` - Obtener proveedor
- `PUT /api/suppliers/{id}` - Actualizar proveedor
- `DELETE /api/suppliers/{id}` - Eliminar proveedor

### Ofertas
- `GET /api/bids` - Listar ofertas
- `POST /api/bids` - Crear oferta
- `GET /api/bids/{id}` - Obtener oferta
- `PUT /api/bids/{id}` - Actualizar oferta
- `DELETE /api/bids/{id}` - Eliminar oferta

### Documentos
- `GET /api/documents` - Listar documentos
- `POST /api/documents/upload` - Subir documento
- `GET /api/documents/{id}/download` - Descargar documento
- `DELETE /api/documents/{id}` - Eliminar documento

### Alertas
- `GET /api/alerts` - Listar alertas
- `POST /api/alerts` - Crear alerta
- `PUT /api/alerts/{id}` - Actualizar alerta
- `POST /api/alerts/check-deadlines` - Verificar vencimientos

### Excel
- `POST /api/excel/upload` - Subir archivo Excel
- `GET /api/excel/templates/{type}` - Descargar plantilla
- `GET /api/excel/data/{type}` - Obtener datos procesados

### Reportes
- `GET /api/reports/dashboard` - Datos del dashboard
- `GET /api/reports/export/suppliers` - Exportar proveedores
- `GET /api/reports/export/processes` - Exportar procesos

### Sistema
- `GET /health` - Estado de salud
- `GET /api/system/status` - Estado del sistema
- `POST /api/system/backup` - Crear respaldo

## Seguridad

- Validación de tipos de archivo
- Sanitización de nombres de archivo
- Control de tamaños de archivo (16MB máximo)
- Logs de actividad del sistema
- Respaldos automáticos

## Monitoreo y Logs

- Sistema de logging con rotación automática
- Monitoreo de recursos del sistema
- Verificación de integridad de base de datos
- Alertas de estado del sistema

## Respaldos

- Respaldo automático de base de datos
- Respaldo de archivos subidos
- Compresión automática
- Limpieza de respaldos antiguos (30 días)

## Soporte

Para soporte técnico o consultas:
1. Revisar logs en `src/logs/`
2. Verificar estado del sistema en `/api/system/status`
3. Crear respaldo manual en `/api/system/backup`

## Licencia

Sistema desarrollado para uso organizacional interno.

---

**¡Sistema listo para producción en Heroku!** 🚀

