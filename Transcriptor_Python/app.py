import os
from groq import Groq
from tkinter import Tk, Label, Frame, filedialog, Button
import tkinterdnd2 as tkdnd
from datetime import datetime
import subprocess
import pyaudio
import wave
import tempfile
import threading

client = Groq(api_key="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")

def transcribir_audio(ruta_archivo_audio):
    try:
        with open(ruta_archivo_audio, "rb") as archivo:
            transcipcion = client.audio.transcriptions.create(
                file=(os.path.basename(ruta_archivo_audio), archivo.read()),
                model="whisper-large-v3",
                prompt="""el audio es de una persona normal trabajando""",
                response_format="text",
                language="es",
            )
        return transcipcion
    except Exception as e:
        print(f"Ocurrió un error: {str(e)}")
        return None

def guardar_transcripcion(texto):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"transcripcion_{timestamp}.txt"
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        initialfile=default_filename,
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
        title="Guardar transcripción"
    )
    
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(texto)
        subprocess.Popen(['notepad.exe', file_path])
        return file_path
    return None

def process_dropped_file(file_path):
    print(f"Transcribiendo archivo: {file_path}")
    transcription = transcribir_audio(file_path)
    if transcription:
        print("\nTranscripción:")
        print("Guardando transcripción en archivo...")
        saved_file = guardar_transcripcion(transcription)
        if saved_file:
            print(f"Transcripción guardada en: {saved_file}")
        else:
            print("Guardado cancelado por el usuario")
    else:
        print("La transcripción falló.")

class AudioRecorder:
    def __init__(self):
        self.frames = []
        self.recording = False
        self.p = None
        self.stream = None
        
    def guardar_audio(self):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_temp:
            wf = wave.open(audio_temp.name, "wb")
            wf.setnchannels(1)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b"".join(self.frames))
            wf.close()
            return audio_temp.name

def create_drop_window():
    root = tkdnd.Tk()
    root.title("Transcriptor de audio")
    root.geometry("500x400") 

    frame = Frame(root, bg="lightgray", width=400, height=300)
    frame.pack(expand=True, fill="both", padx=20, pady=20)

    title_label = Label(
        frame, text="Transcriptor de Audio", bg="lightgray", font=("Arial", 16, "bold")
    )
    title_label.pack(pady=10)

    drop_zone = Frame(frame, bg="white", width=350, height=150, relief="groove", bd=2)
    drop_zone.pack(pady=20, padx=10)
    drop_zone.pack_propagate(False)

    drop_label = Label(
        drop_zone,
        text="Arrastra y suelta aquí\ntu archivo de audio\n\nFormatos soportados:\n.wav, .mp3, .ogg, .opus, .m4a",
        bg="white",
        font=("Arial", 10),
    )
    drop_label.pack(expand=True)

    status_label = Label(
        frame,
        text="Esperando acción...",
        bg="lightgray",
        font=("Arial", 9)
    )
    status_label.pack(pady=5)

    recorder = AudioRecorder()

    def toggle_recording():
        if not recorder.recording:
            recorder.recording = True
            recorder.frames = []
            status_label.config(text="Grabando audio...")
            record_button.config(text="Detener Grabación", bg="#f44336")
            
            def audio_stream():
                recorder.p = pyaudio.PyAudio()
                recorder.stream = recorder.p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024
                )
                
                while recorder.recording:
                    try:
                        data = recorder.stream.read(1024, exception_on_overflow=False)
                        recorder.frames.append(data)
                    except Exception as e:
                        print(f"Error durante la grabación: {e}")
                        break
                
                
                recorder.stream.stop_stream()
                recorder.stream.close()
                recorder.p.terminate()
                
                if recorder.frames:  
                    archivo_audio_temp = recorder.guardar_audio() 
                    root.after(0, lambda: status_label.config(text="Transcribiendo audio..."))
                    process_dropped_file(archivo_audio_temp)
                    os.unlink(archivo_audio_temp)
                    root.after(0, lambda: record_button.config(text="Grabar Audio", bg="#4CAF50"))
                    root.after(0, lambda: status_label.config(text="Grabación procesada"))
            
            threading.Thread(target=audio_stream, daemon=True).start()
        else:
            recorder.recording = False
            status_label.config(text="Finalizando grabación...")
            record_button.config(state="disabled")  
            
            def enable_button():
                record_button.config(state="normal", text="Grabar Audio", bg="#4CAF50")
            
            root.after(1000, enable_button)  

    record_button = Button(
        frame,
        text="Grabar Audio",
        bg="#4CAF50",
        fg="white",
        font=("Arial", 10, "bold"),
        padx=20,
        pady=10,
        command=toggle_recording
    )
    record_button.pack(pady=10)

    def handle_drop(event):
        file_path = event.data.strip("{}")
        if file_path.lower().endswith((".wav", ".mp3", ".ogg", ".opus", ".m4a")):
            status_label.config(text="Procesando archivo...")
            drop_zone.config(bg="#e8f5e9")
            process_dropped_file(file_path)
            drop_zone.config(bg="white")
            status_label.config(text="Archivo procesado correctamente")
        else:
            status_label.config(text="Formato de archivo no soportado")

    drop_zone.drop_target_register("DND_Files")
    drop_zone.dnd_bind("<<Drop>>", handle_drop)

    return root

def main():
    root = create_drop_window()
    root.mainloop()

if __name__ == "__main__":
    main()
