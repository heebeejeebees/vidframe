import { createApp } from "vue";
import router from "./router";
import App from "./App.vue";
import { blobStore, framesStore } from "./store";
import "@coreui/coreui/dist/css/coreui.min.css";

const app = createApp(App);

app.use(router);

blobStore.actions.initializeBlob();
framesStore.actions.initializeFrames();

app.mount("#app");
