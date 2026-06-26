# Despliegue Del Backend En Cloud Run

## Archivos agregados

- `Dockerfile`: contenedor del backend para Cloud Run.
- `.dockerignore`: reduce el contexto de build y evita incluir secretos.
- `cloudrun.env.example.yaml`: plantilla de variables para Cloud Run.
- `.github/workflows/ci.yml`: validaciones automáticas antes de desplegar.
- `.github/workflows/cd-cloud-run.yml`: despliegue automático a Cloud Run cuando `CI` pasa en `main`.

## Variables necesarias

Cloud Run debe tener estas variables:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `GEMINI_API_KEY`
- `APP_NAME`
- `DEBUG`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `CORS_ALLOW_ORIGINS`
- `CORS_ALLOW_ORIGIN_REGEX`

Para produccion normal:

- `DEBUG="False"`
- `CORS_ALLOW_ORIGINS="https://tu-frontend.vercel.app"`
- `CORS_ALLOW_ORIGIN_REGEX=""`

## Preparar el archivo de entorno

1. Copia `cloudrun.env.example.yaml` a `cloudrun.env.yaml`.
2. Reemplaza todos los placeholders por tus valores reales.
3. No subas `cloudrun.env.yaml`; ya esta ignorado por Git.

## APIs de GCP que debes activar

- `run.googleapis.com`
- `cloudbuild.googleapis.com`
- `artifactregistry.googleapis.com`
- `secretmanager.googleapis.com`
- `iamcredentials.googleapis.com`
- `sts.googleapis.com`

## Comando de despliegue

```bash
gcloud run deploy festio-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --port 8080 \
  --env-vars-file cloudrun.env.yaml
```

## GitHub Actions

Para que el despliegue automático funcione, configura en GitHub:

- Secrets:
  - `GCP_WORKLOAD_IDENTITY_PROVIDER`
  - `GCP_SERVICE_ACCOUNT_EMAIL`
- Variables:
  - `GCP_PROJECT_ID`
  - `GCP_REGION`
  - `ARTIFACT_REGISTRY_REPO`
  - `CLOUD_RUN_SERVICE`
  - `CLOUD_RUN_RUNTIME_SA`
  - `CLOUD_RUN_MEMORY`
  - `CLOUD_RUN_CPU`
  - `CLOUD_RUN_MIN_INSTANCES`
  - `CLOUD_RUN_MAX_INSTANCES`
  - `CORS_ALLOW_ORIGINS`
  - `CORS_ALLOW_ORIGIN_REGEX`

Los secretos de aplicación deben vivir en `Secret Manager` y el workflow de CD los inyecta con `--set-secrets`.

## Verificacion posterior

1. Abre la URL del servicio y verifica `GET /`.
2. Verifica `GET /docs`.
3. Prueba desde el frontend desplegado una llamada real al backend.
4. Confirma que no haya errores de CORS en el navegador.

## Migraciones y seed

Ejecuta estos comandos usando el mismo `DATABASE_URL` de Supabase:

```bash
alembic upgrade head
python scripts/seed_demo.py
```

Haz el seed solo si quieres cargar datos demo.

Nota: el historial de Alembic actual parte de cambios incrementales, no de una migración inicial completa. En una BD ya existente como tu Supabase actual, `alembic upgrade head` sigue siendo el camino correcto. Para una BD totalmente vacía habría que generar una migración base o bootstrapear el esquema desde los modelos antes de usar Alembic.
