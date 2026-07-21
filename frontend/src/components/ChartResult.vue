<template>
  <div id="chart-wrapper" ref="chartWrapper">
    <div id="controls" ref="videoControls">
      <button id="reset-zoom-btn" class="btn" ref="resetZoomBtn">
        <i class="fas fa-undo"></i>
      </button>
      <button id="download-btn" class="btn" ref="downloadBtn">download</button>
      <button id="restart-btn" class="btn" ref="restartBtn">restart</button>
    </div>
    <canvas id="timeline" ref="timelineCanvas"></canvas>
    <canvas id="annotation" ref="annotCanvas"></canvas>
    <canvas id="frame" ref="frameCanvas"></canvas>
  </div>
</template>

<script>
import { blobStore, framesStore } from '@/store';
import { ref } from 'vue';
import Chart from 'chart.js/auto';
import { canvasDrawImage } from '../utils';
import { buildFrameDownloadUrl, buildFramePreviewUrl } from '../utils/api';

const videoControls = ref(null)

const timelineCanvas = ref(null);
const annotCanvas = ref(null);
const frameCanvas = ref(null);
const downloadBtn = ref(null);
const resetZoomBtn = ref(null);
const restartBtn = ref(null);

let chart = null;

export default {
  name: 'ChartResult',
  mounted() {
    const frames = framesStore.getters.getFrames();
    if (frames && frames.length > 0) {
      this.plotTimeline(frames);
    } else {
      this.goHome();
    }
  },
  setup() {
    return {
      videoControls,
      timelineCanvas,
      annotCanvas,
      frameCanvas,
      downloadBtn,
      resetZoomBtn,
      restartBtn
    }
  },
  methods: {
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
      return true;
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
      return this.drawVerticalLineFromX(annotCtx, axisY, pixelX, 'rgba(1,1,1,1)', 2);
    }
    ,
    /**
     * update frame and draw vertical line on annotation canvas
     * @param {ImageBitmap} bitmap of image
     * @param {Scale} axisY of timeline
     * @param {number} pixelX x-value in pixels
     */
    async updateFrameAndAnnotation(frameIndex, axisY, pixelX) {
      const frameCtx = frameCanvas.value.getContext('2d', {
        willReadFrequently: true,
      });
      const jobId = framesStore.getters.getJobId();
      if (!jobId) {
        return false;
      }

      const imageUrl = buildFramePreviewUrl(jobId, frameIndex);
      const bitmap = await this.loadFrameBitmap(imageUrl);
      canvasDrawImage(frameCanvas.value, frameCtx, bitmap);
      // draw selected frame vertical line
      return this.clearAndDrawAnnotation(axisY, pixelX);
    },

    async loadFrameBitmap(url) {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error('Failed to load frame preview.');
      }
      const blob = await response.blob();
      return createImageBitmap(blob);
    },

    /**
     * plot the video timeline with laplacian variance value
     */
    plotTimeline(frames) {
      /* chartjs starts */
      let pixelX;
      let dataX;
      let axisY;
       let selectedFrameIndex = 0;
      let hasSelected = false;
      let isDragging = false;
      chart = new Chart(timelineCanvas.value, {
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
                  const annotCtx = annotCanvas.value.getContext('2d', {
                    willReadFrequently: true,
                  });
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
              if (annotCanvas.value) {
                if (annotCanvas.value.width !== args.size.width) {
                  annotCanvas.value.width = args.size.width;
                  annotCanvas.value.style.width = args.size.width + 'px';
                }
                if (annotCanvas.value.height !== args.size.height) {
                  annotCanvas.value.height = args.size.height;
                  annotCanvas.value.style.height = args.size.height + 'px';
                }
              }
            },
            afterRender: (chart, args, options) => {
              if (restartBtn.value.style.display !== 'block') {
                // update restart button
                restartBtn.value.onclick = () => {
                  restartBtn.value.style.display = 'none';
                  framesStore.actions.clearFrames();

                  this.goHome();
                }
                restartBtn.value.style.display = 'block';
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
              selectedFrameIndex = frames[dataX].index;

              if (eventType === 'mousedown' || eventType === 'touchstart') {
                isDragging = true;
                // show selected
                this.updateFrameAndAnnotation(selectedFrameIndex, axisY, pixelX)
                  .then((ok) => {
                    hasSelected = ok;
                  })
                  .catch((err) => {
                    console.error(err);
                  });
              } else if (
                eventType === 'mouseup' ||
                eventType === 'touchend' ||
                eventType === 'mouseleave'
              ) {
                isDragging = false;

                // update download button
                if (hasSelected) {
                  downloadBtn.value.onclick = () => {
                    const jobId = framesStore.getters.getJobId();
                    if (!jobId) {
                      return;
                    }
                    const downloadLink = document.createElement('a');
                    downloadLink.href = buildFrameDownloadUrl(jobId, selectedFrameIndex);
                    downloadLink.click();
                  }
                  if (downloadBtn.value.style.display !== 'block') {
                    downloadBtn.value.style.display = 'block';
                  }
                }

                if (eventType !== 'mouseleave') {
                  // draw selected frame vertical line
                  this.clearAndDrawAnnotation(axisY, pixelX);
                }
              } else if (eventType === 'mousemove' || eventType === 'touchmove') {
                if (isDragging) {
                  // show selected
                  this.updateFrameAndAnnotation(selectedFrameIndex, axisY, pixelX)
                    .then((ok) => {
                      hasSelected = ok;
                    })
                    .catch((err) => {
                      console.error(err);
                    });
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
      blobStore.actions.clearBlob();
      this.$router.replace({ name: 'Home' });
    }
  }
}
</script>

<style scoped>
#chart-wrapper {
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
  height: min-content;
  width: 100%;
  justify-content: center;
  z-index: 4;
}

#download-btn {
  display: none;
  padding: 5px 10px;
  margin: 8px 0;
  border: none;
  outline: none;
  background: var(--primary-color);
  color: var(--background-color);
  border-radius: 5px;
  cursor: pointer;
  width: min-content;
}

#reset-zoom-btn {
  display: none;
  width: 30px;
  padding: 0;
  /* padding: 5px 10px; */
  margin: 8px 0;
  border: none;
  outline: none;
  background: var(--primary-color);
  color: var(--background-color);
  border-radius: 5px;
  cursor: pointer;
  /* width: min-content; */
}

#restart-btn {
  display: none;
  padding: 5px 10px;
  margin: 8px 0;
  border: none;
  outline: none;
  background: var(--primary-color);
  color: var(--background-color);
  border-radius: 5px;
  cursor: pointer;
  width: min-content;
}

#controls>* {
  margin: 0 5px 4vw;
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