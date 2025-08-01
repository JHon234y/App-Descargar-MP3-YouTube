# api.py (Corregido y Mejorado)
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# Configuración de CORS para permitir peticiones desde cualquier origen.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todas las cabeceras
)

@app.get("/get_video_info")
async def get_video_info(url: str = Query(..., description="La URL del video de YouTube")):
    if not url:
        raise HTTPException(status_code=400, detail="La URL no puede estar vacía.")

    # Opciones para pedir la mejor calidad de video y audio en una sola llamada
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Hacemos una sola llamada para obtener toda la información
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Título no disponible')
            uploader = info.get('uploader', 'Canal no disponible')
            thumbnail = info.get('thumbnail', '')
            
            mp4_url = None
            mp3_url = None # Realmente será m4a, pero es el formato de audio más común

            # Iteramos sobre la lista de formatos que nos da yt-dlp
            for f in info.get('formats', []):
                # Buscamos el mejor formato de solo audio (m4a es excelente)
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and f.get('ext') == 'm4a':
                    if mp3_url is None: # Nos quedamos con el primero que suele ser el de mejor calidad
                        mp3_url = f.get('url')
            
            # El enlace de descarga principal ya es el mejor formato de video+audio combinado
            mp4_url = info.get('url')

            if not mp4_url and not mp3_url:
                 raise HTTPException(status_code=404, detail="No se encontraron formatos de descarga válidos.")

            return {
                "title": title,
                "uploader": uploader,
                "thumbnail": thumbnail,
                "download_links": {
                    "mp4": mp4_url,
                    "mp3": mp3_url
                }
            }
    except Exception as e:
        # Si algo falla, devolvemos un error claro
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al procesar la URL: {str(e)}")

# Para ejecutar la API localmente, usa este comando en la terminal:
# uvicorn api:app --reload