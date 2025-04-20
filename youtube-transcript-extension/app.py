from flask import Flask, request, render_template, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)

def extract_video_id(url):
    """
    Extract YouTube video ID from URL
    Supports various YouTube URL formats
    """
    # Examples:
    # - http://youtu.be/SA2iWivDJiE
    # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    # - http://www.youtube.com/embed/SA2iWivDJiE
    # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    
    query = urlparse(url)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        if query.path.startswith('/embed/'):
            return query.path.split('/')[2]
        if query.path.startswith('/v/'):
            return query.path.split('/')[2]
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url')
        if not youtube_url:
            return render_template('index.html', error="Please provide a YouTube URL")
        
        try:
            video_id = extract_video_id(youtube_url)
            if not video_id:
                return render_template('index.html', error="Invalid YouTube URL")
            
            # Get transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine all text segments
            full_text = " ".join([segment['text'] for segment in transcript])
            
            return render_template('index.html', 
                                 transcript=full_text, 
                                 youtube_url=youtube_url,
                                 video_id=video_id)
            
        except TranscriptsDisabled:
            return render_template('index.html', 
                                 error="Transcripts are disabled for this video",
                                 youtube_url=youtube_url)
        except NoTranscriptFound:
            return render_template('index.html', 
                                 error="No transcript found for this video",
                                 youtube_url=youtube_url)
        except Exception as e:
            return render_template('index.html', 
                                 error=f"An error occurred: {str(e)}",
                                 youtube_url=youtube_url)
    
    return render_template('index.html')

@app.route('/api/transcript', methods=['GET'])
def api_transcript():
    youtube_url = request.args.get('url')
    if not youtube_url:
        return jsonify({'error': 'Please provide a YouTube URL'}), 400
    
    try:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return jsonify({
            #'video_id': video_id,
            #'transcript': transcript
            'text': " ".join([segment['text'] for segment in transcript])
        })
        
    except TranscriptsDisabled:
        return jsonify({'error': 'Transcripts are disabled for this video'}), 400
    except NoTranscriptFound:
        return jsonify({'error': 'No transcript found for this video'}), 404
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(port=12345, debug=True)