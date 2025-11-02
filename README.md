```markdown
# IBKR 📈

Herramienta en Python para **trading algorítmico** y **consumo de datos financieros en tiempo real** a través de la API de **Interactive Brokers (IBKR)**.

## 🧭 Descripción general

Este proyecto proporciona una infraestructura flexible para conectarse con la API de **IBKR**, permitiendo:

- Recibir **datos de mercado en tiempo real**
- Ejecutar **órdenes de compra y venta** automatizadas
- Procesar y almacenar datos históricos y en streaming
- Probar estrategias mediante **backtesting**
- Visualizar y analizar resultados desde **notebooks interactivos**

Ideal para desarrolladores, analistas cuantitativos y traders que desean automatizar estrategias de inversión o experimentar con datos financieros de IBKR.

---

## 🏗️ Estructura del repositorio

```

IBKR/
┣ config.json
┣ requirements.txt
┣ data/
┣ doc/
┣ ibkr/             ← paquete principal (conexión, API, lógica de trading)
┣ notebooks/        ← notebooks Jupyter con ejemplos de uso y análisis
┣ packages/         ← utilidades y módulos adicionales
┗ test/             ← pruebas unitarias / de integración

````

### Carpetas clave

- **`ibkr/`** → Contiene el núcleo del sistema: funciones de conexión, manejo de datos en tiempo real y ejecución de órdenes.  
- **`notebooks/`** → Ejemplos prácticos: conexión a la API, suscripción a datos, y estrategias de trading.  
- **`data/`** → Datos históricos o temporales para backtesting o almacenamiento local.  
- **`test/`** → Validaciones automáticas de la lógica del sistema.  

---

## ⚙️ Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Alvaro-Villa/IBKR.git
   cd IBKR
````

2. **Crear entorno virtual (recomendado)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar credenciales**

   * Edita `config.json` con tus credenciales y parámetros de conexión a la API de IBKR.

---

## 🚀 Uso básico

### Importar el módulo

```python
import ibkr

# Ejemplo: conectar al gateway de IBKR
client = ibkr.connect()
data = client.get_realtime_data("AAPL")
print(data)
```

### Ejecutar un notebook

Abre cualquiera de los archivos en `notebooks/` con Jupyter para probar estrategias o explorar datos en tiempo real.

```bash
jupyter notebook notebooks/
```

---

## 🧠 Características principales

✅ Conexión directa con la API de Interactive Brokers
✅ Recepción de datos de mercado en **tiempo real**
✅ Ejecución de **órdenes automáticas**
✅ Análisis y **backtesting** de estrategias
✅ Integración con **notebooks Jupyter** para exploración interactiva
✅ Modular y extensible para proyectos de **trading cuantitativo**

---

## 🤝 Contribuir

1. Realiza un *fork* del proyecto
2. Crea una rama (`feature/nueva-funcionalidad`)
3. Añade tus cambios y tests
4. Envía un *pull request*

---

## 📜 Licencia

Este proyecto se distribuye bajo la licencia **MIT** (puedes modificar según corresponda).

---

## 📬 Contacto

Proyecto mantenido por **Álvaro Villadangos**
Para dudas, sugerencias o colaboración: abre un *issue* o crea un *pull request* en el repositorio.

---
