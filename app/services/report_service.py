from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import io
from app.models.access_log import AccessLog
from app.models.user import User
from app.models.visitor import Visitor

def get_weekly_access_report(db: Session) -> Dict[str, Any]:
    """
    Genera un informe semanal de accesos.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Diccionario con datos del informe
    """
    # Calcular fecha de inicio (hace 7 días)
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    # Obtener registros de acceso de la última semana
    access_logs = db.query(AccessLog).filter(
        and_(
            AccessLog.access_time >= start_date,
            AccessLog.access_time <= end_date
        )
    ).all()
    
    # Estadísticas generales
    total_entries = sum(1 for log in access_logs if log.access_type == 'entry')
    total_exits = sum(1 for log in access_logs if log.access_type == 'exit')
    
    # Estadísticas por tipo de persona
    employee_entries = sum(1 for log in access_logs if log.access_type == 'entry' and log.person_type == 'employee')
    employee_exits = sum(1 for log in access_logs if log.access_type == 'exit' and log.person_type == 'employee')
    visitor_entries = sum(1 for log in access_logs if log.access_type == 'entry' and log.person_type == 'visitor')
    visitor_exits = sum(1 for log in access_logs if log.access_type == 'exit' and log.person_type == 'visitor')
    
    # Estadísticas por día
    daily_stats = {}
    for log in access_logs:
        day = log.access_time.strftime('%Y-%m-%d')
        if day not in daily_stats:
            daily_stats[day] = {'entries': 0, 'exits': 0}
        
        if log.access_type == 'entry':
            daily_stats[day]['entries'] += 1
        else:
            daily_stats[day]['exits'] += 1
    
    # Formato del informe
    report = {
        'period': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'total_stats': {
            'entries': total_entries,
            'exits': total_exits,
            'total': len(access_logs)
        },
        'by_type': {
            'employees': {
                'entries': employee_entries,
                'exits': employee_exits,
                'total': employee_entries + employee_exits
            },
            'visitors': {
                'entries': visitor_entries,
                'exits': visitor_exits,
                'total': visitor_entries + visitor_exits
            }
        },
        'daily_stats': daily_stats,
        'raw_data': [
            {
                'id': log.id,
                'person_type': log.person_type,
                'person_id': log.person_id,
                'access_type': log.access_type,
                'access_time': log.access_time.strftime('%Y-%m-%d %H:%M:%S'),
                'workday_date': log.workday_date.strftime('%Y-%m-%d')
            }
            for log in access_logs
        ]
    }
    
    return report

def generate_html_report(report: Dict[str, Any]) -> str:
    """
    Genera un informe HTML a partir de los datos del informe.
    
    Args:
        report: Datos del informe
        
    Returns:
        Contenido HTML del informe
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Informe Semanal de Accesos</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3 {{
                color: #2c3e50;
            }}
            .header {{
                background-color: #34495e;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .section {{
                margin-bottom: 30px;
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            th, td {{
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            th {{
                background-color: #34495e;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            .summary {{
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
            }}
            .summary-card {{
                flex: 1;
                min-width: 200px;
                background-color: #ecf0f1;
                border-radius: 5px;
                padding: 15px;
                margin: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .summary-card h3 {{
                margin-top: 0;
                border-bottom: 1px solid #bdc3c7;
                padding-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Informe Semanal de Accesos</h1>
            <p>Período: {report['period']['start']} al {report['period']['end']}</p>
        </div>
        
        <div class="section">
            <h2>Resumen General</h2>
            <div class="summary">
                <div class="summary-card">
                    <h3>Total de Accesos</h3>
                    <p>Entradas: {report['total_stats']['entries']}</p>
                    <p>Salidas: {report['total_stats']['exits']}</p>
                    <p><strong>Total: {report['total_stats']['total']}</strong></p>
                </div>
                <div class="summary-card">
                    <h3>Empleados</h3>
                    <p>Entradas: {report['by_type']['employees']['entries']}</p>
                    <p>Salidas: {report['by_type']['employees']['exits']}</p>
                    <p><strong>Total: {report['by_type']['employees']['total']}</strong></p>
                </div>
                <div class="summary-card">
                    <h3>Visitantes</h3>
                    <p>Entradas: {report['by_type']['visitors']['entries']}</p>
                    <p>Salidas: {report['by_type']['visitors']['exits']}</p>
                    <p><strong>Total: {report['by_type']['visitors']['total']}</strong></p>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Estadísticas Diarias</h2>
            <table>
                <tr>
                    <th>Fecha</th>
                    <th>Entradas</th>
                    <th>Salidas</th>
                    <th>Total</th>
                </tr>
    """
    
    # Agregar filas para cada día
    for day, stats in report['daily_stats'].items():
        daily_total = stats['entries'] + stats['exits']
        html += f"""
                <tr>
                    <td>{day}</td>
                    <td>{stats['entries']}</td>
                    <td>{stats['exits']}</td>
                    <td>{daily_total}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Datos Detallados</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Tipo</th>
                    <th>ID Persona</th>
                    <th>Tipo de Acceso</th>
                    <th>Fecha y Hora</th>
                </tr>
    """
    
    # Agregar filas para cada registro
    for log in report['raw_data'][:50]:  # Limitamos a 50 registros para no hacer el correo demasiado grande
        html += f"""
                <tr>
                    <td>{log['id']}</td>
                    <td>{'Empleado' if log['person_type'] == 'employee' else 'Visitante'}</td>
                    <td>{log['person_id']}</td>
                    <td>{'Entrada' if log['access_type'] == 'entry' else 'Salida'}</td>
                    <td>{log['access_time']}</td>
                </tr>
        """
    
    html += """
            </table>
        </div>
        
        <div class="section">
            <p>Este es un correo automático generado por el sistema de control de acceso. Por favor, no responda a este correo.</p>
        </div>
    </body>
    </html>
    """
    
    return html
