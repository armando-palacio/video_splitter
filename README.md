# Video Splitter

Este repositorio contiene el código en python para una aplicación de escritorio (creada con `flet`) que puede a partir de un video, ya sea subido desde la PC o a partir de un enlace de Youtube, recortarlo en clips de duración definida por el ususario. Se puede elegir además el tiempo de inicio y finalización del subclip que se desea fragmentar en clips más pequeños. O simplemente se puede obtener un único clip desde el tiempo `t0` hasta el tiempo `t1`.


## ¿Cómo utilizar el código?

Es necesario tener python previamente instalado en el equipo. Luego se pueden seguir la secuencia de pasos a continuación para ejecutar la aplicación:

1. Clonar el repositorio: `git clone https://github.com/armando-palacio/video_splitter.git`
2. Instalar las dependencias de la aplicación (Es conveniente crear un entorno virtual unicamente para usar la app `conda create -n multimedia python`): `python -m pip install -r requirements.txt`
3. Ejecutar la aplicación de escritorio: `python split_app.py`
