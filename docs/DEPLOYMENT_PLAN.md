# DEPLOYMENT PLAN — AndesPadel

**Date:** 2026-08-26
**Two environments:** Local (dev) + Testing Server (LOYALLIA)

---

## ENVIRONMENT 1: LOCAL (Development)

### What exists
- `docker-compose.yml` — already works
- `Dockerfile.dev` — already works
- `padel/settings/dev.py` — DEBUG=True, CELERY_TASK_ALWAYS_EAGER=True

### Local Architecture
```
localhost:8000  → Django backend (runserver)
localhost:5432  → PostgreSQL
localhost:6379  → Redis
No SSL, no nginx, no domain
```

### Files (NO changes needed)
| File | Status |
|------|--------|
| `docker-compose.yml` | ✅ Already correct |
| `Dockerfile.dev` | ✅ Already correct |
| `padel/settings/dev.py` | ✅ Already correct |
| `docker/backend/secrets.py` | ✅ Dev placeholders work |

### Local Commands
```bash
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_demo  # optional
```

**Local = DONE. No changes needed.**

---

## ENVIRONMENT 2: TESTING SERVER (LOYALLIA — 140.82.15.48)

### Server Constraints
- **DO NOT** touch Loyallia containers/networks/configs
- **DO NOT** use ports 33900-33914 (Loyallia range)
- **DO NOT** use ports 80/443 on Docker (host nginx owns these)
- Nginx reload only (no restart)

### Server Architecture
```
┌──────────────── Host (140.82.15.48) ────────────────┐
│                                                       │
│  Host nginx (ports 80/443)                            │
│    └─ andespadel.yachaq.io:443 → 127.0.0.1:34003    │
│                                                       │
│  Docker: padelapp-net (isolated bridge)               │
│  ┌──────────────────────────────────────────────┐     │
│  │ db:34000      (PostgreSQL 15)                │     │
│  │ redis:34001   (Redis 7)                      │     │
│  │ backend:34002 (Django/Gunicorn)              │     │
│  │ worker         (Celery worker)                │     │
│  │ beat           (Celery beat)                  │     │
│  │ nginx:34003   (Reverse proxy)                │     │
│  └──────────────────────────────────────────────┘     │
│                                                       │
│  Loyallia containers (UNTOUCHED)                      │
│    loyallia-postgres, loyallia-redis, etc.            │
│    on loyallia_backend-net, ports 33900-33914         │
└───────────────────────────────────────────────────────┘
```

### Port Mapping
| Service     | Host Port | Container Port |
|-------------|-----------|----------------|
| PostgreSQL  | 34000     | 5432           |
| Redis       | 34001     | 6379           |
| Backend     | 34002     | 8000           |
| Nginx       | 34003     | 80             |

---

## TODO LIST — ALL CHANGES

### PHASE 1: Code Changes (Local → Push to GitHub)

- [ ] **1.1** Modify `padel/settings/prod.py`
  - Add `andespadel.yachaq.io` to ALLOWED_HOSTS
  - Add `andespadel.yachaq.io` to CORS_ALLOWED_ORIGINS
  - Fix SSL redirect: trust `X-Forwarded-Proto` header (host nginx handles SSL)

- [ ] **1.2** Create `docker/nginx/nginx.conf`
  - Reverse proxy: serve Django API
  - Serve static files from `/static/`
  - Serve media files from `/media/`
  - Upstream: `backend:8000`

- [ ] **1.3** Modify `compose.prod.yml` → rename to `compose.server.yml`
  - Add healthchecks for db and redis
  - Add `padelapp-net` network (isolated)
  - Change ports: db→34000, redis→34001, backend→34002, nginx→34003
  - Add `celery beat` service
  - Fix `POSTGRES_PASSWORD` (use variable, not hardcoded `padel_dev`)
  - Add `depends_on` with `condition: service_healthy`
  - Remove port 80:80 from nginx (use 34003:80)

- [ ] **1.4** Modify `Dockerfile.prod`
  - Add `RUN python manage.py collectstatic --noinput` before USER switch

- [ ] **1.5** Commit and push to GitHub

### PHASE 2: Server Setup (SSH — read-only first, then deploy)

- [ ] **2.1** Create `/opt/padelapp/` directory
- [ ] **2.2** Clone repo: `git clone https://github.com/somatechlat/padelApp.git /opt/padelapp`
- [ ] **2.3** Create `/opt/padelapp/docker/backend/secrets.py` with production values
  - SECRET_KEY (generated, 50+ chars)
  - DB_NAME=padel_prod, DB_USER=padel, DB_PASSWORD=(strong)
  - REDIS_URL=redis://redis:6379/0
  - EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD (SMTP)
  - STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET

### PHASE 3: SSL Certificate

- [ ] **3.1** Create placeholder nginx config for certbot webroot
- [ ] **3.2** Reload host nginx: `nginx -s reload`
- [ ] **3.3** Run certbot: `certbot certonly --webroot -w /var/www/certbot -d andespadel.yachaq.io`
- [ ] **3.4** Verify cert obtained in `/etc/letsencrypt/live/andespadel.yachaq.io/`

### PHASE 4: Build & Launch

- [ ] **4.1** Build images: `docker compose -f compose.server.yml build`
- [ ] **4.2** Start stack: `docker compose -f compose.server.yml up -d`
- [ ] **4.3** Run migrations: `docker compose -f compose.server.yml exec backend python manage.py migrate`
- [ ] **4.4** Create superuser: `docker compose -f compose.server.yml exec backend python manage.py createsuperuser`
- [ ] **4.5** Collect static: `docker compose -f compose.server.yml exec backend python manage.py collectstatic --noinput`

### PHASE 5: Host Nginx

- [ ] **5.1** Create `/etc/nginx/sites-enabled/padelapp`
  - SSL server block for `andespadel.yachaq.io`
  - Proxy to `127.0.0.1:34003`
  - SSL cert from Let's Encrypt
- [ ] **5.2** Reload host nginx: `nginx -s reload`

### PHASE 6: Verify

- [ ] **6.1** `curl -k https://andespadel.yachaq.io/api/docs/` → Swagger UI
- [ ] **6.2** `https://andespadel.yachaq.io/adminpanel/` → Admin login
- [ ] **6.3** `docker compose -f compose.server.yml ps` → all healthy
- [ ] **6.4** `docker ps | grep loyallia` → all still running
- [ ] **6.5** Test login endpoint

---

## FILES SUMMARY

### Files to MODIFY (in repo)
| File | Change |
|------|--------|
| `padel/settings/prod.py` | Add domain, fix SSL proxy |
| `Dockerfile.prod` | Add collectstatic |

### Files to CREATE (in repo)
| File | Purpose |
|------|---------|
| `docker/nginx/nginx.conf` | App reverse proxy |
| `compose.server.yml` | Server compose (based on prod.yml) |

### Files to CREATE (on server only, NOT in git)
| File | Purpose |
|------|---------|
| `/opt/padelapp/docker/backend/secrets.py` | Production secrets |
| `/etc/nginx/sites-enabled/padelapp` | Host nginx SSL |

### Files UNCHANGED
| File | Status |
|------|--------|
| `docker-compose.yml` | Local dev — works as-is |
| `Dockerfile.dev` | Local dev — works as-is |
| `padel/settings/dev.py` | Local dev — works as-is |
| `docker/backend/secrets.py` | Local dev — works as-is |
| All Loyallia files | UNTOUCHED |

---

## SECRETS NEEDED FROM YOU

Before PHASE 2, I need:

1. **SECRET_KEY** — or I generate a random 50-char key
2. **DB_PASSWORD** — or I generate a strong one
3. **SMTP credentials** — host, port, user, password
4. **Stripe keys** — `sk_live_...`, `pk_live_...`, webhook secret
   - Or use test keys for testing: `sk_test_...`, `pk_test_...`

---

## RISK MATRIX

| Risk | Impact | Mitigation |
|------|--------|------------|
| Port conflict with Loyallia | High | Use 34000-34003 (Loyallia: 33900-33914) |
| Nginx restart disrupts Loyallia | High | Use `nginx -s reload` (graceful) |
| SSL cert failure | Medium | DNS already resolves; webroot method |
| DB data loss | Medium | Use Docker named volume (persists) |
| Docker network overlap | Low | Use dedicated `padelapp-net` |
| Disk exhaustion | Low | 36GB free; stack uses ~2-3GB |

---

## STATUS: AWAITING APPROVAL

Once approved, I will execute all phases in order.
