import os
import yt_dlp
from flask import Flask, request, render_template, send_from_directory, redirect, url_for

app = Flask(__name__)

# Configuration
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER


# HTML Form Route
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        video_url = request.form.get('url')
        if video_url:
            try:
                filename = download_video(video_url)
                return redirect(url_for('download_file', filename=filename))
            except Exception as e:
                return f"<h3>Error downloading video: {str(e)}</h3>"
    return '''
        <h2>YouTube Downloader</h2>
        <form method="post">
            <input type="text" name="url" placeholder="Enter YouTube URL" required style="width:300px;">
            <input type="submit" value="Download">
        </form>
    '''


# Download Route
@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)


# Function to Download YouTube Video
def download_video(url):
    ydl_opts = {
        'format': 'best',
        'cookiefile': 'cookies.txt',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
        return os.path.basename(filename)


if __name__ == '__main__':
    app.run(debug=True)
