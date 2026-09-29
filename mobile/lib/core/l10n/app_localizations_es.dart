// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get appTitle => 'Andes Pádel';

  @override
  String get appTagline => 'Reserva tu cancha de pádel';

  @override
  String get login => 'Iniciar sesión';

  @override
  String get loginSubtitle => 'Accede para reservar tu cancha';

  @override
  String get email => 'Email';

  @override
  String get password => 'Contraseña';

  @override
  String get loginButton => 'Entrar';

  @override
  String get noAccount => '¿No tienes cuenta?';

  @override
  String get registerLink => 'Regístrate';

  @override
  String get forgotPassword => '¿Olvidaste tu contraseña?';

  @override
  String get register => 'Crear cuenta';

  @override
  String get registerSubtitle => 'Completa tus datos para registrarte';

  @override
  String get fullName => 'Nombre completo';

  @override
  String get phone => 'Teléfono';

  @override
  String get acceptTerms => 'Acepto los términos y condiciones';

  @override
  String get registerButton => 'Crear cuenta';

  @override
  String get alreadyHaveAccount => '¿Ya tienes cuenta?';

  @override
  String get loginLink => 'Inicia sesión';

  @override
  String get verify => 'Verificar email';

  @override
  String get verifySubtitle => 'Ingresa el código que enviamos a tu email';

  @override
  String get code => 'Código de verificación';

  @override
  String get verifyButton => 'Verificar';

  @override
  String get resendCode => 'Reenviar código';

  @override
  String get resetPassword => 'Recuperar contraseña';

  @override
  String get resetSubtitle => 'Ingresa tu email y te enviaremos un código';

  @override
  String get resetButton => 'Enviar código';

  @override
  String get resetConfirm => 'Nueva contraseña';

  @override
  String get resetConfirmSubtitle => 'Ingresa el código y tu nueva contraseña';

  @override
  String get confirmPassword => 'Confirmar contraseña';

  @override
  String get saveButton => 'Guardar';

  @override
  String get home => 'Inicio';

  @override
  String get homeWelcome => 'Hola';

  @override
  String get eventsEmpty => 'Próximamente nuevas quedadas y eventos.';

  @override
  String get firstName => 'Nombre';

  @override
  String get lastName => 'Apellido';

  @override
  String get birthDate => 'Fecha de nacimiento';

  @override
  String get birthDateRequired => 'Selecciona tu fecha de nacimiento';

  @override
  String get joinEvent => 'Me apunto';

  @override
  String get eventJoined => '¡Te apuntaste a la quedada!';

  @override
  String get eventLeft => 'Ya no asistes a esta quedada';

  @override
  String get eventGoing => 'Ya estás apuntado';

  @override
  String get eventFull => 'Completo';

  @override
  String get fieldRequired => 'Este campo es obligatorio';

  @override
  String fieldRequiredNamed(String field) {
    return 'El campo $field es obligatorio';
  }

  @override
  String get fieldTooShort => 'Mínimo 2 caracteres';

  @override
  String get emailRequired => 'Ingresa tu email';

  @override
  String get emailInvalid => 'Email no válido';

  @override
  String get passwordRequired => 'Ingresa tu contraseña';

  @override
  String get passwordTooShort =>
      'La contraseña debe tener al menos 8 caracteres';

  @override
  String get codeRequired => 'Ingresa el código de verificación';

  @override
  String get codeInvalid => 'El código debe tener 6 dígitos';

  @override
  String get skillLevel => 'Nivel de juego';

  @override
  String get skillIniciacion => 'Iniciación';

  @override
  String get skillIntermedio => 'Intermedio';

  @override
  String get skillAvanzado => 'Avanzado';

  @override
  String get skillCompeticion => 'Competición';

  @override
  String get createMatch => 'Armar partido';

  @override
  String get openMatches => 'Partidos abiertos';

  @override
  String get joinMatch => 'Unirme';

  @override
  String get matchJoined => 'Te uniste al partido';

  @override
  String get matchCreated => 'Partido creado. Se avisó a tu categoría.';

  @override
  String get matchesEmpty => 'No hay partidos abiertos. ¡Arma el primero!';

  @override
  String get matchPlayers => 'Jugadores';

  @override
  String get matchNotes => 'Notas (opcional)';

  @override
  String get homeSubtitle => 'Encuentra tu cancha y reserva en segundos';

  @override
  String get bookNow => 'Reservar ahora';

  @override
  String get bookCourt => 'Reservar cancha';

  @override
  String get upcomingEvents => 'Próximos eventos';

  @override
  String get bookings => 'Mis reservas';

  @override
  String get navBookings => 'Reservas';

  @override
  String get navEvents => 'Eventos';

  @override
  String get navNotifications => 'Alertas';

  @override
  String get noBookings => 'No tienes reservas todavía';

  @override
  String get bookingStatus_confirmed => 'Confirmada';

  @override
  String get bookingStatus_pending => 'Pendiente';

  @override
  String get bookingStatus_cancelled => 'Cancelada';

  @override
  String get bookingStatus_held => 'En espera';

  @override
  String get events => 'Eventos';

  @override
  String get tournaments => 'Torneos';

  @override
  String get noEvents => 'No hay eventos publicados';

  @override
  String get news => 'Noticias';

  @override
  String get registerNow => 'Inscribirme';

  @override
  String get capacity => 'Cupos';

  @override
  String get partnerName => 'Nombre de tu pareja';

  @override
  String get registerPending =>
      'Inscripción registrada. Tu pago está pendiente de confirmación.';

  @override
  String get registerSuccess => '¡Inscripción confirmada!';

  @override
  String get alreadyRegistered => 'Ya estás inscrito en este torneo';

  @override
  String get tournamentFull => 'Torneo lleno';

  @override
  String get registrationsClosed => 'Inscripciones cerradas';

  @override
  String get free => 'Gratis';

  @override
  String get registered => 'Inscrito';

  @override
  String get tournamentStatus_open => 'Inscripciones abiertas';

  @override
  String get tournamentStatus_in_progress => 'En curso';

  @override
  String get tournamentStatus_closed => 'Cerrado';

  @override
  String get tournamentStatus_finished => 'Finalizado';

  @override
  String get tournamentStatus_draft => 'Borrador';

  @override
  String get notifications => 'Notificaciones';

  @override
  String get noNotifications => 'No tienes notificaciones';

  @override
  String get markRead => 'Marcar leída';

  @override
  String get markAllRead => 'Marcar todas leídas';

  @override
  String get unread => 'Sin leer';

  @override
  String get newBadge => 'Nueva';

  @override
  String get profile => 'Perfil';

  @override
  String get role => 'Rol';

  @override
  String get language => 'Idioma';

  @override
  String get logout => 'Cerrar sesión';

  @override
  String get logoutConfirm => '¿Seguro que quieres cerrar sesión?';

  @override
  String get cancel => 'Cancelar';

  @override
  String get confirm => 'Confirmar';

  @override
  String get error => 'Ocurrió un error';

  @override
  String get networkError => 'Error de conexión. Verifica tu internet.';

  @override
  String get invalidCredentials => 'Credenciales inválidas';

  @override
  String get accountLocked => 'Cuenta temporalmente bloqueada';

  @override
  String get accountInactive => 'Cuenta no activa';

  @override
  String get emailNotVerified => 'Verifica tu email antes de iniciar sesión';

  @override
  String get passwordMismatch => 'Las contraseñas no coinciden';

  @override
  String get fillAllFields => 'Completa todos los campos';

  @override
  String get acceptTermsRequired => 'Debes aceptar los términos';

  @override
  String get loading => 'Cargando...';

  @override
  String get retry => 'Reintentar';

  @override
  String get codeSent => 'Enviamos un código a tu email';

  @override
  String get success => 'Operación exitosa';

  @override
  String get sessionExpired => 'Tu sesión expiró. Inicia sesión de nuevo.';

  @override
  String get stepCourt => 'Elige cancha';

  @override
  String get stepSchedule => 'Fecha y hora';

  @override
  String get stepSummary => 'Resumen';

  @override
  String get stepDone => 'Reservada';

  @override
  String get next => 'Continuar';

  @override
  String get back => 'Volver';

  @override
  String get cancelBooking => 'Cancelar reserva';

  @override
  String get cancelBookingConfirm =>
      '¿Cancelar esta reserva? Esta acción no se puede deshacer.';

  @override
  String get duration => 'Duración';

  @override
  String get players => 'Jugadores';

  @override
  String get selectSlot => 'Selecciona una hora disponible';

  @override
  String get noAvailableSlots => 'No hay horarios disponibles para esa fecha';

  @override
  String get selectDate => 'Selecciona una fecha';

  @override
  String get price => 'Precio';

  @override
  String get total => 'Total';

  @override
  String get perHour => 'por hora';

  @override
  String get payTransfer => 'Pagar por transferencia';

  @override
  String get payCard => 'Pagar con tarjeta';

  @override
  String get paymentMethod => 'Método de pago';

  @override
  String get paymentSuccess => '¡Reserva confirmada!';

  @override
  String get paymentPending =>
      'Reserva confirmada. Tu pago está pendiente de confirmación.';

  @override
  String get paymentError => 'No se pudo procesar el pago. Intenta de nuevo.';

  @override
  String get slotTaken => 'Ese horario ya no está disponible. Elige otro.';

  @override
  String get minPlayers => 'Jugadores';

  @override
  String get confirmedAt => 'Confirmada el';

  @override
  String get notificationSettings => 'Configuración de notificaciones';

  @override
  String get save => 'Guardar';

  @override
  String get bookingReminder => 'Recordatorio de reserva';

  @override
  String get tournamentReminder => 'Recordatorio de torneo';

  @override
  String get tournamentConfirmed => 'Inscripción confirmada';

  @override
  String get payments => 'Pagos';

  @override
  String get marketing => 'Promociones y novedades';

  @override
  String get channelEmail => 'Email';

  @override
  String get channelPush => 'Notificaciones push';

  @override
  String get channelInApp => 'Notificaciones en la app';

  @override
  String get timeNow => 'Ahora';

  @override
  String timeAgoMinutes(int minutes) {
    return 'Hace $minutes min';
  }

  @override
  String timeAgoHours(int hours) {
    return 'Hace $hours h';
  }

  @override
  String timeAgoDays(int days) {
    return 'Hace $days d';
  }

  @override
  String get timeYesterday => 'Ayer';

  @override
  String get noNews => 'No hay noticias';

  @override
  String get role_cliente => 'Cliente';

  @override
  String get role_recepcionista => 'Recepcionista';

  @override
  String get role_gerente => 'Gerente';

  @override
  String get role_dueno => 'Dueño';

  @override
  String get role_superadmin => 'Administrador';

  @override
  String homeGreeting(String name) {
    return 'Hola, $name';
  }

  @override
  String get findYourCourt => 'Busca tu cancha';

  @override
  String get seeAll => 'Ver todo';

  @override
  String get availableCourts => 'Canchas disponibles';

  @override
  String get noCourtsAvailable => 'No hay canchas disponibles en este momento';

  @override
  String get courtType_techada => 'Techada';

  @override
  String get courtType_abierta => 'Abierta';

  @override
  String get hasLighting => 'Con iluminación';

  @override
  String get noLighting => 'Sin iluminación';

  @override
  String get basePrice => 'Precio base';

  @override
  String get viewDetails => 'Ver detalles';

  @override
  String get reserve => 'Reservar';

  @override
  String get today => 'Hoy';

  @override
  String get thisWeek => 'Esta semana';

  @override
  String get paymentMethodSubtitle => 'Elige cómo deseas pagar';

  @override
  String get payWithCard => 'Pagar con tarjeta';

  @override
  String get payWithTransfer => 'Transferencia bancaria';

  @override
  String get payWithCash => 'Pago en el establecimiento';

  @override
  String get cardDescription => 'Débito o crédito vía Stripe';

  @override
  String get transferDescription =>
      'Realiza una transferencia y sube tu comprobante';

  @override
  String get cashDescription => 'Paga en el establecimiento al llegar';

  @override
  String get transferInstructions => 'Datos para transferencia';

  @override
  String get bankName => 'Banco';

  @override
  String get accountNumber => 'Número de cuenta';

  @override
  String get accountHolder => 'Titular de la cuenta';

  @override
  String get beneficiaryCode => 'Código de beneficiario';

  @override
  String get transferAmount => 'Monto a transferir';

  @override
  String get uploadProof => 'Subir comprobante';

  @override
  String get uploadProofHint => 'Tomar foto o seleccionar de galería';

  @override
  String get proofUploaded => 'Comprobante subido';

  @override
  String get proofPending => 'Esperando confirmación del comprobante';

  @override
  String get transferPending => 'Transferencia pendiente de verificación';

  @override
  String get transferConfirmed => 'Transferencia confirmada';

  @override
  String get transferRejected => 'Transferencia rechazada';

  @override
  String transferRejectedReason(String reason) {
    return 'Motivo: $reason';
  }

  @override
  String get confirmTransfer => 'Confirmar transferencia';

  @override
  String get rejectTransfer => 'Rechazar transferencia';

  @override
  String get rejectionReason => 'Motivo del rechazo';

  @override
  String get maxFileSize => 'Tamaño máximo: 5 MB';

  @override
  String get allowedFormats => 'Formatos: JPEG, PNG';

  @override
  String get imageTooLarge => 'La imagen excede 5 MB';

  @override
  String get invalidFormat => 'Formato no permitido. Use JPEG o PNG';

  @override
  String get proofUploadSuccess => 'Comprobante enviado correctamente';

  @override
  String get proofUploadError => 'Error al subir el comprobante';

  @override
  String get camera => 'Cámara';

  @override
  String get gallery => 'Galería';

  @override
  String get send => 'Enviar comprobante';

  @override
  String get bookingModified => 'Reserva modificada';

  @override
  String get noShowPenalty => 'Penalizacion por inasistencia';

  @override
  String get tournamentRegistered => 'Inscripcion registrada';

  @override
  String get newsPublished => 'Noticia publicada';

  @override
  String get durationMin => 'min';

  @override
  String get paymentProcessing => 'Procesando pago...';

  @override
  String get tabQuedadas => 'Quedadas';

  @override
  String get tabTorneos => 'Torneos';

  @override
  String get tabLigas => 'Ligas';

  @override
  String get tabAcademia => 'Academia';

  @override
  String get noQuedadas => 'No hay quedadas programadas';

  @override
  String get noLigas => 'No hay ligas activas';

  @override
  String get noAcademia => 'No hay clases disponibles';

  @override
  String get reserveYourCourt => 'Reserva tu cancha';

  @override
  String get reserveNow => 'Reserva ahora';

  @override
  String get clubContact => 'Contacto del club';

  @override
  String get clubInfo => 'Información del club';

  @override
  String get openMaps => 'Abrir mapa';

  @override
  String get call => 'Llamar';

  @override
  String get write => 'Escribir';

  @override
  String get whatsapp => 'WhatsApp';

  @override
  String get instagram => 'Instagram';

  @override
  String get showPassword => 'Mostrar contraseña';

  @override
  String get hidePassword => 'Ocultar contraseña';

  @override
  String get extraInfo => 'Información adicional';

  @override
  String get stepDate => '1. Elige el día';

  @override
  String get stepDuration => '2. Duración';

  @override
  String get stepStartTime => '3. Hora de inicio';

  @override
  String get freeSlotsOnlyHint =>
      'Solo horarios con cancha libre (según ocupación real).';

  @override
  String get noFreeSlotsForSelection =>
      'No hay horas libres para este día y duración. Prueba otro día.';

  @override
  String get timeMorning => 'Mañana';

  @override
  String get timeAfternoon => 'Tarde';

  @override
  String get timeEvening => 'Noche';

  @override
  String freeCourtsCountOne(num count) {
    return '$count libre';
  }

  @override
  String freeCourtsCountOther(num count) {
    return '$count libres';
  }
}
