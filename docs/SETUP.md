# Guía de configuración — TikTok Content Posting API

Fecha: 2026-09-30 · Proyecto: Proyectos AI / TikTok API Publisher

## Paso 1 — Crear la app (Harold, en el navegador)

1. Abrir https://developers.tiktok.com e iniciar sesión **con la cuenta de TikTok donde se va a publicar primero** (Honey and Seduction o Encomiendas Express).
2. Entrar a **Manage apps → Connect an app**.
3. Nombre de la app: `Conecta AI Publisher`.
4. Agregar productos: **Login Kit** y **Content Posting API** (activar la opción **Direct Post**).
5. En la configuración del Login Kit, registrar este Redirect URI **exacto**:
   `http://localhost:8723/callback`
6. En scopes, pedir: `user.info.basic`, `video.upload`, `video.publish`.
7. Guardar. Copiar el **Client Key** y el **Client Secret** al Secure Vault (nunca en el chat ni en archivos del repo).

Estado: ⏳ pendiente (2026-09-30).

## Paso 2 — Autorización OAuth (una vez por cuenta de TikTok)

En la máquina donde corren los scripts:

```bash
cd tiktok-api
cp .env.example .env   # completar TIKTOK_CLIENT_KEY y TIKTOK_CLIENT_SECRET
python3 scripts/tiktok_oauth.py
```

- Se abre el navegador con la pantalla de consentimiento de TikTok. Aprobarla.
- Los tokens se guardan en `scripts/tokens/<open_id>.json` (permisos 600, fuera del repo).
- El `access_token` dura ~24 h y el `refresh_token` ~365 días; el refresco es automático desde entonces.
- Repetir por cada cuenta (H&S, EEX, cada cliente): cada una autoriza una vez.

Estado: ⏳ pendiente.

## Paso 3 — Video de prueba (privado)

```bash
python3 scripts/tiktok_publish.py prueba.mp4 "Prueba de publicación automática #test"
```

- Con `TIKTOK_PRIVACY=SELF_ONLY` (valor por defecto) el video queda **privado** en el perfil: confirma que el flujo funciona sin exponer nada.
- El script muestra el `publish_id` y el estado hasta `PUBLISH_COMPLETE`.

Estado: ⏳ pendiente.

## Paso 4 — Auditoría de TikTok (para publicar en público)

Sin auditoría aprobada, todo sale en privado. Requisitos:

- **Política de privacidad** en una URL pública HTTPS (se publica en conecthn.com — hosting Namecheap ya disponible).
- **Video demo** mostrando el flujo completo de publicación (se graba cuando el paso 3 funcione).
- **Descripción del uso de datos**: qué datos se piden (perfil básico, subida y publicación de video) y para qué.
- La app opera bajo **Conecta US LLC** (entidad comercial de EE. UU.).

Tiempo estimado: 5–10 días hábiles. Se solicita desde el portal de desarrollador (Submit for audit).

Estado: ⏳ pendiente.

## Paso 5 — Producción

1. Auditoría aprobada → cambiar en `.env`: `TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE`.
2. Programar publicaciones con cron (ejemplo: todos los días 10:00 AM):
   `0 10 * * * cd /ruta/tiktok-api && python3 scripts/tiktok_publish.py /ruta/video.mp4 "caption" >> log.txt 2>&1`
3. Dónde corre: Dell OptiPlex (plataforma Hermes) o la VM de Zbot.

Estado: ⏳ pendiente.

## Costos

$0. La API, la app, la auditoría y los tokens son gratis. El único "costo" es el trámite de la auditoría (días de espera). Alternativas de terceros con suscripción (Zernio, Post for Me, ~$10+/mes) no se necesitan.

## Problemas comunes

| Error | Causa | Solución |
|---|---|---|
| `redirect_uri_mismatch` | El URI registrado no es idéntico al usado | Debe ser exactamente `http://localhost:8723/callback` en ambos lados |
| `scope_not_authorized` | Falta la auditoría o el scope no se pidió | Pedir los 3 scopes en el paso 1; completar la auditoría |
| `url_ownership_unverified` | Solo aplica a `PULL_FROM_URL` | Nosotros subimos archivo (`FILE_UPLOAD`), no aplica |
| Videos en privado | App sin auditar | Normal hasta el paso 4; `SELF_ONLY` es lo esperado |
| `invalid_grant` al refrescar | Refresh token vencido (>365 días) o revocado | Repetir el paso 2 |

## Registro de cambios

- 2026-09-30: creada la estructura del proyecto y la documentación. App de TikTok pendiente de creación por Harold.
