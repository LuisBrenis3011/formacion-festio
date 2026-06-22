# Festio

Plataforma inteligente para la gestión y recomendación de eventos. Este proyecto se compone de un backend (API REST con FastAPI) y un frontend (React con Vite).

## Estructura del Proyecto

- `/app`: Código fuente del backend (FastAPI).
- `/frontend`: Código fuente del frontend (React + Vite).
- `/migrations`: Migraciones de la base de datos (Alembic).
- `/tests`: Pruebas automatizadas.

---

##  Requisitos Previos

Asegúrate de tener instalados los siguientes componentes antes de iniciar:

- **Python 3.11+ (no superior a 3.13 osea hasta la 3.12.9)**
- **Node.js 18+** y **npm**
- **PostgreSQL** (en ejecución)
- **Redis** (en ejecución)

---

## ⚙️ Configuración del Backend

1. **Clonar el repositorio y acceder a la carpeta del proyecto:**
   ```bash
   git clone <url-del-repositorio>
   cd formacion-festio
   ```

2. **Crear y activar un entorno virtual:**
   - En **Windows**:
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - En **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar las dependencias:**
   Con el entorno virtual activado, instala los paquetes requeridos:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar las variables de entorno:**
   Copia el archivo `.env.example` y renómbralo a `.env`. El backend puede trabajar en local o apuntando a servicios remotos; hoy la plantilla ya está lista para **Supabase PostgreSQL**, **Upstash Redis** y `GEMINI_API_KEY`. La misma colección de variables se reutiliza después en GCP/Cloud Run:
   ```bash
   cp .env.example .env
   ```

5. **Aplicar las migraciones de la base de datos (Alembic):**
   ```bash
   alembic upgrade head
   ```

6. **Ejecutar el servidor de desarrollo:**
   ```bash
   uvicorn app.main:app --reload
   ```
   El backend estará disponible en: `http://localhost:8000`

### Documentación de la API
Una vez que el backend esté en ejecución, puedes consultar la documentación interactiva en:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

##  Configuración del Frontend

1. **Abrir una nueva terminal** y acceder a la carpeta del frontend:
   ```bash
   cd frontend
   ```

2. **Instalar las dependencias de Node.js:**
   ```bash
   npm install
   ```

3. **Ejecutar el servidor de desarrollo:**
   ```bash
   npm run dev
   ```
   El frontend estará disponible en: `http://localhost:5173` (o el puerto que indique Vite en la consola).

---

##  Notas Adicionales

- Asegúrate de que tanto el backend como el frontend estén corriendo simultáneamente en terminales separadas para que la aplicación funcione correctamente.
- Si utilizas VS Code, asegúrate de seleccionar el intérprete de Python correcto (el que se encuentra dentro de la carpeta `venv`).
