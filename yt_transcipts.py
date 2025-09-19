from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
from youtube_transcript_api.formatters import TextFormatter
import json

ytt_api = YouTubeTranscriptApi()
video_ids = ["nDLb8_wgX50", "5tSTk1083VY", "ngvOyccUzzY", "AbDT2JTSnA8", "azROJC2YJ4g", "Gz3yZC8ZJsA", "ueNtejxVY24", "GdHW1YipmVo", "fl6X5dh6TFU", "bIacYjZHcs4", "MZU-m10Fsio", "BvWB7B8tXK8", "1jRkGa3HpvY", "gWOy7n2_3ic", "dIM7E8e9JKY"]

JSON_formatter = JSONFormatter()
with open("transcripts.json", "w", encoding="utf-8") as f:
    json.dump([], f)

for video_id in video_ids:
    fetched_transcript = ytt_api.fetch(video_id)
  
    # .format_transcript(transcript) turns the transcript into a JSON string.
    json_formatted = JSON_formatter.format_transcript(fetched_transcript)

    # Now we can write it out to a file.
    with open(f"{video_id}.json", 'w', encoding='utf-8') as json_file:
        json_file.write(json_formatted) 
    
    with open("transcripts.json", "r", encoding="utf-8") as file1, open(f"{video_id}.json", "r", encoding="utf-8") as file2:
        all_transcipts = json.load(file1)
        transcipt = json.load(file2)

    merged_transcipts = all_transcipts + transcipt

    with open("transcripts.json", "w", encoding="utf-8") as f:
        json.dump(merged_transcipts, f, indent=2, ensure_ascii=False)


    with open("transcripts.json", "r", encoding="utf-8") as f:
        transcripts = json.load(f)

    # Extract only the "text" field
    cleaned = [{"text": entry["text"]} for entry in transcripts]

    # Save back to JSON
    with open("transcripts_clean.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)


