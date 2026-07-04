<template>
  <div id="video-wrapper" ref="videoWrapper">
    <video id="video" ref="video" muted crossorigin="anonymous" playbackRate="1"></video>
    <!-- TODO loading bar and captcha here -->
  </div>
</template>

<script>
import { blobStore, framesStore } from '@/store';
import { ref } from 'vue';
import { transformMicrosecondsToTimestamp, getLaplacianVar } from '../utils';

const videoWrapper = ref(null)
const video = ref(null)

let offscreenCanvas;
let offscreenCtx;

export default {
  name: 'Process',
  mounted() {
    const file = blobStore.getters.getBlob();
    if (file) {
      // TODO show loading bar
      this.processVideo(file);
    } else {
      this.goHome();
    }
  },
  setup() {
    return {
      videoWrapper,
      video,
    }
  },
  methods: {
    processVideo(file) {
      const fileReader = new FileReader();
      fileReader.onload = async () => {
        video.value.src = fileReader.result;
        video.value.type = file.type;
        videoWrapper.value.append(video.value);
        await this.processVideoTrack(video.value);
        // TODO allow user to remove/replace current file
      };

      fileReader.readAsDataURL(file);
    },
    /**
     * main function to process video after upload
     */
    async processVideoTrack(video) {
      if (window.MediaStreamTrackProcessor) {
        const videoTrack = await this.getVideoTrack(video);
        if (videoTrack) {
          this.readChunk(new MediaStreamTrackProcessor(videoTrack));
          return;
        } else {
          alert("Lost video source, restarting.")
        }
      } else {
        alert(
          "Your browser doesn't support this API yet, try other Chromium browsers."
        );
      }
      this.goHome();
    },
    /**
     * reads VideoFrame recursively by frame
     * @param {MediaStreamTrackProcessor} processor of uploaded HTMLElement video
     */
    readChunk(processor) {
      const self = this;
      const reader = processor.readable.getReader();
      let hasWarned = false;
      let microsecondsOffset = null;
      reader.read().then(async function processFrames({ done, value }) {
        // `value` type == VideoFrame
        // see https://developer.mozilla.org/en-US/docs/Web/API/VideoFrame
        if (value) {
          const bitmap = await createImageBitmap(value);

          // instantiate offscreen canvas on first run
          if (!offscreenCanvas) {
            offscreenCanvas = new OffscreenCanvas(
              value.displayWidth,
              value.displayHeight
            );
            offscreenCtx = offscreenCanvas.getContext('2d', {
              willReadFrequently: true,
            });
          }
          offscreenCtx.drawImage(bitmap, 0, 0);

          // enhance: calculate primary/selected colour %, audio dB + pitch,
          // calculate laplacian variance
          let lapVar = null;
          try {
            lapVar = getLaplacianVar(offscreenCanvas);
          } catch (e) {
            if (!hasWarned) {
              hasWarned = true;
              alert(e.message);
            }
            lapVar = 0;
          }

          // to offset days worth of extra microseconds, as it still increments as video plays
          if (microsecondsOffset == null) {
            microsecondsOffset = value.timestamp;
          }

          const ts = value.timestamp - microsecondsOffset;
          framesStore.actions.addFrames(frames.length, bitmap, lapVar, transformMicrosecondsToTimestamp(ts), ts)

          value.close();
        }
        if (!done) {
          reader.read().then(processFrames);
        } else {
          reader.releaseLock();
          offscreenCanvas = null;
          offscreenCtx = null;
          const frames = framesStore.getters.getFrames();
          console.log(
            `video processed: ${frames.length} frames, ${frames[frames.length - 1].timestamp_microseconds
            }`
          );
          self.$router.replace({ name: 'Result' })
        }
      });
    },
    /**
 * get MediaStream Video Tracks from upload
 * https://stackoverflow.com/a/32708998/9018350
 * @param {HTMLElement} video created from user's file upload
 * @returns array of MediaStreamTrack
 */
    async getVideoTrack(video) {
      // TODO need demuxer/converter for .mov etc
      try {
        await video.play();
      } catch (err) {
        return;
      }
      // TODO add progress bar based on video length 1sec/sec:
      // https://www.codingnepalweb.com/file-upload-with-progress-bar-html-javascript/
      const [track] = video.captureStream().getVideoTracks();
      video.onended = () => {
        track.stop();
        video.remove();
      };
      return track;
    },
    goHome() {
      framesStore.actions.clearFrames();
      this.$router.replace({ name: 'Home' });
    }
  }
}
</script>

<style scoped>
#video-wrapper {
  display: none;
}
</style>