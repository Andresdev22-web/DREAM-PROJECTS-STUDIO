# Arquitectura y estructura de la API de Python

## 1. Descripción general

La API está organizada mediante una arquitectura modular que permite separar las responsabilidades del proyecto. Esta estructura facilita el mantenimiento del código, la reutilización de funciones y la incorporación de nuevas funcionalidades a medida que el proyecto crece.

El proyecto se divide en dos partes principales:

- **Archivos de configuración e infraestructura:** permiten ejecutar la aplicación, instalar sus dependencias y configurar su entorno de despliegue.
- **Carpeta `app/`:** contiene la lógica interna de la aplicación, incluyendo la conexión con la base de datos, la validación de información, los servicios y las rutas de acceso.

## 2. Archivos principales

### `main.py`
Es el punto de entrada de la aplicación. Se encarga de inicializar la API y configurar los componentes necesarios para que pueda comenzar a funcionar.

### `docker-compose.yml`
Define cómo se ejecutan los servicios necesarios para el proyecto mediante Docker. Permite configurar aspectos como los contenedores, las redes y las variables de entorno.

También facilita la integración con Traefik, que actúa como proxy inverso y permite dirigir las solicitudes externas hacia la API.

### `Dockerfile`
Contiene las instrucciones necesarias para construir la imagen Docker de la aplicación. Permite definir la imagen base de Python, instalar dependencias y establecer el comando con el que se ejecutará la API.

Se complementa con `docker-compose.yml`, que se encarga de configurar y ejecutar el contenedor.

### `requirements.txt`
Contiene la lista de bibliotecas y dependencias de Python que necesita el proyecto para funcionar. Permite instalarlas de forma sencilla y mantener identificadas las herramientas utilizadas por la aplicación.

### `.env.example`
Es un archivo de ejemplo que muestra la estructura de las variables de entorno necesarias para configurar el proyecto.

Puede incluir variables como la configuración de la base de datos, las claves secretas y otros parámetros de ejecución. Los valores reales y sensibles deben mantenerse en un archivo `.env` que no se comparta públicamente ni se suba al repositorio.

## 3. Carpeta `app/`

La carpeta `app/` contiene la lógica principal de la API. Sus componentes están separados por responsabilidades para que cada parte del sistema tenga una función específica.

### `app/database.py`
Contiene la configuración y las funciones necesarias para trabajar con la base de datos SQLite. Se encarga de establecer las conexiones y, según su implementación, inicializar las tablas necesarias para almacenar la información del proyecto.

### `app/config.py`
Se encarga de obtener y centralizar las variables de configuración del proyecto, incluidas aquellas definidas mediante variables de entorno o un archivo `.env`.

Esto permite que la aplicación utilice su configuración sin tener que escribir directamente los valores sensibles dentro del código.

### `app/models/`
Contiene los modelos utilizados para definir la estructura de los datos que recibe o devuelve la API.

Estos modelos permiten especificar qué campos se esperan, qué tipos de datos deben tener y qué validaciones deben cumplir. Por ejemplo, pueden definir la información necesaria para registrar un usuario o enviar una solicitud.

### `app/services/`
Contiene las funciones que implementan la lógica de negocio de la aplicación, organizadas por módulos o funcionalidades.

Por ejemplo:

- **Autenticación:** funciones relacionadas con el inicio de sesión y la verificación de credenciales.
- **Administración de usuarios:** operaciones para consultar, registrar, actualizar o eliminar usuarios.
- **Gestión de solicitudes:** funciones para consultar las solicitudes recibidas y modificar su estado.

Los servicios permiten mantener la lógica del proyecto separada de las rutas que reciben las solicitudes HTTP.

### `app/routes/`
Contiene las rutas o endpoints mediante los cuales otros sistemas pueden comunicarse con la API.

Cada ruta define cómo responder a una solicitud HTTP y utiliza los servicios correspondientes para ejecutar las operaciones necesarias.

Por ejemplo, una ruta puede recibir una solicitud para consultar los usuarios registrados, llamar al servicio encargado de obtener esa información y devolver el resultado al cliente.

## 4. ¿Cómo trabajan juntos estos componentes?

Cuando un cliente, como un frontend desarrollado con Astro, envía una solicitud a la API, el proceso general es el siguiente:

1. **Traefik:** recibe la solicitud externa y la dirige al servicio correspondiente cuando está configurado como proxy inverso.
2. **`main.py`:** inicializa la aplicación y registra las rutas disponibles.
3. **`routes/`:** recibe la solicitud HTTP y determina qué operación debe ejecutarse.
4. **`models/`:** valida la estructura y los tipos de los datos recibidos cuando corresponde.
5. **`services/`:** ejecuta la lógica necesaria para procesar la operación.
6. **`database.py`:** proporciona acceso a la base de datos cuando la operación necesita consultar o modificar información.
7. **Respuesta de la API:** los resultados regresan a través de la ruta correspondiente y se envían al cliente en el formato definido por la aplicación.

## 5. Beneficios de esta organización

Esta estructura permite:

- **Mantenimiento:** localizar y modificar el código relacionado con una funcionalidad sin tener que concentrar toda la lógica en un único archivo.
- **Escalabilidad:** incorporar nuevos módulos, servicios y rutas a medida que aumentan las necesidades del proyecto.
- **Reutilización:** utilizar los mismos servicios desde diferentes rutas cuando sea necesario.
- **Separación de responsabilidades:** mantener diferenciadas la configuración, la validación de datos, la lógica de negocio y el acceso a la base de datos.
- **Despliegue organizado:** utilizar Docker y Traefik para facilitar la ejecución y publicación de la API en un servidor.

En conjunto, esta arquitectura proporciona una base organizada para desarrollar, mantener y ampliar la API conforme evolucione el proyecto.