# Arquitectura — TikTok API Publisher

## Componentes

```
tiktok-api/
├── README.md
├── .env.example            # plantilla (sin secretos)
├── .gitignore
├── docs/
│   ├── SETUP.md            # guía paso a paso + registro de estado
│   └── ARQUITECTURA.md     # este archivo
└── scripts/
    ├── tiktok_oauth.py     # autorización única: servidor local temporal → tokens
    ├── tiktok_tokens.py    # almacenamiento + refresco automático de tokens
    ├── tiktok_publish.py   # Direct Post: init → subida por partes → status
    └── tokens/             # git-ignored: <open_id>.json por cuenta
```

Solo librería estándar de Python 3. Sin dependencias externas (`requirements.txt` vacío a propósito).

## Flujo de publicación (Direct Post, FILE_UPLOAD)

1. `POST /v2/post/publish/video/init/` — se envía `post_info` (caption, `privacy_level`,
   flags de duet/comment/stitch) y `source_info` (tamaño del video, tamaño de parte,
   cantidad de partes). Responde con `upload_url` y `publish_id`.
2. `PUT <upload_url>` por partes — cada parte con `Content-Range: bytes <inicio>-<fin>/<total>`.
3. `POST /v2/post/publish/status/fetch/` con el `publish_id` — se sondea hasta `PUBLISH_COMPLETE`.

## Ciclo de vida de tokens

```
código OAuth (10 min)
  → access_token (24 h) + refresh_token (365 días)
  → refresco automático 1 h antes de vencer (cada refresh rota el refresh_token
     y reescribe el archivo)
```

- `tiktok_oauth.py`: levanta `http://127.0.0.1:8723/callback`, abre el consentimiento de TikTok,
  captura el `code`, lo intercambia por tokens y los guarda con permisos 600.
- `tiktok_tokens.py`: `get_access_token()` refresca solo cuando hace falta.
- Los tokens viven **uno por cuenta** (`tokens/<open_id>.json`): H&S, EEX y cada cliente
  autorizan la misma app una vez.

## Programación

La API publica **al momento** (no tiene programación diferida nativa).
La programación se logra disparando `tiktok_publish.py` a la hora deseada con cron.

- Dónde corre: Dell OptiPlex (plataforma Hermes) o la VM de Zbot.
- Límite: ~15 videos/día por cuenta → el programador reparte la cuota entre cuentas/clientes.
- Refresco de tokens: no necesita cron aparte; ocurre dentro de cada ejecución.

## Seguridad

- `.env` y `scripts/tokens/` están en `.gitignore`: jamás se suben al repo.
- `Client Secret` y tokens solo en Secure Vault / KeePass.
- Archivos de tokens con permiso 600.
- En auditoría: política de privacidad pública + video demo del flujo.

## Multi-cliente (cómo lo usa Conecta AI)

Una sola app de TikTok, N cuentas autorizadas (una por cliente).
Cada publicación indica la cuenta (`TIKTOK_OPEN_ID` o detección automática si hay una sola).
A futuro: cola central con cuotas por cliente y registro de publicaciones por cliente.
