"""HTML transactional emails for Andes Pádel (Spanish-first).

Brand palette (same as landing + Flutter app):
  Midnight Blue #002F48 · Celeste #3571B8 · Verde Limón #CEDC29
  Soft lime #E8EFB0 · Background #F5F7FA · Muted #5B6472
"""

from html import escape as html_escape

from django.conf import settings
from django.core import signing
from django.urls import reverse

from apps.verification.models import CODE_TTL

BRAND = "#002F48"
BRAND_DEEP = "#001A2A"
BRAND_LIGHT = "#3571B8"
ACCENT = "#CEDC29"
ACCENT_SOFT = "#E8EFB0"
BG = "#F5F7FA"
SURFACE = "#FFFFFF"
MUTED = "#5B6472"
OUTLINE = "#D8DEE6"

# Real club data from landing/index.html — keep in sync with the website.
CLUB_CITY = "Quito, Ecuador"
CLUB_ADDRESS = "Rodríguez Labandera y Ernesto Albán esquina"
CLUB_HOURS = "Lunes a Domingo · 08:00 – 22:00"
CLUB_WHATSAPP = "099 267 6842"
CLUB_WHATSAPP_URL = "https://wa.me/593992676842"
CLUB_EMAIL = "andespadelclub@gmail.com"
CLUB_INSTAGRAM = "@andespadelec"
CLUB_INSTAGRAM_URL = "https://instagram.com/andespadelec"
CLUB_MAPS_URL = "https://maps.google.com/?q=Rodriguez+Labandera+y+Ernesto+Alban+Quito+Ecuador"
CLUB_SITE = "https://app.andespadelclub.com"
CLUB_PRIVACY = "https://app.andespadelclub.com/privacy"

SALT_VERIFY = "andes.email-verify"
SALT_RESET = "andes.password-reset"

# Display name on every transactional email (From: Andes Pádel <...>)
FROM_NAME = "Andes Pádel"


def from_email() -> str:
    addr = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "reservas@andespadelclub.com"
    if "<" in addr:
        return addr
    return f"{FROM_NAME} <{addr}>"


def make_token(user_id: int, code: str, purpose: str) -> str:
    salt = SALT_VERIFY if purpose == "email_verify" else SALT_RESET
    return signing.dumps({"u": user_id, "c": code, "p": purpose}, salt=salt)


def read_token(token: str, purpose: str) -> dict | None:
    salt = SALT_VERIFY if purpose == "email_verify" else SALT_RESET
    # Single source of truth: the signed link lives exactly as long as the
    # verification code it carries. Letting these drift meant a 24h link
    # against a 15-minute code.
    max_age = int(CODE_TTL.total_seconds())
    try:
        data = signing.loads(token, salt=salt, max_age=max_age)
    except signing.BadSignature:
        return None
    if data.get("p") != purpose:
        return None
    return data


def _verify_url(token: str) -> str:
    path = reverse("users:verify-link")
    return f"{settings.SITE_BASE_URL}{path}?token={token}"


def _reset_url(token: str) -> str:
    path = reverse("users:password-reset-confirm-page")
    return f"{settings.SITE_BASE_URL}{path}?token={token}"


def _layout(body: str, title: str) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="width:100%;max-width:560px;background:{SURFACE};border-radius:16px;overflow:hidden;border:1px solid {OUTLINE};">

          <!-- Header -->
          <tr>
            <td style="background:{BRAND};padding:28px 32px;">
              <div style="font-size:22px;font-weight:800;color:#FFFFFF;letter-spacing:0.3px;">
                Andes <span style="color:{ACCENT};">Pádel</span>
              </div>
              <div style="margin-top:6px;font-size:13px;color:#B7C5CE;letter-spacing:0.4px;">
                Club de pádel · Quito, Ecuador · {CLUB_HOURS}
              </div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              {body}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 32px 28px;border-top:1px solid {OUTLINE};background:{BG};">
              <div style="font-size:12px;color:{MUTED};line-height:1.75;">
                <strong style="color:{BRAND};">Andes Pádel Club</strong><br>
                {CLUB_ADDRESS}<br>
                {CLUB_CITY} · {CLUB_HOURS}<br>
                WhatsApp
                <a href="{CLUB_WHATSAPP_URL}" style="color:{BRAND_LIGHT};text-decoration:underline;">{CLUB_WHATSAPP}</a>
                &nbsp;·&nbsp;
                <a href="mailto:{CLUB_EMAIL}" style="color:{BRAND_LIGHT};text-decoration:underline;">{CLUB_EMAIL}</a><br>
                <a href="{CLUB_INSTAGRAM_URL}" style="color:{BRAND_LIGHT};text-decoration:underline;">Instagram {CLUB_INSTAGRAM}</a>
                &nbsp;·&nbsp;
                <a href="{CLUB_MAPS_URL}" style="color:{BRAND_LIGHT};text-decoration:underline;">Cómo llegar</a>
                &nbsp;·&nbsp;
                <a href="{CLUB_SITE}" style="color:{BRAND_LIGHT};text-decoration:underline;">app.andespadelclub.com</a>
              </div>
              <div style="margin-top:14px;font-size:12px;color:{MUTED};line-height:1.7;">
                Estás recibiendo este correo porque se creó una cuenta o se solicitó un cambio
                con tu dirección en Andes Pádel.<br>
                <a href="{CLUB_PRIVACY}" style="color:{BRAND_LIGHT};text-decoration:underline;">Política de privacidad</a>
                &nbsp;·&nbsp;
                <a href="{CLUB_PRIVACY}" style="color:{BRAND_LIGHT};text-decoration:underline;">Términos del servicio</a>
                &nbsp;·&nbsp;
                <a href="mailto:{CLUB_EMAIL}" style="color:{BRAND_LIGHT};text-decoration:underline;">Soporte</a>
              </div>
              <div style="margin-top:12px;font-size:11px;color:#8A96A3;">
                Si no solicitaste este correo, puedes ignorarlo con seguridad.
                Nunca pedimos tu contraseña por correo.
              </div>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _button(url: str, label: str) -> str:
    return f"""
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:8px 0 20px;">
  <tr>
    <td style="background:{ACCENT};border-radius:12px;">
      <a href="{url}" style="display:inline-block;padding:16px 32px;font-size:16px;font-weight:700;color:{BRAND_DEEP};text-decoration:none;border-radius:12px;">
        {label}
      </a>
    </td>
  </tr>
</table>"""


def _code_box(code: str) -> str:
    spaced = " ".join(code)
    return f"""
<div style="background:{ACCENT_SOFT};border:1px solid {OUTLINE};border-radius:12px;padding:18px;text-align:center;margin:8px 0 18px;">
  <div style="font-size:12px;color:{MUTED};letter-spacing:0.6px;text-transform:uppercase;margin-bottom:8px;">
    Código de verificación
  </div>
  <div style="font-size:32px;font-weight:800;color:{BRAND};letter-spacing:8px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;">
    {spaced}
  </div>
</div>"""


def _steps(items: list[str]) -> str:
    rows = "".join(
        f'<li style="margin:0 0 10px;color:{BRAND};font-size:15px;line-height:1.55;">{i}</li>'
        for i in items
    )
    return f'<ol style="margin:0 0 18px;padding-left:20px;">{rows}</ol>'


def verification_email_html(user, code: str, token: str) -> tuple[str, str]:
    """Return (subject, html_body). One-click link is primary; code is backup."""
    url = _verify_url(token)
    name = html_escape(user.first_name or "jugador")
    body = f"""
      <div style="font-size:13px;color:{MUTED};letter-spacing:0.5px;text-transform:uppercase;font-weight:700;">
        Verificación de cuenta
      </div>
      <h1 style="margin:10px 0 16px;font-size:26px;line-height:1.25;color:{BRAND};font-weight:800;">
        ¡Hola, {name}! Confirma tu correo
      </h1>
      <p style="margin:0 0 12px;font-size:15px;color:{BRAND};line-height:1.65;">
        Gracias por registrarte en <strong>Andes Pádel</strong>. Para activar tu cuenta
        y reservar canchas, solo falta un paso.
      </p>

      <div style="background:{BG};border-left:4px solid {ACCENT};border-radius:0 12px 12px 0;padding:16px 18px;margin:0 0 8px;">
        <div style="font-size:15px;font-weight:700;color:{BRAND};margin-bottom:8px;">
          Cómo activar tu cuenta
        </div>
        {_steps([
            'Haz clic en el botón <strong>«Verificar mi cuenta»</strong> de abajo.',
            'Listo: tu cuenta queda activa y puedes iniciar sesión en la app.',
        ])}
        <p style="margin:0;font-size:13px;color:{MUTED};line-height:1.6;">
          El botón es de un solo uso y expira en <strong>15 minutos</strong>.
          Si el botón no abre el navegador, copia este enlace en tu navegador:
        </p>
        <p style="margin:8px 0 0;word-break:break-all;font-size:12px;">
          <a href="{url}" style="color:{BRAND_LIGHT};text-decoration:underline;">{url}</a>
        </p>
      </div>

      {_button(url, "Verificar mi cuenta")}

      <p style="margin:0 0 8px;font-size:14px;color:{MUTED};line-height:1.6;">
        ¿Prefieres el código manual? Ábrelo en la app y escribe estos 6 dígitos
        en la pantalla de verificación:
      </p>
      {_code_box(code)}

      <div style="background:{BG};border:1px solid {OUTLINE};border-radius:12px;padding:16px 18px;margin:8px 0 4px;">
        <div style="font-size:13px;font-weight:700;color:{BRAND};margin-bottom:8px;">
          Tu privacidad
        </div>
        <p style="margin:0;font-size:13px;color:{MUTED};line-height:1.65;">
          Usamos tu correo solo para iniciar sesión, enviarte códigos de seguridad
          y avisos de tus reservas. No vendemos tus datos.
          Consulta la
          <a href="{CLUB_PRIVACY}" style="color:{BRAND_LIGHT};text-decoration:underline;">política de privacidad</a>
          y los
          <a href="{CLUB_PRIVACY}" style="color:{BRAND_LIGHT};text-decoration:underline;">términos del servicio</a>.
        </p>
      </div>

      <div style="margin:18px 0 4px;font-size:12px;color:{MUTED};line-height:1.7;">
        <strong style="color:{BRAND};">Andes Pádel Club</strong> · {CLUB_CITY}<br>
        {CLUB_ADDRESS} · {CLUB_HOURS}<br>
        WhatsApp {CLUB_WHATSAPP} · {CLUB_EMAIL} · {CLUB_INSTAGRAM}
      </div>
    """
    return "Verifica tu cuenta · Andes Pádel", _layout(body, "Verifica tu cuenta · Andes Pádel")


def password_reset_email_html(user, code: str, token: str) -> tuple[str, str]:
    url = _reset_url(token)
    name = html_escape(user.first_name or "jugador")
    body = f"""
      <div style="font-size:13px;color:{MUTED};letter-spacing:0.5px;text-transform:uppercase;font-weight:700;">
        Seguridad de la cuenta
      </div>
      <h1 style="margin:10px 0 16px;font-size:26px;line-height:1.25;color:{BRAND};font-weight:800;">
        Restablece tu contraseña
      </h1>
      <p style="margin:0 0 12px;font-size:15px;color:{BRAND};line-height:1.65;">
        Hola, {name}: recibimos una solicitud para cambiar la contraseña de tu cuenta
        en <strong>Andes Pádel</strong>.
      </p>

      {_button(url, "Crear nueva contraseña")}

      <p style="margin:0 0 8px;font-size:14px;color:{MUTED};line-height:1.6;">
        O introduce este código en la app:
      </p>
      {_code_box(code)}

      <p style="margin:0;font-size:13px;color:{MUTED};line-height:1.65;">
        El enlace y el código expiran en <strong>15 minutos</strong>.
        Si no solicitaste este cambio,
        <a href="mailto:{CLUB_EMAIL}" style="color:{BRAND_LIGHT};text-decoration:underline;">avísanos</a>
        ({CLUB_WHATSAPP}) y revisa la
        <a href="{CLUB_PRIVACY}" style="color:{BRAND_LIGHT};text-decoration:underline;">política de privacidad</a>.
      </p>

      <div style="margin:18px 0 4px;font-size:12px;color:{MUTED};line-height:1.7;">
        <strong style="color:{BRAND};">Andes Pádel Club</strong> · {CLUB_CITY}<br>
        {CLUB_ADDRESS} · {CLUB_HOURS}<br>
        WhatsApp {CLUB_WHATSAPP} · {CLUB_EMAIL} · {CLUB_INSTAGRAM}
      </div>
    """
    return "Restablece tu contraseña · Andes Pádel", _layout(
        body, "Restablece tu contraseña · Andes Pádel"
    )


def password_reset_form_html(token: str, error: str | None = None) -> str:
    """Real form: user must type a new password. Nothing is changed until POST."""
    err = ""
    if error:
        err = (
            f'<div style="background:#FDECEA;border:1px solid #D32F2F;color:#D32F2F;'
            f'border-radius:12px;padding:12px 14px;margin:0 0 16px;font-size:14px;">{error}</div>'
        )
    safe_token = html_escape(token)
    return f"""\
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nueva contraseña · Andes Pádel</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="width:100%;max-width:480px;background:{SURFACE};border-radius:16px;border:1px solid {OUTLINE};overflow:hidden;">
          <tr>
            <td style="background:{BRAND};padding:24px 28px;">
              <div style="font-size:20px;font-weight:800;color:#FFFFFF;">
                Andes <span style="color:{ACCENT};">Pádel</span>
              </div>
              <div style="margin-top:6px;font-size:13px;color:#B7C5CE;">Restablecer contraseña</div>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 28px;">
              <h1 style="margin:0 0 10px;font-size:24px;color:{BRAND};font-weight:800;">
                Elige tu nueva contraseña
              </h1>
              <p style="margin:0 0 20px;font-size:15px;color:{MUTED};line-height:1.6;">
                Escribe una contraseña nueva para tu cuenta.
                Mínimo 8 caracteres. Este cambio solo se guarda cuando la envías.
              </p>
              {err}
              <form method="post" action="" autocomplete="on">
                <input type="hidden" name="token" value="{safe_token}">
                <label style="display:block;font-size:13px;font-weight:700;color:{BRAND};margin-bottom:6px;">
                  Nueva contraseña
                </label>
                <input type="password" name="password" required minlength="8" autocomplete="new-password"
                  style="width:100%;box-sizing:border-box;padding:14px;border:1px solid {OUTLINE};border-radius:12px;font-size:16px;margin-bottom:16px;">
                <label style="display:block;font-size:13px;font-weight:700;color:{BRAND};margin-bottom:6px;">
                  Repite la contraseña
                </label>
                <input type="password" name="password2" required minlength="8" autocomplete="new-password"
                  style="width:100%;box-sizing:border-box;padding:14px;border:1px solid {OUTLINE};border-radius:12px;font-size:16px;margin-bottom:24px;">
                <button type="submit"
                  style="width:100%;padding:16px;background:{ACCENT};color:{BRAND_DEEP};font-size:16px;font-weight:700;border:none;border-radius:12px;cursor:pointer;">
                  Guardar contraseña
                </button>
              </form>
              <p style="margin:20px 0 0;font-size:13px;color:{MUTED};line-height:1.6;">
                ¿Prefieres la app? Abre Andes Pádel → «¿Olvidaste tu contraseña?»
                e introduce el código de 6 dígitos de este correo.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 28px 24px;border-top:1px solid {OUTLINE};text-align:center;">
              <div style="font-size:12px;color:{MUTED};">
                {CLUB_ADDRESS} · {CLUB_CITY} · {CLUB_HOURS}<br>
                <a href="{CLUB_WHATSAPP_URL}" style="color:{BRAND_LIGHT};text-decoration:underline;">WhatsApp {CLUB_WHATSAPP}</a>
                &nbsp;·&nbsp;
                <a href="mailto:{CLUB_EMAIL}" style="color:{BRAND_LIGHT};text-decoration:underline;">{CLUB_EMAIL}</a>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def verify_confirm_form_html(token: str) -> str:
    """Confirm page: user must POST the token. Mail scanners that prefetch a
    GET therefore cannot verify the account. Spanish copy, brand layout."""
    safe_token = html_escape(token)
    return f"""\
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Confirma tu cuenta · Andes Pádel</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="width:100%;max-width:480px;background:{SURFACE};border-radius:16px;border:1px solid {OUTLINE};overflow:hidden;">
          <tr>
            <td style="background:{BRAND};padding:24px 28px;">
              <div style="font-size:20px;font-weight:800;color:#FFFFFF;">
                Andes <span style="color:{ACCENT};">Pádel</span>
              </div>
              <div style="margin-top:6px;font-size:13px;color:#B7C5CE;">Verificación de cuenta</div>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 28px;">
              <h1 style="margin:0 0 10px;font-size:24px;color:{BRAND};font-weight:800;">
                Confirma tu correo
              </h1>
              <p style="margin:0 0 20px;font-size:15px;color:{MUTED};line-height:1.6;">
                Pulsa el botón para activar tu cuenta en Andes Pádel.
                La verificación solo se realiza cuando la confirmas — abrir
                este enlace no activa la cuenta por sí solo.
              </p>
              <form id="vf" method="post" action="">
                <input type="hidden" name="token" value="{safe_token}">
                <button type="submit"
                  style="width:100%;padding:16px;background:{ACCENT};color:{BRAND_DEEP};font-size:16px;font-weight:700;border:none;border-radius:12px;cursor:pointer;">
                  Verificar mi cuenta
                </button>
              </form>
              <script>document.getElementById('vf').submit();</script>
              <noscript>
                <p style="margin:12px 0 0;font-size:13px;color:{MUTED};">
                  Si no se confirma solo, pulsa el botón «Verificar mi cuenta».
                </p>
              </noscript>
              <p style="margin:20px 0 0;font-size:13px;color:{MUTED};line-height:1.6;">
                El enlace expira en <strong>15 minutos</strong> y solo puede usarse una vez.
                ¿Prefieres la app? Introduce el código de 6 dígitos del correo
                en la pantalla de verificación.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 28px 24px;border-top:1px solid {OUTLINE};text-align:center;">
              <div style="font-size:12px;color:{MUTED};">
                {CLUB_ADDRESS} · {CLUB_CITY} · {CLUB_HOURS}<br>
                <a href="{CLUB_WHATSAPP_URL}" style="color:{BRAND_LIGHT};text-decoration:underline;">WhatsApp {CLUB_WHATSAPP}</a>
                &nbsp;·&nbsp;
                <a href="mailto:{CLUB_EMAIL}" style="color:{BRAND_LIGHT};text-decoration:underline;">{CLUB_EMAIL}</a>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def success_page_html(title: str, message: str, next_url: str = CLUB_SITE) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:48px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="width:100%;max-width:480px;background:{SURFACE};border-radius:16px;border:1px solid {OUTLINE};overflow:hidden;">
          <tr>
            <td style="background:{BRAND};padding:24px 28px;">
              <div style="font-size:20px;font-weight:800;color:#FFFFFF;">
                Andes <span style="color:{ACCENT};">Pádel</span>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:36px 28px;text-align:center;">
              <div style="width:64px;height:64px;margin:0 auto 18px;border-radius:50%;background:{ACCENT_SOFT};line-height:64px;font-size:30px;color:{BRAND};">✓</div>
              <h1 style="margin:0 0 12px;font-size:24px;color:{BRAND};font-weight:800;">{title}</h1>
              <p style="margin:0 0 24px;font-size:15px;color:{MUTED};line-height:1.65;">{message}</p>
              <a href="{next_url}" style="display:inline-block;padding:14px 28px;background:{ACCENT};color:{BRAND_DEEP};font-weight:700;font-size:15px;text-decoration:none;border-radius:12px;">
                Abrir Andes Pádel
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 28px 24px;border-top:1px solid {OUTLINE};text-align:center;">
              <div style="font-size:12px;color:{MUTED};">
                {CLUB_ADDRESS} · {CLUB_CITY} · {CLUB_HOURS}<br>
                <a href="{CLUB_WHATSAPP_URL}" style="color:{BRAND_LIGHT};text-decoration:underline;">WhatsApp {CLUB_WHATSAPP}</a>
                &nbsp;·&nbsp;
                <a href="mailto:{CLUB_EMAIL}" style="color:{BRAND_LIGHT};text-decoration:underline;">{CLUB_EMAIL}</a>
                &nbsp;·&nbsp;
                <a href="{CLUB_PRIVACY}" style="color:{BRAND_LIGHT};text-decoration:underline;">Privacidad</a>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
