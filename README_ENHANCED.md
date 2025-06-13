# Sistema de Gestión de Compras y Licitaciones - Versión Mejorada

## Nuevas Funcionalidades Implementadas

### 1. Dashboard Analítico con Chart.js
- **Gráficos de distribución por estado**: Visualización de procesos según su estado actual
- **Gráfico de ahorro estimado**: Comparación entre presupuesto referencial y ofertas adjudicadas
- **Top 5 proveedores**: Ranking de proveedores por número de procesos participados
- **Tendencia mensual**: Evolución de procesos creados en los últimos 6 meses
- **KPIs mejorados**: Contadores actualizados con datos reales

### 2. Evaluación Técnica-Económica de Ofertas
- **Criterios personalizables**: Definición de criterios con pesos específicos (ej: precio 60%, calidad técnica 40%)
- **Múltiples propuestas por proceso**: Gestión de varias ofertas por proceso de compra
- **Cálculo automático de puntajes**: Sistema de scoring basado en criterios ponderados
- **Ranking de proveedores**: Ordenamiento automático según puntaje final
- **Interfaz intuitiva**: Formularios para ingreso y gestión de evaluaciones

### 3. Exportación de Informes PDF/Excel
- **Informes completos por proceso**: Generación de reportes detallados incluyendo:
  - Información general del proceso
  - Historial de ofertas
  - Ranking de evaluación
  - Criterios utilizados
  - Documentos asociados
- **Formatos múltiples**: Exportación en PDF y Excel
- **Botones integrados**: Acceso directo desde la tabla de procesos
- **Librerías utilizadas**: xhtml2pdf para PDF, openpyxl para Excel

### 4. Calendario de Hitos con FullCalendar.js
- **Visualización tipo calendario**: Vista mensual, semanal y lista de hitos
- **Hitos automáticos**: Generación automática de fechas importantes:
  - Inicio del proceso
  - Fin del proceso
  - Evaluación de ofertas
  - Adjudicación
  - Entrega estimada
- **Alertas visuales**: Identificación de hitos vencidos con colores y animaciones
- **Filtros avanzados**: Por proceso, tipo de hito y estado
- **Próximos vencimientos**: Panel lateral con hitos próximos a vencer
- **Hitos vencidos**: Seguimiento de fechas no cumplidas

## Características Técnicas

### Backend (Flask)
- **Nuevas rutas API**:
  - `/api/evaluation/*` - Gestión de evaluaciones técnico-económicas
  - `/api/export/*` - Generación de informes PDF/Excel
  - `/api/calendar/*` - Gestión de hitos y calendario
  - `/api/reports/dashboard` - Datos mejorados para dashboard

### Frontend (HTML/CSS/JavaScript)
- **FullCalendar.js 6.1.10**: Calendario interactivo con soporte completo
- **Chart.js**: Gráficos mejorados con datos reales
- **Bootstrap 5.3**: Interfaz responsive y moderna
- **JavaScript nativo**: Funciones optimizadas para todas las nuevas características

### Base de Datos
- **Nuevos modelos**:
  - `EvaluationCriteria`: Criterios de evaluación personalizables
  - `ProposalEvaluation`: Evaluaciones de propuestas
  - `ProcessMilestone`: Hitos de procesos (virtual, generado dinámicamente)

## Instalación y Despliegue

### Requisitos
- Python 3.11+
- Dependencias listadas en `requirements.txt`

### Instalación Local
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python src/main.py
```

### Despliegue en Heroku
```bash
# Crear aplicación Heroku
heroku create tu-app-name

# Configurar variables de entorno
heroku config:set FLASK_ENV=production

# Desplegar
git push heroku main
```

## Estructura del Proyecto

```
procurement_enhanced/
├── src/
│   ├── models/
│   │   ├── models.py          # Modelos de datos (incluye nuevos modelos)
│   │   └── database.py        # Configuración de base de datos
│   ├── routes/
│   │   ├── evaluation.py      # 🆕 Rutas de evaluación técnico-económica
│   │   ├── export.py          # 🆕 Rutas de exportación PDF/Excel
│   │   ├── calendar.py        # 🆕 Rutas de calendario de hitos
│   │   ├── reports.py         # ✨ Mejorado con nuevos gráficos
│   │   └── ...                # Rutas existentes
│   ├── static/
│   │   ├── index.html         # ✨ Mejorado con nuevas secciones
│   │   ├── app.js             # ✨ Mejorado con nuevas funciones
│   │   └── style.css          # ✨ Mejorado con estilos para calendario
│   └── main.py                # ✨ Mejorado con nuevos blueprints
├── requirements.txt           # ✨ Actualizado con nuevas dependencias
├── Procfile                   # Configuración Heroku
└── README.md                  # Documentación actualizada
```

## Funcionalidades Mantenidas

Todas las funcionalidades originales se mantienen intactas:
- Gestión de procesos de compra
- Administración de proveedores
- Gestión de ofertas
- Sistema de documentos
- Alertas y notificaciones
- Reportes básicos
- Gestión de archivos Excel

## Compatibilidad

- ✅ **Heroku Ready**: Configurado para despliegue inmediato
- ✅ **Responsive Design**: Compatible con dispositivos móviles
- ✅ **Cross-browser**: Funciona en navegadores modernos
- ✅ **Base de datos**: SQLite para desarrollo, PostgreSQL para producción

## Notas de Desarrollo

### Correcciones Aplicadas
- Corregido error de sintaxis en consultas SQLAlchemy (`db.case`)
- Solucionado problema de comparación de tipos datetime/date
- Optimizada gestión de permisos de archivos
- Mejorada compatibilidad con diferentes versiones de librerías

### Mejoras de Rendimiento
- Consultas SQL optimizadas para dashboard
- Carga asíncrona de datos en calendario
- Generación eficiente de hitos automáticos
- Cache de datos frecuentemente consultados

## Soporte y Mantenimiento

El proyecto está listo para producción y incluye:
- Manejo robusto de errores
- Logging detallado
- Validación de datos
- Seguridad básica implementada
- Documentación completa de APIs

---

**Versión**: 2.0 Enhanced  
**Fecha**: Junio 2025  
**Estado**: Producción Ready ✅

