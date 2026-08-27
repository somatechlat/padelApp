import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ca.dart';
import 'app_localizations_en.dart';
import 'app_localizations_es.dart';
import 'app_localizations_pt.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('ca'),
    Locale('en'),
    Locale('es'),
    Locale('pt')
  ];

  /// No description provided for @appTitle.
  ///
  /// In es, this message translates to:
  /// **'Andes Pádel'**
  String get appTitle;

  /// No description provided for @appTagline.
  ///
  /// In es, this message translates to:
  /// **'Reserva tu cancha de pádel'**
  String get appTagline;

  /// No description provided for @login.
  ///
  /// In es, this message translates to:
  /// **'Iniciar sesión'**
  String get login;

  /// No description provided for @loginSubtitle.
  ///
  /// In es, this message translates to:
  /// **'Accede para reservar tu cancha'**
  String get loginSubtitle;

  /// No description provided for @email.
  ///
  /// In es, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @password.
  ///
  /// In es, this message translates to:
  /// **'Contraseña'**
  String get password;

  /// No description provided for @loginButton.
  ///
  /// In es, this message translates to:
  /// **'Entrar'**
  String get loginButton;

  /// No description provided for @noAccount.
  ///
  /// In es, this message translates to:
  /// **'¿No tienes cuenta?'**
  String get noAccount;

  /// No description provided for @registerLink.
  ///
  /// In es, this message translates to:
  /// **'Regístrate'**
  String get registerLink;

  /// No description provided for @forgotPassword.
  ///
  /// In es, this message translates to:
  /// **'¿Olvidaste tu contraseña?'**
  String get forgotPassword;

  /// No description provided for @register.
  ///
  /// In es, this message translates to:
  /// **'Crear cuenta'**
  String get register;

  /// No description provided for @registerSubtitle.
  ///
  /// In es, this message translates to:
  /// **'Completa tus datos para registrarte'**
  String get registerSubtitle;

  /// No description provided for @fullName.
  ///
  /// In es, this message translates to:
  /// **'Nombre completo'**
  String get fullName;

  /// No description provided for @phone.
  ///
  /// In es, this message translates to:
  /// **'Teléfono'**
  String get phone;

  /// No description provided for @acceptTerms.
  ///
  /// In es, this message translates to:
  /// **'Acepto los términos y condiciones'**
  String get acceptTerms;

  /// No description provided for @registerButton.
  ///
  /// In es, this message translates to:
  /// **'Crear cuenta'**
  String get registerButton;

  /// No description provided for @alreadyHaveAccount.
  ///
  /// In es, this message translates to:
  /// **'¿Ya tienes cuenta?'**
  String get alreadyHaveAccount;

  /// No description provided for @loginLink.
  ///
  /// In es, this message translates to:
  /// **'Inicia sesión'**
  String get loginLink;

  /// No description provided for @verify.
  ///
  /// In es, this message translates to:
  /// **'Verificar email'**
  String get verify;

  /// No description provided for @verifySubtitle.
  ///
  /// In es, this message translates to:
  /// **'Ingresa el código que enviamos a tu email'**
  String get verifySubtitle;

  /// No description provided for @code.
  ///
  /// In es, this message translates to:
  /// **'Código de verificación'**
  String get code;

  /// No description provided for @verifyButton.
  ///
  /// In es, this message translates to:
  /// **'Verificar'**
  String get verifyButton;

  /// No description provided for @resendCode.
  ///
  /// In es, this message translates to:
  /// **'Reenviar código'**
  String get resendCode;

  /// No description provided for @resetPassword.
  ///
  /// In es, this message translates to:
  /// **'Recuperar contraseña'**
  String get resetPassword;

  /// No description provided for @resetSubtitle.
  ///
  /// In es, this message translates to:
  /// **'Ingresa tu email y te enviaremos un código'**
  String get resetSubtitle;

  /// No description provided for @resetButton.
  ///
  /// In es, this message translates to:
  /// **'Enviar código'**
  String get resetButton;

  /// No description provided for @resetConfirm.
  ///
  /// In es, this message translates to:
  /// **'Nueva contraseña'**
  String get resetConfirm;

  /// No description provided for @resetConfirmSubtitle.
  ///
  /// In es, this message translates to:
  /// **'Ingresa el código y tu nueva contraseña'**
  String get resetConfirmSubtitle;

  /// No description provided for @confirmPassword.
  ///
  /// In es, this message translates to:
  /// **'Confirmar contraseña'**
  String get confirmPassword;

  /// No description provided for @saveButton.
  ///
  /// In es, this message translates to:
  /// **'Guardar'**
  String get saveButton;

  /// No description provided for @home.
  ///
  /// In es, this message translates to:
  /// **'Inicio'**
  String get home;

  /// No description provided for @homeWelcome.
  ///
  /// In es, this message translates to:
  /// **'Hola'**
  String get homeWelcome;

  /// No description provided for @homeSubtitle.
  ///
  /// In es, this message translates to:
  /// **'Encuentra tu cancha y reserva en segundos'**
  String get homeSubtitle;

  /// No description provided for @bookNow.
  ///
  /// In es, this message translates to:
  /// **'Reservar ahora'**
  String get bookNow;

  /// No description provided for @bookCourt.
  ///
  /// In es, this message translates to:
  /// **'Reservar cancha'**
  String get bookCourt;

  /// No description provided for @upcomingEvents.
  ///
  /// In es, this message translates to:
  /// **'Próximos eventos'**
  String get upcomingEvents;

  /// No description provided for @bookings.
  ///
  /// In es, this message translates to:
  /// **'Mis reservas'**
  String get bookings;

  /// No description provided for @noBookings.
  ///
  /// In es, this message translates to:
  /// **'No tienes reservas todavía'**
  String get noBookings;

  /// No description provided for @bookingStatus_confirmed.
  ///
  /// In es, this message translates to:
  /// **'Confirmada'**
  String get bookingStatus_confirmed;

  /// No description provided for @bookingStatus_pending.
  ///
  /// In es, this message translates to:
  /// **'Pendiente'**
  String get bookingStatus_pending;

  /// No description provided for @bookingStatus_cancelled.
  ///
  /// In es, this message translates to:
  /// **'Cancelada'**
  String get bookingStatus_cancelled;

  /// No description provided for @bookingStatus_held.
  ///
  /// In es, this message translates to:
  /// **'En espera'**
  String get bookingStatus_held;

  /// No description provided for @events.
  ///
  /// In es, this message translates to:
  /// **'Eventos'**
  String get events;

  /// No description provided for @tournaments.
  ///
  /// In es, this message translates to:
  /// **'Torneos'**
  String get tournaments;

  /// No description provided for @noEvents.
  ///
  /// In es, this message translates to:
  /// **'No hay eventos publicados'**
  String get noEvents;

  /// No description provided for @news.
  ///
  /// In es, this message translates to:
  /// **'Noticias'**
  String get news;

  /// No description provided for @registerNow.
  ///
  /// In es, this message translates to:
  /// **'Inscribirme'**
  String get registerNow;

  /// No description provided for @capacity.
  ///
  /// In es, this message translates to:
  /// **'Cupos'**
  String get capacity;

  /// No description provided for @partnerName.
  ///
  /// In es, this message translates to:
  /// **'Nombre de tu pareja'**
  String get partnerName;

  /// No description provided for @registerPending.
  ///
  /// In es, this message translates to:
  /// **'Inscripción registrada. Tu pago está pendiente de confirmación.'**
  String get registerPending;

  /// No description provided for @registerSuccess.
  ///
  /// In es, this message translates to:
  /// **'¡Inscripción confirmada!'**
  String get registerSuccess;

  /// No description provided for @alreadyRegistered.
  ///
  /// In es, this message translates to:
  /// **'Ya estás inscrito en este torneo'**
  String get alreadyRegistered;

  /// No description provided for @tournamentFull.
  ///
  /// In es, this message translates to:
  /// **'Torneo lleno'**
  String get tournamentFull;

  /// No description provided for @registrationsClosed.
  ///
  /// In es, this message translates to:
  /// **'Inscripciones cerradas'**
  String get registrationsClosed;

  /// No description provided for @free.
  ///
  /// In es, this message translates to:
  /// **'Gratis'**
  String get free;

  /// No description provided for @registered.
  ///
  /// In es, this message translates to:
  /// **'Inscrito'**
  String get registered;

  /// No description provided for @tournamentStatus_open.
  ///
  /// In es, this message translates to:
  /// **'Inscripciones abiertas'**
  String get tournamentStatus_open;

  /// No description provided for @tournamentStatus_in_progress.
  ///
  /// In es, this message translates to:
  /// **'En curso'**
  String get tournamentStatus_in_progress;

  /// No description provided for @tournamentStatus_closed.
  ///
  /// In es, this message translates to:
  /// **'Cerrado'**
  String get tournamentStatus_closed;

  /// No description provided for @tournamentStatus_finished.
  ///
  /// In es, this message translates to:
  /// **'Finalizado'**
  String get tournamentStatus_finished;

  /// No description provided for @tournamentStatus_draft.
  ///
  /// In es, this message translates to:
  /// **'Borrador'**
  String get tournamentStatus_draft;

  /// No description provided for @notifications.
  ///
  /// In es, this message translates to:
  /// **'Notificaciones'**
  String get notifications;

  /// No description provided for @noNotifications.
  ///
  /// In es, this message translates to:
  /// **'No tienes notificaciones'**
  String get noNotifications;

  /// No description provided for @markRead.
  ///
  /// In es, this message translates to:
  /// **'Marcar leída'**
  String get markRead;

  /// No description provided for @profile.
  ///
  /// In es, this message translates to:
  /// **'Perfil'**
  String get profile;

  /// No description provided for @role.
  ///
  /// In es, this message translates to:
  /// **'Rol'**
  String get role;

  /// No description provided for @language.
  ///
  /// In es, this message translates to:
  /// **'Idioma'**
  String get language;

  /// No description provided for @logout.
  ///
  /// In es, this message translates to:
  /// **'Cerrar sesión'**
  String get logout;

  /// No description provided for @logoutConfirm.
  ///
  /// In es, this message translates to:
  /// **'¿Seguro que quieres cerrar sesión?'**
  String get logoutConfirm;

  /// No description provided for @cancel.
  ///
  /// In es, this message translates to:
  /// **'Cancelar'**
  String get cancel;

  /// No description provided for @confirm.
  ///
  /// In es, this message translates to:
  /// **'Confirmar'**
  String get confirm;

  /// No description provided for @error.
  ///
  /// In es, this message translates to:
  /// **'Ocurrió un error'**
  String get error;

  /// No description provided for @networkError.
  ///
  /// In es, this message translates to:
  /// **'Error de conexión. Verifica tu internet.'**
  String get networkError;

  /// No description provided for @invalidCredentials.
  ///
  /// In es, this message translates to:
  /// **'Credenciales inválidas'**
  String get invalidCredentials;

  /// No description provided for @accountLocked.
  ///
  /// In es, this message translates to:
  /// **'Cuenta temporalmente bloqueada'**
  String get accountLocked;

  /// No description provided for @emailNotVerified.
  ///
  /// In es, this message translates to:
  /// **'Verifica tu email antes de iniciar sesión'**
  String get emailNotVerified;

  /// No description provided for @passwordMismatch.
  ///
  /// In es, this message translates to:
  /// **'Las contraseñas no coinciden'**
  String get passwordMismatch;

  /// No description provided for @fillAllFields.
  ///
  /// In es, this message translates to:
  /// **'Completa todos los campos'**
  String get fillAllFields;

  /// No description provided for @acceptTermsRequired.
  ///
  /// In es, this message translates to:
  /// **'Debes aceptar los términos'**
  String get acceptTermsRequired;

  /// No description provided for @loading.
  ///
  /// In es, this message translates to:
  /// **'Cargando...'**
  String get loading;

  /// No description provided for @retry.
  ///
  /// In es, this message translates to:
  /// **'Reintentar'**
  String get retry;

  /// No description provided for @codeSent.
  ///
  /// In es, this message translates to:
  /// **'Enviamos un código a tu email'**
  String get codeSent;

  /// No description provided for @success.
  ///
  /// In es, this message translates to:
  /// **'Operación exitosa'**
  String get success;

  /// No description provided for @sessionExpired.
  ///
  /// In es, this message translates to:
  /// **'Tu sesión expiró. Inicia sesión de nuevo.'**
  String get sessionExpired;

  /// No description provided for @stepCourt.
  ///
  /// In es, this message translates to:
  /// **'Elige cancha'**
  String get stepCourt;

  /// No description provided for @stepSchedule.
  ///
  /// In es, this message translates to:
  /// **'Fecha y hora'**
  String get stepSchedule;

  /// No description provided for @stepSummary.
  ///
  /// In es, this message translates to:
  /// **'Resumen'**
  String get stepSummary;

  /// No description provided for @stepDone.
  ///
  /// In es, this message translates to:
  /// **'Reservada'**
  String get stepDone;

  /// No description provided for @next.
  ///
  /// In es, this message translates to:
  /// **'Continuar'**
  String get next;

  /// No description provided for @back.
  ///
  /// In es, this message translates to:
  /// **'Volver'**
  String get back;

  /// No description provided for @cancelBooking.
  ///
  /// In es, this message translates to:
  /// **'Cancelar reserva'**
  String get cancelBooking;

  /// No description provided for @cancelBookingConfirm.
  ///
  /// In es, this message translates to:
  /// **'¿Cancelar esta reserva? Esta acción no se puede deshacer.'**
  String get cancelBookingConfirm;

  /// No description provided for @duration.
  ///
  /// In es, this message translates to:
  /// **'Duración'**
  String get duration;

  /// No description provided for @players.
  ///
  /// In es, this message translates to:
  /// **'Jugadores'**
  String get players;

  /// No description provided for @selectSlot.
  ///
  /// In es, this message translates to:
  /// **'Selecciona una hora disponible'**
  String get selectSlot;

  /// No description provided for @noAvailableSlots.
  ///
  /// In es, this message translates to:
  /// **'No hay horarios disponibles para esa fecha'**
  String get noAvailableSlots;

  /// No description provided for @selectDate.
  ///
  /// In es, this message translates to:
  /// **'Selecciona una fecha'**
  String get selectDate;

  /// No description provided for @price.
  ///
  /// In es, this message translates to:
  /// **'Precio'**
  String get price;

  /// No description provided for @total.
  ///
  /// In es, this message translates to:
  /// **'Total'**
  String get total;

  /// No description provided for @perHour.
  ///
  /// In es, this message translates to:
  /// **'por hora'**
  String get perHour;

  /// No description provided for @payTransfer.
  ///
  /// In es, this message translates to:
  /// **'Pagar por transferencia'**
  String get payTransfer;

  /// No description provided for @payCard.
  ///
  /// In es, this message translates to:
  /// **'Pagar con tarjeta'**
  String get payCard;

  /// No description provided for @paymentMethod.
  ///
  /// In es, this message translates to:
  /// **'Método de pago'**
  String get paymentMethod;

  /// No description provided for @paymentSuccess.
  ///
  /// In es, this message translates to:
  /// **'¡Reserva confirmada!'**
  String get paymentSuccess;

  /// No description provided for @paymentPending.
  ///
  /// In es, this message translates to:
  /// **'Reserva confirmada. Tu pago está pendiente de confirmación.'**
  String get paymentPending;

  /// No description provided for @paymentError.
  ///
  /// In es, this message translates to:
  /// **'No se pudo procesar el pago. Intenta de nuevo.'**
  String get paymentError;

  /// No description provided for @slotTaken.
  ///
  /// In es, this message translates to:
  /// **'Ese horario ya no está disponible. Elige otro.'**
  String get slotTaken;

  /// No description provided for @minPlayers.
  ///
  /// In es, this message translates to:
  /// **'Jugadores'**
  String get minPlayers;

  /// No description provided for @confirmedAt.
  ///
  /// In es, this message translates to:
  /// **'Confirmada el'**
  String get confirmedAt;

  /// No description provided for @notificationSettings.
  ///
  /// In es, this message translates to:
  /// **'Configuración de notificaciones'**
  String get notificationSettings;

  /// No description provided for @save.
  ///
  /// In es, this message translates to:
  /// **'Guardar'**
  String get save;

  /// No description provided for @bookingReminder.
  ///
  /// In es, this message translates to:
  /// **'Recordatorio de reserva'**
  String get bookingReminder;

  /// No description provided for @tournamentReminder.
  ///
  /// In es, this message translates to:
  /// **'Recordatorio de torneo'**
  String get tournamentReminder;

  /// No description provided for @tournamentConfirmed.
  ///
  /// In es, this message translates to:
  /// **'Inscripción confirmada'**
  String get tournamentConfirmed;

  /// No description provided for @payments.
  ///
  /// In es, this message translates to:
  /// **'Pagos'**
  String get payments;

  /// No description provided for @marketing.
  ///
  /// In es, this message translates to:
  /// **'Promociones y novedades'**
  String get marketing;

  /// No description provided for @channelEmail.
  ///
  /// In es, this message translates to:
  /// **'Email'**
  String get channelEmail;

  /// No description provided for @channelPush.
  ///
  /// In es, this message translates to:
  /// **'Notificaciones push'**
  String get channelPush;

  /// No description provided for @channelInApp.
  ///
  /// In es, this message translates to:
  /// **'Notificaciones en la app'**
  String get channelInApp;

  /// No description provided for @timeNow.
  ///
  /// In es, this message translates to:
  /// **'Ahora'**
  String get timeNow;

  /// No description provided for @timeAgoMinutes.
  ///
  /// In es, this message translates to:
  /// **'Hace {minutes} min'**
  String timeAgoMinutes(int minutes);

  /// No description provided for @timeAgoHours.
  ///
  /// In es, this message translates to:
  /// **'Hace {hours} h'**
  String timeAgoHours(int hours);

  /// No description provided for @timeAgoDays.
  ///
  /// In es, this message translates to:
  /// **'Hace {days} d'**
  String timeAgoDays(int days);

  /// No description provided for @timeYesterday.
  ///
  /// In es, this message translates to:
  /// **'Ayer'**
  String get timeYesterday;

  /// No description provided for @noNews.
  ///
  /// In es, this message translates to:
  /// **'No hay noticias'**
  String get noNews;

  /// No description provided for @role_cliente.
  ///
  /// In es, this message translates to:
  /// **'Cliente'**
  String get role_cliente;

  /// No description provided for @role_recepcionista.
  ///
  /// In es, this message translates to:
  /// **'Recepcionista'**
  String get role_recepcionista;

  /// No description provided for @role_gerente.
  ///
  /// In es, this message translates to:
  /// **'Gerente'**
  String get role_gerente;

  /// No description provided for @role_dueno.
  ///
  /// In es, this message translates to:
  /// **'Dueño'**
  String get role_dueno;

  /// No description provided for @role_superadmin.
  ///
  /// In es, this message translates to:
  /// **'Administrador'**
  String get role_superadmin;

  /// No description provided for @homeGreeting.
  ///
  /// In es, this message translates to:
  /// **'Hola, {name}'**
  String homeGreeting(String name);

  /// No description provided for @findYourCourt.
  ///
  /// In es, this message translates to:
  /// **'Busca tu cancha'**
  String get findYourCourt;

  /// No description provided for @seeAll.
  ///
  /// In es, this message translates to:
  /// **'Ver todo'**
  String get seeAll;

  /// No description provided for @availableCourts.
  ///
  /// In es, this message translates to:
  /// **'Canchas disponibles'**
  String get availableCourts;

  /// No description provided for @noCourtsAvailable.
  ///
  /// In es, this message translates to:
  /// **'No hay canchas disponibles en este momento'**
  String get noCourtsAvailable;

  /// No description provided for @courtType_techada.
  ///
  /// In es, this message translates to:
  /// **'Techada'**
  String get courtType_techada;

  /// No description provided for @courtType_abierta.
  ///
  /// In es, this message translates to:
  /// **'Abierta'**
  String get courtType_abierta;

  /// No description provided for @hasLighting.
  ///
  /// In es, this message translates to:
  /// **'Con iluminación'**
  String get hasLighting;

  /// No description provided for @noLighting.
  ///
  /// In es, this message translates to:
  /// **'Sin iluminación'**
  String get noLighting;

  /// No description provided for @basePrice.
  ///
  /// In es, this message translates to:
  /// **'Precio base'**
  String get basePrice;

  /// No description provided for @viewDetails.
  ///
  /// In es, this message translates to:
  /// **'Ver detalles'**
  String get viewDetails;

  /// No description provided for @reserve.
  ///
  /// In es, this message translates to:
  /// **'Reservar'**
  String get reserve;

  /// No description provided for @today.
  ///
  /// In es, this message translates to:
  /// **'Hoy'**
  String get today;

  /// No description provided for @thisWeek.
  ///
  /// In es, this message translates to:
  /// **'Esta semana'**
  String get thisWeek;

  /// No description provided for @paymentMethodSubtitle.
  ///
  /// In es, this message translates to:
  /// **'Elige cómo deseas pagar'**
  String get paymentMethodSubtitle;

  /// No description provided for @payWithCard.
  ///
  /// In es, this message translates to:
  /// **'Pagar con tarjeta'**
  String get payWithCard;

  /// No description provided for @payWithTransfer.
  ///
  /// In es, this message translates to:
  /// **'Transferencia bancaria'**
  String get payWithTransfer;

  /// No description provided for @payWithCash.
  ///
  /// In es, this message translates to:
  /// **'Efectivo en cancha'**
  String get payWithCash;

  /// No description provided for @cardDescription.
  ///
  /// In es, this message translates to:
  /// **'Débito o crédito vía Stripe'**
  String get cardDescription;

  /// No description provided for @transferDescription.
  ///
  /// In es, this message translates to:
  /// **'Realiza una transferencia y sube tu comprobante'**
  String get transferDescription;

  /// No description provided for @cashDescription.
  ///
  /// In es, this message translates to:
  /// **'Paga al llegar a la cancha'**
  String get cashDescription;

  /// No description provided for @transferInstructions.
  ///
  /// In es, this message translates to:
  /// **'Datos para transferencia'**
  String get transferInstructions;

  /// No description provided for @bankName.
  ///
  /// In es, this message translates to:
  /// **'Banco'**
  String get bankName;

  /// No description provided for @accountNumber.
  ///
  /// In es, this message translates to:
  /// **'Número de cuenta'**
  String get accountNumber;

  /// No description provided for @accountHolder.
  ///
  /// In es, this message translates to:
  /// **'Titular de la cuenta'**
  String get accountHolder;

  /// No description provided for @beneficiaryCode.
  ///
  /// In es, this message translates to:
  /// **'Código de beneficiario'**
  String get beneficiaryCode;

  /// No description provided for @transferAmount.
  ///
  /// In es, this message translates to:
  /// **'Monto a transferir'**
  String get transferAmount;

  /// No description provided for @uploadProof.
  ///
  /// In es, this message translates to:
  /// **'Subir comprobante'**
  String get uploadProof;

  /// No description provided for @uploadProofHint.
  ///
  /// In es, this message translates to:
  /// **'Tomar foto o seleccionar de galería'**
  String get uploadProofHint;

  /// No description provided for @proofUploaded.
  ///
  /// In es, this message translates to:
  /// **'Comprobante subido'**
  String get proofUploaded;

  /// No description provided for @proofPending.
  ///
  /// In es, this message translates to:
  /// **'Esperando confirmación del comprobante'**
  String get proofPending;

  /// No description provided for @transferPending.
  ///
  /// In es, this message translates to:
  /// **'Transferencia pendiente de verificación'**
  String get transferPending;

  /// No description provided for @transferConfirmed.
  ///
  /// In es, this message translates to:
  /// **'Transferencia confirmada'**
  String get transferConfirmed;

  /// No description provided for @transferRejected.
  ///
  /// In es, this message translates to:
  /// **'Transferencia rechazada'**
  String get transferRejected;

  /// No description provided for @transferRejectedReason.
  ///
  /// In es, this message translates to:
  /// **'Motivo: {reason}'**
  String transferRejectedReason(String reason);

  /// No description provided for @confirmTransfer.
  ///
  /// In es, this message translates to:
  /// **'Confirmar transferencia'**
  String get confirmTransfer;

  /// No description provided for @rejectTransfer.
  ///
  /// In es, this message translates to:
  /// **'Rechazar transferencia'**
  String get rejectTransfer;

  /// No description provided for @rejectionReason.
  ///
  /// In es, this message translates to:
  /// **'Motivo del rechazo'**
  String get rejectionReason;

  /// No description provided for @maxFileSize.
  ///
  /// In es, this message translates to:
  /// **'Tamaño máximo: 5 MB'**
  String get maxFileSize;

  /// No description provided for @allowedFormats.
  ///
  /// In es, this message translates to:
  /// **'Formatos: JPEG, PNG'**
  String get allowedFormats;

  /// No description provided for @imageTooLarge.
  ///
  /// In es, this message translates to:
  /// **'La imagen excede 5 MB'**
  String get imageTooLarge;

  /// No description provided for @invalidFormat.
  ///
  /// In es, this message translates to:
  /// **'Formato no permitido. Use JPEG o PNG'**
  String get invalidFormat;

  /// No description provided for @proofUploadSuccess.
  ///
  /// In es, this message translates to:
  /// **'Comprobante enviado correctamente'**
  String get proofUploadSuccess;

  /// No description provided for @proofUploadError.
  ///
  /// In es, this message translates to:
  /// **'Error al subir el comprobante'**
  String get proofUploadError;

  /// No description provided for @camera.
  ///
  /// In es, this message translates to:
  /// **'Cámara'**
  String get camera;

  /// No description provided for @gallery.
  ///
  /// In es, this message translates to:
  /// **'Galería'**
  String get gallery;

  /// No description provided for @send.
  ///
  /// In es, this message translates to:
  /// **'Enviar comprobante'**
  String get send;

  /// No description provided for @bookingModified.
  ///
  /// In es, this message translates to:
  /// **'Reserva modificada'**
  String get bookingModified;

  /// No description provided for @noShowPenalty.
  ///
  /// In es, this message translates to:
  /// **'Penalizacion por inasistencia'**
  String get noShowPenalty;

  /// No description provided for @tournamentRegistered.
  ///
  /// In es, this message translates to:
  /// **'Inscripcion registrada'**
  String get tournamentRegistered;

  /// No description provided for @newsPublished.
  ///
  /// In es, this message translates to:
  /// **'Noticia publicada'**
  String get newsPublished;

  /// No description provided for @durationMin.
  ///
  /// In es, this message translates to:
  /// **'min'**
  String get durationMin;

  /// No description provided for @paymentProcessing.
  ///
  /// In es, this message translates to:
  /// **'Procesando pago...'**
  String get paymentProcessing;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ca', 'en', 'es', 'pt'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ca':
      return AppLocalizationsCa();
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
    case 'pt':
      return AppLocalizationsPt();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
