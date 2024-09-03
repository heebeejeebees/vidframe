<template>
  <div id="video-wrapper" ref="videoWrapper">
    <div id="controls" ref="videoControls">
      <button id="download-btn" class="btn" ref="downloadBtn">download</button>
      <button id="reset-zoom-btn" class="btn" ref="resetZoomBtn">
        <i class="fas fa-undo"></i>
      </button>
    </div>
    <canvas id="timeline" ref="timelineCanvas"></canvas>
    <canvas id="annotation" ref="annotCanvas"></canvas>
    <canvas id="frame" ref="frameCanvas"></canvas>
    <video id="video" ref="video" muted crossorigin="anonymous" playbackRate="1"></video>
  </div>
</template>

<script>
import blobStore from '@/store';
import { ref } from 'vue';
import Chart from 'chart.js/auto';
import { transformMicrosecondsToTimestamp, canvasDrawImage, getLaplacianVar } from '../utils';

const videoWrapper = ref(null)
const video = ref(null)
const videoControls = ref(null)

const timelineCanvas = ref(null);
const annotCanvas = ref(null);
const frameCanvas = ref(null);
const downloadBtn = ref(null);
const resetZoomBtn = ref(null);


const frames = [];
let offscreenCanvas;
let offscreenCtx;

export default {
  name: 'ChartResult',
  mounted() {
    const file = blobStore.getters.getBlob();
    if (file) {
      this.processVideo(file);
    } else {
      this.goHome();
    }
  },
  setup() {
    return {
      videoWrapper,
      video,
      videoControls,
      timelineCanvas,
      annotCanvas,
      frameCanvas,
      downloadBtn,
      resetZoomBtn
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

          frames.push({
            index: frames.length,
            bitmap,
            data: {
              laplacian_variance: lapVar,
            },
            timestamp: transformMicrosecondsToTimestamp(value.timestamp - microsecondsOffset),
            timestamp_microseconds: value.timestamp - microsecondsOffset,
          });
          value.close();
        }
        if (!done) {
          reader.read().then(processFrames);
        } else {
          reader.releaseLock();
          offscreenCanvas = null;
          offscreenCtx = null;
          console.log(
            `video processed: ${frames.length} frames, ${frames[frames.length - 1].timestamp_microseconds
            }`
          );
          self.plotTimeline(frames);
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

    /**
     * draw vertical line on canvas
     * @param {OffscreenCanvasRenderingContext2D } ctx
     * @param {Scale} axisY of timeline
     * @param {number} pixelX x-value in pixels
     * @param {string | CanvasGradient | CanvasPattern} color
     * @param {number} width
     */
    drawVerticalLineFromX(ctx, axisY, pixelX, color, width) {
      ctx.beginPath();
      ctx.moveTo(pixelX, axisY.top);
      ctx.lineTo(pixelX, axisY.bottom);
      ctx.lineWidth = width;
      ctx.strokeStyle = color;
      ctx.stroke();
    },

    /**
     * draw vertical thick line on annotation canvas
     * @param {Scale} axisY of timeline
     * @param {number} pixelX x-value in pixels
     */
    clearAndDrawAnnotation(axisY, pixelX) {
      const annotCtx = annotCanvas.value.getContext('2d', {
        willReadFrequently: true,
      });
      annotCtx.clearRect(0, 0, annotCanvas.value.width, annotCanvas.value.height);
      this.drawVerticalLineFromX(annotCtx, axisY, pixelX, 'rgba(1,1,1,1)', 2);
    }
    ,
    /**
     * update frame and draw vertical line on annotation canvas
     * @param {ImageBitmap} bitmap of image
     * @param {Scale} axisY of timeline
     * @param {number} pixelX x-value in pixels
     */
    updateFrameAndAnnotation(bitmap, axisY, pixelX) {
      const frameCtx = frameCanvas.value.getContext('2d', {
        willReadFrequently: true,
      });
      // show selected video frame
      canvasDrawImage(frameCanvas.value, frameCtx, /* frames[dataX]. */ bitmap);
      // draw selected frame vertical line
      this.clearAndDrawAnnotation(axisY, pixelX);
    },

    /**
     * plot the video timeline with laplacian variance value
     */
    plotTimeline(frames) {
      /* chartjs starts */
      let pixelX;
      let dataX;
      let axisY;
      let bitmap;
      let isDragging = false;
      const chart = new Chart(timelineCanvas.value, {
        type: 'line',
        data: {
          labels: frames.map((frame) => frame.timestamp),
          datasets: [
            {
              data: frames.map((frame) => frame.data.laplacian_variance),
            },
          ],
        },
        options: {
          plugins: {
            legend: {
              display: false,
            },
            tooltip: {
              intersect: false,
              mode: 'index',
            },
            zoom: {
              zoom: {
                wheel: {
                  enabled: true,
                },
                pinch: {
                  enabled: true,
                },
                mode: 'xy',
                onZoom: () => {
                  resetZoomBtn.value.onclick = () => {
                    chart.resetZoom();
                    resetZoomBtn.value.style.display = 'none';

                    const annotCtx = annotCanvas.value.getContext('2d', {
                      willReadFrequently: true,
                    });
                    if (pixelX && dataX && axisY) {
                      annotCtx.clearRect(
                        0,
                        0,
                        annotCanvas.value.width,
                        annotCanvas.value.height
                      );
                    }
                  };
                  resetZoomBtn.value.style.display = 'block';
                  annotCtx.clearRect(0, 0, annotCanvas.value.width, annotCanvas.value.height);
                },
              },
            },
          },
          scales: {
            x: {
              grid: {
                display: false,
              },
            },
            y: {
              grid: {
                display: false,
              },
            },
          },
          events: [
            'mousemove',
            'mousedown',
            'mouseup',
            'click',
            'touchmove',
            'touchstart',
            'touchend',
            'mouseleave',
          ],
        },
        plugins: [
          {
            resize: (_chart, args) => {
              // update annotation canvas to be same as timeline chart canvas
              if (annotCanvas.value.width !== args.size.width) {
                annotCanvas.value.width = args.size.width;
                annotCanvas.value.style.width = args.size.width + 'px';
              }
              if (annotCanvas.value.height !== args.size.height) {
                annotCanvas.value.height = args.size.height;
                annotCanvas.value.style.height = args.size.height + 'px';
              }
            },
            afterEvent: (chart, args) => {
              if (!chart.tooltip._active[0]) {
                return;
              }
              /* for selecting and sliding across video frames */
              const {
                event: { type: eventType },
              } = args;
              // set selected details
              pixelX = chart.tooltip._active[0].element.x;
              dataX = chart.scales.x.getValueForPixel(pixelX);
              axisY = chart.scales.y;
              bitmap = frames[dataX].bitmap;

              if (eventType === 'mousedown' || eventType === 'touchstart') {
                isDragging = true;
                // show selected
                this.updateFrameAndAnnotation(bitmap, axisY, pixelX);
              } else if (
                eventType === 'mouseup' ||
                eventType === 'touchend' ||
                eventType === 'mouseleave'
              ) {
                isDragging = false;

                // update download
                downloadBtn.value.onclick = () => {
                  const downloadLink = document.createElement('a');
                  downloadLink.download = `${frames[dataX].timestamp} picked by vidfra.me.png`;
                  downloadLink.href = frameCanvas.value.toDataURL();
                  downloadLink.click();
                };
                downloadBtn.value.style.display = 'block';

                if (eventType !== 'mouseleave') {
                  // draw selected frame vertical line
                  this.clearAndDrawAnnotation(axisY, pixelX);
                }
              } else if (eventType === 'mousemove' || eventType === 'touchmove') {
                if (isDragging) {
                  // show selected
                  this.updateFrameAndAnnotation(bitmap, axisY, pixelX);
                } else {
                  // draw and erase vertical line for hovering
                  const timelineCtx = timelineCanvas.value.getContext('2d', {
                    willReadFrequently: true,
                  });
                  timelineCtx.save();
                  this.drawVerticalLineFromX(
                    timelineCtx,
                    axisY,
                    pixelX,
                    'rgba(1,1,1,0.5)',
                    1
                  );
                  timelineCtx.restore();
                }
              }
            },
          },
        ],
      });
    },
    goHome() {
      this.$router.replace({ name: 'Home' });
    }
  }
}
</script>

<style scoped>
#video-wrapper {
  display: grid;
  height: 100%;
  width: 100%;
  position: absolute;
  justify-content: center;
  align-items: center;
}

#controls {
  display: flex;
  position: absolute;
  bottom: 0;
  height: 50px;
  width: 100%;
  justify-content: center;
  z-index: 4;
}

#download-btn {
  display: none;
}

#reset-zoom-btn {
  display: none;
  width: 30px;
  padding: 0;
}

#controls>* {
  margin: 10px 5px;
}

#annotation {
  height: 100%;
  width: 100%;
  display: block;
  position: absolute;
  z-index: 2;
}

#frame {
  height: 100%;
  width: 100%;
  z-index: 1;
}

#timeline {
  height: 100%;
  width: 100%;
  position: absolute;
  z-index: 3;
}

video {
  visibility: visible;
  height: 100%;
  width: 100%;
  position: absolute;
  z-index: 1;
}
</style>