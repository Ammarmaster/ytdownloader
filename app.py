import os
import yt_dlp
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from werkzeug.urls import url_quote_plus  # or url_encode # or url_encode
app = Flask(__name__)

# Configuration
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'webm', 'mkv', 'mp3'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max

# Ensure download folder exists
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'simulate': True,
        'format': 'best',
        'referer': 'https://www.youtube.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        
        # Filter video formats and get unique resolutions
        resolutions = set()
        
        for f in formats:
            if f.get('vcodec') != 'none':  # Only video formats
                res = f.get('height', 'Unknown')
                if res != 'Unknown':
                    resolutions.add(res)
        
        return {
            'title': info.get('title', 'Unknown'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'resolutions': sorted(resolutions, reverse=True)
        }

def download_video(url, quality):
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        'outtmpl': os.path.join(app.config['DOWNLOAD_FOLDER'], '%(title)s.%(ext)s'),
        'quiet': False,
        'referer': 'https://www.youtube.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'player_skip': ['configs'],
            }
        },
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")

@app.route('/')
def home():
    return redirect(url_for('index'))

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        
        if not youtube_url:
            return render_template('index.html', error="Please enter a YouTube URL")
        
        try:
            video_info = get_video_info(youtube_url)
            return render_template('index.html', 
                                video_info=video_info, 
                                youtube_url=youtube_url)
        except Exception as e:
            return render_template('index.html', error=f"Error: {str(e)}")
    
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    youtube_url = request.form.get('youtube_url')
    quality = request.form.get('quality')
    
    if not youtube_url or not quality:
        return redirect(url_for('index'))
    
    try:
        filename = download_video(youtube_url, quality)
        return send_from_directory(
            app.config['DOWNLOAD_FOLDER'],
            os.path.basename(filename),
            as_attachment=True
        )
    except Exception as e:
        return render_template('index.html', error=f"Download failed: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
