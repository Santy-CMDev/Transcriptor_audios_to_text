import os
import json
import wave
import tempfile
import threading
import subprocess
from datetime import datetime
from pathlib import Path
import pyaudio
from groq import Groq
from tkinter import Tk, Label, Frame, filedialog, Button, messagebox
import tkinterdnd2 as tkdnd

SUPPORTED_FORMATS = (".wav", ".mp3", ".ogg", ".opus", ".m4a")
MAX_MONTHLY_TRANSCRIPTIONS = 2000
AUDIO_SETTINGS = {
    "channels": 1,
    "rate": 16000,
    "chunk": 1024,
    "format": pyaudio.paInt16,
}

client = Groq(api_key="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")

USAGE_FILE = Path(__file__).parent / "usage_counter.json"


def get_usage_count():
    try:
        if not USAGE_FILE.exists():
            return {"month": datetime.now().strftime("%Y-%m"), "count": 0}

        with open(USAGE_FILE, "r") as f:
            data = json.load(f)

        current_month = datetime.now().strftime("%Y-%m")
        if data["month"] != current_month:
            data = {"month": current_month, "count": 0}

        return data
    except Exception as e:
        print(f"Error reading usage file: {e}")
        return {"month": datetime.now().strftime("%Y-%m"), "count": 0}


def update_usage_count():
    data = get_usage_count()
    data["count"] += 1

    with open(USAGE_FILE, "w") as f:
        json.dump(data, f)

    return data["count"]


counter_label = None


def transcribir_audio(ruta_archivo_audio):
    try:
        usage = get_usage_count()
        if usage["count"] >= MAX_MONTHLY_TRANSCRIPTIONS - 100:
            messagebox.showwarning(
                "Límite de uso",
                f"¡ADVERTENCIA! Has usado {usage['count']} transcripciones este mes.\n"
                f"Te quedan {MAX_MONTHLY_TRANSCRIPTIONS - usage['count']} transcripciones.",
            )

        if not os.path.exists(ruta_archivo_audio):
            raise FileNotFoundError("El archivo de audio no existe")

        with open(ruta_archivo_audio, "rb") as archivo:
            transcipcion = client.audio.transcriptions.create(
                file=(os.path.basename(ruta_archivo_audio), archivo.read()),
                model="whisper-large-v3",
                prompt="Transcripción de dictados médicos radiológicos. Enfoque en: "
                "anatomía (tórax, abdomen, columna, articulaciones), "
                "términos radiológicos (radiopaco, radiolúcido, densidades), "
                "proyecciones (AP, PA, lateral, oblicua), "
                "hallazgos (fracturas, escoliosis, infiltrados, nódulos), "
                "patologías (derrame pleural, hepatomegalia, calcificaciones), "
                "técnica (kV, mA, colimación). "
                "Mantener precisión médica.",
                response_format="text",
                language="es",
            )

        count = update_usage_count()
        if counter_label:
            counter_label.config(
                text=f"Transcripciones: {count}/{MAX_MONTHLY_TRANSCRIPTIONS}"
            )

        return transcipcion
    except Exception as e:
        messagebox.showerror("Error", f"Error en la transcripción: {str(e)}")
        return None


def guardar_transcripcion(texto):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_filename = f"transcripcion_{timestamp}.txt"

    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        initialfile=default_filename,
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
        title="Guardar transcripción",
    )

    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(texto)
        subprocess.Popen(["notepad.exe", file_path])
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
            return True, "Transcripción guardada correctamente"
        else:
            print("Guardado cancelado por el usuario")
            return False, "Guardado cancelado por el usuario"
    else:
        print("La transcripción falló.")
        return False, "La transcripción falló"


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
    root.geometry("600x500")
    root.configure(bg="#f0f0f0")

    main_frame = Frame(
        root, bg="#ffffff", highlightbackground="#3498db", highlightthickness=2
    )
    main_frame.place(relx=0.5, rely=0.5, relwidth=0.9, relheight=0.9, anchor="center")

    header_frame = Frame(main_frame, bg="#3498db", height=60)
    header_frame.pack(fill="x", pady=0)

    title_label = Label(
        header_frame,
        text="Transcriptor de Audio",
        bg="#3498db",
        fg="white",
        font=("Segoe UI", 18, "bold"),
    )
    title_label.pack(pady=10)

    content_frame = Frame(main_frame, bg="#ffffff")
    content_frame.pack(expand=True, fill="both", padx=20, pady=10)

    usage = get_usage_count()
    global counter_label
    counter_label = Label(
        content_frame,
        text=f"Transcripciones: {usage['count']}/{MAX_MONTHLY_TRANSCRIPTIONS}",
        bg="#ffffff",
        fg="#555555",
        font=("Segoe UI", 9),
    )
    counter_label.pack(pady=5, anchor="e")

    drop_zone = Frame(
        content_frame,
        bg="#f8f9fa",
        width=350,
        height=180,
        relief="flat",
        bd=1,
        highlightbackground="#dddddd",
        highlightthickness=1,
    )
    drop_zone.pack(pady=15, padx=10, fill="x")
    drop_zone.pack_propagate(False)

    drop_icon_label = Label(drop_zone, text="📁", bg="#f8f9fa", font=("Segoe UI", 24))
    drop_icon_label.pack(pady=(20, 5))

    drop_label = Label(
        drop_zone,
        text="Arrastra y suelta aquí tu archivo de audio",
        bg="#f8f9fa",
        fg="#333333",
        font=("Segoe UI", 11),
    )
    drop_label.pack()

    formats_label = Label(
        drop_zone,
        text="Formatos soportados: .wav, .mp3, .ogg, .opus, .m4a",
        bg="#f8f9fa",
        fg="#666666",
        font=("Segoe UI", 9),
    )
    formats_label.pack(pady=5)

    status_frame = Frame(content_frame, bg="#ffffff", height=30)
    status_frame.pack(fill="x", pady=5)

    status_label = Label(
        status_frame,
        text="Esperando acción...",
        bg="#ffffff",
        fg="#555555",
        font=("Segoe UI", 9),
    )
    status_label.pack(side="left", padx=5)

    button_frame = Frame(content_frame, bg="#ffffff")
    button_frame.pack(pady=15, fill="x")

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
                    frames_per_buffer=1024,
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
                    root.after(
                        0, lambda: status_label.config(text="Transcribiendo audio...")
                    )
                    success, message = process_dropped_file(archivo_audio_temp)
                    os.unlink(archivo_audio_temp)

                    root.after(
                        0,
                        lambda: record_button.config(text="Grabar Audio", bg="#2ecc71"),
                    )

                    if success:
                        root.after(
                            0, lambda: status_label.config(text=message, fg="#2e7d32")
                        )
                    else:
                        root.after(
                            0, lambda: status_label.config(text=message, fg="#c62828")
                        )
                        if "cancelado" in message.lower():
                            root.after(
                                0,
                                lambda: messagebox.showinfo(
                                    "Información",
                                    "Transcripción cancelada por el usuario",
                                ),
                            )

            threading.Thread(target=audio_stream, daemon=True).start()
        else:
            recorder.recording = False
            status_label.config(text="Finalizando grabación...")
            record_button.config(state="disabled")

            def enable_button():
                record_button.config(state="normal", text="Grabar Audio", bg="#2ecc71")

            root.after(1000, enable_button)

    record_button = Button(
        button_frame,
        text="Grabar Audio",
        bg="#2ecc71",
        fg="white",
        font=("Segoe UI", 10, "bold"),
        padx=20,
        pady=10,
        relief="flat",
        command=toggle_recording,
        cursor="hand2",
    )
    record_button.pack(pady=10)

    footer_frame = Frame(main_frame, bg="#f5f5f5", height=30)
    footer_frame.pack(fill="x", side="bottom")

    footer_label = Label(
        footer_frame,
        text="© Santy_CMDev",
        bg="#f5f5f5",
        fg="#999999",
        font=("Segoe UI", 8),
    )
    footer_label.pack(pady=5)

    def handle_drop(event):
        file_path = event.data.strip("{}")
        if file_path.lower().endswith(SUPPORTED_FORMATS):
            status_label.config(text="Procesando archivo...")
            drop_zone.config(bg="#e8f5e9")

            progress_label = Label(
                drop_zone,
                text="Procesando...",
                bg="#e8f5e9",
                fg="#2e7d32",
                font=("Segoe UI", 10, "italic"),
            )
            progress_label.pack(pady=5)

            def process_file():
                success, message = process_dropped_file(file_path)

                root.after(0, lambda: drop_zone.config(bg="#f8f9fa"))
                root.after(0, lambda: progress_label.destroy())

                if success:
                    root.after(
                        0, lambda: status_label.config(text=message, fg="#2e7d32")
                    )
                else:
                    root.after(
                        0, lambda: status_label.config(text=message, fg="#c62828")
                    )

                    if "cancelado" in message.lower():
                        root.after(
                            0,
                            lambda: messagebox.showinfo(
                                "Información", "Transcripción cancelada por el usuario"
                            ),
                        )

            threading.Thread(target=process_file, daemon=True).start()
        else:
            status_label.config(text="Formato de archivo no soportado")
            messagebox.showerror("Error", "Formato de archivo no soportado")

    drop_zone.drop_target_register("DND_Files")
    drop_zone.dnd_bind("<<Drop>>", handle_drop)

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry("{}x{}+{}+{}".format(width, height, x, y))

    return root


def main():
    root = create_drop_window()
    root.mainloop()


if __name__ == "__main__":
    main()
