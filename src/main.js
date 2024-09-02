import { createApp } from "vue";
import router from "./router";
import App from "./App.vue";
import blobStore from "./store";

const app = createApp(App).use(router);

blobStore.actions.initializeBlob();
// app.config.globalProperties.file = new Blob();

app.mount("#app");
