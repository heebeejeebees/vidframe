import { createApp } from "vue";
import router from "./router";
import App from "./App.vue";

const app = createApp(App).use(router);

// app.config.globalProperties.file = new Blob();

app.mount("#app");
