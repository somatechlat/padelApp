// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Catalan Valencian (`ca`).
class AppLocalizationsCa extends AppLocalizations {
  AppLocalizationsCa([String locale = 'ca']) : super(locale);

  @override
  String get appTitle => 'Andes Pádel';

  @override
  String get appTagline => 'Reserva la teva pista de pàdel';

  @override
  String get login => 'Iniciar sessió';

  @override
  String get loginSubtitle => 'Accedeix per reservar la teva pista';

  @override
  String get email => 'Email';

  @override
  String get password => 'Contrasenya';

  @override
  String get loginButton => 'Entrar';

  @override
  String get noAccount => 'No tens compte?';

  @override
  String get registerLink => 'Registra\'t';

  @override
  String get forgotPassword => 'Has oblidat la contrasenya?';

  @override
  String get register => 'Crear compte';

  @override
  String get registerSubtitle => 'Completa les teves dades per registrar-te';

  @override
  String get fullName => 'Nom complet';

  @override
  String get phone => 'Telèfon';

  @override
  String get acceptTerms => 'Accepto els termes i condicions';

  @override
  String get registerButton => 'Crear compte';

  @override
  String get alreadyHaveAccount => 'Ja tens compte?';

  @override
  String get loginLink => 'Inicia sessió';

  @override
  String get verify => 'Verificar email';

  @override
  String get verifySubtitle =>
      'Introdueix el codi que t\'hem enviat al teu email';

  @override
  String get code => 'Codi de verificació';

  @override
  String get verifyButton => 'Verificar';

  @override
  String get resendCode => 'Reenviar codi';

  @override
  String get resetPassword => 'Recuperar contrasenya';

  @override
  String get resetSubtitle => 'Introdueix el teu email i t\'enviarem un codi';

  @override
  String get resetButton => 'Enviar codi';

  @override
  String get resetConfirm => 'Nova contrasenya';

  @override
  String get resetConfirmSubtitle =>
      'Introdueix el codi i la teva nova contrasenya';

  @override
  String get confirmPassword => 'Confirmar contrasenya';

  @override
  String get saveButton => 'Desar';

  @override
  String get home => 'Inici';

  @override
  String get homeWelcome => 'Hola';

  @override
  String get eventsEmpty => 'Properament noves quedades i esdeveniments.';

  @override
  String get firstName => 'Nom';

  @override
  String get lastName => 'Cognom';

  @override
  String get birthDate => 'Data de naixement';

  @override
  String get birthDateRequired => 'Selecciona la teva data de naixement';

  @override
  String get joinEvent => 'M\'apunto';

  @override
  String get eventJoined => 'T\'has apuntat!';

  @override
  String get eventLeft => 'Ja no hi vas';

  @override
  String get eventGoing => 'Hi vas';

  @override
  String get eventFull => 'Complet';

  @override
  String get fieldRequired => 'Aquest camp és obligatori';

  @override
  String fieldRequiredNamed(String field) {
    return 'El camp $field és obligatori';
  }

  @override
  String get fieldTooShort => 'Mínim 2 caràcters';

  @override
  String get emailRequired => 'Introdueix el teu email';

  @override
  String get emailInvalid => 'Email no vàlid';

  @override
  String get emailAlreadyExists =>
      'Aquest email ja està registrat. Et portem a recuperar la contrasenya.';

  @override
  String get passwordRequired => 'Introdueix la teva contrasenya';

  @override
  String get passwordTooShort =>
      'La contrasenya ha de tenir com a mínim 8 caràcters';

  @override
  String get codeRequired => 'Introdueix el codi de verificació';

  @override
  String get codeInvalid => 'El codi ha de tenir 6 dígits';

  @override
  String get skillLevel => 'Nivell de joc';

  @override
  String get skillIniciacion => 'Iniciació';

  @override
  String get skillIntermedio => 'Intermedi';

  @override
  String get skillAvanzado => 'Avançat';

  @override
  String get skillCompeticion => 'Competició';

  @override
  String get createMatch => 'Muntar partit';

  @override
  String get openMatches => 'Partits oberts';

  @override
  String get joinMatch => 'Unir-me';

  @override
  String get matchJoined => 'T\'has unit al partit';

  @override
  String get matchCreated => 'Partit creat. S\'ha avisat la teva categoria.';

  @override
  String get matchesEmpty => 'No hi ha partits oberts. Munta el primer!';

  @override
  String get matchPlayers => 'Jugadors';

  @override
  String get matchNotes => 'Notes (opcional)';

  @override
  String get homeSubtitle => 'Troba la teva pista i reserva en segons';

  @override
  String get bookNow => 'Reservar ara';

  @override
  String get bookCourt => 'Reservar pista';

  @override
  String get upcomingEvents => 'Properes esdeveniments';

  @override
  String get bookings => 'Les meves reserves';

  @override
  String get navBookings => 'Reserves';

  @override
  String get navEvents => 'Esdeveniments';

  @override
  String get navNotifications => 'Avisos';

  @override
  String get noBookings => 'Encara no tens reserves';

  @override
  String get bookingStatus_confirmed => 'Confirmada';

  @override
  String get bookingStatus_pending => 'Pendent';

  @override
  String get bookingStatus_cancelled => 'Cancel·lada';

  @override
  String get bookingStatus_held => 'En espera';

  @override
  String get events => 'Esdeveniments';

  @override
  String get tournaments => 'Torneigs';

  @override
  String get noEvents => 'No hi ha esdeveniments publicats';

  @override
  String get news => 'Notícies';

  @override
  String get registerNow => 'Inscriure\'m';

  @override
  String get capacity => 'Places';

  @override
  String get partnerName => 'Nom de la teva parella';

  @override
  String get registerPending =>
      'Inscripció registrada. El teu pagament està pendent de confirmació.';

  @override
  String get registerSuccess => 'Inscripció confirmada!';

  @override
  String get alreadyRegistered => 'Ja estàs inscrit en aquest torneig';

  @override
  String get tournamentFull => 'Torneig ple';

  @override
  String get registrationsClosed => 'Inscripcions tancades';

  @override
  String get free => 'Gratuït';

  @override
  String get registered => 'Inscrit';

  @override
  String get tournamentStatus_open => 'Inscripcions obertes';

  @override
  String get tournamentStatus_in_progress => 'En curs';

  @override
  String get tournamentStatus_closed => 'Tancat';

  @override
  String get tournamentStatus_finished => 'Finalitzat';

  @override
  String get tournamentStatus_draft => 'Esborrany';

  @override
  String get notifications => 'Notificacions';

  @override
  String get noNotifications => 'No tens notificacions';

  @override
  String get markRead => 'Marcar com a llegida';

  @override
  String get markAllRead => 'Marca-les totes com a llegides';

  @override
  String get unread => 'Sense llegir';

  @override
  String get newBadge => 'Nova';

  @override
  String get profile => 'Perfil';

  @override
  String get role => 'Perfil';

  @override
  String get language => 'Idioma';

  @override
  String get logout => 'Tancar sessió';

  @override
  String get logoutConfirm => 'Segur que vols tancar sessió?';

  @override
  String get deleteAccount => 'Esborrar compte';

  @override
  String get deleteAccountConfirm =>
      'Segur que vols esborrar el teu compte? Les teves dades seran anonimitzades i aquesta acció no es pot desfer.';

  @override
  String get deleteAccountDone => 'El teu compte ha estat esborrat.';

  @override
  String get changePassword => 'Canviar contrasenya';

  @override
  String get changePasswordSubtitle =>
      'Indica la contrasenya actual i tria una de nova';

  @override
  String get currentPassword => 'Contrasenya actual';

  @override
  String get currentPasswordRequired => 'Introdueix la contrasenya actual';

  @override
  String get newPassword => 'Contrasenya nova';

  @override
  String get passwordsDontMatch => 'Les contrasenyes no coincideixen';

  @override
  String get passwordChanged =>
      'Contrasenya actualitzada. Torna a iniciar sessió.';

  @override
  String get cancel => 'Cancel·lar';

  @override
  String get confirm => 'Confirmar';

  @override
  String get error => 'S\'ha produït un error';

  @override
  String get networkError => 'Error de connexió. Comprova el teu internet.';

  @override
  String get invalidCredentials => 'Credencials invàlides';

  @override
  String get accountLocked => 'Compte bloquejat temporalment';

  @override
  String get accountInactive => 'Compte no actiu';

  @override
  String get emailNotVerified =>
      'Verifica el teu email abans d\'iniciar sessió';

  @override
  String get passwordMismatch => 'Les contrasenyes no coincideixen';

  @override
  String get fillAllFields => 'Omple tots els camps';

  @override
  String get acceptTermsRequired => 'Has d\'acceptar els termes';

  @override
  String get loading => 'Carregant...';

  @override
  String get retry => 'Reintentar';

  @override
  String get codeSent => 'T\'hem enviat un codi al teu email';

  @override
  String get emailVerified => 'Email verificat. Ja pots iniciar sessió.';

  @override
  String get success => 'Operació correcta';

  @override
  String get sessionExpired =>
      'La teva sessió ha expirat. Torna a iniciar sessió.';

  @override
  String get stepCourt => 'Tria la pista';

  @override
  String get stepSchedule => 'Data i hora';

  @override
  String get stepSummary => 'Resum';

  @override
  String get stepDone => 'Reservada';

  @override
  String get next => 'Continuar';

  @override
  String get back => 'Tornar';

  @override
  String get cancelBooking => 'Cancel·lar reserva';

  @override
  String get cancelBookingConfirm =>
      'Cancel·lar aquesta reserva? Aquesta acció no es pot desfer.';

  @override
  String get duration => 'Durada';

  @override
  String get players => 'Jugadors';

  @override
  String get selectSlot => 'Selecciona una hora disponible';

  @override
  String get noAvailableSlots =>
      'No hi ha horaris disponibles per a aquesta data';

  @override
  String get selectDate => 'Selecciona una data';

  @override
  String get price => 'Preu';

  @override
  String get total => 'Total';

  @override
  String get perHour => 'per hora';

  @override
  String get payTransfer => 'Pagar per transferència';

  @override
  String get payCard => 'Pagar amb targeta';

  @override
  String get paymentMethod => 'Mètode de pagament';

  @override
  String get paymentSuccess => 'Reserva confirmada!';

  @override
  String get paymentPending =>
      'Reserva confirmada. El teu pagament està pendent de confirmació.';

  @override
  String get paymentError =>
      'No s\'ha pogut processar el pagament. Torna-ho a provar.';

  @override
  String get slotTaken =>
      'Aquest horari ja no està disponible. Tria\'n un altre.';

  @override
  String get minPlayers => 'Jugadors';

  @override
  String get confirmedAt => 'Confirmada el';

  @override
  String get notificationSettings => 'Configuració de notificacions';

  @override
  String get save => 'Desa';

  @override
  String get bookingReminder => 'Recordatori de reserva';

  @override
  String get tournamentReminder => 'Recordatori de torneig';

  @override
  String get tournamentConfirmed => 'Inscripció confirmada';

  @override
  String get payments => 'Pagaments';

  @override
  String get marketing => 'Promocions i novetats';

  @override
  String get channelEmail => 'Email';

  @override
  String get channelPush => 'Notificacions push';

  @override
  String get channelInApp => 'Notificacions a l\'app';

  @override
  String get timeNow => 'Ara';

  @override
  String timeAgoMinutes(int minutes) {
    return 'Fa $minutes min';
  }

  @override
  String timeAgoHours(int hours) {
    return 'Fa $hours h';
  }

  @override
  String timeAgoDays(int days) {
    return 'Fa $days d';
  }

  @override
  String get timeYesterday => 'Ahir';

  @override
  String get noNews => 'Sense notícies';

  @override
  String get role_cliente => 'Client';

  @override
  String get role_recepcionista => 'Recepcionista';

  @override
  String get role_gerente => 'Gerent';

  @override
  String get role_dueno => 'Propietari';

  @override
  String get role_superadmin => 'Administrador';

  @override
  String homeGreeting(String name) {
    return 'Hola, $name';
  }

  @override
  String get findYourCourt => 'Busca la teva pista';

  @override
  String get seeAll => 'Veure tot';

  @override
  String get availableCourts => 'Pistes disponibles';

  @override
  String get noCourtsAvailable => 'No hi ha pistes disponibles ara mateix';

  @override
  String get courtType_techada => 'Coberta';

  @override
  String get courtType_abierta => 'Oberta';

  @override
  String get hasLighting => 'Amb il·luminació';

  @override
  String get noLighting => 'Sense il·luminació';

  @override
  String get basePrice => 'Preu base';

  @override
  String get viewDetails => 'Veure detalls';

  @override
  String get reserve => 'Reservar';

  @override
  String get today => 'Avui';

  @override
  String get thisWeek => 'Aquesta setmana';

  @override
  String get paymentMethodSubtitle => 'Tria com vols pagar';

  @override
  String get payWithCard => 'Pagar amb targeta';

  @override
  String get payWithTransfer => 'Transferència bancària';

  @override
  String get payWithCash => 'Pagament a l\'establiment';

  @override
  String get cardDescription => 'Dèbit o crèdit mitjançant Stripe';

  @override
  String get transferDescription =>
      'Fes una transferència i puja el comprovant';

  @override
  String get cashDescription => 'Paga a l\'establiment en arribar';

  @override
  String get transferInstructions => 'Dades per a la transferència';

  @override
  String get bankName => 'Banc';

  @override
  String get accountNumber => 'Número de compte';

  @override
  String get accountHolder => 'Titular del compte';

  @override
  String get beneficiaryCode => 'Codi de beneficiari';

  @override
  String get transferAmount => 'Import a transferir';

  @override
  String get uploadProof => 'Pujar comprovant';

  @override
  String get uploadProofHint => 'Fes una foto o selecciona de la galeria';

  @override
  String get proofUploaded => 'Comprovant pujat';

  @override
  String get proofPending => 'S\'espera la confirmació del comprovant';

  @override
  String get transferPending => 'Transferència pendent de verificació';

  @override
  String get transferConfirmed => 'Transferència confirmada';

  @override
  String get transferRejected => 'Transferència rebutjada';

  @override
  String transferRejectedReason(String reason) {
    return 'Motiu: $reason';
  }

  @override
  String get confirmTransfer => 'Confirmar transferència';

  @override
  String get rejectTransfer => 'Rebutjar transferència';

  @override
  String get rejectionReason => 'Motiu del rebuig';

  @override
  String get maxFileSize => 'Mida màxima: 5 MB';

  @override
  String get allowedFormats => 'Formats: JPEG, PNG';

  @override
  String get imageTooLarge => 'La imatge supera els 5 MB';

  @override
  String get invalidFormat => 'Format no permès. Useu JPEG o PNG';

  @override
  String get proofUploadSuccess => 'Comprovant enviat correctament';

  @override
  String get proofUploadError => 'Error en pujar el comprovant';

  @override
  String get camera => 'Càmera';

  @override
  String get gallery => 'Galeria';

  @override
  String get send => 'Enviar comprovant';

  @override
  String get bookingModified => 'Reserva modificada';

  @override
  String get noShowPenalty => 'Penalització per incompareixença';

  @override
  String get tournamentRegistered => 'Inscripció registrada';

  @override
  String get newsPublished => 'Notícia publicada';

  @override
  String get durationMin => 'min';

  @override
  String get paymentProcessing => 'S\'està processant el pagament...';

  @override
  String get tabQuedadas => 'Quedades';

  @override
  String get tabTorneos => 'Torneigs';

  @override
  String get tabLigas => 'Lligues';

  @override
  String get tabAcademia => 'Acadèmia';

  @override
  String get noQuedadas => 'No hi ha quedades programades';

  @override
  String get noLigas => 'No hi ha lligues actives';

  @override
  String get noAcademia => 'No hi ha classes disponibles';

  @override
  String get reserveYourCourt => 'Reserva la teva pista';

  @override
  String get reserveNow => 'Reserva ara';

  @override
  String get clubContact => 'Contacte del club';

  @override
  String get clubInfo => 'Informació del club';

  @override
  String get openMaps => 'Obrir mapa';

  @override
  String get call => 'Trucar';

  @override
  String get write => 'Escriure';

  @override
  String get whatsapp => 'WhatsApp';

  @override
  String get instagram => 'Instagram';

  @override
  String get showPassword => 'Mostra la contrasenya';

  @override
  String get hidePassword => 'Amaga la contrasenya';

  @override
  String get extraInfo => 'Informació addicional';

  @override
  String get stepDate => '1. Tria un dia';

  @override
  String get stepDuration => '2. Durada';

  @override
  String get stepStartTime => '3. Hora d’inici';

  @override
  String get freeSlotsOnlyHint =>
      'Només horaris amb pista lliure (segons ocupació real).';

  @override
  String get noFreeSlotsForSelection =>
      'No hi ha hores lliures per a aquest dia i durada. Prova un altre dia.';

  @override
  String get timeMorning => 'Matí';

  @override
  String get timeAfternoon => 'Tarda';

  @override
  String get timeEvening => 'Nit';

  @override
  String freeCourtsCountOne(num count) {
    return '$count lliure';
  }

  @override
  String freeCourtsCountOther(num count) {
    return '$count lliures';
  }
}
