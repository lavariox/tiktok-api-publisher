# TikTok API Publisher

Proyecto general de infraestructura (**Proyectos AI**), configurado con IA — no es proyecto de un cliente.
Publicación automática de videos en TikTok desde la IA, con la Content Posting API oficial de TikTok.

Automatic TikTok video publishing from AI, using TikTok's official Content Posting API.

---

## 🇪🇸 Español

### Qué es

Integración oficial con TikTok para publicar videos (**Direct Post**) desde scripts, sin subir nada a mano.
Lo usa Conecta AI para publicar por Honey and Seduction, Encomiendas Express y futuros clientes, pero el proyecto en sí es de infraestructura general.

### Estado (2026-09-30)

- [ ] App creada en developers.tiktok.com (`Conecta AI Publisher`)
- [ ] Productos: Login Kit + Content Posting API (Direct Post)
- [ ] Redirect URI registrado: `http://localhost:8723/callback`
- [ ] Scopes: `user.info.basic`, `video.upload`, `video.publish`
- [ ] OAuth inicial completado (tokens guardados)
- [ ] Video de prueba publicado (privado)
- [ ] Auditoría de TikTok aprobada → publicaciones públicas

Detalle paso a paso en [docs/SETUP.md](docs/SETUP.md).

### Uso rápido

```bash
cp .env.example .env   # completar TIKTOK_CLIENT_KEY y TIKTOK_CLIENT_SECRET
python3 scripts/tiktok_oauth.py                        # autorización única por cuenta
python3 scripts/tiktok_publish.py video.mp4 "caption con #hashtags"
```

### Cómo funciona

1. **OAuth2** — autorización única por cuenta de TikTok; `tiktok_oauth.py` levanta un servidor local temporal para capturar el código.
2. **Tokens** — `tiktok_tokens.py` guarda `access_token` (24 h) y `refresh_token` (365 días) en `scripts/tokens/<open_id>.json` (nunca se sube al repo) y refresca automáticamente antes de que venzan.
3. **Publicación** — `tiktok_publish.py` usa Direct Post con `FILE_UPLOAD` (subida por partes) y verifica el estado hasta `PUBLISH_COMPLETE`.
4. **Programación** — la API publica al momento; la programación se logra disparando el script a la hora deseada (cron en la OptiPlex / plataforma Hermes).

Ver [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

### Límites

- ~15 videos/día por cuenta de TikTok.
- Sin auditoría aprobada, todo sale en privado (`SELF_ONLY`).
- `TIKTOK_PRIVACY=SELF_ONLY` hasta pasar la auditoría; después `PUBLIC_TO_EVERYONE`.

### Secretos

Nunca se suben al repo: `.env`, `scripts/tokens/` (ver `.gitignore`).
Las credenciales viven en el Secure Vault / KeePass de Harold.

### Cuentas

Cada cuenta de TikTok (H&S, EEX, clientes) autoriza la app una vez con `tiktok_oauth.py`.
Los tokens se guardan separados por `open_id`; `tiktok_publish.py` usa `TIKTOK_OPEN_ID` o detecta la cuenta automáticamente si hay una sola.

> **Nota de organización:** este repo vive temporalmente en la cuenta `lavariox`.
> Cuando se cree la organización `conecta-us-llc` (casa comercial de Conecta AI), se transfiere ahí.

---

## 🇬🇧 English

Official TikTok integration for publishing videos (**Direct Post**) from scripts — no manual uploads.
A general **Proyectos AI** infrastructure project (not a client project), configured with AI and used by Conecta AI for Honey and Seduction, Encomiendas Express, and future clients.

- **Setup:** create the app at developers.tiktok.com (`Conecta AI Publisher`), add Login Kit + Content Posting API products, register redirect URI `http://localhost:8723/callback`, request scopes `user.info.basic`, `video.upload`, `video.publish`.
- **Auth:** `python3 scripts/tiktok_oauth.py` (one-time per TikTok account; tokens auto-refresh).
- **Publish:** `python3 scripts/tiktok_publish.py video.mp4 "caption with #hashtags"`.
- **Limits:** ~15 videos/day per account. Until TikTok approves the app audit, everything posts private (`SELF_ONLY`); set `TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE` after approval.
- **Secrets:** `.env` and `scripts/tokens/` are git-ignored; credentials live in Harold's Secure Vault / KeePass.
- Full step-by-step guide: [docs/SETUP.md](docs/SETUP.md) · Architecture: [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).
