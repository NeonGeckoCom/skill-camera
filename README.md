# <img src='https://0000.us/klatchat/app/files/neon_images/icons/neon_skill.png' card_color="#FF8600" width="50" style="vertical-align:bottom">Camera 
  
## Summary  

Take pictures and videos.
  
## Requirements  

This skill requires a camera connected and configured to work in Linux.

[fswebcam](http://manpages.ubuntu.com/manpages/bionic/man1/fswebcam.1.html)  
[streamer](http://manpages.ubuntu.com/manpages/xenial/man1/streamer.1.html)  
[MPV](https://mpv.io/)
 
The above requirements should be installed automatically, but can be installed manually:  

    ```bash
    sudo apt install fswebcam streamer mpv
    ```

## Description  
  
The skill allows you to capture pictures and videos and saves them to your local device.
  
## Examples  
  
First, make your request:  
  
Say `“Hey Neon”` if you are in the wake words mode. 
  
- "neon take a picture"
      
- "neon take a video"
      
- “neon record for 30 seconds”

- "neon show me my last picture"

If you are taking a new picture or video, you will hear an audible shutter. After the picture or video is captured, it
will be displayed on screen.

If you are requesting your most recent picture or video, a notification sound will play and the image will be displayed
on screen.

## Location  
  

     ${skills}/usb-cam.neon

## Files
<details>
<summary>Click to expand.</summary>
<br>

    ${skills}/usb-cam.neon/
    ${skills}/usb-cam.neon/res
    ${skills}/usb-cam.neon/res/wav
    ${skills}/usb-cam.neon/res/wav/notify.wav
    ${skills}/usb-cam.neon/res/wav/beep.wav
    ${skills}/usb-cam.neon/res/wav/shutter.wav
    ${skills}/usb-cam.neon/res/wav/LICENSE
    ${skills}/usb-cam.neon/__pycache__
    ${skills}/usb-cam.neon/__pycache__/__init__.cpython-36.pyc
    ${skills}/usb-cam.neon/vocab
    ${skills}/usb-cam.neon/vocab/en-us
    ${skills}/usb-cam.neon/vocab/en-us/ShowLastIntent.intent
    ${skills}/usb-cam.neon/vocab/en-us/TakeVidIntent.intent
    ${skills}/usb-cam.neon/vocab/en-us/duration.entity
    ${skills}/usb-cam.neon/vocab/en-us/TakePicIntent.intent
    ${skills}/usb-cam.neon/README.md
    ${skills}/usb-cam.neon/__init__.py
    ${skills}/usb-cam.neon/requirements.sh
    ${skills}/usb-cam.neon/test
    ${skills}/usb-cam.neon/test/intent
    ${skills}/usb-cam.neon/test/intent/005.ShowLastIntent.intent.json
    ${skills}/usb-cam.neon/test/intent/003.TakeVidIntent.intent.json
    ${skills}/usb-cam.neon/test/intent/002.TakePicIntent.intent.json
    ${skills}/usb-cam.neon/test/intent/004.TakeVidIntent.intent.json
    ${skills}/usb-cam.neon/test/intent/001.TakePicIntent.intent.json
    ${skills}/usb-cam.neon/dialog
    ${skills}/usb-cam.neon/dialog/en-us
    ${skills}/usb-cam.neon/dialog/en-us/hour.list
    ${skills}/usb-cam.neon/dialog/en-us/minute.list
    ${skills}/usb-cam.neon/dialog/en-us/second.list
    ${skills}/usb-cam.neon/settings.json
    ${skills}/usb-cam.neon/LICENSE



</details>
  

## Class Diagram
[Click Here](https://0000.us/klatchat/app/files/neon_images/class_diagrams/usb-cam.png)
  

## Available Intents
<details>
<summary>Show list</summary>
<br>


### duration.entity

    (#|##|###) (minutes|seconds|hours) (and|)
    (#|##|###) (minute|second|hour) (and|)

### ShowLastIntent.intent

    display last picture
    display last photo
    display latest picture
    display latest photo
    display (my user |) last picture
    display my last photo
    display my latest picture
    display my latest photo
    show the last picture
    show the last photo
    show the last pic
    show the last pick
    show latest picture
    show latest photo
    show latest pic
    show latest pick
    show me my last picture
    show me my latest picture
    show me my latest photo
    show me my latest pic
    show me my latest pick
    
    display last video
    display latest video
    display my last video
    display my latest video
    show the last video
    show latest video
    show me my the last video
    show me my latest video
    playback my last video
    play back (my user |) last video
    show my user photo
    show my user picture
    show my user video

### TakePicIntent.intent

    take (my user |)picture
    take (my user |)photo
    take a picture
    camera capture
    webcam capture

### TakeVidIntent.intent

    (neon |)record (my user |){duration} video
    (neon |)video (my user |){duration}
    (neon |)take (my user |){duration} recording
    (neon |)take (my user |){duration} video
    (neon |)record for {duration}
    (neon |)video record for {duration}
    (neon |)take a video


</details>


## Details

### Text

	    Take a picture    
	    >> *shutter* 
	       
        Video record for 10 seconds    
        >> Recording for 10 seconds
        
        Show me my last picture
        >> Here you go.

### Picture

### Video

## Troubleshooting
Ensure your webcam is connected and working in Ubuntu, you can check functionality in `Cheese`.  
    ```bash
    sudo apt install cheese
    ```
 
## Contact Support
Use the [link](https://neongecko.com/ContactUs) or [submit an issue on GitHub](https://help.github.com/en/articles/creating-an-issue)

## Credits
[NeonGeckoCom](https://github.com/NeonGeckoCom)
[reginaneon](https://github.com/reginaneon)
