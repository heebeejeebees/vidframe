import { reactive } from "vue";

const blobStore = {
  state: reactive({
    blob: null,
  }),
  getters: {
    getBlob() {
      return blobStore.state.blob;
    },
  },
  mutations: {
    setBlob(blob) {
      blobStore.state.blob = blob;
    },
  },
  actions: {
    initializeBlob() {
      blobStore.state.blob = new Blob();
    },
    clearBlob() {
      blobStore.state.blob = null;
    },
  },
};

const framesStore = {
  state: reactive({
    frames: null,
  }),
  getters: {
    getFrames() {
      return framesStore.state.frames;
    },
  },
  mutations: {
    setFrames(frames) {
      framesStore.state.frames = frames;
    },
  },
  actions: {
    initializeFrames() {
      framesStore.state.frames = [];
    },
    addFrames(index, bitmap, lapVar, timestamp, timestamp_ms) {
      framesStore.state.frames.push({
        index,
        bitmap,
        data: {
          laplacian_variance: lapVar,
        },
        timestamp,
        timestamp_microseconds: timestamp_ms,
      });
    },
    clearFrames() {
      framesStore.state.frames = [];
    },
  },
};

export { blobStore, framesStore };
