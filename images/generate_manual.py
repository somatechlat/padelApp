#!/usr/bin/env python3
"""Generate a Word user manual for Andes Padel admin panel (Spanish)."""

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

IMAGES = Path(__file__).parent
OUTPUT = IMAGES.parent / "Manual_Usuario_AndesPadel.docx"

doc = Document()

# ── Styles ──
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)
style.paragraph_format.space_after = Pt(6)

for level in range(1, 4):
    hs = doc.styles[f"Heading {level}"]
    hs.font.color.rgb = RGBColor(0x00, 0x2F, 0x48)  # Midnight Blue

# ── Helper functions ──
def add_screenshot(name, caption, width=5.5):
    path = IMAGES / f"{name}.png"
    if path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(path), width=Inches(width))
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.style = doc.styles["Normal"]
        run2 = cap.runs[0] if cap.runs else cap.add_run()
        run2.font.size = Pt(9)
        run2.font.italic = True
        run2.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

def add_table(headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(10)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = table.rows[ri + 1].cells[ci]
            cell.text = str(val)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(10)

def add_bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.bold = True
        p.add_run(f" {text}")
    else:
        p.add_run(text)

# ════════════════════════════════════════════════════════════════════════
#  PORTADA
# ════════════════════════════════════════════════════════════════════════
for _ in range(6):
    doc.add_paragraph()

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("Manual de Usuario")
run.font.size = Pt(32)
run.font.bold = True
run.font.color.rgb = RGBColor(0x00, 0x2F, 0x48)  # Midnight Blue

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run("Andes Padél — Sistema de Gestión de Reservas")
run.font.size = Pt(16)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

doc.add_paragraph()
doc.add_paragraph()

meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = meta.add_run("Versión 1.0 — Agosto 2026\n")
run.font.size = Pt(11)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
run = meta.add_run("Plataforma: Panel de Administración Web\n")
run.font.size = Pt(11)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
run = meta.add_run("Documento confidencial — Solo para uso interno")
run.font.size = Pt(11)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
#  ÍNDICE
# ════════════════════════════════════════════════════════════════════════
doc.add_heading("Índice", level=1)

toc_items = [
    "1. Introducción",
    "2. Acceso al Sistema",
    "3. Panel de Administración Django (/admin/)",
    "   3.1. Panel Principal (Dashboard)",
    "   3.2. Gestión de Usuarios",
    "   3.3. Gestión de Canchas",
    "   3.4. Gestión de Reservas",
    "   3.5. Gestión de Eventos y Torneos",
    "   3.6. Gestión de Horarios",
    "   3.7. Gestión de Precios",
    "   3.8. Gestión de Pagos",
    "   3.9. Gestión de Notificaciones",
    "   3.10. Gestión de Sedes",
    "   3.11. Políticas de Cancelación",
    "   3.12. Registro de Auditoría",
    "4. Panel de Administración Personalizado (/adminpanel/)",
    "   4.1. Panel de Control Principal",
    "   4.2. Calendario de Reservas",
    "   4.3. Gestión de Canchas",
    "   4.4. Gestión de Usuarios",
    "   4.5. Gestión de Pagos",
    "   4.6. Eventos, Torneos y Noticias",
    "   4.7. Reportes e Ingresos",
    "   4.8. Configuración",
    "   4.9. Registro de Auditoría",
    "5. Documentación de la API (Swagger / ReDoc)",
    "   5.1. Vista General de Endpoints",
    "   5.2. Autenticación con JWT",
    "6. Cuentas de Prueba",
    "7. Solución de Problemas",
]
for item in toc_items:
    p = doc.add_paragraph(item)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(0)
    if not item.startswith("   "):
        for r in p.runs:
            r.font.bold = True

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
#  1. INTRODUCCIÓN
# ════════════════════════════════════════════════════════════════════════
doc.add_heading("1. Introducción", level=1)

doc.add_paragraph(
    "Andes Padél es un sistema completo de gestión de reservas de canchas de pádel "
    "diseñado para el complejo deportivo Andes Padél en Quito, Ecuador. El sistema "
    "comprende una API RESTful, una aplicación móvil Flutter y dos paneles de "
    "administración web."
)
doc.add_paragraph(
    "Este manual describe paso a paso cómo utilizar el Panel de Administración Web, "
    "que permite gestionar usuarios, canchas, reservas, pagos, eventos, torneos, "
    "reportes y configuración del complejo."
)

doc.add_heading("Componentes del Sistema", level=2)
add_table(
    ["Componente", "Tecnología", "URL / Acceso"],
    [
        ["API REST", "Django 5.2 + DRF", "http://[IP]:8000/api/"],
        ["Documentación API", "Swagger / ReDoc", "http://[IP]:8000/api/docs/"],
        ["Admin Django", "Django Admin", "http://[IP]:8000/admin/"],
        ["Admin Personalizado", "Django Templates", "http://[IP]:8000/adminpanel/"],
        ["App Móvil", "Flutter 3.27", "APK en Android"],
    ],
)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
#  2. ACCESO AL SISTEMA
# ════════════════════════════════════════════════════════════════════════
doc.add_heading("2. Acceso al Sistema", level=1)

doc.add_paragraph(
    "Para acceder al panel de administración, abra su navegador web e ingrese "
    "la dirección correspondiente:"
)

doc.add_heading("Panel Django Admin", level=2)
doc.add_paragraph(
    "1. Navegue a http://[IP_DEL_SERVIDOR]:8000/admin/\n"
    "2. Ingrese su correo electrónico en el campo \"Email\"\n"
    "3. Ingrese su contraseña en el campo \"Contraseña\"\n"
    "4. Haga clic en \"Iniciar sesión\""
)
add_screenshot("03_admin_login", "Figura 1: Pantalla de inicio de sesión del Admin Django")

doc.add_heading("Panel Personalizado", level=2)
doc.add_paragraph(
    "1. Navegue a http://[IP_DEL_SERVIDOR]:8000/adminpanel/\n"
    "2. Será redirigido a la pantalla de inicio de sesión\n"
    "3. Ingrese sus credenciales (correo y contraseña)\n"
    "4. Haga clic en \"Iniciar sesión\""
)

doc.add_paragraph(
    "Nota: Ambos paneles utilizan las mismas credenciales. Si no tiene acceso, "
    "contacte al administrador del sistema."
)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
#  3. PANEL DE ADMINISTRACIÓN DJANGO
# ════════════════════════════════════════════════════════════════════════
doc.add_heading("3. Panel de Administración Django (/admin/)", level=1)

doc.add_paragraph(
    "El panel de administración Django proporciona acceso completo a todos los "
    "modelos del sistema. Es la herramienta principal para la gestión técnica "
    "de los datos."
)

# 3.1 Dashboard
doc.add_heading("3.1. Panel Principal (Dashboard)", level=2)
doc.add_paragraph(
    "Al iniciar sesión, se muestra el panel principal con un resumen de todas "
    "las secciones disponibles:"
)
add_bullet("Usuarios — Gestión completa de cuentas de usuario")
add_bullet("Canchas — Administración de canchas y sedes")
add_bullet("Reservas — Lista y gestión de todas las reservas")
add_bullet("Eventos — Torneos, eventos y noticias")
add_bullet("Horarios — Gestión de franjas horarias")
add_bullet("Precios — Reglas de pricing y tarifas")
add_bullet("Pagos — Registro y seguimiento de pagos")
add_bullet("Notificaciones — Sistema de notificaciones in-app")
add_bullet("Políticas — Reglas de cancelación y penalidades")
add_bullet("Seguridad — Registro de auditoría")

add_screenshot("04_admin_dashboard", "Figura 2: Panel principal de administración Django")

# 3.2 Usuarios
doc.add_heading("3.2. Gestión de Usuarios", level=2)
doc.add_paragraph(
    "La sección de Usuarios permite administrar todas las cuentas del sistema. "
    "Puede crear, editar, activar/desactivar usuarios y gestionar roles."
)

doc.add_heading("Roles disponibles:", level=3)
add_table(
    ["Rol", "Descripción"],
    [
        ["superadmin", "Acceso total al sistema y configuración"],
        ["admin", "Administrador con acceso amplio"],
        ["staff", "Personal del complejo deportivo"],
        ["client", "Usuario cliente que realiza reservas"],
    ],
)
doc.add_paragraph()

doc.add_heading("Cada usuario incluye:", level=3)
add_bullet("Correo electrónico (identificador único)")
add_bullet("Nombre completo")
add_bullet("Teléfono")
add_bullet("Rol y estado (activo/inactivo)")
add_bullet("Verificación de email")
add_bullet("Idioma preferido (es/en/pt/ca)")
add_bullet("Fecha de registro")

add_screenshot("05_admin_users", "Figura 3: Gestión de usuarios")

# 3.3 Canchas
doc.add_heading("3.3. Gestión de Canchas", level=2)
doc.add_paragraph(
    "Permite administrar las canchas de pádel del complejo. Cada cancha pertenece "
    "a una sede (venue) y tiene propiedades específicas."
)

doc.add_heading("Propiedades de cada cancha:", level=3)
add_bullet("Nombre (ej: C1, C2)")
add_bullet("Tipo de cancha: techada o abierta")
add_bullet("Iluminación disponible (sí/no)")
add_bullet("Precio base por hora")
add_bullet("Estado: activa o inactiva")

add_screenshot("06_admin_courts", "Figura 4: Gestión de canchas")

# 3.4 Reservas
doc.add_heading("3.4. Gestión de Reservas", level=2)
doc.add_paragraph(
    "Muestra todas las reservas realizadas en el sistema. Cada reserva está "
    "asociada a un usuario, una cancha, una fecha y un horario específico."
)

doc.add_heading("Estados de una reserva:", level=3)
add_table(
    ["Estado", "Descripción"],
    [
        ["pending_payment", "Reserva creada, esperando pago"],
        ["confirmed", "Reserva confirmada y pagada"],
        ["in_progress", "Reserva en curso (fecha/hora actual)"],
        ["completed", "Reserva finalizada"],
        ["cancelled", "Reserva cancelada"],
        ["no_show", "El cliente no se presentó"],
    ],
)
doc.add_paragraph()

doc.add_paragraph("Información visible por cada reserva:")
add_bullet("Usuario que realizó la reserva")
add_bullet("Cancha asignada")
add_bullet("Fecha y hora de inicio/fin")
add_bullet("Duración en minutos")
add_bullet("Número de jugadores")
add_bullet("Precio total")
add_bullet("Estado actual")
add_bullet("Slots horarios reservados")

add_screenshot("07_admin_bookings", "Figura 5: Gestión de reservas")

# 3.5 Eventos
doc.add_heading("3.5. Gestión de Eventos y Torneos", level=2)
doc.add_paragraph(
    "Permite crear y administrar torneos, eventos especiales y noticias "
    "para los usuarios del complejo."
)

doc.add_heading("Contenido gestionable:", level=3)
add_bullet("Torneos: nombre, categoría, máximo de equipos, cuota de inscripción, fechas")
add_bullet("Eventos: título, descripción, fecha/hora, ubicación, estado")
add_bullet("Noticias: título, contenido, fecha de publicación")

add_screenshot("08_admin_events", "Figura 6: Gestión de eventos y torneos")

# 3.6 Horarios
doc.add_heading("3.6. Gestión de Horarios", level=2)
doc.add_paragraph(
    "Las franjas horarias (TimeSlots) representan los bloques de 30 minutos "
    "disponibles para reserva en cada cancha. Este sistema permite un control "
    "granular de la disponibilidad."
)

doc.add_heading("Estados de un horario:", level=3)
add_table(
    ["Estado", "Descripción"],
    [
        ["available", "Disponible para reserva"],
        ["held", "Mantenido temporalmente (carrito de compra)"],
        ["booked", "Reservado por un cliente"],
        ["blocked", "Bloqueado por administración"],
    ],
)
doc.add_paragraph()

add_screenshot("09_admin_timeslots", "Figura 7: Gestión de horarios")

# 3.7 Precios
doc.add_heading("3.7. Gestión de Precios", level=2)
doc.add_paragraph(
    "Las reglas de precios permiten definir tarifas dinámicas según la cancha, "
    "el día de la hora, y otros factores."
)

doc.add_heading("Configuración de reglas:", level=3)
add_bullet("Cancha aplicable")
add_bullet("Día de la semana")
add_bullet("Hora de inicio y fin")
add_bullet("Precio por bloque de 30 minutos")
add_bullet("Prioridad de la regla (para superposición)")

add_screenshot("10_admin_pricing", "Figura 8: Gestión de reglas de precios")

# 3.8 Pagos
doc.add_heading("3.8. Gestión de Pagos", level=2)
doc.add_paragraph(
    "Registra y administra todos los pagos asociados a reservas. Soporta "
    "múltiples métodos de pago y estados de transacción."
)

doc.add_heading("Estados de pago:", level=3)
add_table(
    ["Estado", "Descripción"],
    [
        ["pending", "Pago pendiente de procesamiento"],
        ["pending_transfer", "Esperando confirmación de transferencia"],
        ["captured", "Pago capturado exitosamente"],
        ["confirmed", "Pago confirmado manualmente"],
        ["failed", "Pago fallido o rechazado"],
        ["refunded", "Reembolso procesado"],
    ],
)
doc.add_paragraph()

doc.add_heading("Métodos de pago soportados:", level=3)
add_bullet("Stripe (tarjeta de crédito/débito)")
add_bullet("Transferencia bancaria")
add_bullet("Efectivo")

add_screenshot("11_admin_payments", "Figura 9: Gestión de pagos")

# 3.9 Notificaciones
doc.add_heading("3.9. Gestión de Notificaciones", level=2)
doc.add_paragraph(
    "El sistema de notificaciones permite enviar avisos a los usuarios "
    "a través de múltiples canales: in-app, email y push (FCM)."
)

doc.add_heading("Tipos de notificación:", level=3)
add_bullet("Confirmación de reserva")
add_bullet("Recordatorio de reserva")
add_bullet("Cancelación de reserva")
add_bullet("Actualización de estado de pago")
add_bullet("Noticias y eventos")

add_screenshot("12_admin_notifications", "Figura 10: Gestión de notificaciones")

# 3.10 Sedes
doc.add_heading("3.10. Gestión de Sedes", level=2)
doc.add_paragraph(
    "Las sedes (venues) representan las ubicaciones físicas del complejo deportivo. "
    "Cada sede contiene una o más canchas."
)

doc.add_heading("Información de cada sede:", level=3)
add_bullet("Nombre del complejo")
add_bullet("Dirección")
add_bullet("Estado (activo/inactivo)")

add_screenshot("13_admin_venues", "Figura 11: Gestión de sedes")

# 3.11 Políticas
doc.add_heading("3.11. Políticas de Cancelación", level=2)
doc.add_paragraph(
    "Las políticas de cancelación definen las reglas y penalidades cuando "
    "un usuario cancela una reserva."
)

doc.add_heading("Parámetros configurables:", level=3)
add_bullet("Nombre de la política")
add_bullet("Horas de antelación mínima para cancelar sin penalidad")
add_bullet("Porcentaje de penalidad (0-100%)")
add_bullet("Monto fijo de penalidad")
add_bullet("Descripción de la política")

add_screenshot("14_admin_policies", "Figura 12: Políticas de cancelación")

# 3.12 Auditoría
doc.add_heading("3.12. Registro de Auditoría", level=2)
doc.add_paragraph(
    "El registro de auditoría captura automáticamente todas las acciones "
    "realizadas en el sistema para fines de trazabilidad y seguridad."
)

doc.add_heading("Información registrada:", level=3)
add_bullet("Usuario que realizó la acción")
add_bullet("Tipo de acción (crear, editar, eliminar, login, etc.)")
add_bullet("Entidad afectada (usuario, reserva, cancha, etc.)")
add_bullet("ID de la entidad")
add_bullet("Fecha y hora exacta")
add_bullet("Dirección IP")

add_screenshot("15_admin_audit_logs", "Figura 13: Registro de auditoría")

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
#  4. PANEL PERSONALIZADO
# ════════════════════════════════════════════════════════════════════════
doc.add_heading("4. Panel de Administración Personalizado (/adminpanel/)", level=1)

doc.add_paragraph(
    "El panel personalizado ofrece una interfaz más amigable y visual para las "
    "operaciones diarias del complejo. A diferencia del admin Django, está "
    "diseñado para tareas frecuentes como crear reservas, bloquear horarios "
    "y verificar pagos."
)

# 4.1 Dashboard
doc.add_heading("4.1. Panel de Control Principal", level=2)
doc.add_paragraph(
    "El dashboard principal muestra un resumen ejecutivo del estado actual "
    "del complejo deportivo."
)

doc.add_heading("Métricas en tiempo real:", level=3)
add_bullet("Reservas de hoy: cantidad de reservas activas para la fecha actual")
add_bullet("Ocupación de hoy: porcentaje de slots reservados vs disponibles")
add_bullet("Ingresos del día: total de pagos recibidos hoy")
add_bullet("Alertas de mantenimiento: canchas con ventanas de mantenimiento programadas")
add_bullet("Transferencias pendientes: pagos por transferencia esperando confirmación")
add_bullet("Reservas sin pagar: reservas con estado pendiente de pago")

doc.add_heading("Accesos rápidos:", level=3)
add_bullet("Reservas de hoy — Lista de las reservas del día con detalles")
add_bullet("Pagos recientes — Últimos 5 pagos registrados")
add_bullet("Total de usuarios registrados en el sistema")
add_bullet("Total de canchas activas")

add_screenshot("16_custom_admin_dashboard", "Figura 14: Panel de control principal")

# 4.2 Calendario
doc.add_heading("4.2. Calendario de Reservas", level=2)
doc.add_paragraph(
    "El calendario es la herramienta principal para la gestión diaria. Muestra "
    "una cuadrícula visual de todos los horarios por cancha, permitiendo "
    "bloquear, desbloquear y crear reservas directamente."
)

doc.add_heading("Funcionalidades del calendario:", level=3)
add_bullet("Navegación por fecha — Botones para día anterior/siguiente")
add_bullet("Vista de cuadrícula — Filas = horas (6:00 a 23:00), Columnas = canchas")
add_bullet("Bloquear slot — Bloquea un horario para mantenimiento u otro motivo")
add_bullet("Desbloquear slot — Restaura un horario bloqueado a disponible")
add_bullet("Crear reserva manual — Reserva un horario para un usuario específico")

doc.add_heading("Crear una reserva manual:", level=3)
doc.add_paragraph(
    "1. Seleccione la fecha en el calendario\n"
    "2. En la sección \"Crear reserva manual\", seleccione la cancha\n"
    "3. Seleccione el usuario (desplegable con todos los usuarios activos)\n"
    "4. Ingrese la hora de inicio (formato HH:MM)\n"
    "5. Seleccione la duración (30, 60, 90 o 120 minutos)\n"
    "6. Haga clic en \"Crear reserva\"\n"
    "7. Se creará la reserva con estado \"confirmada\" y se enviará una notificación"
)

add_screenshot("17_custom_admin_calendar", "Figura 15: Calendario de reservas")

# 4.3 Canchas Panel
doc.add_heading("4.3. Gestión de Canchas (Panel Personalizado)", level=2)
doc.add_paragraph(
    "Vista simplificada para la gestión rápida de canchas con acciones frecuentes."
)

doc.add_heading("Acciones disponibles:", level=3)
add_bullet("Activar/Desactivar cancha — Cambia el estado con un clic")
add_bullet("Crear nueva cancha — Nombre, tipo (techada/abierta), iluminación")
add_bullet("Programar mantenimiento — Seleccionar cancha, motivo, fecha/hora inicio-fin")

add_screenshot("18_custom_admin_courts", "Figura 16: Gestión de canchas (panel personalizado)")

# 4.4 Usuarios Panel
doc.add_heading("4.4. Gestión de Usuarios (Panel Personalizado)", level=2)
doc.add_paragraph(
    "Lista paginada de usuarios con opciones de búsqueda y filtrado."
)

doc.add_heading("Funcionalidades:", level=3)
add_bullet("Buscar — Por nombre o correo electrónico")
add_bullet("Filtrar por rol — superadmin, admin, staff, client")
add_bullet("Filtrar por estado — activo, inactivo")
add_bullet("Cambiar rol — Asignar nuevo rol desde la lista")
add_bullet("Cambiar estado — Activar o desactivar usuario")
add_bullet("Paginación — 30 usuarios por página")

add_screenshot("19_custom_admin_users", "Figura 17: Gestión de usuarios (panel personalizado)")

# 4.5 Pagos Panel
doc.add_heading("4.5. Gestión de Pagos (Panel Personalizado)", level=2)
doc.add_paragraph(
    "Interfaz para verificar y gestionar pagos, especialmente útil para "
    "confirmar transferencias bancarias."
)

doc.add_heading("Acciones por cada pago:", level=3)
add_bullet("Confirmar transferencia — Marca el pago como confirmado y confirma la reserva")
add_bullet("Rechazar transferencia — Rechaza el pago y marca como fallido")
add_bullet("Reembolsar — Procesa un reembolso y cancela la reserva asociada")

doc.add_heading("Filtros disponibles:", level=3)
add_bullet("Por estado del pago")
add_bullet("Por método de pago")

add_screenshot("20_custom_admin_payments", "Figura 18: Gestión de pagos (panel personalizado)")

# 4.6 Eventos Panel
doc.add_heading("4.6. Eventos, Torneos y Noticias (Panel Personalizado)", level=2)
doc.add_paragraph(
    "Gestión centralizada de todo el contenido del complejo: torneos, "
    "eventos especiales y noticias para los usuarios."
)

doc.add_heading("Crear un torneo:", level=3)
doc.add_paragraph(
    "1. Ingrese el título del torneo\n"
    "2. Seleccione la categoría (Open, Intermedio, etc.)\n"
    "3. Defina el máximo de equipos\n"
    "4. Establezca la cuota de inscripción\n"
    "5. Seleccione fecha de inicio y fin\n"
    "6. Haga clic en \"Crear torneo\""
)

doc.add_heading("Crear una noticia:", level=3)
doc.add_paragraph(
    "1. Ingrese el título de la noticia\n"
    "2. Escriba el contenido\n"
    "3. Haga clic en \"Publicar\""
)

add_screenshot("21_custom_admin_events", "Figura 19: Eventos, torneos y noticias")

# 4.7 Reportes
doc.add_heading("4.7. Reportes e Ingresos (Panel Personalizado)", level=2)
doc.add_paragraph(
    "Sección de reportes para el análisis del rendimiento del complejo."
)

doc.add_heading("Métricas disponibles:", level=3)
add_bullet("Ingresos del mes — Total de pagos confirmados en el mes actual")
add_bullet("Reservas por estado — Distribución de reservas según su estado")
add_bullet("Ingresos por cancha — Desglose de ingresos por cada cancha")
add_bullet("Top clientes — Los 10 usuarios con más reservas")
add_bullet("Exportar CSV — Descarga un reporte completo en formato CSV")

add_screenshot("22_custom_admin_reports", "Figura 20: Reportes e ingresos")

# 4.8 Configuración
doc.add_heading("4.8. Configuración (Panel Personalizado)", level=2)
doc.add_paragraph(
    "Vista de configuración que muestra las políticas de cancelación y "
    "reglas de precios actualmente activas."
)

doc.add_heading("Información visible:", level=3)
add_bullet("Políticas de cancelación — Lista de todas las políticas configuradas")
add_bullet("Reglas de precios — Tarifas activas por cancha y horario")

add_screenshot("23_custom_admin_settings", "Figura 21: Configuración del sistema")

# 4.9 Auditoría Panel
doc.add_heading("4.9. Registro de Auditoría (Panel Personalizado)", level=2)
doc.add_paragraph(
    "Vista detallada del registro de auditoría con opciones de filtrado."
)

doc.add_heading("Filtros de auditoría:", level=3)
add_bullet("Por tipo de acción (login, creación, edición, etc.)")
add_bullet("Por entidad (usuario, reserva, cancha, etc.)")
add_bullet("Por usuario — Buscar por correo electrónico")

add_screenshot("24_custom_admin_audit", "Figura 22: Registro de auditoría (panel personalizado)")

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
#  5. DOCUMENTACIÓN API
# ════════════════════════════════════════════════════════════════════════
doc.add_heading("5. Documentación de la API (Swagger / ReDoc)", level=1)

doc.add_paragraph(
    "La API REST del sistema está documentada interactivamente utilizando "
    "Swagger UI y ReDoc. Estas herramientas permiten explorar y probar "
    "todos los endpoints disponibles."
)

doc.add_heading("Acceso a la documentación:", level=2)
add_bullet("Swagger UI — http://[IP]:8000/api/docs/")
add_bullet("ReDoc — http://[IP]:8000/api/redoc/")

doc.add_heading("5.1. Vista General de Endpoints", level=2)
doc.add_paragraph(
    "Swagger UI muestra todos los endpoints agrupados por categoría. "
    "Cada endpoint incluye la documentación de parámetros, respuestas "
    "y esquemas de datos."
)

doc.add_heading("Grupos de endpoints principales:", level=3)
add_table(
    ["Grupo", "Endpoints", "Descripción"],
    [
        ["Autenticación", "login, register, verify, refresh, logout", "Gestión de sesiones JWT"],
        ["Usuarios", "me, password-reset", "Perfil y recuperación de contraseña"],
        ["Canchas", "list, create, retrieve, update", "CRUD de canchas"],
        ["Reservas", "list, create, cancel, confirm", "Gestión de reservas"],
        ["Pagos", "create, confirm, refund", "Procesamiento de pagos"],
        ["Eventos", "list, create", "Torneos y eventos"],
        ["Notificaciones", "list, mark-read", "Notificaciones in-app"],
        ["Reportes", "revenue, occupancy, export", "Generación de reportes"],
    ],
)

add_screenshot("01_swagger_overview", "Figura 23: Documentación Swagger (vista pública)")

doc.add_heading("5.2. Autenticación con JWT", level=2)
doc.add_paragraph(
    "Para acceder a los endpoints protegidos, es necesario autenticarse "
    "utilizando tokens JWT (JSON Web Token). El proceso es:"
)

doc.add_paragraph(
    "1. Realizar una solicitud POST a /api/auth/login/ con email y contraseña\n"
    "2. El servidor responde con un token de acceso (access) y uno de refresco (refresh)\n"
    "3. Incluir el header Authorization: Bearer <access_token> en las solicitudes\n"
    "4. Cuando el access token expire, usar el refresh token para obtener uno nuevo\n"
    "5. Los tokens de refresco tienen un mecanismo de rotación y blacklist"
)

doc.add_paragraph(
    "En Swagger UI, puede hacer clic en el botón \"Authorize\" (candado) "
    "e ingresar su token de acceso para probar los endpoints protegidos "
    "directamente desde la interfaz."
)

add_screenshot("25_swagger_authenticated", "Figura 24: Swagger con autenticación JWT activa")

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
#  6. CUENTAS DE PRUEBA
# ════════════════════════════════════════════════════════════════════════
doc.add_heading("6. Cuentas de Prueba", level=1)

doc.add_paragraph(
    "Las siguientes cuentas están disponibles para pruebas en el entorno "
    "de desarrollo. Todas comparten la misma contraseña."
)

add_table(
    ["Cuenta", "Correo Electrónico", "Contraseña", "Rol"],
    [
        ["Administrador", "admin@andespadel.com", "Andes12345!", "superadmin"],
        ["Cliente", "cliente@andespadel.com", "Andes12345!", "client"],
    ],
)

doc.add_paragraph()
doc.add_paragraph(
    "Nota: Estas credenciales son solo para entornos de desarrollo. "
    "En producción, cada usuario debe tener credenciales únicas y seguras."
)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════
#  7. SOLUCIÓN DE PROBLEMAS
# ════════════════════════════════════════════════════════════════════════
doc.add_heading("7. Solución de Problemas", level=1)

problems = [
    ("No puedo iniciar sesión",
     "Verifique que está usando el correo electrónico correcto (no un nombre de usuario). "
     "La contraseña es sensible a mayúsculas y minúsculas. Si olvidó su contraseña, "
     "contacte al administrador."),
    ("La página no carga o muestra error 500",
     "El servidor puede estar reiniciándose. Espere unos segundos y recargue la página. "
     "Si el problema persiste, verifique que los contenedores Docker estén ejecutándose "
     "con el comando: docker compose ps"),
    ("No se guardan los cambios",
     "Verifique que tiene permisos de edición para la sección. Algunas acciones requieren "
     "confirmación. Revise si aparece un mensaje de error en la parte superior de la página."),
    ("El calendario no muestra las canchas",
     "Asegúrese de que existan canchas activas en el sistema. Las canchas inactivas no "
     "aparecen en el calendario. Cree canchas desde la sección de Gestión de Canchas."),
    ("Los pagos por transferencia no se confirman",
     "Los pagos por transferencia requieren verificación manual. Vaya a Gestión de Pagos, "
     "encuentre el pago con estado \"pending_transfer\" y haga clic en \"Confirmar transferencia\"."),
    ("No recibo notificaciones push",
     "Las notificaciones push requieren configuración de Firebase. Las notificaciones in-app "
     "y por email funcionan sin configuración adicional."),
]

for problem, solution in problems:
    doc.add_heading(problem, level=3)
    doc.add_paragraph(solution)

doc.add_paragraph()
doc.add_paragraph()

# Footer
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("— Fin del Manual —")
run.font.size = Pt(12)
run.font.italic = True
run.font.color.rgb = RGBColor(0x00, 0x2F, 0x48)  # Midnight Blue

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Andes Padél © 2026 — Todos los derechos reservados")
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

# ── Save ──
doc.save(str(OUTPUT))
print(f"Manual saved: {OUTPUT}")
print(f"Sections: 7 chapters, 24 screenshots embedded")
