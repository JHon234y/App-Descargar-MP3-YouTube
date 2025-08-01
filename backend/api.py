# api.py (Corregido con soporte para Cookies)
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_video_info")
async def get_video_info(url: str = Query(..., description="La URL del video de YouTube")):
    if not url:
        raise HTTPException(status_code=400, detail="La URL no puede estar vacía.")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }

    # Añadir la opción de cookies si el archivo existe
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Título no disponible')
            uploader = info.get('uploader', 'Canal no disponible')
            thumbnail = info.get('thumbnail', '')
            
            mp4_url = None
            mp3_url = None

            for f in info.get('formats', []):
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and f.get('ext') == 'm4a':
                    if mp3_url is None:
                        mp3_url = f.get('url')
            
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
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al procesar la URL: {str(e)}")
