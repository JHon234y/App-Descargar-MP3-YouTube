# api.py (Versión Final Definitiva con Proxy y Cookies en Requests)
import os
import http.cookiejar # Necesario para cargar las cookies
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint para obtener la información del video
@app.get("/get_video_info")
async def get_video_info(url: str = Query(..., description="La URL del video de YouTube")):
    if not url:
        raise HTTPException(status_code=400, detail="La URL no puede estar vacía.")
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get('title', 'Sin título'),
                "uploader": info.get('uploader', 'Desconocido'),
                "thumbnail": info.get('thumbnail', ''),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la URL: {str(e)}")

# Endpoint para gestionar las descargas
@app.get("/download")
async def download_media(video_url: str = Query(..., description="URL del video de YouTube"), format: str = Query(..., description="Formato a descargar (mp3 o mp4)")):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    if format == 'mp4':
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif format == 'mp3':
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
    else:
        raise HTTPException(status_code=400, detail="Formato no válido. Use 'mp3' o 'mp4'.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url')
            title = info.get('title', 'media').replace(' ', '_')
            # Sanitizar nombre de archivo para evitar errores
            safe_title = "".join(c for c in title if c.isalnum() or c in ('_', '-')).rstrip()
            filename = f"{safe_title}.{format}"

        if not download_url:
            raise HTTPException(status_code=404, detail="No se pudo obtener el enlace de descarga.")

        # Cargar las cookies para que requests las use
        cookie_jar = None
        if os.path.exists('cookies.txt'):
            cookie_jar = http.cookiejar.MozillaCookieJar('cookies.txt')
            cookie_jar.load()

        # Hacemos streaming del contenido
        def stream_content():
            # Usamos las cookies en la petición de requests
            with requests.get(download_url, stream=True, cookies=cookie_jar) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    yield chunk

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return StreamingResponse(stream_content(), headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la descarga: {str(e)}")
