# Práctica final de NOSQL

### Autor: Jorge Hernández Palop

Este repositorio contiene los archivos para la práctica final de la asignatura de Bases de Datos no SQL.

La práctica consiste en un __servidor web__ conectado a una base de datos de __Redis__ para jugar a las damas en el navegador.


El __frontend__ está hecho JavaScript y la única dependencia es Bootstrap para los estilos de la web. Para comunicarse con el servidor uso
websockets. 

El __backend__ está hecho en Python por medio de la librería __Quart__ que permite hacer servidores web al estilo de Flask de manera
asíncrona.  El servidor no tiene estado. Lo único que almacena son los websockets a través de las cuáles se comunica el servidor con el
cliente. Todos los mensajes se pasan a través de Redis por medio de colas de eventos implementadas como listas. Existe
una única cola de eventos para todas las partidas que se están ejecutando actualmente y una cola de eventos para cada cliente conectado.
Al usar este diseño teóricamente debería ser posible iniciar varias instancias del servidor conectadas a la misma base de datos a la vez
distribuyendo el trabajo entre los servidores por medio de las colas de eventos, aunque esto no está probado.

## Instalación y ejecución

Para ejecutar el servidor en local (Linux) hay que ejecutar:

```bash
pip install --requirement requirements.txt
redis-server &
python main.py
```

Primero instalamos las dependencias de python `Flask`, `redis` y `Quart`. Luego arrancamos el servidor de redis en local `127.0.0.1:6379`.
Finalmente, ejecutamos el servidor web situado en `main.py`.

También está la posibilidad de crear una imagen de `Docker` y correrla directamente.

```bash
docker build -t damas .
docker run -p 5000:5000 damas
```

Una vez esté corriendo el servidor podemos acceder a través del puerto `5000`.

![Menú principal](/img/main.png)

![Partida](/img/playing.png)




























### Enlace a github
[https://github.com/NotTete/Damas-NOSQL](https://github.com/NotTete/Damas-NOSQL)
