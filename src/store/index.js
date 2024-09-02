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
  },
};

export default blobStore;
