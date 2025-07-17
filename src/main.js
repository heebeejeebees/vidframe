import { createApp } from "vue";
import router from "./router";
import App from "./App.vue";
import { blobStore, framesStore } from "./store";

const app = createApp(App).use(router);

blobStore.actions.initializeBlob();
framesStore.actions.initializeFrames();

app.mount("#app");
