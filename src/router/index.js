import { createRouter, createWebHistory } from "vue-router";
import UploadFile from "@/components/UploadFile.vue";
import HelloWorld from "@/components/HelloWorld.vue";
import ChartResult from "@/components/ChartResult.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "Home",
      component: UploadFile,
    },
    {
      path: "/result",
      name: "Result",
      component: ChartResult,
    },
    {
      path: "/hello",
      name: "Hello",
      component: HelloWorld,
    },
    {
      path: "/:pathMatch(.*)*",
      name: "NotFound",
      redirect: "/",
    },
  ],
});

export default router;
