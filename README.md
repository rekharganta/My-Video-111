# Love Your Neighbor — AI-generated video

A ~1:40 narrated video generated entirely in code, inspired by the Sower and Seeds
Ministries message **"Israelis or Palestinians: Whom should I support and why?"**
(https://www.youtube.com/watch?v=SQ4wA0pgaJo).

Message: both Israelis and Palestinians are our neighbours, and the Lord taught us to
love our neighbours as ourselves. Pray and work for peace, and come to Christ for rest.

**Watch:** [`output/love_your_neighbor.mp4`](output/love_your_neighbor.mp4) (1280×720, 24 fps)

## How it's made
- **Visuals:** 10 drawn scenes (night sky, dusk hills, light rays, two lights coming together,
  olive branch, candles, sunrise, dawn with birds) rendered frame by frame with Pillow + numpy,
  with slow zooms, fades and animated captions.
- **Narration:** synthesized offline with `espeak-ng`.
- **Music:** a soft chord pad synthesized in numpy.
- **Scripture:** quoted from the King James Version (public domain).

## Re-generate it (Mac)
```bash
brew install ffmpeg espeak-ng
pip3 install numpy pillow
python3 make_video.py      # writes output/love_your_neighbor.mp4
```
Edit the `SCENES` list in `make_video.py` to change the text, narration or order of scenes.
