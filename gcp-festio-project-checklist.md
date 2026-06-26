# Checklist GCP Para Festio

Configuracion aterrizada para:

- Proyecto GCP: `festio-project`
- Frontend productivo: `https://project-festio.vercel.app/`
- Region recomendada: `us-central1`

## Valores definidos

Usare estos nombres en todo el despliegue:

- `PROJECT_ID=festio-project`
- `REGION=us-central1`
- `ARTIFACT_REPO=festio`
- `CLOUD_RUN_SERVICE=festio-backend`
- `DEPLOYER_SA=github-actions-deployer`
- `RUNTIME_SA=festio-cloud-run-runtime`
- `WORKLOAD_POOL=github-pool`
- `WORKLOAD_PROVIDER=github-provider`
- `CORS_ALLOW_ORIGINS=https://project-festio.vercel.app`
- `CORS_ALLOW_ORIGIN_REGEX=`

## Lo Que Ya Esta Listo En El Repo

- `Dockerfile` para Cloud Run
- `.dockerignore`
- `cloudrun.env.example.yaml`
- `deploy-cloud-run.md`
- `.github/workflows/ci.yml`
- `.github/workflows/cd-cloud-run.yml`
- CORS configurable por variables de entorno
- Inicializacion de Gemini corregida para no romper el arranque
- `app.domain.all_models` agregado para que Alembic importe modelos correctamente

## 1. Activar APIs En GCP

```bash
gcloud config set project festio-project

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com
```

## 2. Crear Artifact Registry

```bash
gcloud artifacts repositories create festio \
  --repository-format=docker \
  --location=us-central1
```

Si ya existe, este paso devolvera error y puedes ignorarlo.

## 3. Crear Service Accounts

```bash
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer"

gcloud iam service-accounts create festio-cloud-run-runtime \
  --display-name="Festio Cloud Run Runtime"
```

## 4. Asignar Permisos IAM

### 4.1 Permisos para la cuenta que despliega

```bash
gcloud projects add-iam-policy-binding festio-project \
  --member="serviceAccount:github-actions-deployer@festio-project.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding festio-project \
  --member="serviceAccount:github-actions-deployer@festio-project.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding festio-project \
  --member="serviceAccount:github-actions-deployer@festio-project.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

### 4.2 Permitir que el deployer use la runtime service account

```bash
gcloud iam service-accounts add-iam-policy-binding \
  festio-cloud-run-runtime@festio-project.iam.gserviceaccount.com \
  --member="serviceAccount:github-actions-deployer@festio-project.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 4.3 Permisos para la cuenta runtime de Cloud Run

```bash
gcloud projects add-iam-policy-binding festio-project \
  --member="serviceAccount:festio-cloud-run-runtime@festio-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 5. Crear Secretos En Secret Manager

Crear secretos:

```bash
gcloud secrets create festio-database-url --replication-policy=automatic
gcloud secrets create festio-redis-url --replication-policy=automatic
gcloud secrets create festio-secret-key --replication-policy=automatic
gcloud secrets create festio-gemini-api-key --replication-policy=automatic
```

Cargar valores:

```bash
echo -n "TU_DATABASE_URL" | gcloud secrets versions add festio-database-url --data-file=-
echo -n "TU_REDIS_URL" | gcloud secrets versions add festio-redis-url --data-file=-
echo -n "TU_SECRET_KEY" | gcloud secrets versions add festio-secret-key --data-file=-
echo -n "TU_GEMINI_API_KEY" | gcloud secrets versions add festio-gemini-api-key --data-file=-
```

## 6. Configurar Workload Identity Federation Para GitHub Actions

Antes de ejecutar esto, reemplaza:

- `TU_GITHUB_OWNER`
- `TU_GITHUB_REPO`

### 6.1 Crear el pool

```bash
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Pool"
```

### 6.2 Crear el provider

```bash
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --attribute-condition="assertion.repository=='TU_GITHUB_OWNER/TU_GITHUB_REPO'"
```

### 6.3 Permitir que GitHub impersonifique la cuenta deployer

```bash
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-deployer@festio-project.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/TU_GITHUB_OWNER/TU_GITHUB_REPO"
```

Para obtener `PROJECT_NUMBER`:

```bash
gcloud projects describe festio-project --format="value(projectNumber)"
```

### 6.4 Obtener el valor que ira en GitHub Secret

```bash
gcloud iam workload-identity-pools providers describe github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
```

Ese resultado completo es el valor de `GCP_WORKLOAD_IDENTITY_PROVIDER`.

## 7. Configurar Secrets Y Variables En GitHub

### Secrets

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT_EMAIL=github-actions-deployer@festio-project.iam.gserviceaccount.com`

### Variables

- `GCP_PROJECT_ID=festio-project`
- `GCP_REGION=us-central1`
- `ARTIFACT_REGISTRY_REPO=festio`
- `CLOUD_RUN_SERVICE=festio-backend`
- `CLOUD_RUN_RUNTIME_SA=festio-cloud-run-runtime@festio-project.iam.gserviceaccount.com`
- `CLOUD_RUN_MEMORY=512Mi`
- `CLOUD_RUN_CPU=1`
- `CLOUD_RUN_MIN_INSTANCES=0`
- `CLOUD_RUN_MAX_INSTANCES=1`
- `CORS_ALLOW_ORIGINS=https://project-festio.vercel.app`
- `CORS_ALLOW_ORIGIN_REGEX=`

## 8. Primer Despliegue Manual Opcional

Si quieres probar antes de depender del CD, puedes hacer un despliegue manual desde tu maquina:

1. Copia `cloudrun.env.example.yaml` a `cloudrun.env.yaml`
2. Deja ahi solo variables no secretas
3. Despliega:

```bash
gcloud run deploy festio-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account festio-cloud-run-runtime@festio-project.iam.gserviceaccount.com \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 1 \
  --port 8080 \
  --set-secrets DATABASE_URL=festio-database-url:latest,REDIS_URL=festio-redis-url:latest,SECRET_KEY=festio-secret-key:latest,GEMINI_API_KEY=festio-gemini-api-key:latest \
  --env-vars-file cloudrun.env.yaml
```

## 9. Activar El Despliegue Automatico

Una vez configurado GitHub:

1. Haz push a `main`
2. GitHub ejecutara `CI`
3. Si `CI` pasa, se ejecutara `CD Cloud Run`

## 10. Verificaciones Finales

### Backend desplegado

- `GET /`
- `GET /docs`

### Integracion con frontend

- Las llamadas desde `https://project-festio.vercel.app` no deben fallar por CORS
- El flujo de reservas debe poder hablar con Supabase y Upstash

## 11. Lo Que Tu Todavia Tienes Que Hacer

Esto no puedo hacerlo desde el repo y queda de tu lado:

1. Ejecutar los comandos `gcloud`
2. Crear y cargar los secretos reales en `Secret Manager`
3. Reemplazar `TU_GITHUB_OWNER` y `TU_GITHUB_REPO`
4. Obtener el `PROJECT_NUMBER`
5. Crear los secrets y variables en GitHub
6. Hacer push a `main`
7. Validar el servicio desplegado

## 12. Nota Sobre La Base De Datos

Tu Supabase ya esta migrado. En este estado:

- no necesitas correr migraciones nuevas si `alembic_version` ya esta en la revision `b020bade6acb`
- si en el futuro agregas nuevas migraciones, Cloud Run no las aplicara automaticamente con el workflow actual

Para comprobar la version actual:

```sql
select version_num from alembic_version;
```
