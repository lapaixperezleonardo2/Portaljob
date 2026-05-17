📄 Proyecto: Portal Job
🧰 Stack
Frontend: HTML, CSS, JavaScript
Backend: Flask
Base de datos: MySQL
📁 Estructura del proyecto

portal-job/
│
├── backend/
│   ├── app.py
│   ├── database.py
│   └── ...
│
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── jobs.html
│   ├── job-detail.html
│   ├── profile.html
│   │
│   ├── css/
│   ├── js/
│   └── assets/
│
├── database/
│   └── schema.sql


Estado actual (IMPORTANTE)
✅ Backend
Flask funcionando correctamente
Conexión a MySQL estable
Rutas implementadas:
/ → Home
/login → Login
/register → Registro
/jobs → Lista de trabajos
/job/<id> → Detalle
/profile.html → Perfil
/create-job → Crear trabajos
Sistema de sesiones activo (session)
Usuario disponible globalmente con context_processor

✅ Frontend
Todas las páginas conectadas a Flask (NO archivos estáticos)
CSS funcionando correctamente
Sidebar funcional
Navbar dinámico (detecta sesión)

✅ Funcionalidades COMPLETAS
Registro de usuarios ✔
Login funcional ✔
Logout ✔
Mostrar trabajos desde base de datos ✔
Crear trabajos desde el panel ✔
Aplicar a trabajos ✔
Cancelar aplicación ✔
Mostrar trabajos aplicados en perfil ✔
Render dinámico con Jinja ✔
Usuario visible en navbar y sidebar ✔

⚠️ Notas importantes
❌ NO abrir HTML directamente
✅ SIEMPRE usar Flask:
http://127.0.0.1:5000
El frontend depende de Jinja ({{ }}), por eso no funciona fuera del servidor
 Estado del sistema

El proyecto ya es un portal funcional tipo bolsa de empleo

Incluye:

Autenticación
CRUD básico de trabajos
Relación usuario ↔ aplicaciones
Render dinámico completo
Próximos pasos (Roadmap)
 Editar trabajos
 Eliminar trabajos
 Sistema de favoritos ⭐
 Separar usuarios vs empresas 🏢
 Filtros de búsqueda 🔎
 Subida de CV 📄
 Mejorar UI/UX

Punto de continuación
 Último avance:
Creación de trabajos desde el panel funcionando

ultima actualizacion: estado actual del proyecto, completado ✅

pasos para correr el proyecto en otro portatil antes de subirlo a la red: 
# Portal Job - Guía de instalación
## Requisitos

* Tener instalado Python 3.10 o superior
* Tener instalado pip

## 📦 1. Clonar o descargar el proyecto
Descargar el proyecto y abrirlo en Visual Studio Code o cualquier editor.

## ⚙️ 2. Crear entorno virtual (opcional pero recomendado)
Abrir la terminal en la carpeta del proyecto y ejecutar:

```bash
python -m venv venv
```

Activar entorno virtual:
Windows:
```bash
venv\Scripts\activate
```

## 📥 3. Instalar dependencias
```bash
pip install flask flask-cors mysql-connector-python
```

## 🗄️ 4. Configurar base de datos
Crear una base de datos en MySQL y ejecutar los siguientes comandos:
```sql

CREATE DATABASE portal_job;

USE portal_job;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100),
    password VARCHAR(100),
    birth_date DATE
);

CREATE TABLE jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    salary INT,
    location VARCHAR(100),
    user_id INT,
    company VARCHAR(255),
    job_type VARCHAR(50),
    requirements TEXT,
    benefits TEXT
);

CREATE TABLE applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    job_id INT,
    cv VARCHAR(255)
);

CREATE TABLE favorites (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    job_id INT
);
```

## 5. Configurar conexión a la base de datos
Editar el archivo `database.py` y colocar:

```python
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="TU_PASSWORD",
        database="portal_job"
    )
```

## ▶️ 6. Ejecutar el servidor
En la terminal:
```bash
python app.py
```

## 🌐 7. Abrir en el navegador
Ir a:
http://127.0.0.1:5000


## 🛠️ Notas
* Si algo falla, asegurence de que MySQL esté corriendo.
* Si cambian estilos, solo modificar archivos en `/frontend/css`
