import { createRouter, createWebHistory } from "vue-router";
import UploadFile from "@/components/UploadFile.vue";
import HelloWorld from "@/components/HelloWorld.vue";
import ChartResult from "@/components/ChartResult.vue";

const router = createRouter({
  history: createWebHistory(""),
  routes: [
    {
      path: "/",
      name: "home",
      component: UploadFile,
      children: [
        {
          path: '/result',
          component: ChartResult
        }
      ]
    },
    {
      path: "/hello",
      name: "hello",
      component: HelloWorld,
    },
  ],
});

export default router;
