# Transcriptor de Audio Médico

Una aplicación de escritorio para transcribir archivos de audio y grabaciones en vivo, especialmente optimizada para terminología médica y radiológica.

## Características

- Transcripción de archivos de audio (.wav, .mp3, .ogg, .opus, .m4a)
- Grabación de audio en vivo desde el micrófono
- Optimizado para terminología médica especializada y radiológica
- Interfaz de arrastrar y soltar para archivos
- Contador de uso mensual (límite de 2000 transcripciones)
- Guardado automático de transcripciones en archivos de texto
- Interfaz gráfica moderna y amigable

## Tecnologías utilizadas

- Python 3.x
- Groq API (modelo whisper-large-v3)
- Tkinter para la interfaz gráfica
- PyAudio para grabación de audio

## Requisitos

- Python 3.7 o superior
- Clave API de Groq
- Bibliotecas Python: groq, tkinterdnd2, pyaudio

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/SantyCMDev/Transcriptor_Python.git
cd Transcriptor_Python
```