import { createRouter, createWebHistory } from "vue-router";
import HelloWorld from "@/components/HelloWorld.vue";
import ChartResult from "@/components/ChartResult.vue";
import ProcessFile from "@/components/ProcessFile.vue";
import Home from "@/components/Home.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "Home",
      component: Home,
    },
    {
      path: "/process",
      name: "Process",
      component: ProcessFile,
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
