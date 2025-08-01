# api.py (Versión con Logging para Depuración Final)
import os
import http.cookiejar
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE_PATH = os.path.join(SCRIPT_DIR, 'cookies.txt')

@app.get("/get_video_info")
async def get_video_info(url: str = Query(..., description="La URL del video de YouTube")):
    # ... (Esta función no necesita logging, la dejamos como está)
    if not url:
        raise HTTPException(status_code=400, detail="La URL no puede estar vacía.")
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    if os.path.exists(COOKIE_FILE_PATH):
        ydl_opts['cookiefile'] = COOKIE_FILE_PATH
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

@app.get("/download")
async def download_media(video_url: str = Query(..., description="URL del video de YouTube"), format: str = Query(..., description="Formato a descargar (mp3 o mp4)")):
    print("--- INICIANDO PROCESO DE DESCARGA ---")
    print(f"Formato solicitado: {format}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    if os.path.exists(COOKIE_FILE_PATH):
        print(f"Archivo de cookies encontrado en: {COOKIE_FILE_PATH}")
        ydl_opts['cookiefile'] = COOKIE_FILE_PATH
    else:
        print("ADVERTENCIA: No se encontró el archivo de cookies.")

    if format == 'mp4':
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif format == 'mp3':
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
    else:
        raise HTTPException(status_code=400, detail="Formato no válido.")

    try:
        print("Ejecutando yt-dlp para obtener el enlace de descarga...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            download_url = info.get('url')
            title = info.get('title', 'media').replace(' ', '_')
            safe_title = "".join(c for c in title if c.isalnum() or c in ('_', '-')).rstrip()
            filename = f"{safe_title}.{format}"

        if not download_url:
            print("ERROR: yt-dlp no devolvió una URL de descarga.")
            raise HTTPException(status_code=404, detail="No se pudo obtener el enlace de descarga.")
        
        print(f"URL de descarga obtenida de yt-dlp: {download_url[:80]}...")

        cookie_jar = None
        if os.path.exists(COOKIE_FILE_PATH):
            print("Cargando cookies en http.cookiejar para la petición de requests...")
            session = requests.Session()
            if os.path.exists(COOKIE_FILE_PATH):
                with open(COOKIE_FILE_PATH, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            parts = line.strip().split('\t')
                            if len(parts) >= 7:
                                domain, flag, path, secure, expiration, name, value = parts[:7]
                                session.cookies.set(name, value, domain=domain, path=path)
            print("Cookies cargadas exitosamente.")
        else:
            print("No se usarán cookies para la petición de requests.")

        def stream_content():
            print("Iniciando petición de streaming con requests...")
            with session.get(download_url, stream=True, cookies=cookie_jar) as r:
                print(f"Respuesta de googlevideo.com: Status {r.status_code}")
                print(f"Cabeceras de respuesta: {r.headers}")
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    yield chunk
            print("--- STREAMING FINALIZADO ---")

        headers = {'Content-Disposition': f'attachment; filename="{filename}"'}
        return StreamingResponse(stream_content(), headers=headers)

    except Exception as e:
        print(f"ERROR FATAL durante la descarga: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error durante la descarga: {str(e)}")
