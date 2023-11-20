#!/bin/bash
if ! command -v youtube-dl &> /dev/null; then
    echo "youtube-dl is not installed. Please install it first."
    exit 1
fi
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg is not installed. Please install it first."
    exit 1
fi
if [ -z "$1" ]; then
    echo "Usage: $0 <URL>"
    exit 1
fi

URL="$1"
input_file=$(youtube-dl --get-filename "$URL")
cleaned=$(echo $input_file | cut -c 1-18 | tr -cd '[:alnum:]')
cleaned_inp="../data/media/$cleaned.mp4"
cleaned_out="$cleaned.mp3"
if [ ! -f "$cleaned_inp" ]; then
    youtube-dl "$URL"
fi

if [ ! -f "$cleaned_out" ]; then
    mv "$input_file" "$cleaned_inp"
    ffmpeg -i "$cleaned_inp" -vn -acodec libmp3lame -ar 16000 -q:a 2 "$cleaned_out"
fi

mkdir "../data/segments/$cleaned"
# Split the audio into 30-second segments
ffmpeg -i "$cleaned_out" -f segment -segment_time 30 -c copy "../data/segments/$cleaned/out%03d.mp3"
