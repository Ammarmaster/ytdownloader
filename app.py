import os
import yt_dlp
from flask import Flask, render_template, request, send_from_directory, url_for, redirect

app = Flask(__name__)

# Configuration
DOWNLOAD_FOLDER = 'downloads'
COOKIE_FILE = 'cookies.txt'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

# Ensure download folder exists
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Base yt-dlp options
YDL_COMMON_OPTIONS = {
    'cookiefile': COOKIE_FILE,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'quiet': True,
    'no_warnings': True,
    'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')
}


def get_video_info(url):
    options = {
        **YDL_COMMON_OPTIONS,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        resolutions = set()
        for fmt in info.get('formats', []):
            if fmt.get('vcodec') != 'none':
                height = fmt.get('height')
                if height:
                    resolutions.add(height)

        return {
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'resolutions': sorted(resolutions, reverse=True)
        }


def download_video(url, quality):
    options = {
        **YDL_COMMON_OPTIONS,
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('index'))


@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        if not youtube_url:
            return render_template("index.html", error="Please enter a YouTube URL.")
        try:
            video_info = get_video_info(youtube_url)
            return render_template("index.html", youtube_url=youtube_url, video_info=video_info)
        except Exception as e:
            return render_template("index.html", error=str(e))

    return render_template("index.html")


@app.route('/download', methods=['POST'])
def download():
    youtube_url = request.form.get('youtube_url')
    quality = request.form.get('quality')

    if not youtube_url or not quality:
        return redirect(url_for('index'))

    try:
        filepath = download_video(youtube_url, quality)
        filename = os.path.basename(filepath)
        return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
    except Exception as e:
        return render_template("index.html", error=f"Download failed: {str(e)}")


if __name__ == '__main__':
    app.run(debug=True, port=10000)
